"""JioMart Storefront Connector."""
import urllib.parse
import re
from bs4 import BeautifulSoup
from typing import List, Optional
from app.connectors.base_connector import BaseConnector, RawProductListing
from app.connectors.http_client import fetch_page
from app.schemas.platform_schema import PlatformStatus, PlatformCategory


def build_universal_jiomart_url(raw_product_url: Optional[str] = None, product_name: str = "") -> str:
    """
    Universally generates a valid, working JioMart URL for ANY product.
    Prioritizes canonical product page URLs (/p/...) and handles search fallbacks
    without invalid query parameters (?q=) or search-breaking tokens.
    """
    # 1. If a valid, full product page URL is already captured, use it directly
    if raw_product_url and raw_product_url.startswith("http"):
        # Ensure it's not an already broken ?q= URL
        if "search?q=" not in raw_product_url:
            return raw_product_url

    # 2. If it's a relative path from scraping (e.g. /p/groceries/...), append domain
    if raw_product_url and raw_product_url.startswith("/"):
        return f"https://www.jiomart.com{raw_product_url}"

    # 3. Universal query cleaner for search fallback (applies to ALL products)
    # Remove decimal normalized units that break JioMart routing (e.g., 0.1kg, 0.5L)
    clean = re.sub(r'\b0\.\d+\s*(kg|l|litre|litres|gm|g|ml)\b', '', product_name, flags=re.IGNORECASE)
    
    # Remove technical punctuation/symbols that cause 404s in JioMart path routing
    clean = re.sub(r'[/\\#?&%+]', ' ', clean)
    
    # Collapse multiple spaces
    clean = re.sub(r'\s+', ' ', clean).strip()

    # Fallback to base product name if clean became empty
    if not clean:
        clean = product_name.strip()

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

                raw_href = link_node.get("href", "")
                product_url = build_universal_jiomart_url(raw_product_url=raw_href, product_name=raw_title)

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
                        product_url=product_url,
                        deep_link_url=f"jiomart://product/{product_url.split('/')[-1]}",
                        image_url=img_node.get("src") if img_node else None,
                        is_live=True,
                        delivery_pin=pin_code,
                        delivery_time_estimate="Today / Tomorrow"
                    )
                )

        self.status = PlatformStatus.AVAILABLE
        return listings
