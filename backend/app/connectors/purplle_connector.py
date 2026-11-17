"""Purplle Beauty & Personal Care Connector."""
import urllib.parse
from typing import List, Optional
from app.connectors.base_connector import BaseConnector, RawProductListing
from app.connectors.http_client import fetch_page
from app.schemas.platform_schema import PlatformStatus, PlatformCategory


class PurplleConnector(BaseConnector):
    platform_id = "purplle"
    platform_name = "Purplle"
    platform_category = PlatformCategory.BEAUTY
    domain = "purplle.com"
    requires_pin = False
    enabled = True
    status = PlatformStatus.AVAILABLE
    logo_url = "https://www.purplle.com/favicon.ico"
    app_scheme = "purplle://shop"

    async def search(self, query: str, pin_code: Optional[str] = None) -> List[RawProductListing]:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.purplle.com/search?q={encoded}"
        response = await fetch_page(url)

        listings: List[RawProductListing] = []
        if not listings and response and response.status_code in [403, 503]:
            self.status = PlatformStatus.RESTRICTED_BY_ROBOTS
        else:
            self.status = PlatformStatus.AVAILABLE

        return listings
