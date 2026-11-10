"""JioMart Storefront Connector."""
import urllib.parse
import re
from bs4 import BeautifulSoup
from typing import List, Optional
from app.connectors.base_connector import BaseConnector, RawProductListing
from app.connectors.http_client import fetch_page
from app.schemas.platform_schema import PlatformStatus, PlatformCategory


def format_jiomart_product_url(raw_url: Optional[str]) -> str:
    """
    Ensures JioMart URLs strictly follow the modern working pattern:
    https://www.jiomart.com/product/<slug-and-sku>
    Rejects legacy /p/ paths and search fallbacks.
    """
    if not raw_url or not isinstance(raw_url, str):
        return ""

    url = raw_url.strip()

    # Reject legacy /p/ paths, search routes, and empty paths that cause 404s
    if "/p/" in url or "/search" in url or "?q=" in url or "&q=" in url:
        return ""

    # Ensure it follows the modern /product/ pattern
    if "/product/" in url:
        if url.startswith("http://") or url.startswith("https://"):
            return url
        if url.startswith("/"):
            return f"https://www.jiomart.com{url}"
        return f"https://www.jiomart.com/{url}"

    return ""


def build_universal_jiomart_url(raw_product_url: Optional[str] = None, product_name: str = "") -> str:
    """
    Universally generates a valid JioMart URL.
    Prioritizes canonical product page URLs (/product/...) and handles search query
    routing for connector scraping without invalid query parameters (?q=) or search-breaking tokens.
    """
    # 1. If a product page URL is captured, format via strict modern /product/ pattern
    if raw_product_url:
        formatted = format_jiomart_product_url(raw_product_url)
        if formatted:
            return formatted
        if not product_name:
            return ""

    # 2. Universal query cleaner for search fallback (used when scraping search results)
    # Remove decimal normalized units that break JioMart routing (e.g., 0.1kg, 0.5L)
    clean = re.sub(r'\b0\.\d+\s*(kg|l|litre|litres|gm|g|ml)\b', '', product_name, flags=re.IGNORECASE)
    
    # Remove technical punctuation/symbols that cause 404s in JioMart path routing
    clean = re.sub(r'[/\\#?&%+]', ' ', clean)
    
    # Collapse multiple spaces
    clean = re.sub(r'\s+', ' ', clean).strip()

    # Fallback to base product name if clean became empty
    if not clean:
        clean = product_name.strip()

    if not clean:
        return ""

    # JioMart uses path-based search routing: /search/<encoded_term> (NEVER ?q=)
    encoded_term = urllib.parse.quote(clean)
    return f"https://www.jiomart.com/search/{encoded_term}"


class JioMartConnector(BaseConnector):
    platform_id = "jiomart"
    platform_name = "JioMart"
    platform_category = PlatformCategory.GROCERY
    domain = "jiomart.com"
    requires_pin = True
    logo_url = "https://www.jiomart.com/assets/ds2web/jio-mart-logo-square.svg"
    app_scheme = "jiomart://home"

    async def search(self, query: str, pin_code: Optional[str] = None) -> List[RawProductListing]:
        url = build_universal_jiomart_url(product_name=query)
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
            link_node = item.select_one("a[href*='/product/']")
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

                raw_href = link_node.get("href", "")
                product_url = format_jiomart_product_url(raw_href)
                # Strictly require a verified direct /product/ URL
                if not product_url:
                    continue

                discount = None
                if orig_price and orig_price > price:
                    discount = round(((orig_price - price) / orig_price) * 100, 1)

                sku_part = product_url.split('/')[-1]
                listings.append(
                    RawProductListing(
                        platform_id=self.platform_id,
                        platform_name=self.platform_name,
                        platform_category=self.platform_category.value,
                        title=raw_title,
                        price=price,
                        original_price=orig_price,
                        discount_percent=discount,
                        product_url=product_url,
                        deep_link_url=f"jiomart://product/{sku_part}",
                        image_url=img_node.get("src") if img_node else None,
                        is_live=True,
                        delivery_pin=pin_code,
                        delivery_time_estimate="Today / Tomorrow"
                    )
                )

        self.status = PlatformStatus.AVAILABLE
        return listings
