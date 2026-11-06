"""Universal query parsing and attribute extraction."""
import re
from typing import Optional, Tuple
from app.schemas.search_schema import ParsedQuery

# Standard volume and weight unit normalization patterns
UNIT_PATTERNS = [
    (r'(?i)\b(\d+(?:\.\d+)?)\s*(?:litres?|liter|ltr|l)\b', 'L', 1.0),
    (r'(?i)\b(\d+(?:\.\d+)?)\s*(?:millilitres?|milliliter|ml)\b', 'L', 0.001),
    (r'(?i)\b(\d+(?:\.\d+)?)\s*(?:kilograms?|kilogram|kg|kgs)\b', 'kg', 1.0),
    (r'(?i)\b(\d+(?:\.\d+)?)\s*(?:grams?|gram|gm|gms|g)\b', 'kg', 0.001),
    (r'(?i)\b(\d+(?:\.\d+)?)\s*(?:gb|gigabytes?)\b', 'GB', 1.0),
    (r'(?i)\b(\d+(?:\.\d+)?)\s*(?:tb|terabytes?)\b', 'GB', 1024.0),
    (r'(?i)\b(\d+(?:\.\d+)?)\s*(?:pack|pcs|pieces?|units?)\b', 'pack', 1.0),
]


def extract_unit_and_quantity(query: str) -> Tuple[Optional[float], Optional[str]]:
    """Extract and normalize quantity and standard measurement unit."""
    for pattern, target_unit, multiplier in UNIT_PATTERNS:
        match = re.search(pattern, query)
        if match:
            raw_val = float(match.group(1))
            normalized_val = round(raw_val * multiplier, 3)
            return normalized_val, target_unit
    return None, None


def parse_query(query: str) -> ParsedQuery:
    """Parse unstructured query string into structured product attributes."""
    cleaned = query.strip()
    qty, unit = extract_unit_and_quantity(cleaned)
    
    # Generic brand/category extraction logic (further enhanced in Phase 3)
    return ParsedQuery(
        raw_query=cleaned,
        brand=None,
        product_name=cleaned,
        category=None,
        model=None,
        normalized_quantity=qty,
        normalized_unit=unit,
        variant=None
    )
