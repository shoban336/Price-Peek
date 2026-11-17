"""Apollo Pharmacy Healthcare & Pharmacy Connector."""
import urllib.parse
from typing import List, Optional
from app.connectors.base_connector import BaseConnector, RawProductListing
from app.connectors.http_client import fetch_page
from app.schemas.platform_schema import PlatformStatus, PlatformCategory


class ApolloPharmacyConnector(BaseConnector):
    platform_id = "apollo_pharmacy"
    platform_name = "Apollo Pharmacy"
    platform_category = PlatformCategory.PHARMACY
    domain = "apollopharmacy.in"
    requires_pin = True
    enabled = True
    status = PlatformStatus.AVAILABLE
    logo_url = "https://www.apollopharmacy.in/favicon.ico"
    app_scheme = "apollo://shop"

    async def search(self, query: str, pin_code: Optional[str] = None) -> List[RawProductListing]:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.apollopharmacy.in/search-medicines/{encoded}"
        response = await fetch_page(url)

        listings: List[RawProductListing] = []
        if not listings and response and response.status_code in [403, 503]:
            self.status = PlatformStatus.RESTRICTED_BY_ROBOTS
        else:
            self.status = PlatformStatus.AVAILABLE

        return listings
