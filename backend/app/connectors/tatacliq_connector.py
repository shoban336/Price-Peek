"""Tata CLiQ Omni-Channel Marketplace Connector."""
import urllib.parse
from typing import List, Optional
from app.connectors.base_connector import BaseConnector, RawProductListing
from app.connectors.http_client import fetch_page
from app.schemas.platform_schema import PlatformStatus, PlatformCategory


class TataCliqConnector(BaseConnector):
    platform_id = "tatacliq"
    platform_name = "Tata CLiQ"
    platform_category = PlatformCategory.ELECTRONICS
    domain = "tatacliq.com"
    requires_pin = False
    enabled = True
    status = PlatformStatus.AVAILABLE
    logo_url = "https://www.tatacliq.com/favicon.ico"
    app_scheme = "tatacliq://shop"

    async def search(self, query: str, pin_code: Optional[str] = None) -> List[RawProductListing]:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.tatacliq.com/search/?searchCategory=all&text={encoded}"
        response = await fetch_page(url)

        listings: List[RawProductListing] = []
        if not listings and response and response.status_code in [403, 503]:
            self.status = PlatformStatus.RESTRICTED_BY_ROBOTS
        else:
            self.status = PlatformStatus.AVAILABLE

        return listings
