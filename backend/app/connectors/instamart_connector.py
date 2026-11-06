"""Swiggy Instamart Delivery Connector."""
import urllib.parse
from typing import List, Optional
from app.connectors.base_connector import BaseConnector, RawProductListing
from app.connectors.http_client import fetch_page
from app.schemas.platform_schema import PlatformStatus, PlatformCategory


class InstamartConnector(BaseConnector):
    platform_id = "instamart"
    platform_name = "Swiggy Instamart"
    platform_category = PlatformCategory.QUICK_COMMERCE
    domain = "swiggy.com/instamart"
    requires_pin = True
    logo_url = "https://res.cloudinary.com/swiggy/image/upload/fl_lossy,f_auto,q_auto/portal/m/seo/Logos/Swiggy_logo.png"
    app_scheme = "swiggy://instamart"

    async def search(self, query: str, pin_code: Optional[str] = None) -> List[RawProductListing]:
        url = "https://www.swiggy.com/api/instamart/search"
        params = {"query": query}
        response = await fetch_page(url, params=params)
        
        listings: List[RawProductListing] = []
        if response and response.status_code == 200:
            try:
                data = response.json()
                items = data.get("data", {}).get("widgets", [])
                for widget in items:
                    for item in widget.get("data", {}).get("items", []):
                        name = item.get("name")
                        price = item.get("price") or item.get("final_price")
                        item_id = item.get("id")
                        if name and price and item_id:
                            clean_price = float(price) / 100.0 if float(price) > 1000 else float(price)
                            listings.append(
                                RawProductListing(
                                    platform_id=self.platform_id,
                                    platform_name=self.platform_name,
                                    platform_category=self.platform_category.value,
                                    title=name,
                                    price=clean_price,
                                    product_url=f"https://www.swiggy.com/instamart/item/{item_id}",
                                    deep_link_url=f"swiggy://instamart/item/{item_id}",
                                    is_live=True,
                                    delivery_pin=pin_code,
                                    delivery_time_estimate="15 mins"
                                )
                            )
            except Exception:
                pass

        if not listings and response and response.status_code in [403, 503]:
            self.status = PlatformStatus.RESTRICTED_BY_ROBOTS
        else:
            self.status = PlatformStatus.AVAILABLE

        return listings
