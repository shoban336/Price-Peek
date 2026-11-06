"""Universal query parsing and product attribute extractor.
Parses any unstructured product search into structured components:
- Brand
- Product Name / Title
- Category
- Model
- Normalized Quantity and Unit
- Specific Variant
"""
import re
from typing import Optional
from app.schemas.search_schema import ParsedQuery
from app.intelligence.units import parse_and_normalize_unit
from app.intelligence.variants import extract_variants, format_variant_string
from app.intelligence.brands import detect_brand, classify_category

MODEL_PATTERNS = [
    # Specific series names first
    (r'\b(air\s*max(?:\s*\d+)?)\b', 1),
    (r'\b(pavilion|thinkpad|macbook\s*(?:air|pro)|inspiron|legion|yoga)\b', 1),
    (r'\b(?:galaxy\s*)([sza]\d{2}(?:\s*(?:ultra|plus|fe))?)\b', 1),
    # Explicit iPhone model numbering (requires "iphone" before the digit)
    (r'\b(?:iphone\s+)(\d{1,2}(?:\s*(?:pro\s*max|pro|plus|mini))?)\b', 1),
]


def extract_model(text: str) -> Optional[str]:
    """Extract model identifier if present in query."""
    for pattern, group_idx in MODEL_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(group_idx).strip().title()
    return None


def parse_query(raw_query: str) -> ParsedQuery:
    """Universal parser that transforms any free-text query into structured product attributes."""
    cleaned = raw_query.strip()
    if not cleaned:
        return ParsedQuery(
            raw_query="",
            brand=None,
            product_name="",
            category=None,
            model=None,
            normalized_quantity=None,
            normalized_unit=None,
            variant=None,
        )

    # 1. Extract Unit and Quantity (e.g., 1L, 1000ml, 500g, 256GB)
    unit_result = parse_and_normalize_unit(cleaned)
    normalized_qty = unit_result.normalized_value if unit_result else None
    normalized_unit = unit_result.canonical_unit if unit_result else None

    # 2. Extract Variants (Color, RAM, Apparel/Shoe Size, Formulation)
    variants = extract_variants(cleaned)
    variant_str = format_variant_string(variants)

    # 3. Detect Brand and strip brand from remaining tokens
    brand, remaining_query = detect_brand(cleaned)

    # 4. Detect Model
    model = extract_model(cleaned)

    # 5. Classify Category
    category = classify_category(cleaned)

    # 6. Refine product name by stripping extracted unit text to prevent redundant tokens
    clean_name = remaining_query
    if unit_result:
        clean_name = re.sub(re.escape(unit_result.original_text), '', clean_name, flags=re.IGNORECASE)

    # Clean whitespace and trailing punctuation
    clean_name = re.sub(r'[\s\-_]+', ' ', clean_name).strip()
    if not clean_name:
        clean_name = cleaned

    return ParsedQuery(
        raw_query=cleaned,
        brand=brand,
        product_name=clean_name,
        category=category.value if category else None,
        model=model,
        normalized_quantity=normalized_qty,
        normalized_unit=normalized_unit,
        variant=variant_str,
    )
