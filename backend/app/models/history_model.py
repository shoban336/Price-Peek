"""SQLAlchemy model for recording historical price changes."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.config.database import Base


class PriceHistoryRecord(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    platform_id = Column(String(50), ForeignKey("platforms.id"), nullable=False, index=True)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    product = relationship("Product", back_populates="history_entries")
    platform = relationship("Platform", back_populates="history_entries")
