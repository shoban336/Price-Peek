"""Pandas and NumPy based price comparison, ranking, and discount computation engine."""
from typing import List, Tuple, Optional
import pandas as pd
import numpy as np

from app.schemas.search_schema import ProductListing, ComparisonSummary


def compare_and_rank_prices(
    listings: List[ProductListing],
    sort_by: str = "price_asc",
    total_platforms_queried: int = 0
) -> Tuple[List[ProductListing], ComparisonSummary]:
    """Process, statistically analyze, and sort product prices using Pandas and NumPy.
    
    Identifies the cheapest option, calculates max savings and statistical spread,
    and returns sorted listings with a detailed ComparisonSummary.
    """
    if not listings:
        empty_summary = ComparisonSummary(
            cheapest_platform=None,
            cheapest_platform_id=None,
            lowest_price=None,
            highest_price=None,
            average_price=None,
            max_savings=None,
            total_active_listings=0,
            total_platforms_queried=total_platforms_queried,
        )
        return [], empty_summary

    # Build DataFrame from Pydantic models
    records = [item.model_dump() for item in listings]
    df = pd.DataFrame.from_records(records)

    # Price validation and cleaning
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["price"])
    df = df[df["price"] > 0]

    if df.empty:
        empty_summary = ComparisonSummary(
            cheapest_platform=None,
            cheapest_platform_id=None,
            lowest_price=None,
            highest_price=None,
            average_price=None,
            max_savings=None,
            total_active_listings=0,
            total_platforms_queried=total_platforms_queried,
        )
        return [], empty_summary

    # NumPy / Pandas statistics
    price_series = df["price"].to_numpy()
    lowest_price = float(np.min(price_series))
    highest_price = float(np.max(price_series))
    average_price = round(float(np.mean(price_series)), 2)
    max_savings = round(highest_price - lowest_price, 2)

    # Locate the cheapest listing
    cheapest_idx = df["price"].idxmin()
    cheapest_row = df.loc[cheapest_idx]
    cheapest_platform_name = str(cheapest_row["platform_name"])
    cheapest_platform_id = str(cheapest_row["platform_id"])

    # Sorting options
    if sort_by == "price_desc":
        df = df.sort_values(by="price", ascending=False)
    elif sort_by == "discount_desc":
        df = df.sort_values(by=["discount_percent", "price"], ascending=[False, True], na_position="last")
    elif sort_by == "rating_desc":
        df = df.sort_values(by=["rating", "price"], ascending=[False, True], na_position="last")
    else:  # Default price_asc
        df = df.sort_values(by="price", ascending=True)

    sorted_listings = [ProductListing(**row) for row in df.to_dict(orient="records")]

    summary = ComparisonSummary(
        cheapest_platform=cheapest_platform_name,
        cheapest_platform_id=cheapest_platform_id,
        lowest_price=lowest_price,
        highest_price=highest_price,
        average_price=average_price,
        max_savings=max_savings,
        total_active_listings=len(sorted_listings),
        total_platforms_queried=total_platforms_queried,
    )

    return sorted_listings, summary
