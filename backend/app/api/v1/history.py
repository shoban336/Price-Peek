"""Price History API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, status
from pydantic import BaseModel
from datetime import datetime, timedelta

router = APIRouter(prefix="/history", tags=["Price History"])


class PriceHistoryPoint(BaseModel):
    date: datetime
    platform_id: str
    platform_name: str
    price: float


class PriceHistoryResponse(BaseModel):
    product_identifier: str
    total_data_points: int
    history: List[PriceHistoryPoint]


@router.get("/{product_identifier}", response_model=PriceHistoryResponse)
def get_price_history(
    product_identifier: str,
    days: int = Query(30, ge=1, le=365, description="Historical lookback window in days")
) -> PriceHistoryResponse:
    """Retrieve historical price movements for an identified product across registered stores."""
    # Placeholder for Phase 2 API skeleton - backed by database in Phase 6
    now = datetime.utcnow()
    sample_points = [
        PriceHistoryPoint(
            date=now - timedelta(days=15),
            platform_id="amazon",
            platform_name="Amazon India",
            price=145.0,
        ),
        PriceHistoryPoint(
            date=now - timedelta(days=5),
            platform_id="zepto",
            platform_name="Zepto",
            price=142.0,
        ),
        PriceHistoryPoint(
            date=now,
            platform_id="blinkit",
            platform_name="Blinkit",
            price=138.0,
        ),
    ]
    return PriceHistoryResponse(
        product_identifier=product_identifier,
        total_data_points=len(sample_points),
        history=sample_points,
    )
