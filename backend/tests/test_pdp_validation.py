"""Unit & integration tests for strict direct PDP listing validation and platform exclusion."""
import pytest
from app.comparison.comparator import is_valid_pdp_listing, compare_and_rank_prices
from app.schemas.search_schema import ProductListing
from app.services.search_service import execute_universal_search


def test_is_valid_pdp_listing_accepts_canonical_urls():
    """Verify genuine direct PDP URLs pass validation."""
    valid_urls = [
        "https://www.amazon.in/dp/B0FNX5ZG78",
        "https://www.flipkart.com/apple-iphone-15-black-128-gb/p/itm6ac6485515ae4",
        "https://www.zeptonow.com/pn/gold-winner-refined-sunflower-oil-pouch/pvid/93a89783",
        "https://blinkit.com/prn/gold-winner-sunflower-oil/prid/66192",
        "https://www.jiomart.com/product/dettol-original-liquid-handwash-200-ml-mffmsl-7504743",
        "https://www.bigbasket.com/pd/274141/gold-winner-refined-sunflower-oil-1-l-pouch/",
        "https://www.croma.com/apple-iphone-15-128gb-black-/p/300652",
        "https://www.1mg.com/drugs/dolo-650-tablet-41639",
    ]
    for u in valid_urls:
        listing = ProductListing(
            platform_id="test",
            platform_name="Test Store",
            platform_category="grocery",
            title="Valid Product",
            price=150.0,
            product_url=u,
        )
        assert is_valid_pdp_listing(listing) is True, f"Failed for valid PDP: {u}"


def test_is_valid_pdp_listing_rejects_search_and_homepages():
    """Verify search fallbacks, homepages, and empty URLs are strictly rejected."""
    invalid_urls = [
        "https://www.amazon.in/s?k=dettol",
        "https://www.flipkart.com/search?q=oil",
        "https://www.jiomart.com/search/oil",
        "https://www.jiomart.com/search?q=oil",
        "https://www.jiomart.com/p/groceries/dettol-original-liquid-handwash-refill-750-ml/490001844",
        "https://www.jiomart.com/p/electronics/apple-iphone-15/590798548",
        "https://www.bigbasket.com/ps/?q=oil",
        "https://blinkit.com/s/?q=oil",
        "https://www.zeptonow.com/search?q=oil",
        "https://www.croma.com/searchb?q=iphone",
        "https://www.1mg.com/search/all?name=dolo",
        "https://www.amazon.in/",
        "https://flipkart.com",
        "https://jiomart.com/",
        "http://invalid",
        "",
    ]
    for u in invalid_urls:
        listing = {
            "platform_id": "test",
            "platform_name": "Test Store",
            "platform_category": "grocery",
            "title": "Invalid Product",
            "price": 150.0,
            "product_url": u,
        }
        assert is_valid_pdp_listing(listing) is False, f"Should reject invalid URL: {u}"


def test_is_valid_pdp_listing_rejects_zero_or_negative_price():
    """Verify items without a valid positive price are rejected."""
    listing = ProductListing(
        platform_id="test",
        platform_name="Test Store",
        platform_category="grocery",
        title="Zero Price Item",
        price=0.0,
        product_url="https://www.amazon.in/dp/B0FNX5ZG78",
    )
    assert is_valid_pdp_listing(listing) is False


def test_comparator_excludes_invalid_listings():
    """Verify compare_and_rank_prices filters out invalid search fallbacks."""
    listings = [
        ProductListing(
            platform_id="amazon",
            platform_name="Amazon India",
            platform_category="ecommerce",
            title="Valid Amazon PDP",
            price=200.0,
            product_url="https://www.amazon.in/dp/B0FNX5ZG78",
        ),
        ProductListing(
            platform_id="fake_store",
            platform_name="Fake Store",
            platform_category="ecommerce",
            title="Broken Search Fallback",
            price=180.0,
            product_url="https://www.fakestore.com/search?q=product",
        ),
    ]
    sorted_res, summary = compare_and_rank_prices(listings)
    assert len(sorted_res) == 1
    assert sorted_res[0].platform_id == "amazon"
    assert summary.lowest_price == 200.0
    assert summary.cheapest_platform == "Amazon India"


@pytest.mark.asyncio
async def test_search_results_contain_only_authentic_pdp_links():
    """Verify end-to-end universal search produces strictly authentic PDP links."""
    result = await execute_universal_search("Gold Winner Sunflower Oil 1L", "560001")
    assert len(result.listings) > 0
    for item in result.listings:
        assert is_valid_pdp_listing(item) is True
        # Explicit check: must not contain search syntax
        assert "/search" not in item.product_url.lower()
        assert "?q=" not in item.product_url.lower()
        assert "?k=" not in item.product_url.lower()
        assert "/s/?q=" not in item.product_url.lower()


@pytest.mark.asyncio
async def test_jiomart_listings_strictly_use_product_route():
    """Verify any JioMart listings returned by search use modern /product/ URL pattern and never /p/."""
    result = await execute_universal_search("Gold Winner Sunflower Oil 1L", "560001")
    jiomart_items = [it for it in result.listings if it.platform_id == "jiomart"]
    assert len(jiomart_items) > 0, "Expected at least one JioMart item"
    for item in jiomart_items:
        assert item.product_url.startswith("https://www.jiomart.com/product/"), f"Invalid JioMart URL: {item.product_url}"
        assert "/p/" not in item.product_url
        assert "/search" not in item.product_url

