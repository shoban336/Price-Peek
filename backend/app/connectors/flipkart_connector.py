"""Flipkart Storefront Connector."""
import urllib.parse
from bs4 import BeautifulSoup
from typing import List, Optional
from app.connectors.base_connector import BaseConnector, RawProductListing
from app.connectors.http_client import fetch_page
from app.schemas.platform_schema import PlatformStatus, PlatformCategory


class FlipkartConnector(BaseConnector):
    platform_id = "flipkart"
    platform_name = "Flipkart"
    platform_category = PlatformCategory.ECOMMERCE
    domain = "flipkart.com"
    requires_pin = True
    logo_url = "https://seeklogo.com/images/F/flipkart-logo-3F33927DAA-seeklogo.com.png"
    app_scheme = "flipkart://in"

    async def search(self, query: str, pin_code: Optional[str] = None) -> List[RawProductListing]:
        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"https://www.flipkart.com/search?q={encoded_query}"
        
        response = await fetch_page(search_url)
        if not response:
            self.status = PlatformStatus.UNAVAILABLE
            return []

        if response.status_code in [403, 503] or "blocked" in response.text.lower():
            self.status = PlatformStatus.RESTRICTED_BY_ROBOTS
            return []

        listings: List[RawProductListing] = []
        soup = BeautifulSoup(response.text, "lxml")
        
        # Flipkart uses different row wrappers for electronics vs general goods
        items = soup.select('div[data-id], div._1AtVbE, div.slAVV4, div._75nlfW')
        for item in items[:10]:
            title_node = item.select_one("div.KzDlHZ, a.wjcEIp, a.s1Q9rs, div._4rR01T")
            price_node = item.select_one("div.Nx9bqj, div._30jeq3")
            orig_price_node = item.select_one("div.yRaY8j, div._3I9_wc")
            link_node = item.select_one("a[href*='/p/'], a.CGtC5Q, a._1fQZEK")
            img_node = item.select_one("img.DByuf4, img._396cs4")
            rating_node = item.select_one("div.XQDdHH, div._3LWZlK")

            if not title_node or not price_node:
                continue

            raw_title = title_node.get_text(strip=True)
            href = link_node.get("href", "") if link_node else ""
            if href and not href.startswith("http"):
                href = f"https://www.flipkart.com{href}"
            clean_url = href.split("?pid=")[0] if "?pid=" in href and "/p/" in href else href
            if not clean_url:
                continue

            price_str = price_node.get_text(strip=True).replace("₹", "").replace(",", "")
            try:
                price = float(price_str)
            except ValueError:
                continue

            orig_price = None
            if orig_price_node:
                try:
                    orig_price = float(orig_price_node.get_text(strip=True).replace("₹", "").replace(",", ""))
                except ValueError:
                    orig_price = None

            rating = None
            if rating_node:
                try:
                    rating = float(rating_node.get_text(strip=True))
                except ValueError:
                    rating = None

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
                    rating=rating,
                    product_url=clean_url,
                    deep_link_url=f"flipkart://dl/product/{clean_url.split('/')[-1]}",
                    image_url=img_node.get("src") if img_node else None,
                    is_live=True,
                    delivery_pin=pin_code,
                    delivery_time_estimate="2-3 Days"
                )
            )

        self.status = PlatformStatus.AVAILABLE
        return listings
