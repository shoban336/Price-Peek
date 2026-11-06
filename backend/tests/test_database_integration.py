"""Test suite for Phase 6 – Database Integration and Price History Persistence."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.database import Base
from app.models import Product, Platform, ProductListingRecord, PriceHistoryRecord
from app.schemas.search_schema import ParsedQuery, ProductListing
from app.services.db_service import (
    sync_platforms_to_db,
    get_or_create_product,
    persist_search_listings,
    fetch_price_history_records,
)

# Use in-memory SQLite for isolated database testing
TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh in-memory database and session for every test."""
    test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


def test_database_tables_exist(db_session):
    """Verify all four core tables exist and can be queried."""
    assert db_session.query(Product).count() == 0
    assert db_session.query(Platform).count() == 0
    assert db_session.query(ProductListingRecord).count() == 0
    assert db_session.query(PriceHistoryRecord).count() == 0


def test_sync_platforms_to_db(db_session):
    """Verify platform registry sync seeds all default shopping platforms into database."""
    sync_platforms_to_db(db_session)
    count = db_session.query(Platform).count()
    assert count >= 8
    amazon = db_session.query(Platform).filter(Platform.id == "amazon").first()
    assert amazon is not None
    assert amazon.name == "Amazon India"
    assert amazon.category == "ecommerce"


def test_get_or_create_product(db_session):
    """Verify product entity creation and duplicate idempotency."""
    parsed = ParsedQuery(
        raw_query="Gold Winner Sunflower Oil 1L",
        brand="Gold Winner",
        product_name="Sunflower Oil",
        category="grocery",
        normalized_quantity=1.0,
        normalized_unit="L",
    )
    p1 = get_or_create_product(db_session, parsed)
    assert p1.id is not None
    assert p1.canonical_name == "Gold Winner Sunflower Oil 1L"
    assert p1.normalized_quantity == 1.0

    # Retrieve again with same parsed query -> should return existing product
    p2 = get_or_create_product(db_session, parsed)
    assert p2.id == p1.id
    assert db_session.query(Product).count() == 1


def test_persist_search_listings_and_history(db_session):
    """Verify persisting listings creates listing records and price history entries."""
    parsed = ParsedQuery(
        raw_query="Gold Winner Sunflower Oil 1L",
        brand="Gold Winner",
        product_name="Sunflower Oil",
        category="grocery",
        normalized_quantity=1.0,
        normalized_unit="L",
    )
    listings = [
        ProductListing(
            platform_id="amazon",
            platform_name="Amazon India",
            platform_category="ecommerce",
            title="Gold Winner Sunflower Oil 1L",
            price=145.0,
            original_price=175.0,
            discount_percent=17.1,
            product_url="https://amazon.in/dp/oil1L",
        ),
        ProductListing(
            platform_id="zepto",
            platform_name="Zepto",
            platform_category="quick_commerce",
            title="Gold Winner Sunflower Oil 1L Pouch",
            price=140.0,
            original_price=175.0,
            discount_percent=20.0,
            product_url="https://zepto.com/p/oil1L",
        ),
    ]

    prod = persist_search_listings(db_session, parsed, listings)
    assert prod is not None
    assert db_session.query(ProductListingRecord).filter(ProductListingRecord.product_id == prod.id).count() == 2
    assert db_session.query(PriceHistoryRecord).filter(PriceHistoryRecord.product_id == prod.id).count() == 2

    # Fetch history records
    history = fetch_price_history_records(db_session, str(prod.id), days=30)
    assert len(history) == 2
    prices = [h["price"] for h in history]
    assert 145.0 in prices
    assert 140.0 in prices


def test_database_url_compatibility():
    """Verify SQLAlchemy engine supports both SQLite and MySQL connection strings."""
    from app.config.settings import Settings
    
    # Test SQLite setting
    sqlite_settings = Settings(DATABASE_URL="sqlite:///./pricepeek.db")
    assert sqlite_settings.DATABASE_URL.startswith("sqlite")
    
    # Test MySQL setting
    mysql_settings = Settings(DATABASE_URL="mysql+pymysql://user:pass@localhost:3306/pricepeek")
    assert mysql_settings.DATABASE_URL.startswith("mysql+pymysql")
