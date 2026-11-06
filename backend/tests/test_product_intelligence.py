"""Test suite for Phase 3 – Product Intelligence and Unit Normalization."""
import pytest
from app.intelligence import (
    parse_query,
    parse_and_normalize_unit,
    is_unit_equivalent,
    extract_variants,
    detect_brand,
    classify_category,
)


def test_unit_normalization_volume():
    """Verify milliliters and liters normalize to identical canonical values."""
    u1 = parse_and_normalize_unit("Gold Winner Sunflower Oil 1L")
    assert u1 is not None
    assert u1.canonical_unit == "L"
    assert u1.normalized_value == 1.0

    u2 = parse_and_normalize_unit("Gold Winner Sunflower Oil 1000ml")
    assert u2 is not None
    assert u2.canonical_unit == "L"
    assert u2.normalized_value == 1.0

    u3 = parse_and_normalize_unit("Fortune Oil 500 ml")
    assert u3 is not None
    assert u3.canonical_unit == "L"
    assert u3.normalized_value == 0.5


def test_unit_equivalence_strictness():
    """Verify strict matching: 1000ml equals 1L, but strictly rejects 500ml or 5L."""
    # 1000ml == 1L
    assert is_unit_equivalent(1.0, "L", 1.0, "L") is True
    # 500ml (0.5L) != 1L (1.0L)
    assert is_unit_equivalent(0.5, "L", 1.0, "L") is False
    # 5L (5.0L) != 1L (1.0L)
    assert is_unit_equivalent(5.0, "L", 1.0, "L") is False
    # 128GB != 256GB
    assert is_unit_equivalent(128.0, "GB", 256.0, "GB") is False
    # 1000g == 1kg
    assert is_unit_equivalent(1.0, "kg", 1.0, "kg") is True
    # Incompatible dimensions (1L vs 1kg)
    assert is_unit_equivalent(1.0, "L", 1.0, "kg") is False


def test_grocery_query_parsing():
    """Verify parsing of grocery queries."""
    parsed = parse_query("Gold Winner Sunflower Oil 1L")
    assert parsed.brand == "Gold Winner"
    assert "Sunflower Oil" in parsed.product_name
    assert parsed.category == "grocery"
    assert parsed.normalized_unit == "L"
    assert parsed.normalized_quantity == 1.0


def test_electronics_query_parsing():
    """Verify parsing of tech specs, storage, and models."""
    parsed = parse_query("Apple iPhone 15 256GB Natural Titanium")
    assert parsed.brand == "Apple"
    assert parsed.category == "electronics"
    assert parsed.model == "15"
    assert parsed.normalized_unit == "GB"
    assert parsed.normalized_quantity == 256.0
    assert "Natural Titanium" in str(parsed.variant) or "Titanium" in str(parsed.variant)


def test_fashion_query_parsing():
    """Verify footwear size and fashion brand extraction."""
    parsed = parse_query("Nike Air Max shoes UK 9")
    assert parsed.brand == "Nike"
    assert parsed.category == "fashion"
    assert "Air Max" in str(parsed.model)
    assert "UK 9" in str(parsed.variant)


def test_beauty_query_parsing():
    """Verify shampoo volume and formulation parsing."""
    parsed = parse_query("Dove Intense Repair Shampoo 650ml")
    assert parsed.brand == "Dove"
    assert parsed.category == "beauty"
    assert parsed.normalized_unit == "L"
    assert parsed.normalized_quantity == 0.65
    assert "Intense Repair" in str(parsed.variant)


def test_pharmacy_query_parsing():
    """Verify medicine query classification."""
    parsed = parse_query("Dolo 650 tablets strip")
    assert parsed.brand == "Dolo"
    assert parsed.category == "pharmacy"


def test_arbitrary_unlisted_product_parsing():
    """Verify universal capability on arbitrary queries without hardcoding."""
    parsed = parse_query("Quantum Dynamics Wireless Mouse 5000 DPI")
    assert parsed.brand == "Quantum"
    assert "Wireless Mouse 5000 DPI" in parsed.product_name
