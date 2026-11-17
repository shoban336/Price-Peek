"""Reliance Digital Electronics Retail Connector."""
import urllib.parse
from typing import List, Optional
from app.connectors.base_connector import BaseConnector, RawProductListing
from app.connectors.http_client import fetch_page
from app.schemas.platform_schema import PlatformStatus, PlatformCategory


class RelianceDigitalConnector(BaseConnector):
    platform_id = "reliance_digital"
    platform_name = "Reliance Digital"
    platform_category = PlatformCategory.ELECTRONICS
    domain = "reliancedigital.in"
    requires_pin = True
    enabled = True
    status = PlatformStatus.AVAILABLE
    logo_url = "https://www.reliancedigital.in/build/client/images/loaders/rd_logo.svg"
    app_scheme = "reliancedigital://shop"

    async def search(self, query: str, pin_code: Optional[str] = None) -> List[RawProductListing]:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.reliancedigital.in/rildigitalws/v2/rrldigital/cms/pagedata?pageType=productSearchResultPage&q={encoded}:relevance"
        headers = {"Accept": "application/json"}
        response = await fetch_page(url, headers=headers)

        listings: List[RawProductListing] = []
        if response and response.status_code == 200:
            try:
                data = response.json()
                for prod in data.get("data", {}).get("results", [])[:10]:
                    name = prod.get("name")
                    code = prod.get("code")
                    price = prod.get("price", {}).get("value")
                    mrp = prod.get("mrp", {}).get("value")
                    url_path = prod.get("url")
                    if name and price and url_path:
                        clean_url = f"https://www.reliancedigital.in{url_path}" if not url_path.startswith("http") else url_path
                        listings.append(
                            RawProductListing(
                                platform_id=self.platform_id,
                                platform_name=self.platform_name,
                                platform_category=self.platform_category.value,
                                title=name,
                                price=float(price),
                                original_price=float(mrp) if mrp else None,
                                product_url=clean_url,
                                deep_link_url=f"reliancedigital://product/{code}" if code else None,
                                is_live=True,
                                delivery_pin=pin_code,
                                delivery_time_estimate="Fast Delivery (1-2 Days)"
                            )
                        )
            except Exception:
                pass

        if not listings and response and response.status_code in [403, 503]:
            self.status = PlatformStatus.RESTRICTED_BY_ROBOTS
        else:
            self.status = PlatformStatus.AVAILABLE

        return listings
