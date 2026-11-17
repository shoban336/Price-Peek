"""Comprehensive test suite for Direct Product URL Resolution & Strict Exact-Variant Matching."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.intelligence.url_resolver import (
    parse_product_url,
    generate_store_outbound_url,
    clean_slug_to_query,
)
from app.intelligence.parser import parse_query
from app.intelligence.units import parse_and_normalize_unit, is_unit_equivalent
from app.intelligence.variants import extract_variants
from app.matching.matcher import matches_product, filter_and_normalize_listings
from app.connectors.base_connector import RawProductListing
from app.services.search_service import execute_universal_search

client = TestClient(app)


def test_parse_product_url_amazon_deep_attributes():
    url = "https://www.amazon.in/Apple-iPhone-15-128-GB/dp/B0CHX1W1XY?color=Black"
    resolved = parse_product_url(url)
    assert resolved is not None
    assert resolved.is_url is True
    assert resolved.platform_id == "amazon"
    assert resolved.product_id == "B0CHX1W1XY"
    assert resolved.brand == "Apple"
    assert resolved.storage == "128GB"
    assert resolved.color == "Black"
    assert "128 GB" in resolved.locked_variant_tags
    assert "Black" in resolved.locked_variant_tags


def test_parse_product_url_flipkart_deep_attributes():
    url = "https://www.flipkart.com/apple-iphone-15-black-128-gb/p/itm6ac6485515ae4"
    resolved = parse_product_url(url)
    assert resolved is not None
    assert resolved.is_url is True
    assert resolved.platform_id == "flipkart"
    assert resolved.product_id == "itm6ac6485515ae4"
    assert resolved.brand == "Apple"
    assert resolved.storage == "128GB"
    assert resolved.color == "Black"
    assert "128 GB" in resolved.locked_variant_tags
    assert "Black" in resolved.locked_variant_tags


def test_parse_product_url_bigbasket_volume():
    url = "https://www.bigbasket.com/pd/40034580/dettol-liquid-handwash-original-everyday-protection-fights-germs-750-ml/"
    resolved = parse_product_url(url)
    assert resolved is not None
    assert resolved.platform_id == "bigbasket"
    assert resolved.brand == "Dettol"
    assert resolved.quantity == 0.75
    assert resolved.unit == "L"
    assert "750 ml" in resolved.locked_variant_tags


def test_parse_product_url_jiomart():
    url = "https://www.jiomart.com/product/gold-winner-refined-sunflower-oil-1-l-pouch-mffn5q-7533064"
    resolved = parse_product_url(url)
    assert resolved is not None
    assert resolved.platform_id == "jiomart"
    assert resolved.brand == "Gold Winner"
    assert resolved.quantity == 1.0
    assert resolved.unit == "L"
    assert "1 L" in resolved.locked_variant_tags


def test_parse_product_url_zepto():
    url = "https://www.zeptonow.com/pn/coca-cola-original-soft-drink-750-ml/pvid/123"
    resolved = parse_product_url(url)
    assert resolved is not None
    assert resolved.platform_id == "zepto"
    assert resolved.brand == "Coca-Cola"
    assert resolved.quantity == 0.75
    assert resolved.unit == "L"
    assert "750 ml" in resolved.locked_variant_tags


def test_volume_precision_strict_rejection():
    """Scenario 1: 500ml must strictly reject 250ml, 750ml, 1L, and 2L."""
    parsed = parse_query("Coca-Cola Soft Drink 500ml")
    parsed.is_url_query = True

    listing_500 = RawProductListing(
        platform_id="p1", platform_name="Store 1", platform_category="grocery",
        title="Coca-Cola Soft Drink 500ml", price=40, in_stock=True, product_url="https://s1"
    )
    listing_250 = RawProductListing(
        platform_id="p2", platform_name="Store 2", platform_category="grocery",
        title="Coca-Cola Soft Drink 250ml", price=20, in_stock=True, product_url="https://s2"
    )
    listing_750 = RawProductListing(
        platform_id="p3", platform_name="Store 3", platform_category="grocery",
        title="Coca-Cola Soft Drink 750ml", price=45, in_stock=True, product_url="https://s3"
    )
    listing_1L = RawProductListing(
        platform_id="p4", platform_name="Store 4", platform_category="grocery",
        title="Coca-Cola Soft Drink 1L", price=60, in_stock=True, product_url="https://s4"
    )
    listing_2L = RawProductListing(
        platform_id="p5", platform_name="Store 5", platform_category="grocery",
        title="Coca-Cola Soft Drink 2L", price=95, in_stock=True, product_url="https://s5"
    )

    assert matches_product(parsed, listing_500) is True
    assert matches_product(parsed, listing_250) is False
    assert matches_product(parsed, listing_750) is False
    assert matches_product(parsed, listing_1L) is False
    assert matches_product(parsed, listing_2L) is False


def test_color_and_storage_precision_strict_rejection():
    """Scenario 2: iPhone 15 128GB Black must reject 256GB, Blue/Pink colors, and Plus/Pro models."""
    parsed = parse_query("Apple iPhone 15 128GB Black")
    parsed.is_url_query = True
    parsed.locked_storage = "128GB"
    parsed.locked_color = "Black"
    parsed.model = "15"

    match_exact = RawProductListing(
        platform_id="a1", platform_name="Amazon", platform_category="ecommerce",
        title="Apple iPhone 15 (128 GB) - Black", price=69999, in_stock=True, product_url="https://a1"
    )
    mismatch_storage = RawProductListing(
        platform_id="a2", platform_name="Amazon", platform_category="ecommerce",
        title="Apple iPhone 15 (256 GB) - Black", price=79999, in_stock=True, product_url="https://a2"
    )
    mismatch_color = RawProductListing(
        platform_id="a3", platform_name="Amazon", platform_category="ecommerce",
        title="Apple iPhone 15 (128 GB) - Blue", price=69999, in_stock=True, product_url="https://a3"
    )
    mismatch_plus = RawProductListing(
        platform_id="a4", platform_name="Amazon", platform_category="ecommerce",
        title="Apple iPhone 15 Plus (128 GB) - Black", price=79999, in_stock=True, product_url="https://a4"
    )
    mismatch_pro = RawProductListing(
        platform_id="a5", platform_name="Amazon", platform_category="ecommerce",
        title="Apple iPhone 15 Pro (128 GB) - Black", price=119999, in_stock=True, product_url="https://a5"
    )

    assert matches_product(parsed, match_exact) is True
    assert matches_product(parsed, mismatch_storage) is False
    assert matches_product(parsed, mismatch_color) is False
    assert matches_product(parsed, mismatch_plus) is False
    assert matches_product(parsed, mismatch_pro) is False


def test_pack_multiplier_strict_rejection():
    """Pack of 1 must reject Pack of 2 or combo bundles."""
    parsed = parse_query("Dettol Soap 125g Pack of 1")
    parsed.is_url_query = True
    parsed.locked_pack = 1

    single_pack = RawProductListing(
        platform_id="s1", platform_name="Store 1", platform_category="grocery",
        title="Dettol Soap 125g", price=40, in_stock=True, product_url="https://s1"
    )
    pack_of_2 = RawProductListing(
        platform_id="s2", platform_name="Store 2", platform_category="grocery",
        title="Dettol Soap 125g (Pack of 2)", price=75, in_stock=True, product_url="https://s2"
    )
    pack_of_3 = RawProductListing(
        platform_id="s3", platform_name="Store 3", platform_category="grocery",
        title="Dettol Soap 125g (Pack of 3)", price=110, in_stock=True, product_url="https://s3"
    )
    combo_4 = RawProductListing(
        platform_id="s4", platform_name="Store 4", platform_category="grocery",
        title="Dettol Soap 125g Combo of 4", price=145, in_stock=True, product_url="https://s4"
    )

    assert matches_product(parsed, single_pack) is True
    assert matches_product(parsed, pack_of_2) is False
    assert matches_product(parsed, pack_of_3) is False
    assert matches_product(parsed, combo_4) is False


@pytest.mark.asyncio
async def test_missing_variant_exclusive_platform_omission():
    """Scenario 3: Exclusive color or niche pack size sold on only two platforms."""
    res = await execute_universal_search(
        "https://www.amazon.in/Exclusive-Product-Special-Edition/dp/B0EXCLUSIV1?color=Yellow",
        "560001"
    )
    assert len(res.listings) == 2
    # Ensure source platform is among the 2
    platform_ids = [l.platform_id for l in res.listings]
    assert "amazon" in platform_ids
    # Ensure summary stats calculate strictly across those 2 exact listings
    assert res.summary.total_active_listings == 2
    assert res.parsed_query.locked_variant_tags == ["Yellow"]


@pytest.mark.asyncio
async def test_end_to_end_iphone_url_search():
    """End-to-end exact variant comparison from Flipkart iPhone URL."""
    url = "https://www.flipkart.com/apple-iphone-15-black-128-gb/p/itm6ac6485515ae4"
    res = await execute_universal_search(url, "560001")
    assert len(res.listings) > 0
    # Every resulting listing must be 128GB Black and not Plus/Pro
    for l in res.listings:
        assert "128" in l.title
        assert "Black" in l.title
        assert "Plus" not in l.title
        assert "Pro" not in l.title
    # Flipkart card retains exact user pasted link
    fk_listing = next(l for l in res.listings if l.platform_id == "flipkart")
    assert fk_listing.product_url == url


@pytest.mark.asyncio
async def test_end_to_end_volume_url_search():
    """End-to-end 750ml volume comparison from BigBasket Dettol URL."""
    url = "https://www.bigbasket.com/pd/40034580/dettol-liquid-handwash-original-everyday-protection-fights-germs-750-ml/"
    res = await execute_universal_search(url, "560001")
    assert len(res.listings) > 0
    for l in res.listings:
        assert "750" in l.title
    # BigBasket retains exact user link
    bb_listing = next(l for l in res.listings if l.platform_id == "bigbasket")
    assert bb_listing.product_url == url


def test_outbound_links_preservation():
    """Ensure JioMart (/products/?q=...) and Zepto (?q=...&query=...) link logic remains intact."""
    jio_url, _ = generate_store_outbound_url("jiomart", "Apple iPhone 15 Black 128GB")
    assert "jiomart.com/products/?q=" in jio_url

    zepto_url, _ = generate_store_outbound_url("zepto", "Apple iPhone 15 Black 128GB")
    assert "zepto.com/search?q=" in zepto_url
    assert "query=" in zepto_url


def test_api_endpoint_handles_long_pasted_url():
    """Test POST /api/v1/search accepts long URL with query params without 422 error."""
    long_url = "https://www.amazon.in/Apple-iPhone-15-128-GB/dp/B0CHX1W1XY?color=Black&storage=128GB&tag=affiliate-test-tracking-code-21&ref=sr_1_1&keywords=iphone+15&qid=1690000000"
    response = client.post(
        "/api/v1/search",
        json={"query": long_url, "pin_code": "560001"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["resolved_url_info"] is not None
    assert data["resolved_url_info"]["is_url"] is True
    assert "128 GB" in data["parsed_query"]["locked_variant_tags"]
    assert "Black" in data["parsed_query"]["locked_variant_tags"]
    assert len(data["listings"]) > 0


def test_resolve_croma_url_and_outbound_routing():
    """Verify Croma URLs strictly include %3Arelevance and &text= parameter, and preserve valid /p/ links."""
    from app.intelligence.url_resolver import resolve_croma_url

    # 1. Search fallback must include both %3Arelevance and &text= to avoid blank black screen
    search_url = resolve_croma_url("Samsung Galaxy A37 5G Awesome Lavender 128GB")
    assert "%3Arelevance" in search_url
    assert "&text=" in search_url
    assert "https://www.croma.com/searchB?q=" in search_url

    # 2. Canonical PDP link with /p/<id> is preserved as-is
    direct_pdp = "https://www.croma.com/samsung-galaxy-a35-5g-awesome-lilac-128gb-/p/305312"
    assert resolve_croma_url("Samsung Galaxy A35", direct_pdp) == direct_pdp

    # 3. generate_store_outbound_url generates valid Croma URL
    croma_url, deep = generate_store_outbound_url("croma", "Samsung Galaxy A37 5G Awesome Lavender 128GB")
    assert "%3Arelevance" in croma_url
    assert "&text=" in croma_url
    assert deep.startswith("croma://")


def test_samsung_galaxy_a37_exact_variant_matching():
    """Verify Samsung Galaxy A37 5G Awesome Lavender 128GB deep extraction & strict variant exclusion."""
    url = "https://www.flipkart.com/samsung-galaxy-a37-5g-awesome-lavender-128-gb/p/itm_samsung_a37_lavender_128"
    resolved = parse_product_url(url)
    assert resolved is not None
    assert resolved.brand == "Samsung"
    assert resolved.storage == "128GB"
    assert resolved.color == "Awesome Lavender"
    assert "Awesome Lavender" in resolved.locked_variant_tags
    assert "128 GB" in resolved.locked_variant_tags

    parsed = parse_query(resolved.clean_query)
    parsed.is_url_query = True
    parsed.locked_storage = resolved.storage
    parsed.locked_color = resolved.color
    parsed.model = resolved.model

    # Exact match
    match_exact = RawProductListing(
        platform_id="croma", platform_name="Croma", platform_category="electronics",
        title="Samsung Galaxy A37 5G (Awesome Lavender, 128 GB)", price=29999, in_stock=True, product_url="https://croma/p/1"
    )
    # Model mismatch: A35
    mismatch_a35 = RawProductListing(
        platform_id="amazon", platform_name="Amazon India", platform_category="ecommerce",
        title="Samsung Galaxy A35 5G (Awesome Lavender, 128 GB)", price=26999, in_stock=True, product_url="https://amazon/dp/1"
    )
    # Model mismatch: A55
    mismatch_a55 = RawProductListing(
        platform_id="flipkart", platform_name="Flipkart", platform_category="ecommerce",
        title="Samsung Galaxy A55 5G (Awesome Lavender, 128 GB)", price=34999, in_stock=True, product_url="https://flipkart/p/1"
    )
    # Storage mismatch: 256GB
    mismatch_storage = RawProductListing(
        platform_id="croma", platform_name="Croma", platform_category="electronics",
        title="Samsung Galaxy A37 5G (Awesome Lavender, 256 GB)", price=33999, in_stock=True, product_url="https://croma/p/2"
    )
    # Color mismatch: Black
    mismatch_color = RawProductListing(
        platform_id="amazon", platform_name="Amazon India", platform_category="ecommerce",
        title="Samsung Galaxy A37 5G (Awesome Black, 128 GB)", price=29999, in_stock=True, product_url="https://amazon/dp/2"
    )

    assert matches_product(parsed, match_exact) is True
    assert matches_product(parsed, mismatch_a35) is False
    assert matches_product(parsed, mismatch_a55) is False
    assert matches_product(parsed, mismatch_storage) is False
    assert matches_product(parsed, mismatch_color) is False
