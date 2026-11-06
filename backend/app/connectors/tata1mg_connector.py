"""Tata 1mg Healthcare & Pharmacy Connector."""
import urllib.parse
from bs4 import BeautifulSoup
from typing import List, Optional
from app.connectors.base_connector import BaseConnector, RawProductListing
from app.connectors.http_client import fetch_page
from app.schemas.platform_schema import PlatformStatus, PlatformCategory


class Tata1mgConnector(BaseConnector):
    platform_id = "tata1mg"
    platform_name = "Tata 1mg"
    platform_category = PlatformCategory.PHARMACY
    domain = "1mg.com"
    requires_pin = True
    logo_url = "https://www.1mg.com/favicon.ico"
    app_scheme = "tata1mg://app"

    async def search(self, query: str, pin_code: Optional[str] = None) -> List[RawProductListing]:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.1mg.com/search/all?name={encoded}"
        response = await fetch_page(url)
        
        listings: List[RawProductListing] = []
        if response and response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")
            items = soup.select("div.style__product-box___3oEU6, div.style__horizontal-card___1Zwmt")
            for item in items[:10]:
                title_node = item.select_one("div.style__pro-title___3zxNC, span.style__pro-title___2QwJy")
                price_node = item.select_one("div.style__price-tag___KzOkY")
                link_node = item.select_one("a[href*='/drugs/'], a[href*='/otc/']")
                img_node = item.select_one("img")
                
                if title_node and price_node and link_node:
                    title = title_node.get_text(strip=True)
                    price_str = price_node.get_text(strip=True).replace("₹", "").replace(",", "")
                    try:
                        price = float(price_str)
                    except ValueError:
                        continue
                        
                    href = link_node.get("href", "")
                    if href and not href.startswith("http"):
                        href = f"https://www.1mg.com{href}"
                        
                    listings.append(
                        RawProductListing(
                            platform_id=self.platform_id,
                            platform_name=self.platform_name,
                            platform_category=self.platform_category.value,
                            title=title,
                            price=price,
                            product_url=href,
                            deep_link_url=f"tata1mg://otc/{href.split('/')[-1]}",
                            image_url=img_node.get("src") if img_node else None,
                            is_live=True,
                            delivery_pin=pin_code,
                            delivery_time_estimate="Same Day Delivery"
                        )
                    )

        if not listings and response and response.status_code in [403, 503]:
            self.status = PlatformStatus.RESTRICTED_BY_ROBOTS
        else:
            self.status = PlatformStatus.AVAILABLE

        return listings
