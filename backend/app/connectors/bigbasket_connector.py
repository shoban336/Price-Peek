"""BigBasket Storefront Connector."""
import urllib.parse
from bs4 import BeautifulSoup
from typing import List, Optional
from app.connectors.base_connector import BaseConnector, RawProductListing
from app.connectors.http_client import fetch_page
from app.schemas.platform_schema import PlatformStatus, PlatformCategory


class BigBasketConnector(BaseConnector):
    platform_id = "bigbasket"
    platform_name = "BigBasket"
    platform_category = PlatformCategory.GROCERY
    domain = "bigbasket.com"
    requires_pin = True
    logo_url = "https://www.bigbasket.com/favicon.ico"
    app_scheme = "bigbasket://app"

    async def search(self, query: str, pin_code: Optional[str] = None) -> List[RawProductListing]:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.bigbasket.com/ps/?q={encoded}"
        response = await fetch_page(url)
        
        listings: List[RawProductListing] = []
        if response and response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")
            items = soup.select("li.PaginateItems___StyledLi-sc-1yrbjdr-0, div.SKUDeck___StyledDiv-sc-1e5ogfd-0")
            for item in items[:10]:
                title_node = item.select_one("h3, div.break-words")
                price_node = item.select_one("span.Pricing___StyledLabel-sc-pldi2d-1, span.Pricing___StyledLabel2-sc-pldi2d-2")
                link_node = item.select_one("a[href*='/pd/']")
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
                        href = f"https://www.bigbasket.com{href}"
                    
                    listings.append(
                        RawProductListing(
                            platform_id=self.platform_id,
                            platform_name=self.platform_name,
                            platform_category=self.platform_category.value,
                            title=title,
                            price=price,
                            product_url=href,
                            deep_link_url=f"bigbasket://product/{href.split('/')[-2]}" if "/pd/" in href else None,
                            image_url=img_node.get("src") if img_node else None,
                            is_live=True,
                            delivery_pin=pin_code,
                            delivery_time_estimate="Tomorrow Morning"
                        )
                    )

        if not listings and response and response.status_code in [403, 503]:
            self.status = PlatformStatus.RESTRICTED_BY_ROBOTS
        else:
            self.status = PlatformStatus.AVAILABLE

        return listings
