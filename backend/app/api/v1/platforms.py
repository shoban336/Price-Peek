"""Dynamic Platform Registry API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.schemas.platform_schema import (
    PlatformSchema,
    PlatformListResponse,
    PlatformUpdateSchema,
    PlatformStatus,
    PlatformCategory,
)

router = APIRouter(prefix="/platforms", tags=["Dynamic Platform Registry"])

# In-memory platform seed list (backed by Database in Phase 6)
_REGISTERED_PLATFORMS: dict[str, PlatformSchema] = {
    "amazon": PlatformSchema(
        id="amazon",
        name="Amazon India",
        category=PlatformCategory.ECOMMERCE,
        domain="amazon.in",
        enabled=True,
        status=PlatformStatus.AVAILABLE,
        requires_pin=True,
        logo_url="https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg",
        app_scheme="com.amazon.mShop.android.shopping",
        description="Major national e-commerce platform across all retail categories."
    ),
    "flipkart": PlatformSchema(
        id="flipkart",
        name="Flipkart",
        category=PlatformCategory.ECOMMERCE,
        domain="flipkart.com",
        enabled=True,
        status=PlatformStatus.AVAILABLE,
        requires_pin=True,
        logo_url="https://seeklogo.com/images/F/flipkart-logo-3F33927DAA-seeklogo.com.png",
        app_scheme="com.flipkart.android",
        description="Major national marketplace for electronics, fashion, and home goods."
    ),
    "zepto": PlatformSchema(
        id="zepto",
        name="Zepto",
        category=PlatformCategory.QUICK_COMMERCE,
        domain="zeptonow.com",
        enabled=True,
        status=PlatformStatus.AVAILABLE,
        requires_pin=True,
        logo_url="https://cdn.zeptonow.com/web-static-assets-prod/artifacts/12.18.0/tr:w-120,ar-120-120,pr-true,f-auto,q-80/images/logo.svg",
        app_scheme="com.zeptoconsumerapp",
        description="10-minute quick commerce delivery for groceries, essentials, and snacks."
    ),
    "blinkit": PlatformSchema(
        id="blinkit",
        name="Blinkit",
        category=PlatformCategory.QUICK_COMMERCE,
        domain="blinkit.com",
        enabled=True,
        status=PlatformStatus.AVAILABLE,
        requires_pin=True,
        logo_url="https://blinkit.com/images/blinkit-logo.png",
        app_scheme="com.grofers.customerapp",
        description="Instant delivery commerce network for groceries and daily electronics."
    ),
    "instamart": PlatformSchema(
        id="instamart",
        name="Swiggy Instamart",
        category=PlatformCategory.QUICK_COMMERCE,
        domain="swiggy.com/instamart",
        enabled=True,
        status=PlatformStatus.AVAILABLE,
        requires_pin=True,
        logo_url="https://res.cloudinary.com/swiggy/image/upload/fl_lossy,f_auto,q_auto/portal/m/seo/Logos/Swiggy_logo.png",
        app_scheme="in.swiggy.android",
        description="Swiggy's quick grocery delivery service."
    ),
    "bigbasket": PlatformSchema(
        id="bigbasket",
        name="BigBasket",
        category=PlatformCategory.GROCERY,
        domain="bigbasket.com",
        enabled=True,
        status=PlatformStatus.AVAILABLE,
        requires_pin=True,
        logo_url="https://www.bigbasket.com/favicon.ico",
        app_scheme="com.bigbasket.mobileapp",
        description="Comprehensive online grocery, household, and fresh foods supermarket."
    ),
    "croma": PlatformSchema(
        id="croma",
        name="Croma",
        category=PlatformCategory.ELECTRONICS,
        domain="croma.com",
        enabled=True,
        status=PlatformStatus.AVAILABLE,
        requires_pin=True,
        logo_url="https://www.croma.com/assets/images/croma_logo.svg",
        app_scheme="com.croma.android",
        description="Tata enterprise electronics retail chain."
    ),
    "tata1mg": PlatformSchema(
        id="tata1mg",
        name="Tata 1mg",
        category=PlatformCategory.PHARMACY,
        domain="1mg.com",
        enabled=True,
        status=PlatformStatus.AVAILABLE,
        requires_pin=True,
        logo_url="https://www.1mg.com/favicon.ico",
        app_scheme="com.aranoah.healthkart.plus",
        description="Online healthcare, pharmacy, vitamins, and personal care platform."
    ),
}


@router.get("", response_model=PlatformListResponse)
def list_platforms(
    category: Optional[PlatformCategory] = None,
    enabled_only: bool = True
) -> PlatformListResponse:
    """Retrieve all registered shopping platforms with optional category and status filtering."""
    results = list(_REGISTERED_PLATFORMS.values())
    if enabled_only:
        results = [p for p in results if p.enabled]
    if category:
        results = [p for p in results if p.category == category]
    return PlatformListResponse(total=len(results), platforms=results)


@router.get("/{platform_id}", response_model=PlatformSchema)
def get_platform(platform_id: str) -> PlatformSchema:
    """Retrieve details for a specific platform by identifier."""
    if platform_id not in _REGISTERED_PLATFORMS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform '{platform_id}' not found in registry."
        )
    return _REGISTERED_PLATFORMS[platform_id]


@router.post("", response_model=PlatformSchema, status_code=status.HTTP_201_CREATED)
def register_platform(platform: PlatformSchema) -> PlatformSchema:
    """Register a new shopping platform into the registry (Plug-and-Play capability)."""
    if platform.id in _REGISTERED_PLATFORMS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Platform '{platform.id}' is already registered."
        )
    _REGISTERED_PLATFORMS[platform.id] = platform
    return platform


@router.patch("/{platform_id}", response_model=PlatformSchema)
def update_platform(platform_id: str, updates: PlatformUpdateSchema) -> PlatformSchema:
    """Update active status or ethical crawl state of a registered platform."""
    if platform_id not in _REGISTERED_PLATFORMS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform '{platform_id}' not found in registry."
        )
    current = _REGISTERED_PLATFORMS[platform_id]
    updated_data = current.model_dump()
    for field, value in updates.model_dump(exclude_unset=True).items():
        updated_data[field] = value
    updated_platform = PlatformSchema(**updated_data)
    _REGISTERED_PLATFORMS[platform_id] = updated_platform
    return updated_platform
