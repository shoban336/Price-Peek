"""SQLAlchemy model for Buyhatke-style Price Drop Alerts."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from app.config.database import Base


class PriceAlertRecord(Base):
    __tablename__ = "price_alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_name = Column(String(255), nullable=False, index=True)
    product_id = Column(String(100), nullable=True)
    target_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    email = Column(String(255), nullable=False, index=True)
    status = Column(String(20), default="active")  # "active", "triggered"
    created_at = Column(DateTime, default=datetime.utcnow)
    triggered_at = Column(DateTime, nullable=True)
