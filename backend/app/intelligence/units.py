"""Universal measurement unit normalization and equivalence validation.
Strict rule: 1000ml matches 1L, but NEVER matches 500ml or 5L.
"""
import re
from typing import Optional, NamedTuple


class NormalizedQuantity(NamedTuple):
    normalized_value: float
    canonical_unit: str
    original_text: str


# Canonical units:
# Volume -> 'L' (liters)
# Mass/Weight -> 'kg' (kilograms)
# Digital Storage -> 'GB' (gigabytes)
# Count/Pieces -> 'pack' or 'pcs'

UNIT_CONVERSION_MAP = {
    # Volume -> Canonical 'L'
    'l': ('L', 1.0),
    'litre': ('L', 1.0),
    'litres': ('L', 1.0),
    'liter': ('L', 1.0),
    'liters': ('L', 1.0),
    'ltr': ('L', 1.0),
    'ltrs': ('L', 1.0),
    'ml': ('L', 0.001),
    'millilitre': ('L', 0.001),
    'millilitres': ('L', 0.001),
    'milliliter': ('L', 0.001),
    'milliliters': ('L', 0.001),
    
    # Weight -> Canonical 'kg'
    'kg': ('kg', 1.0),
    'kgs': ('kg', 1.0),
    'kilogram': ('kg', 1.0),
    'kilograms': ('kg', 1.0),
    'g': ('kg', 0.001),
    'gm': ('kg', 0.001),
    'gms': ('kg', 0.001),
    'gram': ('kg', 0.001),
    'grams': ('kg', 0.001),
    'mg': ('kg', 0.000001),
    'milligram': ('kg', 0.000001),
    'milligrams': ('kg', 0.000001),

    # Storage -> Canonical 'GB'
    'gb': ('GB', 1.0),
    'gigabyte': ('GB', 1.0),
    'gigabytes': ('GB', 1.0),
    'tb': ('GB', 1024.0),
    'terabyte': ('GB', 1024.0),
    'terabytes': ('GB', 1024.0),
    'mb': ('GB', 0.0009765625),

    # Count/Pack
    'pack': ('pack', 1.0),
    'packs': ('pack', 1.0),
    'piece': ('pcs', 1.0),
    'pieces': ('pcs', 1.0),
    'pc': ('pcs', 1.0),
    'pcs': ('pcs', 1.0),
    'strip': ('strip', 1.0),
    'strips': ('strip', 1.0),
    'tablets': ('tablets', 1.0),
    'capsules': ('capsules', 1.0),
}

# Regex to detect value and unit in titles (e.g. "1L", "1000 ml", "500g", "256 GB", "pack of 3", "750-ml")
UNIT_REGEX = re.compile(
    r'\b(?:(?:pack\s+of\s+(\d+))|(\d+(?:\.\d+)?)[\s\-]*([a-zA-Z]+))\b',
    re.IGNORECASE
)


def parse_and_normalize_unit(text: str) -> Optional[NormalizedQuantity]:
    """Parse text and extract the first valid physical/tech unit, normalized to canonical standard."""
    if not text:
        return None

    # Search for physical/tech/count units first
    pack_fallback = None
    for match in UNIT_REGEX.finditer(text):
        pack_val, num_val, unit_val = match.groups()
        if pack_val and not pack_fallback:
            pack_fallback = NormalizedQuantity(float(pack_val), 'pack', match.group(0))
        if num_val and unit_val:
            clean_unit = unit_val.lower().strip()
            if clean_unit in UNIT_CONVERSION_MAP and clean_unit not in ['pack', 'packs']:
                raw_number = float(num_val)
                # Differentiate dosage strength (e.g. 500/650 in Dolo 650) from packaging count of tablets
                if clean_unit in ['tablets', 'capsules'] and raw_number >= 50:
                    continue
                canonical, multiplier = UNIT_CONVERSION_MAP[clean_unit]
                normalized = round(raw_number * multiplier, 4)
                return NormalizedQuantity(
                    normalized_value=normalized,
                    canonical_unit=canonical,
                    original_text=match.group(0)
                )

    # Fallback to pack multiplier only if no physical weight/volume/tech unit exists
    pack_match = re.search(r'\bpack\s+of\s+(\d+)\b', text, re.IGNORECASE)
    if pack_match:
        return NormalizedQuantity(
            normalized_value=float(pack_match.group(1)),
            canonical_unit='pack',
            original_text=pack_match.group(0)
        )
    if pack_fallback:
        return pack_fallback

    return None


def is_unit_equivalent(
    qty1: Optional[float], unit1: Optional[str],
    qty2: Optional[float], unit2: Optional[str],
    tolerance: float = 0.005
) -> bool:
    """Validate whether two normalized unit quantities represent the exact same product package.
    
    Returns:
        True if units and amounts match (e.g., 1000ml == 1L).
        False if quantities or unit dimensions differ (e.g. 1L != 500ml, 128GB != 256GB).
    """
    if qty1 is None and qty2 is None and unit1 is None and unit2 is None:
        # Neither specified a unit; allowed to match by title
        return True

    if (qty1 is None or qty2 is None) or (unit1 is None or unit2 is None):
        # One has a strict unit and the other does not -> Reject to prevent cross-size pollution
        return False

    if unit1.lower() != unit2.lower():
        # Different canonical dimensions (e.g., kg vs L, or GB vs kg)
        return False

    # Check numeric equality within small floating-point tolerance
    return abs(qty1 - qty2) <= tolerance
