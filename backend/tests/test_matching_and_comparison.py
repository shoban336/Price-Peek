"""Test suite for Phase 5 – Product Matching and Price Comparison Engine."""
import pytest
from app.intelligence.parser import parse_query
from app.matching.matcher import compute_similarity, matches_product, filter_and_normalize_listings
from app.comparison.comparator import compare_and_rank_prices
from app.connectors.base_connector import RawProductListing
from app.schemas.search_schema import ProductListing
from app.services.search_service import execute_universal_search


def test_string_similarity_scoring():
    """Verify rapidfuzz similarity scoring handles variations."""
    score1 = compute_similarity("Gold Winner Sunflower Oil", "Gold Winner Refined Sunflower Oil")
    assert score1 >= 0.75

    score2 = compute_similarity("Apple iPhone 15", "Samsung Galaxy S24")
    assert score2 < 0.40


def test_strict_unit_rejection_matching():
    """Verify strict unit isolation: 1L does NOT match 500ml or 5L."""
    parsed_1L = parse_query("Gold Winner Sunflower Oil 1L")
    assert parsed_1L.normalized_quantity == 1.0
    assert parsed_1L.normalized_unit == "L"

    # Listing 1: 500ml pouch
    listing_500ml = RawProductListing(
        platform_id="zepto",
        platform_name="Zepto",
        platform_category="quick_commerce",
        title="Gold Winner Sunflower Oil 500ml Pouch",
        price=75.0,
        product_url="https://zepto.com/p/500ml",
    )
    assert matches_product(parsed_1L, listing_500ml) is False

    # Listing 2: 5L Jar
    listing_5L = RawProductListing(
        platform_id="blinkit",
        platform_name="Blinkit",
        platform_category="quick_commerce",
        title="Gold Winner Sunflower Oil 5L Can",
        price=720.0,
        product_url="https://blinkit.com/p/5l",
    )
    assert matches_product(parsed_1L, listing_5L) is False

    # Listing 3: 1000ml pouch -> MUST MATCH!
    listing_1000ml = RawProductListing(
        platform_id="amazon",
        platform_name="Amazon India",
        platform_category="ecommerce",
        title="Gold Winner Refined Sunflower Oil, 1000 ml Pouch",
        price=145.0,
        product_url="https://amazon.in/dp/1000ml",
    )
    assert matches_product(parsed_1L, listing_1000ml) is True


def test_tech_storage_tier_separation():
    """Verify 128GB does not match 256GB."""
    parsed_256gb = parse_query("Apple iPhone 15 256GB Blue")
    
    listing_128gb = RawProductListing(
        platform_id="croma",
        platform_name="Croma",
        platform_category="electronics",
        title="Apple iPhone 15 (128GB, Blue)",
        price=65999.0,
        product_url="https://croma.com/p/128gb",
    )
    assert matches_product(parsed_256gb, listing_128gb) is False

    listing_256gb = RawProductListing(
        platform_id="amazon",
        platform_name="Amazon India",
        platform_category="electronics",
        title="Apple iPhone 15 (256 GB) - Blue",
        price=75999.0,
        product_url="https://amazon.in/dp/256gb",
    )
    assert matches_product(parsed_256gb, listing_256gb) is True


def test_brand_conflict_rejection():
    """Verify distinct brand is rejected."""
    parsed_dove = parse_query("Dove Daily Shine Shampoo 650ml")
    
    listing_pantene = RawProductListing(
        platform_id="blinkit",
        platform_name="Blinkit",
        platform_category="quick_commerce",
        title="Pantene Advanced Hairfall Solution Shampoo 650ml",
        price=340.0,
        product_url="https://blinkit.com/p/pantene",
    )
    assert matches_product(parsed_dove, listing_pantene) is False


def test_pandas_numpy_comparison_engine():
    """Verify statistical price processing, ranking, and discount identification."""
    listings = [
        ProductListing(
            platform_id="amazon",
            platform_name="Amazon India",
            platform_category="ecommerce",
            title="Gold Winner Sunflower Oil 1L",
            price=152.0,
            original_price=175.0,
            discount_percent=13.1,
            product_url="https://amazon.in/dp/oil1",
        ),
        ProductListing(
            platform_id="zepto",
            platform_name="Zepto",
            platform_category="quick_commerce",
            title="Gold Winner Sunflower Oil 1L Pouch",
            price=139.0,
            original_price=175.0,
            discount_percent=20.5,
            product_url="https://zepto.com/p/oil2",
        ),
        ProductListing(
            platform_id="blinkit",
            platform_name="Blinkit",
            platform_category="quick_commerce",
            title="Gold Winner Sunflower Oil 1L",
            price=144.0,
            original_price=175.0,
            discount_percent=17.7,
            product_url="https://blinkit.com/p/oil3",
        ),
    ]

    # Test sorting ascending
    sorted_asc, summary = compare_and_rank_prices(listings, sort_by="price_asc")
    assert summary.cheapest_platform == "Zepto"
    assert summary.lowest_price == 139.0
    assert summary.highest_price == 152.0
    assert summary.max_savings == 13.0
    assert summary.average_price == 145.0
    assert sorted_asc[0].platform_id == "zepto"
    assert sorted_asc[-1].platform_id == "amazon"

    # Test sorting descending
    sorted_desc, _ = compare_and_rank_prices(listings, sort_by="price_desc")
    assert sorted_desc[0].platform_id == "amazon"
    assert sorted_desc[-1].platform_id == "zepto"


@pytest.mark.asyncio
async def test_end_to_end_search_service():
    """Verify complete search service pipeline execution."""
    result = await execute_universal_search(
        query="Gold Winner Sunflower Oil 1L",
        pin_code="560001",
        sort_by="price_asc"
    )
    assert result.query == "Gold Winner Sunflower Oil 1L"
    assert result.delivery_pin == "560001"
    assert result.parsed_query.normalized_unit == "L"
    assert result.parsed_query.normalized_quantity == 1.0
    assert len(result.listings) > 0
    assert result.summary.lowest_price is not None
    assert result.summary.cheapest_platform is not None
    # Verify mandatory direct links
    for listing in result.listings:
        assert listing.product_url.startswith("http")
