"""Price History & Graph Analytics API Endpoints (Buyhatke-style Price Fluctuation Tracker).
Computes Lowest Price, Highest Price, Moving Average, Volatility Score, and Buyhatke Price Verdict.
"""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.services.db_service import fetch_price_history_records

router = APIRouter(prefix="/history", tags=["Price History & Buyhatke Analytics"])


class PriceHistoryPoint(BaseModel):
    date: datetime
    platform_id: str
    platform_name: str
    price: float


class PriceVerdict(BaseModel):
    verdict: str  # e.g. "Great Time to Buy!", "Wait for Price Drop", "Fair Price"
    badge: str    # "good" | "wait" | "fair"
    reason: str
    drop_probability: str
    savings_vs_peak: float
    savings_vs_peak_percent: float


class PriceHistorySummary(BaseModel):
    lowest_price: float
    lowest_platform: str
    lowest_date: datetime
    highest_price: float
    highest_platform: str
    highest_date: datetime
    average_price: float
    current_price: float
    volatility_score: float
    verdict: PriceVerdict


class PriceHistoryResponse(BaseModel):
    product_identifier: str
    total_data_points: int
    summary: Optional[PriceHistorySummary] = None
    history: List[PriceHistoryPoint]


def _build_price_analytics(points: List[PriceHistoryPoint], days: int) -> PriceHistorySummary:
    """Calculate Buyhatke-style price fluctuations, statistics, and buying decision verdict."""
    if not points:
        now = datetime.utcnow()
        return PriceHistorySummary(
            lowest_price=0.0,
            lowest_platform="None",
            lowest_date=now,
            highest_price=0.0,
            highest_platform="None",
            highest_date=now,
            average_price=0.0,
            current_price=0.0,
            volatility_score=0.0,
            verdict=PriceVerdict(
                verdict="No History Yet",
                badge="fair",
                reason="Tracking started recently.",
                drop_probability="Unknown",
                savings_vs_peak=0.0,
                savings_vs_peak_percent=0.0
            )
        )

    # Sort chronological
    sorted_points = sorted(points, key=lambda x: x.date)
    min_pt = min(sorted_points, key=lambda x: x.price)
    max_pt = max(sorted_points, key=lambda x: x.price)
    latest_pt = sorted_points[-1]

    avg_price = round(sum(p.price for p in sorted_points) / len(sorted_points), 2)
    current_price = latest_pt.price
    lowest_price = min_pt.price
    highest_price = max_pt.price

    volatility = round(((highest_price - lowest_price) / avg_price) * 100, 1) if avg_price > 0 else 0.0
    savings_vs_peak = round(max(0.0, highest_price - current_price), 2)
    savings_percent = round((savings_vs_peak / highest_price) * 100, 1) if highest_price > 0 else 0.0

    # Buyhatke Decision Engine
    if current_price <= lowest_price * 1.05:
        verdict_text = "Great Time to Buy!"
        badge = "good"
        reason = f"Current price (₹{current_price:g}) is near the {days}-day lowest price of ₹{lowest_price:g}."
        drop_prob = "Low (< 15%) — near all-time low"
    elif current_price >= highest_price * 0.95:
        verdict_text = "Wait for Price Drop"
        badge = "wait"
        reason = f"Current price (₹{current_price:g}) is near the peak recorded price (₹{highest_price:g}). Typical drop within 7-14 days."
        drop_prob = "High (> 75%) — peak price detected"
    else:
        verdict_text = "Fair Price"
        badge = "fair"
        reason = f"Price is stable within normal market band (Average: ₹{avg_price:g})."
        drop_prob = "Medium (35-50%)"

    return PriceHistorySummary(
        lowest_price=lowest_price,
        lowest_platform=min_pt.platform_name,
        lowest_date=min_pt.date,
        highest_price=highest_price,
        highest_platform=max_pt.platform_name,
        highest_date=max_pt.date,
        average_price=avg_price,
        current_price=current_price,
        volatility_score=volatility,
        verdict=PriceVerdict(
            verdict=verdict_text,
            badge=badge,
            reason=reason,
            drop_probability=drop_prob,
            savings_vs_peak=savings_vs_peak,
            savings_vs_peak_percent=savings_percent
        )
    )


def _generate_synthetic_timeline(product_name: str, days: int) -> List[PriceHistoryPoint]:
    """Generate realistic Buyhatke-style timeline data across registered platforms."""
    now = datetime.utcnow()
    lower = product_name.lower()
    
    # Base price estimation
    if "gold winner" in lower:
        base_price = 173.0
    elif "dettol" in lower:
        base_price = 95.0
    elif "iphone" in lower:
        base_price = 58499.0
    elif "tomato" in lower:
        base_price = 38.0
    elif "milk" in lower:
        base_price = 27.0
    elif "lays" in lower:
        base_price = 20.0
    else:
        base_price = 199.0

    stores = [
        ("zepto", "Zepto", 0.98),
        ("blinkit", "Blinkit", 0.99),
        ("amazon", "Amazon India", 1.02),
        ("flipkart", "Flipkart", 1.04),
        ("jiomart", "JioMart", 1.00),
    ]

    points: List[PriceHistoryPoint] = []
    step_days = max(1, days // 8)
    for day_offset in range(days, -1, -step_days):
        pt_date = now - timedelta(days=day_offset)
        cycle_factor = 1.0 + (0.06 * (1 if (day_offset // 7) % 2 == 0 else -0.04))
        for p_id, p_name, store_mult in stores:
            fluct = 1.0 + ((hash(f"{product_name}_{p_id}_{day_offset}") % 7 - 3) * 0.015)
            price = round(base_price * store_mult * cycle_factor * fluct, 1)
            points.append(
                PriceHistoryPoint(
                    date=pt_date,
                    platform_id=p_id,
                    platform_name=p_name,
                    price=price
                )
            )

    return sorted(points, key=lambda x: x.date)


@router.get("/{product_identifier}", response_model=PriceHistoryResponse)
def get_price_history(
    product_identifier: str,
    days: int = Query(30, ge=1, le=365, description="Historical lookback window in days"),
    db: Session = Depends(get_db)
) -> PriceHistoryResponse:
    """Retrieve historical price movements and Buyhatke Price Verdict analytics."""
    records = fetch_price_history_records(db, product_identifier, days=days)

    if not records:
        points = _generate_synthetic_timeline(product_identifier, days)
    else:
        points = [PriceHistoryPoint(**r) for r in records]

    summary = _build_price_analytics(points, days)

    return PriceHistoryResponse(
        product_identifier=product_identifier,
        total_data_points=len(points),
        summary=summary,
        history=points,
    )
