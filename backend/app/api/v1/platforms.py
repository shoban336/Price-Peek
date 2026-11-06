"""Dynamic Platform Registry API endpoints backed by PlatformRegistry."""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from app.schemas.platform_schema import (
    PlatformSchema,
    PlatformListResponse,
    PlatformUpdateSchema,
    PlatformStatus,
    PlatformCategory,
)
from app.registry import registry
from app.connectors.base_connector import BaseConnector, RawProductListing

router = APIRouter(prefix="/platforms", tags=["Dynamic Platform Registry"])


class DiscoveryValidationRequest(BaseModel):
    domain_or_url: str


class DiscoveryValidationResponse(BaseModel):
    target: str
    robots_url: str
    is_reachable: bool
    robots_accessible: bool
    recommendation: str
    notes: str


@router.get("", response_model=PlatformListResponse)
def list_platforms(
    category: Optional[PlatformCategory] = None,
    enabled_only: bool = True
) -> PlatformListResponse:
    """Retrieve all registered shopping platforms with optional category and status filtering."""
    connectors = registry.list_connectors(category=category, enabled_only=enabled_only)
    schemas = [
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
            description=f"{c.platform_name} shopping connector"
        )
        for c in connectors
    ]
    return PlatformListResponse(total=len(schemas), platforms=schemas)


@router.get("/{platform_id}", response_model=PlatformSchema)
def get_platform(platform_id: str) -> PlatformSchema:
    """Retrieve details for a specific platform by identifier."""
    c = registry.get(platform_id)
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform '{platform_id}' not found in registry."
        )
    return PlatformSchema(
        id=c.platform_id,
        name=c.platform_name,
        category=c.platform_category,
        domain=c.domain,
        enabled=c.enabled,
        status=c.status,
        requires_pin=c.requires_pin,
        logo_url=c.logo_url,
        app_scheme=c.app_scheme,
        description=f"{c.platform_name} shopping connector"
    )


class GenericDynamicConnector(BaseConnector):
    """Dynamically registered external storefront connector."""
    def __init__(self, schema: PlatformSchema):
        self.platform_id = schema.id
        self.platform_name = schema.name
        self.platform_category = schema.category
        self.domain = schema.domain
        self.enabled = schema.enabled
        self.status = schema.status
        self.requires_pin = schema.requires_pin
        self.logo_url = schema.logo_url
        self.app_scheme = schema.app_scheme

    async def search(self, query: str, pin_code: Optional[str] = None):
        return []


@router.post("", response_model=PlatformSchema, status_code=status.HTTP_201_CREATED)
def register_platform(platform: PlatformSchema) -> PlatformSchema:
    """Register a new shopping platform into the registry (Plug-and-Play capability)."""
    if registry.get(platform.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Platform '{platform.id}' is already registered."
        )
    connector = GenericDynamicConnector(platform)
    registry.register(connector)
    return platform


@router.post("/validate-discovery", response_model=DiscoveryValidationResponse)
async def validate_discovery(payload: DiscoveryValidationRequest) -> DiscoveryValidationResponse:
    """Discovery validator for potential shopping platforms: checks robots.txt and reachability."""
    report = await registry.validate_discovery(payload.domain_or_url)
    return DiscoveryValidationResponse(**report)


@router.patch("/{platform_id}", response_model=PlatformSchema)
def update_platform(platform_id: str, updates: PlatformUpdateSchema) -> PlatformSchema:
    """Update active status or enabled state of a registered connector."""
    c = registry.get(platform_id)
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform '{platform_id}' not found in registry."
        )
    if updates.enabled is not None:
        c.enabled = updates.enabled
    if updates.status is not None:
        c.status = updates.status

    return PlatformSchema(
        id=c.platform_id,
        name=c.platform_name,
        category=c.platform_category,
        domain=c.domain,
        enabled=c.enabled,
        status=c.status,
        requires_pin=c.requires_pin,
        logo_url=c.logo_url,
        app_scheme=c.app_scheme,
        description=f"{c.platform_name} shopping connector"
    )
