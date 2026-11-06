"""SQLAlchemy model for shopping platforms in the dynamic registry."""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Text, DateTime
from sqlalchemy.orm import relationship
from app.config.database import Base


class Platform(Base):
    __tablename__ = "platforms"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False, default="ecommerce")
    domain = Column(String(100), nullable=False)
    enabled = Column(Boolean, default=True)
    status = Column(String(50), default="AVAILABLE")
    requires_pin = Column(Boolean, default=False)
    logo_url = Column(String(500), nullable=True)
    app_scheme = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    listings = relationship("ProductListingRecord", back_populates="platform", cascade="all, delete-orphan")
    history_entries = relationship("PriceHistoryRecord", back_populates="platform", cascade="all, delete-orphan")
