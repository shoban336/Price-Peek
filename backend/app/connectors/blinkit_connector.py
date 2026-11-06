"""Blinkit Instant Commerce Connector."""
import urllib.parse
from typing import List, Optional
from app.connectors.base_connector import BaseConnector, RawProductListing
from app.connectors.http_client import fetch_page
from app.schemas.platform_schema import PlatformStatus, PlatformCategory


class BlinkitConnector(BaseConnector):
    platform_id = "blinkit"
    platform_name = "Blinkit"
    platform_category = PlatformCategory.QUICK_COMMERCE
    domain = "blinkit.com"
    requires_pin = True
    logo_url = "https://blinkit.com/images/blinkit-logo.png"
    app_scheme = "grofers://app"

    async def search(self, query: str, pin_code: Optional[str] = None) -> List[RawProductListing]:
        url = "https://blinkit.com/v1/search"
        headers = {
            "Accept": "application/json",
            "lat": "12.9716",
            "lon": "77.5946",
        }
        params = {"q": query, "start": 0, "size": 10}
        
        response = await fetch_page(url, headers=headers, params=params)
        listings: List[RawProductListing] = []
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                products = data.get("products", []) or data.get("items", [])
                for prod in products[:10]:
                    name = prod.get("name")
                    product_id = prod.get("product_id") or prod.get("id")
                    price = prod.get("price") or prod.get("selling_price")
                    mrp = prod.get("mrp") or prod.get("original_price")
                    image = prod.get("image_url") or prod.get("image")
                    unit_text = prod.get("unit")
                    
                    if name and price and product_id:
                        prod_url = f"https://blinkit.com/prn/{urllib.parse.quote_plus(name.lower().replace(' ', '-'))}/prid/{product_id}"
                        listings.append(
                            RawProductListing(
                                platform_id=self.platform_id,
                                platform_name=self.platform_name,
                                platform_category=self.platform_category.value,
                                title=name,
                                price=float(price),
                                original_price=float(mrp) if mrp else None,
                                raw_quantity_str=unit_text,
                                product_url=prod_url,
                                deep_link_url=f"grofers://product/{product_id}",
                                image_url=image,
                                is_live=True,
                                delivery_pin=pin_code,
                                delivery_time_estimate="12 mins"
                            )
                        )
            except Exception:
                pass

        if not listings and response and response.status_code in [403, 503]:
            self.status = PlatformStatus.RESTRICTED_BY_ROBOTS
        else:
            self.status = PlatformStatus.AVAILABLE

        return listings
