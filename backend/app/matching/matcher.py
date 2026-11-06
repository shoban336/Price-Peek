"""Product matching engine: String similarity, attribute matching, and strict unit separation."""
import re
from typing import List, Optional
from rapidfuzz import fuzz

from app.schemas.search_schema import ParsedQuery, ProductListing
from app.connectors.base_connector import RawProductListing
from app.intelligence.units import parse_and_normalize_unit, is_unit_equivalent
from app.intelligence.variants import extract_variants
from app.intelligence.brands import detect_brand


def compute_similarity(query: str, target: str) -> float:
    """Compute token-based string similarity score between 0.0 and 1.0."""
    if not query or not target:
        return 0.0
    token_set = fuzz.token_set_ratio(query.lower(), target.lower())
    token_sort = fuzz.token_sort_ratio(query.lower(), target.lower())
    # Weighted average favoring token presence
    score = (token_set * 0.6 + token_sort * 0.4) / 100.0
    return round(score, 3)


def matches_product(
    parsed_query: ParsedQuery,
    listing: RawProductListing,
    threshold: float = 0.55
) -> bool:
    """Validate whether an extracted listing matches the target user query.
    
    Strict rules enforced:
    1. Quantity & Unit dimension must match (e.g. 1000ml matches 1L, but strictly rejects 500ml or 5L).
    2. Specific variants (e.g. 128GB vs 256GB) must not collide.
    3. Distinct brands must not mismatch.
    4. Text similarity score must meet minimum threshold.
    """
    listing_title = listing.title.strip()

    # 1. Normalize listing unit if not pre-populated
    listing_qty = listing.normalized_quantity
    listing_unit = listing.normalized_unit
    if listing_qty is None and listing_unit is None:
        extracted = parse_and_normalize_unit(listing_title)
        if extracted:
            listing_qty = extracted.normalized_value
            listing_unit = extracted.canonical_unit

    # Enforce strict unit equivalence if user requested a specific package quantity
    if parsed_query.normalized_quantity is not None and parsed_query.normalized_unit is not None:
        if not is_unit_equivalent(
            parsed_query.normalized_quantity, parsed_query.normalized_unit,
            listing_qty, listing_unit
        ):
            return False

    # 2. Variant / Specification verification (e.g. Storage, Footwear size)
    listing_variants = extract_variants(listing_title)
    if parsed_query.normalized_unit == "GB" and parsed_query.normalized_quantity:
        # Check storage separation (e.g. 128GB vs 256GB)
        if listing_qty and abs(listing_qty - parsed_query.normalized_quantity) > 0.01:
            return False

    # 3. Brand consistency check
    if parsed_query.brand:
        listing_brand, _ = detect_brand(listing_title)
        # If listing has an identifiable brand that conflicts with user's requested brand, reject
        if listing_brand and listing_brand.lower() != parsed_query.brand.lower():
            # Check if brand is just a substring difference
            if parsed_query.brand.lower() not in listing_title.lower():
                return False

    # 4. Model check (if specified)
    if parsed_query.model:
        if parsed_query.model.lower() not in listing_title.lower():
            return False

    # 5. Fuzzy string similarity check on core product name
    score = compute_similarity(parsed_query.product_name, listing_title)
    return score >= threshold


def filter_and_normalize_listings(
    parsed_query: ParsedQuery,
    raw_listings: List[RawProductListing],
    threshold: float = 0.55
) -> List[ProductListing]:
    """Filter raw platform listings against strict matching criteria and convert to standardized schemas."""
    matched: List[ProductListing] = []

    for raw in raw_listings:
        if matches_product(parsed_query, raw, threshold=threshold):
            # Ensure quantity and unit are populated
            qty = raw.normalized_quantity
            unit = raw.normalized_unit
            if qty is None and unit is None:
                parsed_u = parse_and_normalize_unit(raw.title)
                if parsed_u:
                    qty = parsed_u.normalized_value
                    unit = parsed_u.canonical_unit

            matched.append(
                ProductListing(
                    platform_id=raw.platform_id,
                    platform_name=raw.platform_name,
                    platform_category=raw.platform_category,
                    title=raw.title,
                    brand=raw.brand or parsed_query.brand,
                    price=raw.price,
                    original_price=raw.original_price,
                    discount_percent=raw.discount_percent,
                    currency=raw.currency,
                    in_stock=raw.in_stock,
                    rating=raw.rating,
                    rating_count=raw.rating_count,
                    product_url=raw.product_url,
                    deep_link_url=raw.deep_link_url,
                    image_url=raw.image_url,
                    normalized_quantity=qty,
                    normalized_unit=unit,
                    variant=raw.variant or parsed_query.variant,
                    is_live=raw.is_live,
                    delivery_pin=raw.delivery_pin,
                    delivery_time_estimate=raw.delivery_time_estimate,
                )
            )

    return matched
