"""Croma Electronics Retail Connector."""
import urllib.parse
from typing import List, Optional
from app.connectors.base_connector import BaseConnector, RawProductListing
from app.connectors.http_client import fetch_page
from app.schemas.platform_schema import PlatformStatus, PlatformCategory
from app.intelligence.url_resolver import resolve_croma_url


class CromaConnector(BaseConnector):
    platform_id = "croma"
    platform_name = "Croma"
    platform_category = PlatformCategory.ELECTRONICS
    domain = "croma.com"
    requires_pin = True
    logo_url = "https://www.croma.com/assets/images/croma_logo.svg"
    app_scheme = "croma://app"

    async def search(self, query: str, pin_code: Optional[str] = None) -> List[RawProductListing]:
        encoded = urllib.parse.quote_plus(query)
        # Croma internal search query API
        url = f"https://api.croma.com/search/v1/search"
        headers = {"Accept": "application/json"}
        params = {"query": query, "pageSize": 10}
        
        response = await fetch_page(url, headers=headers, params=params)
        listings: List[RawProductListing] = []
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                for prod in data.get("products", [])[:10]:
                    name = prod.get("name")
                    code = prod.get("code")
                    price = prod.get("price", {}).get("value")
                    mrp = prod.get("mrp", {}).get("value")
                    url_path = prod.get("url")
                    if name and price and url_path:
                        clean_url = f"https://www.croma.com{url_path}" if not url_path.startswith("http") else url_path
                        clean_url = resolve_croma_url(name, clean_url)
                        listings.append(
                            RawProductListing(
                                platform_id=self.platform_id,
                                platform_name=self.platform_name,
                                platform_category=self.platform_category.value,
                                title=name,
                                price=float(price),
                                original_price=float(mrp) if mrp else None,
                                product_url=clean_url,
                                deep_link_url=f"croma://product/{code}" if code else None,
                                is_live=True,
                                delivery_pin=pin_code,
                                delivery_time_estimate="Standard Delivery (2-4 Days)"
                            )
                        )
            except Exception:
                pass

        if not listings and response and response.status_code in [403, 503]:
            self.status = PlatformStatus.RESTRICTED_BY_ROBOTS
        else:
            self.status = PlatformStatus.AVAILABLE

        return listings
