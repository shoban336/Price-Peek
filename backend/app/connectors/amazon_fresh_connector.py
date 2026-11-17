"""Amazon Fresh Grocery Delivery Connector."""
import urllib.parse
from typing import List, Optional
from app.connectors.base_connector import BaseConnector, RawProductListing
from app.connectors.http_client import fetch_page
from app.schemas.platform_schema import PlatformStatus, PlatformCategory


class AmazonFreshConnector(BaseConnector):
    platform_id = "amazon_fresh"
    platform_name = "Amazon Fresh"
    platform_category = PlatformCategory.GROCERY
    domain = "amazon.in"
    requires_pin = True
    enabled = True
    status = PlatformStatus.AVAILABLE
    logo_url = "https://www.amazon.in/favicon.ico"
    app_scheme = "amazon://fresh"

    async def search(self, query: str, pin_code: Optional[str] = None) -> List[RawProductListing]:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.amazon.in/s?k={encoded}&i=nowstore"
        response = await fetch_page(url)

        listings: List[RawProductListing] = []
        if not listings and response and response.status_code in [403, 503]:
            self.status = PlatformStatus.RESTRICTED_BY_ROBOTS
        else:
            self.status = PlatformStatus.AVAILABLE

        return listings
