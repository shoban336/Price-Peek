"""Amazon India Storefront Connector."""
import urllib.parse
from bs4 import BeautifulSoup
from typing import List, Optional
from app.connectors.base_connector import BaseConnector, RawProductListing
from app.connectors.http_client import fetch_page
from app.schemas.platform_schema import PlatformStatus, PlatformCategory


class AmazonConnector(BaseConnector):
    platform_id = "amazon"
    platform_name = "Amazon India"
    platform_category = PlatformCategory.ECOMMERCE
    domain = "amazon.in"
    requires_pin = True
    logo_url = "https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg"
    app_scheme = "amazon://in"

    async def search(self, query: str, pin_code: Optional[str] = None) -> List[RawProductListing]:
        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"https://www.amazon.in/s?k={encoded_query}"
        
        response = await fetch_page(search_url)
        if not response:
            self.status = PlatformStatus.UNAVAILABLE
            return []

        if response.status_code in [403, 503] or "api-services-support@amazon.com" in response.text or "Robot Check" in response.text:
            self.status = PlatformStatus.RESTRICTED_BY_ROBOTS
            return []

        listings: List[RawProductListing] = []
        soup = BeautifulSoup(response.text, "lxml")
        
        items = soup.select('div[data-component-type="s-search-result"]')
        for item in items[:10]:
            title_node = item.select_one("h2 a span, h2 span")
            link_node = item.select_one("h2 a")
            price_node = item.select_one("span.a-price-whole")
            orig_price_node = item.select_one("span.a-price.a-text-price span.a-offscreen")
            img_node = item.select_one("img.s-image")
            rating_node = item.select_one("span.a-icon-alt")
            
            if not title_node or not price_node or not link_node:
                continue

            raw_title = title_node.get_text(strip=True)
            href = link_node.get("href", "")
            if not href.startswith("http"):
                href = f"https://www.amazon.in{href}"
            # Clean tracking parameters to get direct product link
            clean_url = href.split("/ref=")[0] if "/ref=" in href else href
            
            clean_price_str = price_node.get_text(strip=True).replace(",", "").replace("₹", "")
            try:
                price = float(clean_price_str)
            except ValueError:
                continue

            orig_price = None
            if orig_price_node:
                try:
                    orig_price = float(orig_price_node.get_text(strip=True).replace(",", "").replace("₹", ""))
                except ValueError:
                    orig_price = None

            rating = None
            if rating_node:
                parts = rating_node.get_text(strip=True).split()
                try:
                    rating = float(parts[0])
                except (ValueError, IndexError):
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
                    deep_link_url=f"amazon://in/dp/{clean_url.split('/dp/')[-1]}" if "/dp/" in clean_url else None,
                    image_url=img_node.get("src") if img_node else None,
                    is_live=True,
                    delivery_pin=pin_code,
                    delivery_time_estimate="1-2 Days (Prime)"
                )
            )

        self.status = PlatformStatus.AVAILABLE
        return listings
