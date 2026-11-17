"""Product variant identification and extraction.
Extracts colors, tech specifications (RAM/Storage), footwear/clothing sizes, packaging, and formulation variants.
"""
import re
from typing import Optional, Dict, List, Any

# Common color identifiers (longest/specific phrases first)
COLOR_PATTERNS = [
    r'\b(?:awesome\s+lavender|awesome\s+lilac|awesome\s+iceblue|awesome\s+navy|awesome\s+lemon|awesome\s+violet|awesome\s+graphite|awesome\s+lime|awesome\s+silver|awesome\s+black|awesome\s+white|awesome\s+mint|awesome\s+peach|lavender|lilac|violet|lime|graphite|cream|mint|emerald|cyan|magenta|burgundy|natural\s+titanium|desert\s+titanium|black\s+titanium|white\s+titanium|space\s+gray|space\s+black|rose\s+gold|cosmic\s+blue|cosmic\s+orange|midnight\s+black|starlight|midnight|black|white|silver|gold|blue|red|green|purple|yellow|pink|orange|navy|grey|gray|coral)\b'
]

# Tech specifications
RAM_PATTERN = r'\b(\d+\s*gb)\s*(?:ram|memory)\b'
STORAGE_PATTERN = r'\b(\d+\s*(?:gb|tb))\s*(?:storage|rom|ssd|internal)?\b'

# Footwear / Apparel sizes
SHOE_SIZE_PATTERN = r'\b(?:uk|us|eu)\s*(\d+(?:\.\d+)?)\b'
APPAREL_SIZE_PATTERN = r'\b(?:size\s+)?(xxl|xxxl|xs|s|m|l|xl)\b'

# Pack multiplier patterns
PACK_PATTERN = r'\b(?:pack\s+of\s+(\d+)|combo\s+of\s+(\d+)|set\s+of\s+(\d+)|(\d+)\s*pack)\b'

# Packaging types
PACKAGING_PATTERNS = [
    r'\b(pouch|bottle|can|carton|tetra\s*pack|strip|tin|jar|refill)\b'
]

# Formulation / Edition variants
FORMULATION_PATTERNS = [
    r'\b(?:sugar\s*free|zero\s*sugar|diet|original)\b',
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

    # Extract Storage (ensure it's not matching RAM)
    storage_matches = list(re.finditer(STORAGE_PATTERN, text, re.IGNORECASE))
    for sm in storage_matches:
        cand = sm.group(1).upper().replace(" ", "")
        # Avoid overriding RAM
        if 'ram' in variants and cand == variants['ram'] and not re.search(r'(?:storage|rom|ssd|internal)', sm.group(0), re.IGNORECASE):
            continue
        variants['storage'] = cand
        break

    # Extract Footwear size
    shoe_match = re.search(SHOE_SIZE_PATTERN, text, re.IGNORECASE)
    if shoe_match:
        variants['shoe_size'] = shoe_match.group(0).upper()

    # Extract Apparel size
    apparel_match = re.search(APPAREL_SIZE_PATTERN, text, re.IGNORECASE)
    if apparel_match and not shoe_match:
        variants['apparel_size'] = apparel_match.group(1).upper()

    # Extract Pack Multiplier
    pack_match = re.search(PACK_PATTERN, text, re.IGNORECASE)
    if pack_match:
        val = next(g for g in pack_match.groups() if g is not None)
        variants['pack'] = int(val)

    # Extract Packaging
    for pkg_pat in PACKAGING_PATTERNS:
        pkg_m = re.search(pkg_pat, text, re.IGNORECASE)
        if pkg_m:
            variants['packaging'] = pkg_m.group(1).strip().title()
            break

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
    for k in ['storage', 'ram', 'shoe_size', 'apparel_size', 'color', 'packaging', 'formulation']:
        if k in variants:
            ordered_parts.append(str(variants[k]))
    if 'pack' in variants and variants['pack'] > 1:
        ordered_parts.append(f"Pack of {variants['pack']}")
    return " | ".join(ordered_parts) if ordered_parts else None
