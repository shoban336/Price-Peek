"""Pydantic schemas for Dynamic Platform Registry management."""
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class PlatformStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    RESTRICTED_BY_ROBOTS = "RESTRICTED_BY_ROBOTS"
    UNAVAILABLE = "UNAVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"


class PlatformCategory(str, Enum):
    ECOMMERCE = "ecommerce"
    QUICK_COMMERCE = "quick_commerce"
    GROCERY = "grocery"
    ELECTRONICS = "electronics"
    FASHION = "fashion"
    PHARMACY = "pharmacy"
    BEAUTY = "beauty"
    OTHER = "other"


class PlatformSchema(BaseModel):
    """Platform details in the dynamic registry."""
    id: str = Field(..., description="Unique platform identifier (e.g. 'amazon', 'blinkit', 'croma')")
    name: str = Field(..., description="Display name of the platform")
    category: PlatformCategory
    domain: str = Field(..., description="Storefront domain (e.g. 'blinkit.com')")
    enabled: bool = True
    status: PlatformStatus = PlatformStatus.AVAILABLE
    requires_pin: bool = False
    supported_regions: List[str] = ["IN"]
    logo_url: Optional[str] = None
    app_scheme: Optional[str] = Field(None, description="Mobile URI scheme for deep linking")
    description: Optional[str] = None


class PlatformUpdateSchema(BaseModel):
    """Schema to update an existing platform registration."""
    enabled: Optional[bool] = None
    status: Optional[PlatformStatus] = None
    description: Optional[str] = None


class PlatformListResponse(BaseModel):
    """Response containing all registered shopping platforms."""
    total: int
    platforms: List[PlatformSchema]
