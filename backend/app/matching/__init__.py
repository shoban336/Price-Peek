"""Matching package for PricePeek."""
from .matcher import compute_similarity, matches_product, filter_and_normalize_listings

__all__ = ["compute_similarity", "matches_product", "filter_and_normalize_listings"]
