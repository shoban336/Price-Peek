"""Zepto 10-Minute Delivery Connector."""
import urllib.parse
from typing import List, Optional
from app.connectors.base_connector import BaseConnector, RawProductListing
from app.connectors.http_client import fetch_page
from app.schemas.platform_schema import PlatformStatus, PlatformCategory


class ZeptoConnector(BaseConnector):
    platform_id = "zepto"
    platform_name = "Zepto"
    platform_category = PlatformCategory.QUICK_COMMERCE
    domain = "zeptonow.com"
    requires_pin = True
    logo_url = "https://cdn.zeptonow.com/web-static-assets-prod/artifacts/12.18.0/images/logo.svg"
    app_scheme = "zepto://app"

    async def search(self, query: str, pin_code: Optional[str] = None) -> List[RawProductListing]:
        encoded_query = urllib.parse.quote_plus(query)
        # Zepto public catalog endpoint
        url = f"https://api.zeptonow.com/api/v3/search"
        headers = {
            "Accept": "application/json",
            "x-without-store": "true",
            "compatible_mode": "true",
            "pin-code": pin_code or "560001",
        }
        params = {"query": query, "pageNumber": 0, "mode": "AUTOSUGGEST"}
        
        response = await fetch_page(url, headers=headers, params=params)
        listings: List[RawProductListing] = []
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                items = data.get("layout", []) or data.get("products", [])
                for block in items:
                    for prod in block.get("data", {}).get("resolver", {}).get("data", {}).get("items", []):
                        p_info = prod.get("product", {}) or prod
                        name = p_info.get("name")
                        slug = p_info.get("slug") or p_info.get("id")
                        price = p_info.get("sellingPrice", 0) / 100.0 if p_info.get("sellingPrice", 0) > 1000 else p_info.get("sellingPrice", 0)
                        mrp = p_info.get("mrp", 0) / 100.0 if p_info.get("mrp", 0) > 1000 else p_info.get("mrp", 0)
                        
                        if name and price and slug:
                            prod_url = f"https://www.zeptonow.com/pn/{slug}/pvid/{p_info.get('id', '')}"
                            listings.append(
                                RawProductListing(
                                    platform_id=self.platform_id,
                                    platform_name=self.platform_name,
                                    platform_category=self.platform_category.value,
                                    title=name,
                                    price=float(price),
                                    original_price=float(mrp) if mrp else None,
                                    product_url=prod_url,
                                    deep_link_url=f"zepto://product/{slug}",
                                    in_stock=p_info.get("outOfStock", False) is False,
                                    is_live=True,
                                    delivery_pin=pin_code,
                                    delivery_time_estimate="10 mins"
                                )
                            )
            except Exception:
                pass

        if not listings and response and response.status_code in [403, 503]:
            self.status = PlatformStatus.RESTRICTED_BY_ROBOTS
        else:
            self.status = PlatformStatus.AVAILABLE

        return listings
