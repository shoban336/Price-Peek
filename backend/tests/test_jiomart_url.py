"""Unit tests for modern JioMart /product/... URL handling and resolver formatting."""
import pytest
from app.connectors.jiomart_connector import format_jiomart_product_url, build_universal_jiomart_url


def test_format_jiomart_product_url_valid():
    """Verify modern /product/... URLs are preserved or prepended with domain."""
    full = "https://www.jiomart.com/product/gold-winner-refined-sunflower-oil-1-l-pouch-mffn5q-7533064"
    assert format_jiomart_product_url(full) == full

    rel = "/product/amul-butter-pasteurised-100-g-carton-490000073"
    assert format_jiomart_product_url(rel) == f"https://www.jiomart.com{rel}"


def test_format_jiomart_product_url_rejects_legacy_and_search():
    """Verify legacy /p/ paths, search fallbacks, and query params are strictly rejected."""
    assert format_jiomart_product_url("https://www.jiomart.com/p/groceries/dettol/12345") == ""
    assert format_jiomart_product_url("/p/electronics/phone/12345") == ""
    assert format_jiomart_product_url("https://www.jiomart.com/search/oil") == ""
    assert format_jiomart_product_url("https://www.jiomart.com/search?q=butter") == ""
    assert format_jiomart_product_url("") == ""
    assert format_jiomart_product_url(None) == ""


def test_canonical_full_product_url():
    """Verify build_universal_jiomart_url preserves modern /product/ URLs."""
    url = "https://www.jiomart.com/product/amul-butter-pasteurised-100-g-carton-490000073"
    result = build_universal_jiomart_url(raw_product_url=url)
    assert result == url


def test_relative_scraped_product_url():
    """Verify build_universal_jiomart_url prepends domain to relative /product/ paths."""
    rel = "/product/dettol-original-liquid-handwash-200-ml-mffmsl-7504743"
    result = build_universal_jiomart_url(raw_product_url=rel)
    assert result == f"https://www.jiomart.com{rel}"


def test_removes_decimal_units():
    # 0.1kg should be stripped, resulting in clean path search without broken decimal
    result = build_universal_jiomart_url(product_name="Amul Butter 0.1kg")
    assert result == "https://www.jiomart.com/search/Amul%20Butter"
    assert "0.1" not in result
    assert "?q=" not in result

    result_l = build_universal_jiomart_url(product_name="Fortune Sunlite Oil 0.5L")
    assert result_l == "https://www.jiomart.com/search/Fortune%20Sunlite%20Oil"
    assert "0.5" not in result_l


def test_removes_technical_punctuation():
    # Punctuation like /, \, #, ?, &, %, + should be stripped to avoid breaking JioMart path routing
    result = build_universal_jiomart_url(product_name="Apple iPhone 15 & Pro + Charger/Case")
    assert "?q=" not in result
    assert "&" not in result
    assert "+" not in result
    assert "/" not in result.replace("https://www.jiomart.com/search/", "")
    assert "Apple%20iPhone%2015%20Pro%20Charger%20Case" in result


def test_replaces_broken_search_q_url():
    broken_url = "https://www.jiomart.com/search?q=dettol+handwash"
    result = build_universal_jiomart_url(raw_product_url=broken_url, product_name="Dettol Handwash")
    assert "?q=" not in result
    assert result == "https://www.jiomart.com/search/Dettol%20Handwash"
