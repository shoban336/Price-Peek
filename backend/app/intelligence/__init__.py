"""Product Intelligence package for PricePeek."""
from .parser import parse_query
from .units import parse_and_normalize_unit, is_unit_equivalent, NormalizedQuantity
from .variants import extract_variants, format_variant_string
from .brands import detect_brand, classify_category

__all__ = [
    "parse_query",
    "parse_and_normalize_unit",
    "is_unit_equivalent",
    "NormalizedQuantity",
    "extract_variants",
    "format_variant_string",
    "detect_brand",
    "classify_category",
]
