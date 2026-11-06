"""Universal Product Search and Price Comparison Endpoint."""
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, status
from app.config.settings import get_settings
from app.schemas.search_schema import (
    SearchRequest,
    SearchResponse,
    ParsedQuery,
    ComparisonSummary,
    ProductListing,
)

router = APIRouter(prefix="/search", tags=["Universal Search"])
settings = get_settings()


@router.get("", response_model=SearchResponse)
async def search_products(
    q: str = Query(..., min_length=1, description="Universal search query (e.g. 'Gold Winner Sunflower Oil 1L')"),
    pin_code: Optional[str] = Query(None, description="6-digit Indian Postal Delivery PIN code"),
    sort_by: str = Query("price_asc", description="Sorting criteria (price_asc, price_desc, discount_desc)")
) -> SearchResponse:
    """Universal product search across all active registered shopping platforms.
    
    Extracts brand/unit/variant attributes, delegates to registered platform connectors,
    and returns matched and price-ranked listings with mandatory direct links.
    """
    effective_pin = pin_code or settings.DEFAULT_PIN_CODE
    
    # Placeholder for Phase 2 API skeleton - replaced dynamically by orchestrator in Phase 3-5
    from app.intelligence.parser import parse_query
    parsed = parse_query(q)
    
    summary = ComparisonSummary(
        cheapest_platform=None,
        cheapest_platform_id=None,
        lowest_price=None,
        highest_price=None,
        average_price=None,
        max_savings=None,
        total_active_listings=0,
        total_platforms_queried=0,
    )
    
    return SearchResponse(
        query=q,
        delivery_pin=effective_pin,
        parsed_query=parsed,
        summary=summary,
        listings=[]
    )
