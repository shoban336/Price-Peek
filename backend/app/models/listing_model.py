"""SQLAlchemy model for product listings on specific platforms."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.config.database import Base


class ProductListingRecord(Base):
    __tablename__ = "product_listings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    platform_id = Column(String(50), ForeignKey("platforms.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    price = Column(Float, nullable=False)
    original_price = Column(Float, nullable=True)
    discount_percent = Column(Float, nullable=True)
    product_url = Column(Text, nullable=False)
    deep_link_url = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    in_stock = Column(Boolean, default=True)
    rating = Column(Float, nullable=True)
    delivery_pin = Column(String(10), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="listings")
    platform = relationship("Platform", back_populates="listings")
