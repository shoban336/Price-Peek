"""Product variant identification and extraction.
Extracts colors, tech specifications (RAM/Storage), footwear/clothing sizes, and formulation variants.
"""
import re
from typing import Optional, Dict, List, Any

# Common color identifiers
COLOR_PATTERNS = [
    r'\b(?:black|space\s+gray|space\s+black|titanium|natural\s+titanium|white|silver|gold|rose\s+gold|blue|midnight|starlight|red|green|purple|yellow|pink|orange|navy|grey|gray)\b'
]

# Tech specifications
RAM_PATTERN = r'\b(\d+\s*gb)\s*(?:ram|memory)\b'
STORAGE_PATTERN = r'\b(\d+\s*(?:gb|tb))\s*(?:storage|rom|ssd|internal)?\b'

# Footwear / Apparel sizes
SHOE_SIZE_PATTERN = r'\b(?:uk|us|eu)\s*(\d+(?:\.\d+)?)\b'
APPAREL_SIZE_PATTERN = r'\b(?:size\s+)?(xxl|xxxl|xs|s|m|l|xl)\b'

# Formulation / Edition variants
FORMULATION_PATTERNS = [
    r'\b(?:sugar\s*free|zero\s*sugar|diet)\b',
    r'\b(?:extra\s*virgin|refined|cold\s*pressed)\b',
    r'\b(?:anti\s*dandruff|hair\s*fall\s*control|intense\s*repair|daily\s*shine)\b',
]


def extract_variants(text: str) -> Dict[str, Any]:
    """Extract all recognizable variant attributes from product description or search query."""
    variants = {}

    # Extract Color
    for pat in COLOR_PATTERNS:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            variants['color'] = match.group(0).strip().title()
            break

    # Extract RAM
    ram_match = re.search(RAM_PATTERN, text, re.IGNORECASE)
    if ram_match:
        variants['ram'] = ram_match.group(1).upper().replace(" ", "")

    # Extract Footwear size
    shoe_match = re.search(SHOE_SIZE_PATTERN, text, re.IGNORECASE)
    if shoe_match:
        variants['shoe_size'] = shoe_match.group(0).upper()

    # Extract Apparel size
    apparel_match = re.search(APPAREL_SIZE_PATTERN, text, re.IGNORECASE)
    if apparel_match and not shoe_match:
        variants['apparel_size'] = apparel_match.group(1).upper()

    # Extract Formulations
    for f_pat in FORMULATION_PATTERNS:
        f_match = re.search(f_pat, text, re.IGNORECASE)
        if f_match:
            variants['formulation'] = f_match.group(0).title()
            break

    return variants


def format_variant_string(variants: Dict[str, Any]) -> Optional[str]:
    """Format variant dictionary into a canonical composite string."""
    if not variants:
        return None
    ordered_parts = []
    for k in ['ram', 'shoe_size', 'apparel_size', 'color', 'formulation']:
        if k in variants:
            ordered_parts.append(str(variants[k]))
    return " | ".join(ordered_parts) if ordered_parts else None
