"""Universal Product Search and Price Comparison Endpoint."""
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, status
from app.config.settings import get_settings
from app.schemas.search_schema import (
    SearchRequest,
    SearchResponse,
    AutocompleteItem,
)
from app.services.search_service import execute_universal_search
from app.services.autocomplete_service import get_autocomplete_suggestions

router = APIRouter(prefix="/search", tags=["Universal Search"])
settings = get_settings()


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
