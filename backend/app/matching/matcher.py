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
    
    Strict zero-tolerance rules enforced:
    1. Quantity & Unit dimension must match (e.g. 1000ml matches 1L, but strictly rejects 500ml, 750ml, or 5L).
    2. Specific variants (e.g. 128GB vs 256GB, Black vs Blue/Pink) must not collide.
    3. Distinct models (e.g. iPhone 15 vs iPhone 15 Pro / iPhone 15 Plus) must not collide.
    4. Pack multipliers (e.g. Pack of 1 vs Pack of 2 or combo bundles) must not collide.
    5. Distinct brands must not mismatch.
    6. Listing must be in stock.
    7. Text similarity score must meet minimum threshold.
    """
    # Reject out of stock items immediately
    if not listing.in_stock:
        return False

    listing_title = listing.title.strip()
    listing_variants = extract_variants(listing_title)

    # 1. Normalize listing unit if not pre-populated
    listing_qty = listing.normalized_quantity
    listing_unit = listing.normalized_unit
    if listing_qty is None and listing_unit is None:
        extracted = parse_and_normalize_unit(listing_title)
        if extracted:
            listing_qty = extracted.normalized_value
            listing_unit = extracted.canonical_unit

    # 1a. Strict Volume & Weight Quantity / Unit equivalence
    if parsed_query.normalized_quantity is not None and parsed_query.normalized_unit is not None:
        # If user searched/pasted a strict unit and listing has no identifiable unit
        if listing_qty is None or listing_unit is None:
            if parsed_query.is_url_query:
                return False
        else:
            if not is_unit_equivalent(
                parsed_query.normalized_quantity, parsed_query.normalized_unit,
                listing_qty, listing_unit
            ):
                return False

        # Additional regex scan on listing title to catch conflicting volume/weight numbers
        if parsed_query.normalized_unit == "L":
            target_ml = round(parsed_query.normalized_quantity * 1000)
            for m in re.finditer(r'\b(\d+)\s*ml\b', listing_title, re.IGNORECASE):
                if int(m.group(1)) != target_ml:
                    return False
            for m in re.finditer(r'\b(\d+(?:\.\d+)?)\s*(?:l|litre|litres)\b', listing_title, re.IGNORECASE):
                val_l = float(m.group(1))
                if abs(val_l - parsed_query.normalized_quantity) > 0.01:
                    return False
        elif parsed_query.normalized_unit == "kg":
            target_g = round(parsed_query.normalized_quantity * 1000)
            for m in re.finditer(r'\b(\d+)\s*(?:g|gm|gms)\b', listing_title, re.IGNORECASE):
                if int(m.group(1)) != target_g:
                    return False
            for m in re.finditer(r'\b(\d+(?:\.\d+)?)\s*(?:kg|kgs|kilogram)\b', listing_title, re.IGNORECASE):
                val_kg = float(m.group(1))
                if abs(val_kg - parsed_query.normalized_quantity) > 0.01:
                    return False

    # 2. Strict Storage Equivalence (e.g. 128GB vs 256GB vs 512GB)
    locked_storage = parsed_query.locked_storage
    if not locked_storage and parsed_query.normalized_unit == "GB" and parsed_query.normalized_quantity:
        locked_storage = f"{int(parsed_query.normalized_quantity) if parsed_query.normalized_quantity.is_integer() else parsed_query.normalized_quantity}GB"

    if locked_storage:
        norm_target_storage = locked_storage.upper().replace(" ", "")
        listing_storage = listing_variants.get('storage')
        if listing_storage and listing_storage.upper().replace(" ", "") != norm_target_storage:
            return False

        # Check for any conflicting storage capacity in listing title
        for sm in re.finditer(r'\b(\d+\s*(?:GB|TB))\b', listing_title, re.IGNORECASE):
            cand = sm.group(1).upper().replace(" ", "")
            if listing_variants.get('ram') and cand == listing_variants['ram']:
                continue
            if cand != norm_target_storage:
                return False

        if parsed_query.is_url_query and norm_target_storage not in listing_title.upper().replace(" ", ""):
            return False

    # 3. Strict Color Equivalence (e.g. Black vs Blue, Pink, Starlight, Yellow)
    if parsed_query.locked_color:
        target_color = parsed_query.locked_color.strip().lower()
        listing_color = listing_variants.get('color')
        if listing_color and listing_color.strip().lower() != target_color:
            return False

        # Scan for conflicting recognized colors in title
        from app.intelligence.variants import COLOR_PATTERNS
        for pat in COLOR_PATTERNS:
            for cm in re.finditer(pat, listing_title, re.IGNORECASE):
                found_col = cm.group(0).strip().lower()
                if found_col != target_color:
                    return False

        if parsed_query.is_url_query:
            if target_color not in listing_title.lower() and (not listing_color or listing_color.strip().lower() != target_color):
                return False

    # 4. Strict Sub-Model and Series Collision Prevention (e.g. iPhone 15 vs iPhone 15 Plus/Pro)
    query_lower = parsed_query.raw_query.lower()
    is_iphone = "iphone" in query_lower or (parsed_query.brand and parsed_query.brand.lower() == "apple" and "iphone" in parsed_query.product_name.lower())
    if is_iphone:
        target_has_pro = "pro" in query_lower
        target_has_plus = "plus" in query_lower
        target_has_max = "max" in query_lower
        target_has_mini = "mini" in query_lower

        listing_has_pro = bool(re.search(r'\bpro\b', listing_title, re.IGNORECASE))
        listing_has_plus = bool(re.search(r'\bplus\b', listing_title, re.IGNORECASE))
        listing_has_max = bool(re.search(r'\bmax\b', listing_title, re.IGNORECASE))
        listing_has_mini = bool(re.search(r'\bmini\b', listing_title, re.IGNORECASE))

        if not target_has_pro and listing_has_pro:
            return False
        if not target_has_plus and listing_has_plus:
            return False
        if not target_has_max and listing_has_max:
            return False
        if not target_has_mini and listing_has_mini:
            return False

        if target_has_pro and not listing_has_pro:
            return False
        if target_has_plus and not listing_has_plus:
            return False

    # 5. Strict Pack Multiplier Equivalence (e.g. Pack of 1 vs Pack of 2 or combo bundles)
    if parsed_query.locked_pack:
        target_pack = parsed_query.locked_pack
        listing_pack = listing_variants.get('pack')
        if listing_pack and listing_pack != target_pack:
            return False
        if target_pack == 1:
            # Strictly reject multi-pack indicators
            if re.search(r'\b(?:pack\s+of\s+[2-9]\d*|combo\s+of\s+[2-9]\d*|set\s+of\s+[2-9]\d*|[2-9]\s*pack)\b', listing_title, re.IGNORECASE):
                return False
        elif target_pack > 1:
            if not re.search(rf'\b(?:pack\s+of\s+{target_pack}|combo\s+of\s+{target_pack}|set\s+of\s+{target_pack}|{target_pack}\s*pack)\b', listing_title, re.IGNORECASE):
                return False

    # 6. Brand consistency check
    if parsed_query.brand:
        listing_brand, _ = detect_brand(listing_title)
        # If listing has an identifiable brand that conflicts with user's requested brand, reject
        if listing_brand and listing_brand.lower() != parsed_query.brand.lower():
            if parsed_query.brand.lower() not in listing_title.lower():
                return False

    # 7. Model check (if specified)
    if parsed_query.model:
        if parsed_query.model.lower() not in listing_title.lower():
            return False

    # 8. Fuzzy string similarity check on core product name
    target_text = f"{parsed_query.brand} {parsed_query.product_name}".strip() if parsed_query.brand and parsed_query.brand.lower() not in parsed_query.product_name.lower() else parsed_query.product_name
    score = max(compute_similarity(target_text, listing_title), compute_similarity(parsed_query.product_name, listing_title))
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
