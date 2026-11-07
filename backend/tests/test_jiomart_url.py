"""Unit tests for universal JioMart URL handling."""
import pytest
from app.connectors.jiomart_connector import build_universal_jiomart_url


def test_canonical_full_url():
    url = "https://www.jiomart.com/p/groceries/amul-butter-100-g-carton/490000073"
    result = build_universal_jiomart_url(raw_product_url=url)
    assert result == url


def test_relative_scraped_url():
    rel = "/p/groceries/dettol-original-liquid-handwash-refill-750-ml/490001844"
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
