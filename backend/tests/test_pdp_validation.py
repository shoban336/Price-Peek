"""Unit & integration tests for strict direct PDP listing validation and platform exclusion."""
import pytest
from app.comparison.comparator import is_valid_pdp_listing, compare_and_rank_prices
from app.schemas.search_schema import ProductListing
from app.services.search_service import execute_universal_search


def test_is_valid_pdp_listing_accepts_canonical_urls():
    """Verify genuine direct PDP URLs and official store search URLs pass validation."""
    valid_urls = [
        "https://www.amazon.in/dp/B0FNX5ZG78",
        "https://www.flipkart.com/apple-iphone-15-black-128-gb/p/itm6ac6485515ae4",
        "https://www.zeptonow.com/pn/gold-winner-refined-sunflower-oil-pouch/pvid/93a89783",
        "https://blinkit.com/prn/gold-winner-sunflower-oil/prid/66192",
        "https://www.jiomart.com/product/dettol-original-liquid-handwash-200-ml-mffmsl-7504743",
        "https://www.bigbasket.com/pd/274141/gold-winner-refined-sunflower-oil-1-l-pouch/",
        "https://www.croma.com/apple-iphone-15-128gb-black-/p/300652",
        "https://www.1mg.com/drugs/dolo-650-tablet-41639",
        "https://www.amazon.in/s?k=dolo+650",
        "https://www.flipkart.com/search?q=oil",
        "https://blinkit.com/s/?q=good+day+biscuit",
        "https://www.zeptonow.com/search?q=coca+cola",
        "https://www.jiomart.com/search/Good%20Day%20Biscuit",
        "https://www.bigbasket.com/ps/?q=atta",
        "https://www.1mg.com/search/all?name=paracetamol",
        "https://www.croma.com/searchB?q=boat+headphones",
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
        assert is_valid_pdp_listing(listing) is True, f"Failed for valid PDP/Search URL: {u}"


def test_is_valid_pdp_listing_rejects_search_and_homepages():
    """Verify naked homepages, empty URLs, and legacy JioMart /p/ paths are strictly rejected."""
    invalid_urls = [
        "https://www.jiomart.com/p/groceries/dettol-original-liquid-handwash-refill-750-ml/490001844",
        "https://www.jiomart.com/p/electronics/apple-iphone-15/590798548",
        "https://www.amazon.in/",
        "https://flipkart.com",
        "https://jiomart.com/",
        "https://blinkit.com/",
        "http://invalid",
        "site:jiomart.com oil",
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
            price=0.0,
            product_url="https://www.fakestore.com/",
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


@pytest.mark.asyncio
async def test_dolo_650_no_fake_ids_and_working_urls():
    """Verify Dolo 650 search eliminates all 404 fake IDs and returns working store URLs."""
    result = await execute_universal_search("Dolo 650 tablets strip", "560001")
    assert len(result.listings) > 0
    # Must contain Tata 1mg, Zepto, Blinkit, and Amazon
    platform_ids = {it.platform_id for it in result.listings}
    assert "tata1mg" in platform_ids
    assert "zepto" in platform_ids
    assert "blinkit" in platform_ids
    assert "amazon" in platform_ids

    for item in result.listings:
        # Absolutely NO fake IDs
        assert "dolo650-pvid" not in item.product_url
        assert "/prid/dolo650" not in item.product_url
        assert "B07XB2Z92T" not in item.product_url
        # Must be valid working URL
        assert item.product_url.startswith("https://")
        assert is_valid_pdp_listing(item) is True


@pytest.mark.asyncio
async def test_good_day_biscuit_universal_catalog():
    """Verify Good day Biscuit returns comparison results across grocery stores."""
    result = await execute_universal_search("Good day Biscuit", "560001")
    assert len(result.listings) >= 4
    for item in result.listings:
        assert is_valid_pdp_listing(item) is True
        assert item.price > 0
        assert item.product_url.startswith("https://")


@pytest.mark.asyncio
async def test_coca_cola_universal_catalog():
    """Verify Coca-Cola Original Soft Drink returns comparison results."""
    result = await execute_universal_search("Coca-Cola Original Soft Drink", "560001")
    assert len(result.listings) >= 4
    for item in result.listings:
        assert is_valid_pdp_listing(item) is True
        assert item.price > 0


@pytest.mark.asyncio
async def test_unprompted_arbitrary_products():
    """Verify unprompted items like Aashirvaad Atta and Boat Rockerz dynamically produce comparison results."""
    atta_res = await execute_universal_search("Aashirvaad Shudh Chakki Atta 5kg", "560001")
    assert len(atta_res.listings) >= 4
    for item in atta_res.listings:
        assert is_valid_pdp_listing(item) is True

    boat_res = await execute_universal_search("Boat Rockerz headphones", "560001")
    assert len(boat_res.listings) >= 4
    for item in boat_res.listings:
        assert is_valid_pdp_listing(item) is True


