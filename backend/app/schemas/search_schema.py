"""Pydantic schemas for Universal Product Search and Price Comparison."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime


class ParsedQuery(BaseModel):
    """Structured attributes extracted from an unstructured user search query."""
    raw_query: str
    brand: Optional[str] = None
    product_name: str
    category: Optional[str] = None
    model: Optional[str] = None
    normalized_quantity: Optional[float] = None
    normalized_unit: Optional[str] = None
    variant: Optional[str] = None


class ProductListing(BaseModel):
    """Standardized representation of a single product listing from any shopping platform."""
    platform_id: str
    platform_name: str
    platform_category: str  # e.g., quick_commerce, ecommerce, pharmacy, grocery, electronics
    title: str
    brand: Optional[str] = None
    price: float = Field(..., ge=0.0, description="Current selling price")
    original_price: Optional[float] = Field(None, ge=0.0, description="MRP or original listed price")
    discount_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    currency: str = "INR"
    in_stock: bool = True
    rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    rating_count: Optional[int] = Field(None, ge=0)
    product_url: str = Field(..., description="Mandatory direct URL to exact product page")
    deep_link_url: Optional[str] = Field(None, description="App deep link (e.g. native app intent)")
    image_url: Optional[str] = None
    normalized_quantity: Optional[float] = None
    normalized_unit: Optional[str] = None
    variant: Optional[str] = None
    is_live: bool = Field(True, description="True if fetched live; False if cached/fallback")
    delivery_pin: Optional[str] = None
    delivery_time_estimate: Optional[str] = None  # e.g. "10 mins", "Same Day", "2 Days"


class ComparisonSummary(BaseModel):
    """Aggregated numerical price insights computed via Pandas/NumPy."""
    cheapest_platform: Optional[str] = None
    cheapest_platform_id: Optional[str] = None
    lowest_price: Optional[float] = None
    highest_price: Optional[float] = None
    average_price: Optional[float] = None
    max_savings: Optional[float] = None
    total_active_listings: int = 0
    total_platforms_queried: int = 0


class SearchRequest(BaseModel):
    """Request payload for universal product price search."""
    query: str = Field(..., min_length=1, max_length=200, description="Product search string")
    pin_code: Optional[str] = Field(None, description="6-digit Indian Postal Delivery Code")
    platforms: Optional[List[str]] = Field(None, description="Optional filter of specific platform IDs")
    sort_by: Optional[str] = Field("price_asc", description="Sorting criteria: price_asc, price_desc, discount_desc, rating_desc")


class SearchResponse(BaseModel):
    """Unified API response for product price comparison."""
    query: str
    delivery_pin: str
    parsed_query: ParsedQuery
    summary: ComparisonSummary
    listings: List[ProductListing] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AutocompleteItem(BaseModel):
    """Rich product suggestion for live autocomplete dropdown (Blinkit style)."""
    id: str
    name: str
    imageUrl: Optional[str] = None
    category: Optional[str] = None
    pack_size: Optional[str] = None
    subtitle: Optional[str] = None
