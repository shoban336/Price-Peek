"""Unit & integration tests verifying browser outbound links, zero redirect notices,
and category-specific store exclusions.
"""
import pytest
from app.services.url_resolver import resolve_store_url, generate_store_outbound_url
from app.intelligence.url_resolver import clean_store_search_query
from app.intelligence.brands import classify_category
from app.schemas.platform_schema import PlatformCategory
from app.services.search_service import get_platforms_for_category, execute_universal_search


def test_clean_store_search_query_medicines():
    """Verify medicine dosage extraction removes noise and captures dosage."""
    assert clean_store_search_query("Dolo strip 650tablets") == "Dolo 650"
    assert clean_store_search_query("Dolo 650 tablets strip") == "Dolo 650"
    assert clean_store_search_query("Paracetamol 500mg strip") == "Paracetamol 500"
    assert clean_store_search_query("Crocin 650") == "Crocin 650"


def test_zepto_auto_executes_search_with_query_param():
    """Verify Zepto search outbound URL contains ?query= to avoid empty search bar."""
    url, deep = generate_store_outbound_url("zepto", "Dolo strip 650tablets")
    assert "query=Dolo+650" in url
    assert "q=Dolo+650" in url
    assert "pvid" not in url
    assert "prid" not in url


def test_tata1mg_rejects_broken_41639():
    """Verify 1mg rejects broken ID 41639 and falls back to clean search or canonical."""
    url, _ = generate_store_outbound_url("tata1mg", "Dolo 650", "https://www.1mg.com/drugs/dolo-650-tablet-41639")
    assert "41639" not in url
    assert url == "https://www.1mg.com/search/all?name=Dolo+650"


def test_jiomart_eliminates_google_redirect_notice_and_404_search():
    """Verify JioMart unwraps google.com/url and replaces broken /search/ with /products/?q=."""
    # Google redirect notice wrapper
    wrapped_google_url = "https://www.google.com/url?q=https://www.jiomart.com/collection/books"
    resolved_google = resolve_store_url("jiomart", "Books", wrapped_google_url)
    assert "google.com" not in resolved_google
    assert resolved_google == "https://www.jiomart.com/products/?q=Books"

    # Broken /search/ URL that leads to 404
    broken_search_url = "https://www.jiomart.com/search/Coca-Cola%20Original%20Soft%20Drink"
    resolved_search = resolve_store_url("jiomart", "Coca-Cola Original Soft Drink", broken_search_url)
    assert "/search/" not in resolved_search
    assert resolved_search == "https://www.jiomart.com/products/?q=Coca-Cola+Original+Soft+Drink"


def test_books_category_and_store_exclusion():
    """Verify Books are classified as ECOMMERCE and do not include quick-commerce grocery stores."""
    cat = classify_category("Books")
    assert cat == PlatformCategory.ECOMMERCE

    platforms = get_platforms_for_category(cat)
    platform_ids = [p["id"] for p in platforms]
    # Quick commerce and grocery stores must NOT be in candidate stores for books
    assert "zepto" not in platform_ids
    assert "blinkit" not in platform_ids
    assert "bigbasket" not in platform_ids
    assert "instamart" not in platform_ids
    assert "amazon_fresh" not in platform_ids
    assert "flipkart_minutes" not in platform_ids

    # E-commerce marketplaces must be present
    assert "amazon" in platform_ids
    assert "flipkart" in platform_ids
    assert "jiomart" in platform_ids


@pytest.mark.asyncio
async def test_coca_cola_search_stores_and_links():
    """Verify Coca-Cola search returns valid, non-broken links across grocery stores."""
    res = await execute_universal_search("Coca-Cola Original Soft Drink", "560001")
    assert len(res.listings) >= 4
    platform_ids = {l.platform_id for l in res.listings}
    assert "blinkit" in platform_ids
    assert "zepto" in platform_ids
    assert "jiomart" in platform_ids
    assert "bigbasket" in platform_ids

    for l in res.listings:
        assert not l.product_url.startswith("https://www.google.com")
        if l.platform_id == "jiomart":
            assert "/search/" not in l.product_url
            assert ("products/?q=" in l.product_url or "/product/" in l.product_url)
        if l.platform_id == "zepto":
            assert ("query=" in l.product_url or "/product/" in l.product_url or "/pn/" in l.product_url)
            assert "pvid/dolo" not in l.product_url


def test_samsung_official_store_outbound_url():
    """Verify Samsung Official Store uses working /search/?searchvalue= URL (no 404 multistore or google)."""
    url, deep = generate_store_outbound_url("brand_official", "Samsung Galaxy S24 Ultra")
    assert "samsung.com/in/search/?searchvalue=" in url
    assert "multistore" not in url
    assert "google.com" not in url


def test_reliance_digital_outbound_url():
    """Verify Reliance Digital outbound URL uses /products?q= without :relevance."""
    url, _ = generate_store_outbound_url("reliance_digital", "Samsung Galaxy S24 Ultra")
    assert url == "https://www.reliancedigital.in/products?q=Samsung+Galaxy+S24+Ultra"
    assert ":relevance" not in url


def test_vijay_sales_outbound_url():
    """Verify Vijay Sales outbound URL uses /search-listing?q= (never /search/ 404)."""
    url, _ = generate_store_outbound_url("vijay_sales", "Samsung Galaxy S24 Ultra")
    assert url == "https://www.vijaysales.com/search-listing?q=Samsung+Galaxy+S24+Ultra"
    assert "/search/" not in url


def test_sangeetha_mobiles_outbound_url():
    """Verify Sangeetha Mobiles outbound URL uses www.sangeethamobiles.com/search-result/."""
    url, _ = generate_store_outbound_url("sangeetha_mobiles", "Samsung Galaxy S24 Ultra")
    assert url.startswith("https://www.sangeethamobiles.com/search-result/")
    assert "sangeetha.com" not in url or "sangeethamobiles.com" in url
    assert "/search?q=" not in url


def test_tatacliq_outbound_url_strips_color():
    """Verify Tata CLiQ strips descriptive color tokens so search hits the core product."""
    url, _ = generate_store_outbound_url("tatacliq", "Samsung Galaxy A37 5G Awesome Lavender 128GB")
    assert "Lavender" not in url
    assert "Awesome" not in url
    assert "https://www.tatacliq.com/search/?searchCategory=all&text=Samsung+Galaxy+A37+5G+128GB" in url


def test_brand_official_never_uses_google_redirect():
    """Verify all brand official stores resolve direct domain URLs without google.com redirect notice."""
    from app.connectors.brand_official_connector import build_brand_official_outbound_url
    for brand in ["apple", "sony", "puma", "boat", "oneplus"]:
        url, _ = build_brand_official_outbound_url(brand, f"{brand.title()} Product")
        assert "google.com" not in url
        assert "btnI" not in url
