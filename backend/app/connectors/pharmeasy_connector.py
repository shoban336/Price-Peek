"""PharmEasy Healthcare & Pharmacy Connector."""
import urllib.parse
from typing import List, Optional
from app.connectors.base_connector import BaseConnector, RawProductListing
from app.connectors.http_client import fetch_page
from app.schemas.platform_schema import PlatformStatus, PlatformCategory


class PharmEasyConnector(BaseConnector):
    platform_id = "pharmeasy"
    platform_name = "PharmEasy"
    platform_category = PlatformCategory.PHARMACY
    domain = "pharmeasy.in"
    requires_pin = True
    enabled = True
    status = PlatformStatus.AVAILABLE
    logo_url = "https://pharmeasy.in/favicon.ico"
    app_scheme = "pharmeasy://shop"

    async def search(self, query: str, pin_code: Optional[str] = None) -> List[RawProductListing]:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://pharmeasy.in/search/all?name={encoded}"
        response = await fetch_page(url)

        listings: List[RawProductListing] = []
        if not listings and response and response.status_code in [403, 503]:
            self.status = PlatformStatus.RESTRICTED_BY_ROBOTS
        else:
            self.status = PlatformStatus.AVAILABLE

        return listings
