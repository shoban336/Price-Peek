"""Pandas and NumPy based price comparison, ranking, and discount computation engine."""
import re
import urllib.parse
from typing import List, Tuple, Optional, Any
import pandas as pd
import numpy as np

from app.schemas.search_schema import ProductListing, ComparisonSummary


def is_valid_pdp_listing(listing: Any) -> bool:
    """
    Ensures only genuine, direct product listings are included in comparison results.
    Excludes search fallbacks, homepages, and empty URLs across ALL platforms.
    """
    if not listing:
        return False

    # Extract product_url and price supporting dicts, dataclasses, and Pydantic models
    if isinstance(listing, dict):
        product_url = listing.get("product_url")
        price = listing.get("price") if listing.get("price") is not None else listing.get("current_price")
    else:
        product_url = getattr(listing, "product_url", None)
        price = getattr(listing, "price", None)
        if price is None:
            price = getattr(listing, "current_price", None)

    if not product_url or not isinstance(product_url, str):
        return False

    url = product_url.strip().lower()

    # Exclude invalid URL structures
    if not (url.startswith("http://") or url.startswith("https://")):
        return False

    parsed_url = urllib.parse.urlparse(url)
    path = parsed_url.path.strip('/')
    if not path:
        return False

    # Reject generic homepages
    domain_only = re.sub(r'https?://(www\.)?', '', url).strip('/')
    if domain_only in [
        "amazon.in", "flipkart.com", "jiomart.com", "blinkit.com",
        "zeptonow.com", "bigbasket.com", "croma.com", "myntra.com",
        "ajio.com", "nykaa.com", "1mg.com"
    ]:
        return False

    # Reject search route fallbacks across all platforms
    search_patterns = [
        "/search/", "/search?", "?q=", "&q=", "?k=", 
        "/ps/?q=", "/s/?q=", "site:jiomart.com", "site:amazon.in",
        "/searchb?", "/catalogsearch/", "/search"
    ]
    if any(pattern in url for pattern in search_patterns):
        return False

    # Strictly require modern /product/ URL pattern for JioMart and reject legacy /p/ paths
    if "jiomart.com" in parsed_url.netloc or "jiomart" in parsed_url.netloc:
        if "/product/" not in url or "/p/" in url:
            return False

    # Must have a valid positive price
    if price is None:
        return False
    try:
        if float(price) <= 0:
            return False
    except (ValueError, TypeError):
        return False

    return True


def compare_and_rank_prices(
    listings: List[ProductListing],
    sort_by: str = "price_asc",
    total_platforms_queried: int = 0
) -> Tuple[List[ProductListing], ComparisonSummary]:
    """Process, statistically analyze, and sort product prices using Pandas and NumPy.
    
    Identifies the cheapest option, calculates max savings and statistical spread,
    and returns sorted listings with a detailed ComparisonSummary.
    Strictly excludes any listings that fail direct canonical PDP verification.
    """
    # Strict validation: exclude any non-PDP or search fallback listing
    valid_listings = [item for item in listings if is_valid_pdp_listing(item)]

    if not valid_listings:
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
    records = [item.model_dump() for item in valid_listings]
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
    in_stock_df = df[df["in_stock"] == True]
    calc_df = in_stock_df if not in_stock_df.empty else df

    price_series = calc_df["price"].to_numpy()
    lowest_price = float(np.min(price_series))
    highest_price = float(np.max(price_series))
    average_price = round(float(np.mean(price_series)), 2)
    max_savings = round(highest_price - lowest_price, 2)

    # Locate the cheapest in-stock listing
    cheapest_idx = calc_df["price"].idxmin()
    cheapest_row = calc_df.loc[cheapest_idx]
    cheapest_platform_name = str(cheapest_row["platform_name"])
    cheapest_platform_id = str(cheapest_row["platform_id"])

    # Sorting options (in-stock items prioritized first)
    if sort_by == "price_desc":
        df = df.sort_values(by=["in_stock", "price"], ascending=[False, False])
    elif sort_by == "discount_desc":
        df = df.sort_values(by=["in_stock", "discount_percent", "price"], ascending=[False, False, True], na_position="last")
    elif sort_by == "rating_desc":
        df = df.sort_values(by=["in_stock", "rating", "price"], ascending=[False, False, True], na_position="last")
    else:  # Default price_asc
        df = df.sort_values(by=["in_stock", "price"], ascending=[False, True])

    # Clean NaN values that Pandas introduces for Optional fields
    records = df.to_dict(orient="records")
    cleaned_records = []
    for r in records:
        cleaned_row = {}
        for k, v in r.items():
            if pd.isna(v):
                cleaned_row[k] = None
            else:
                cleaned_row[k] = v
        cleaned_records.append(cleaned_row)

    sorted_listings = [ProductListing(**row) for row in cleaned_records]

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
