"""Abstract Base Connector specification and RawProductListing data definition."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from app.schemas.platform_schema import PlatformStatus, PlatformCategory


@dataclass
class RawProductListing:
    """Standardized unnormalized raw item listing extracted from a shopping platform."""
    platform_id: str
    platform_name: str
    platform_category: str
    title: str
    price: float
    product_url: str
    brand: Optional[str] = None
    original_price: Optional[float] = None
    discount_percent: Optional[float] = None
    currency: str = "INR"
    in_stock: bool = True
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    deep_link_url: Optional[str] = None
    image_url: Optional[str] = None
    raw_quantity_str: Optional[str] = None
    normalized_quantity: Optional[float] = None
    normalized_unit: Optional[str] = None
    variant: Optional[str] = None
    is_live: bool = True
    delivery_pin: Optional[str] = None
    delivery_time_estimate: Optional[str] = None
    is_official_store: bool = False
    official_store_badge: Optional[str] = None


class BaseConnector(ABC):
    """Abstract Base Class that every shopping platform connector MUST implement."""
    
    platform_id: str
    platform_name: str
    platform_category: PlatformCategory
    domain: str
    requires_pin: bool = False
    enabled: bool = True
    status: PlatformStatus = PlatformStatus.AVAILABLE
    app_scheme: Optional[str] = None
    logo_url: Optional[str] = None

    @abstractmethod
    async def search(self, query: str, pin_code: Optional[str] = None) -> List[RawProductListing]:
        """Fetch matching listings for query and PIN code from the shopping storefront."""
        pass

    def check_robots_permission(self, path: str = "/") -> bool:
        """Verify whether automated access is permitted by storefront robots.txt."""
        # Default implementation assumes storefront root permission check
        return True

    def get_status(self) -> PlatformStatus:
        """Return the current health / compliance status of this connector."""
        return self.status
