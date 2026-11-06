"""Price Drop Alert API Endpoints (Buyhatke Feature).
Allows shoppers to set target price thresholds and tracks alerts.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.alert_model import PriceAlertRecord
from app.schemas.alert_schema import (
    CreatePriceAlertRequest,
    PriceAlertResponse,
    PriceAlertListResponse,
)

router = APIRouter(prefix="/alerts", tags=["Price Drop Alerts (Buyhatke)"])


@router.post("", response_model=PriceAlertResponse, status_code=status.HTTP_201_CREATED)
def create_price_alert(
    payload: CreatePriceAlertRequest,
    db: Session = Depends(get_db)
) -> PriceAlertResponse:
    """Create a new Price Drop Alert threshold for a tracked product."""
    is_triggered = payload.current_price <= payload.target_price
    
    alert = PriceAlertRecord(
        product_name=payload.product_name.strip(),
        product_id=payload.product_id,
        target_price=payload.target_price,
        current_price=payload.current_price,
        email=payload.email.strip().lower(),
        status="triggered" if is_triggered else "active",
        created_at=datetime.utcnow(),
        triggered_at=datetime.utcnow() if is_triggered else None
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    return PriceAlertResponse(
        id=alert.id,
        product_name=alert.product_name,
        target_price=alert.target_price,
        current_price=alert.current_price,
        email=alert.email,
        status=alert.status,
        created_at=alert.created_at,
        triggered_at=alert.triggered_at
    )


@router.get("", response_model=PriceAlertListResponse)
def list_price_alerts(
    email: Optional[str] = Query(None, description="Filter alerts by user email"),
    status_filter: Optional[str] = Query(None, description="Filter by status: active, triggered"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
) -> PriceAlertListResponse:
    """List active or triggered price drop alerts."""
    query = db.query(PriceAlertRecord)
    if email:
        query = query.filter(PriceAlertRecord.email == email.strip().lower())
    if status_filter:
        query = query.filter(PriceAlertRecord.status == status_filter.strip().lower())
        
    records = query.order_by(PriceAlertRecord.created_at.desc()).limit(limit).all()
    
    alerts = [
        PriceAlertResponse(
            id=r.id,
            product_name=r.product_name,
            target_price=r.target_price,
            current_price=r.current_price,
            email=r.email,
            status=r.status,
            created_at=r.created_at,
            triggered_at=r.triggered_at
        )
        for r in records
    ]
    return PriceAlertListResponse(total_alerts=len(alerts), alerts=alerts)


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_price_alert(alert_id: int, db: Session = Depends(get_db)):
    """Delete an active price drop alert."""
    alert = db.query(PriceAlertRecord).filter(PriceAlertRecord.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Price alert not found")
    db.delete(alert)
    db.commit()
    return None
