"""Database CRUD and price persistence service."""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models import Product, Platform, ProductListingRecord, PriceHistoryRecord
from app.schemas.search_schema import ParsedQuery, ProductListing
from app.registry import registry


def sync_platforms_to_db(db: Session) -> None:
    """Ensure all dynamically registered platform connectors are mirrored in the database."""
    schemas = registry.get_schemas(enabled_only=False)
    for s in schemas:
        existing = db.query(Platform).filter(Platform.id == s.id).first()
        if not existing:
            new_p = Platform(
                id=s.id,
                name=s.name,
                category=s.category.value,
                domain=s.domain,
                enabled=s.enabled,
                status=s.status.value,
                requires_pin=s.requires_pin,
                logo_url=s.logo_url,
                app_scheme=s.app_scheme,
                description=s.description,
            )
            db.add(new_p)
        else:
            existing.status = s.status.value
            existing.enabled = s.enabled
    db.commit()


def get_or_create_product(db: Session, parsed: ParsedQuery) -> Product:
    """Find existing product entity matching canonical attributes or insert a new record."""
    unit_str = f" {parsed.normalized_quantity:g}{parsed.normalized_unit}" if parsed.normalized_quantity and parsed.normalized_unit else ""
    brand_prefix = f"{parsed.brand} " if parsed.brand else ""
    canonical = f"{brand_prefix}{parsed.product_name}{unit_str}".strip()

    product = (
        db.query(Product)
        .filter(Product.canonical_name.ilike(canonical))
        .first()
    )
    if not product:
        product = Product(
            canonical_name=canonical,
            brand=parsed.brand,
            category=parsed.category,
            model=parsed.model,
            normalized_quantity=parsed.normalized_quantity,
            normalized_unit=parsed.normalized_unit,
            variant=parsed.variant,
        )
        db.add(product)
        db.commit()
        db.refresh(product)
    return product


def persist_search_listings(db: Session, parsed: ParsedQuery, listings: List[ProductListing]) -> Product:
    """Store matched listings and append price history datapoints."""
    sync_platforms_to_db(db)
    product = get_or_create_product(db, parsed)
    now = datetime.utcnow()

    for item in listings:
        # Update or create platform listing record
        rec = (
            db.query(ProductListingRecord)
            .filter(
                ProductListingRecord.product_id == product.id,
                ProductListingRecord.platform_id == item.platform_id
            )
            .first()
        )
        if not rec:
            rec = ProductListingRecord(
                product_id=product.id,
                platform_id=item.platform_id,
                title=item.title,
                price=item.price,
                original_price=item.original_price,
                discount_percent=item.discount_percent,
                product_url=item.product_url,
                deep_link_url=item.deep_link_url,
                image_url=item.image_url,
                in_stock=item.in_stock,
                rating=item.rating,
                delivery_pin=item.delivery_pin,
                updated_at=now,
            )
            db.add(rec)
        else:
            rec.price = item.price
            rec.original_price = item.original_price
            rec.discount_percent = item.discount_percent
            rec.in_stock = item.in_stock
            rec.updated_at = now

        # Append to historical timeline
        history_entry = PriceHistoryRecord(
            product_id=product.id,
            platform_id=item.platform_id,
            price=item.price,
            timestamp=now
        )
        db.add(history_entry)

    db.commit()
    return product


def fetch_price_history_records(
    db: Session,
    product_identifier: str,
    days: int = 30
) -> List[dict]:
    """Retrieve historical price movements for product by ID or title match."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Try by numeric ID
    product = None
    if product_identifier.isdigit():
        product = db.query(Product).filter(Product.id == int(product_identifier)).first()
    if not product:
        # Search by name match
        product = (
            db.query(Product)
            .filter(Product.canonical_name.ilike(f"%{product_identifier.replace('-', ' ')}%"))
            .first()
        )

    if not product:
        return []

    entries = (
        db.query(PriceHistoryRecord, Platform.name)
        .join(Platform, PriceHistoryRecord.platform_id == Platform.id)
        .filter(
            PriceHistoryRecord.product_id == product.id,
            PriceHistoryRecord.timestamp >= cutoff
        )
        .order_by(PriceHistoryRecord.timestamp.asc())
        .all()
    )

    history_points = []
    for record, platform_name in entries:
        history_points.append({
            "date": record.timestamp,
            "platform_id": record.platform_id,
            "platform_name": platform_name,
            "price": record.price,
        })

    return history_points
