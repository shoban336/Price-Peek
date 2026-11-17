"""Dynamic Platform Registry Manager.
Provides plug-and-play connector management, asynchronous search aggregation, and ethical discovery validation.
"""
import asyncio
import urllib.parse
from typing import Dict, List, Optional, Any, Type
import httpx

from app.connectors.base_connector import BaseConnector, RawProductListing
from app.connectors.amazon_connector import AmazonConnector
from app.connectors.flipkart_connector import FlipkartConnector
from app.connectors.zepto_connector import ZeptoConnector
from app.connectors.blinkit_connector import BlinkitConnector
from app.connectors.instamart_connector import InstamartConnector
from app.connectors.bigbasket_connector import BigBasketConnector
from app.connectors.croma_connector import CromaConnector
from app.connectors.tata1mg_connector import Tata1mgConnector
from app.connectors.jiomart_connector import JioMartConnector
from app.connectors.myntra_connector import MyntraConnector
from app.connectors.ajio_connector import AjioConnector
from app.connectors.nykaa_connector import NykaaConnector
from app.connectors.reliance_digital_connector import RelianceDigitalConnector
from app.connectors.sangeetha_connector import SangeethaMobilesConnector
from app.connectors.vijay_sales_connector import VijaySalesConnector
from app.connectors.tatacliq_connector import TataCliqConnector
from app.connectors.nykaafashion_connector import NykaaFashionConnector
from app.connectors.amazon_fresh_connector import AmazonFreshConnector
from app.connectors.flipkart_minutes_connector import FlipkartMinutesConnector
from app.connectors.tira_connector import TiraBeautyConnector
from app.connectors.purplle_connector import PurplleConnector
from app.connectors.pharmeasy_connector import PharmEasyConnector
from app.connectors.apollo_connector import ApolloPharmacyConnector
from app.connectors.netmeds_connector import NetmedsConnector
from app.connectors.brand_official_connector import BrandOfficialConnector
from app.schemas.platform_schema import PlatformSchema, PlatformStatus, PlatformCategory


class PlatformRegistry:
    """Dynamic registry managing active shopping connectors."""

    def __init__(self):
        self._connectors: Dict[str, BaseConnector] = {}
        self._register_default_connectors()

    def _register_default_connectors(self):
        """Seed registry with all default platform connectors."""
        defaults: List[BaseConnector] = [
            AmazonConnector(),
            FlipkartConnector(),
            JioMartConnector(),
            ZeptoConnector(),
            BlinkitConnector(),
            InstamartConnector(),
            BigBasketConnector(),
            MyntraConnector(),
            AjioConnector(),
            CromaConnector(),
            Tata1mgConnector(),
            NykaaConnector(),
            RelianceDigitalConnector(),
            SangeethaMobilesConnector(),
            VijaySalesConnector(),
            TataCliqConnector(),
            NykaaFashionConnector(),
            AmazonFreshConnector(),
            FlipkartMinutesConnector(),
            TiraBeautyConnector(),
            PurplleConnector(),
            PharmEasyConnector(),
            ApolloPharmacyConnector(),
            NetmedsConnector(),
            BrandOfficialConnector(),
        ]
        for conn in defaults:
            self._connectors[conn.platform_id] = conn

    def register(self, connector: BaseConnector) -> None:
        """Register a new plug-and-play connector dynamically."""
        self._connectors[connector.platform_id] = connector

    def unregister(self, platform_id: str) -> bool:
        """Remove a connector from active registration."""
        if platform_id in self._connectors:
            del self._connectors[platform_id]
            return True
        return False

    def get(self, platform_id: str) -> Optional[BaseConnector]:
        """Fetch connector instance by identifier."""
        return self._connectors.get(platform_id)

    def list_connectors(
        self,
        category: Optional[PlatformCategory] = None,
        enabled_only: bool = True
    ) -> List[BaseConnector]:
        """List connectors matching category and enablement filters."""
        results = list(self._connectors.values())
        if enabled_only:
            results = [c for c in results if c.enabled]
        if category:
            results = [c for c in results if c.platform_category == category]
        return results

    def get_schemas(self, enabled_only: bool = True) -> List[PlatformSchema]:
        """Export platform metadata schemas for API and Admin Dashboard."""
        connectors = self.list_connectors(enabled_only=enabled_only)
        schemas = []
        for c in connectors:
            schemas.append(
                PlatformSchema(
                    id=c.platform_id,
                    name=c.platform_name,
                    category=c.platform_category,
                    domain=c.domain,
                    enabled=c.enabled,
                    status=c.status,
                    requires_pin=c.requires_pin,
                    logo_url=c.logo_url,
                    app_scheme=c.app_scheme,
                    description=f"{c.platform_name} connector"
                )
            )
        return schemas

    async def validate_discovery(self, domain_or_url: str) -> Dict[str, Any]:
        """Discovery validator that probes robots.txt and server availability for a prospective platform."""
        clean = domain_or_url.strip()
        if not clean.startswith("http://") and not clean.startswith("https://"):
            clean = f"https://{clean}"
        parsed = urllib.parse.urlparse(clean)
        domain = parsed.netloc or parsed.path
        
        robots_url = f"https://{domain}/robots.txt"
        result = {
            "target": domain,
            "robots_url": robots_url,
            "is_reachable": False,
            "robots_accessible": False,
            "recommendation": "UNAVAILABLE",
            "notes": ""
        }

        try:
            async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
                res = await client.get(robots_url)
                if res.status_code == 200:
                    result["is_reachable"] = True
                    result["robots_accessible"] = True
                    robots_text = res.text.lower()
                    if "user-agent: *" in robots_text and "disallow: /" in robots_text:
                        result["recommendation"] = "RESTRICTED_BY_ROBOTS"
                        result["notes"] = "robots.txt explicitly disallows general automated agents."
                    else:
                        result["recommendation"] = "COMPLIANT_CANDIDATE"
                        result["notes"] = "Storefront is responsive and permits selective crawling."
                elif res.status_code in [403, 401]:
                    result["is_reachable"] = True
                    result["recommendation"] = "RESTRICTED_BY_ROBOTS"
                    result["notes"] = "Access denied by Cloudflare or firewall."
                else:
                    result["is_reachable"] = True
                    result["recommendation"] = "AVAILABLE"
                    result["notes"] = f"Responded with status {res.status_code}."
        except Exception as e:
            result["notes"] = f"Connection failed: {str(e)}"

        return result

    async def search_all(
        self,
        query: str,
        pin_code: Optional[str] = None,
        category: Optional[PlatformCategory] = None,
        platform_ids: Optional[List[str]] = None
    ) -> List[RawProductListing]:
        """Asynchronously query all eligible and active connectors in parallel."""
        selected_connectors = self.list_connectors(category=category, enabled_only=True)
        
        if platform_ids:
            selected_connectors = [c for c in selected_connectors if c.platform_id in platform_ids]

        # Execute searches concurrently
        tasks = [c.search(query=query, pin_code=pin_code) for c in selected_connectors]
        results_nested = await asyncio.gather(*tasks, return_exceptions=True)

        all_listings: List[RawProductListing] = []
        for res in results_nested:
            if isinstance(res, list):
                all_listings.extend(res)
            elif isinstance(res, Exception):
                # An individual connector failure never breaks the search
                continue

        return all_listings


# Global registry singleton
registry = PlatformRegistry()
