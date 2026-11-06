"""Pydantic schemas for Price Drop Alerts (Buyhatke style)."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr


class CreatePriceAlertRequest(BaseModel):
    product_name: str = Field(..., min_length=2, max_length=255)
    target_price: float = Field(..., gt=0.0)
    current_price: float = Field(..., gt=0.0)
    email: str = Field(..., min_length=5, max_length=255)
    product_id: Optional[str] = None


class PriceAlertResponse(BaseModel):
    id: int
    product_name: str
    target_price: float
    current_price: float
    email: str
    status: str
    created_at: datetime
    triggered_at: Optional[datetime] = None


class PriceAlertListResponse(BaseModel):
    total_alerts: int
    alerts: List[PriceAlertResponse]
