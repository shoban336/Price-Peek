"""Nykaa Beauty Storefront Connector."""
import urllib.parse
from bs4 import BeautifulSoup
from typing import List, Optional
from app.connectors.base_connector import BaseConnector, RawProductListing
from app.connectors.http_client import fetch_page
from app.schemas.platform_schema import PlatformStatus, PlatformCategory


class NykaaConnector(BaseConnector):
    platform_id = "nykaa"
    platform_name = "Nykaa"
    platform_category = PlatformCategory.BEAUTY
    domain = "nykaa.com"
    requires_pin = False
    logo_url = "https://seeklogo.com/images/N/nykaa-logo-7DAAE38FA4-seeklogo.com.png"
    app_scheme = "nykaa://home"

    async def search(self, query: str, pin_code: Optional[str] = None) -> List[RawProductListing]:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.nykaa.com/search/result/?q={encoded}"
        response = await fetch_page(url)

        if not response:
            self.status = PlatformStatus.UNAVAILABLE
            return []

        if response.status_code in [403, 503] or "blocked" in response.text.lower():
            self.status = PlatformStatus.RESTRICTED_BY_ROBOTS
            return []

        listings: List[RawProductListing] = []
        soup = BeautifulSoup(response.text, "lxml")
        items = soup.select("div.productWrapper, div.css-d5w база")

        for item in items[:10]:
            title_node = item.select_one("div.css-xrzmfa, div.product-title")
            price_node = item.select_one("span.css-111z9ua, span.post-discount")
            orig_price_node = item.select_one("span.css-17x46n5, span.pre-discount")
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
                    href = f"https://www.nykaa.com{href}"

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
                        deep_link_url=f"nykaa://product/{href.split('/')[-1]}",
                        image_url=img_node.get("src") if img_node else None,
                        is_live=True,
                        delivery_pin=pin_code,
                        delivery_time_estimate="2-3 Days"
                    )
                )

        self.status = PlatformStatus.AVAILABLE
        return listings
