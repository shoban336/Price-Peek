"""SQLAlchemy model for normalized product entities."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from app.config.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    canonical_name = Column(String(255), nullable=False, index=True)
    brand = Column(String(100), nullable=True, index=True)
    category = Column(String(50), nullable=True, index=True)
    model = Column(String(100), nullable=True)
    normalized_quantity = Column(Float, nullable=True)
    normalized_unit = Column(String(20), nullable=True)
    variant = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    listings = relationship("ProductListingRecord", back_populates="product", cascade="all, delete-orphan")
    history_entries = relationship("PriceHistoryRecord", back_populates="product", cascade="all, delete-orphan")
