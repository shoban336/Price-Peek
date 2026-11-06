"""JioMart Storefront Connector."""
import urllib.parse
from bs4 import BeautifulSoup
from typing import List, Optional
from app.connectors.base_connector import BaseConnector, RawProductListing
from app.connectors.http_client import fetch_page
from app.schemas.platform_schema import PlatformStatus, PlatformCategory


class JioMartConnector(BaseConnector):
    platform_id = "jiomart"
    platform_name = "JioMart"
    platform_category = PlatformCategory.GROCERY
    domain = "jiomart.com"
    requires_pin = True
    logo_url = "https://www.jiomart.com/assets/ds2web/jio-mart-logo-square.svg"
    app_scheme = "jiomart://home"

    async def search(self, query: str, pin_code: Optional[str] = None) -> List[RawProductListing]:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.jiomart.com/search?q={encoded}"
        response = await fetch_page(url)

        if not response:
            self.status = PlatformStatus.UNAVAILABLE
            return []

        if response.status_code in [403, 503] or "blocked" in response.text.lower():
            self.status = PlatformStatus.RESTRICTED_BY_ROBOTS
            return []

        listings: List[RawProductListing] = []
        soup = BeautifulSoup(response.text, "lxml")
        items = soup.select("div.product-card, div.ais-InfiniteHits-item, li.ais-InfiniteHits-item")
        
        for item in items[:10]:
            title_node = item.select_one("div.plp-card-details-name, span.clsgetname")
            price_node = item.select_one("span.jm-heading-xxs, span.price")
            orig_price_node = item.select_one("span.jm-body-xxs.line-through, span.mrp")
            link_node = item.select_one("a[href*='/p/']")
            img_node = item.select_one("img")

            if title_node and price_node and link_node:
                raw_title = title_node.get_text(strip=True)
                price_str = price_node.get_text(strip=True).replace("₹", "").replace(",", "").strip()
                try:
                    price = float(price_str)
                except ValueError:
                    continue

                orig_price = None
                if orig_price_node:
                    try:
                        orig_str = orig_price_node.get_text(strip=True).replace("₹", "").replace(",", "").strip()
                        orig_price = float(orig_str)
                    except ValueError:
                        orig_price = None

                href = link_node.get("href", "")
                if href and not href.startswith("http"):
                    href = f"https://www.jiomart.com{href}"

                discount = None
                if orig_price and orig_price > price:
                    discount = round(((orig_price - price) / orig_price) * 100, 1)

                listings.append(
                    RawProductListing(
                        platform_id=self.platform_id,
                        platform_name=self.platform_name,
                        platform_category=self.platform_category.value,
                        title=raw_title,
                        price=price,
                        original_price=orig_price,
                        discount_percent=discount,
                        product_url=href,
                        deep_link_url=f"jiomart://product/{href.split('/')[-1]}",
                        image_url=img_node.get("src") if img_node else None,
                        is_live=True,
                        delivery_pin=pin_code,
                        delivery_time_estimate="Today / Tomorrow"
                    )
                )

        self.status = PlatformStatus.AVAILABLE
        return listings
