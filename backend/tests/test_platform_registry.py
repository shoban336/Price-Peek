"""Test suite for Phase 4 – Dynamic Platform Registry and Base Connectors."""
import pytest
from app.registry import PlatformRegistry
from app.connectors.base_connector import BaseConnector, RawProductListing
from app.schemas.platform_schema import PlatformStatus, PlatformCategory


class MockPartnerConnector(BaseConnector):
    """Custom plug-and-play connector test class."""
    platform_id = "test_partner"
    platform_name = "Test Partner Market"
    platform_category = PlatformCategory.GROCERY
    domain = "testpartner.com"
    requires_pin = True

    async def search(self, query: str, pin_code: str = None):
        return [
            RawProductListing(
                platform_id=self.platform_id,
                platform_name=self.platform_name,
                platform_category=self.platform_category.value,
                title=f"{query} Premium Pack",
                price=199.0,
                product_url="https://testpartner.com/product/123",
                deep_link_url="testpartner://prod/123",
                is_live=True
            )
        ]


def test_default_connectors_initialized():
    """Verify that PlatformRegistry is pre-seeded with all default platform connectors."""
    reg = PlatformRegistry()
    connectors = reg.list_connectors(enabled_only=False)
    ids = [c.platform_id for c in connectors]
    assert "amazon" in ids
    assert "flipkart" in ids
    assert "zepto" in ids
    assert "blinkit" in ids
    assert "instamart" in ids
    assert "bigbasket" in ids
    assert "croma" in ids
    assert "tata1mg" in ids


def test_plug_and_play_registration():
    """Verify newly authored connectors register without any core search alterations."""
    reg = PlatformRegistry()
    partner = MockPartnerConnector()
    reg.register(partner)

    retrieved = reg.get("test_partner")
    assert retrieved is not None
    assert retrieved.platform_name == "Test Partner Market"
    assert retrieved.domain == "testpartner.com"

    # Verify unregister
    success = reg.unregister("test_partner")
    assert success is True
    assert reg.get("test_partner") is None


@pytest.mark.asyncio
async def test_search_all_parallel_execution():
    """Verify asynchronous multi-platform query aggregation."""
    reg = PlatformRegistry()
    partner = MockPartnerConnector()
    reg.register(partner)

    # Filter to only query mock partner to test speed and schema validity
    listings = await reg.search_all(query="Sunflower Oil", platform_ids=["test_partner"])
    assert len(listings) == 1
    assert listings[0].platform_id == "test_partner"
    assert listings[0].price == 199.0
    assert listings[0].product_url == "https://testpartner.com/product/123"


@pytest.mark.asyncio
async def test_discovery_validator_local():
    """Verify discovery validation logic formats structured compliance report."""
    reg = PlatformRegistry()
    report = await reg.validate_discovery("example.com")
    assert "target" in report
    assert "robots_url" in report
    assert "recommendation" in report
    assert report["robots_url"] == "https://example.com/robots.txt"
