"""Universal Product Search and Price Comparison Endpoint."""
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, status
from pydantic import BaseModel
from app.config.settings import get_settings
from app.schemas.search_schema import (
    SearchRequest,
    SearchResponse,
    AutocompleteItem,
)
from app.services.search_service import execute_universal_search
from app.services.autocomplete_service import get_autocomplete_suggestions
from app.intelligence.url_resolver import parse_product_url

router = APIRouter(prefix="/search", tags=["Universal Search"])
settings = get_settings()


class ResolveURLRequest(BaseModel):
    url: str
    pin_code: Optional[str] = None


class ResolveURLResponse(BaseModel):
    is_url: bool
    platform_id: Optional[str] = None
    platform_name: Optional[str] = None
    product_id: Optional[str] = None
    clean_query: Optional[str] = None
    search_results: SearchResponse


@router.post("/resolve-url", response_model=ResolveURLResponse)
async def resolve_product_link(payload: ResolveURLRequest) -> ResolveURLResponse:
    """Buyhatke Direct Product Link Resolver Endpoint.
    
    Accepts direct product URL from Amazon, Flipkart, Myntra, Blinkit, etc.,
    extracts product ASIN/ID and title, and performs full cross-platform price comparison.
    """
    resolved = parse_product_url(payload.url)
    if not resolved or not resolved.is_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or unsupported store URL. Please provide a valid product link from Amazon, Flipkart, Blinkit, Myntra, etc."
        )

    effective_pin = payload.pin_code or settings.DEFAULT_PIN_CODE
    search_resp = await execute_universal_search(
        query=resolved.clean_query or payload.url,
        pin_code=effective_pin
    )

    return ResolveURLResponse(
        is_url=True,
        platform_id=resolved.platform_id,
        platform_name=resolved.platform_name,
        product_id=resolved.product_id,
        clean_query=resolved.clean_query,
        search_results=search_resp
    )


@router.get("/autocomplete", response_model=List[AutocompleteItem])
async def autocomplete_search(
    q: str = Query(..., min_length=1, description="Partial search query (e.g. 'mil', 'apple', 'lays', 'tomato')"),
    limit: int = Query(8, ge=1, le=20, description="Max number of suggestions to return")
) -> List[AutocompleteItem]:
    """Rich live search autocomplete endpoint (Blinkit style).
    
    Returns lightweight JSON with product thumbnails, categories, pack sizes, and direct search titles.
    """
    return get_autocomplete_suggestions(query=q, limit=limit)


@router.get("", response_model=SearchResponse)
async def search_products(
    q: str = Query(..., min_length=1, description="Universal search query (e.g. 'Gold Winner Sunflower Oil 1L')"),
    pin_code: Optional[str] = Query(None, description="6-digit Indian Postal Delivery PIN code"),
    sort_by: str = Query("price_asc", description="Sorting criteria: price_asc, price_desc, discount_desc, rating_desc"),
    platforms: Optional[str] = Query(None, description="Comma-separated platform IDs to filter (e.g. 'amazon,blinkit')")
) -> SearchResponse:
    """Universal product search across all active registered shopping platforms.
    
    1. Parses query into brand, unit, model, variant.
    2. Dynamically queries registered platform connectors filtered by PIN code.
    3. Matches identical products using strict unit and variant separation.
    4. Analyzes price spread with Pandas/NumPy, flags cheapest option, and returns direct product links.
    """
    effective_pin = pin_code or settings.DEFAULT_PIN_CODE
    platform_list = [p.strip() for p in platforms.split(",")] if platforms else None
    
    return await execute_universal_search(
        query=q,
        pin_code=effective_pin,
        sort_by=sort_by,
        platform_ids=platform_list
    )


@router.post("", response_model=SearchResponse)
async def search_products_post(payload: SearchRequest) -> SearchResponse:
    """POST endpoint for structured search requests."""
    effective_pin = payload.pin_code or settings.DEFAULT_PIN_CODE
    return await execute_universal_search(
        query=payload.query,
        pin_code=effective_pin,
        sort_by=payload.sort_by or "price_asc",
        platform_ids=payload.platforms
    )
