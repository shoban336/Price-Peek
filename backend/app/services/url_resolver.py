"""Service layer URL resolver providing targeted store routing logic."""
import re
import urllib.parse
from typing import Optional, Tuple

# Re-export core intelligence resolvers
from app.intelligence.url_resolver import (
    ResolvedProductURL,
    parse_product_url,
    clean_slug_to_query,
    clean_store_search_query,
    generate_store_outbound_url as _generate_store_outbound_url,
)


def resolve_store_url(platform_id: str, query: str, raw_url: str = None) -> str:
    """
    Targeted URL resolver specifically for JioMart and Zepto, preserving
    all other platform URLs completely untouched.
    """
    p_id = platform_id.lower().strip()

    # --- ZEPTO ONLY ---
    if "zepto" in p_id:
        # Keep verified PDP links, but discard fake/broken mock IDs
        if raw_url and raw_url.startswith("http") and not any(fake in raw_url for fake in ["pvid", "prid", "dummy"]):
            return raw_url
        clean_query = re.sub(r'[/\\#?&%+]', ' ', query).strip()
        encoded = urllib.parse.quote_plus(clean_query)
        # Pass both q and query parameters so search executes immediately on load without requiring Enter
        return f"https://www.zepto.com/search?q={encoded}&query={encoded}"

    # --- JIOMART ONLY ---
    if "jiomart" in p_id:
        # Keep valid direct product links formatted with /product/
        if raw_url and "/product/" in raw_url and "search" not in raw_url and "google.com" not in raw_url:
            if raw_url.startswith("http"):
                return raw_url
            return f"https://www.jiomart.com{raw_url}"
        clean_query = re.sub(r'[/\\#?&%+]', ' ', query).strip()
        clean_query = re.sub(r'\b0\.\d+\s*(kg|l|litre|litres|gm|g|ml)\b', '', clean_query, flags=re.IGNORECASE).strip()
        clean_query = re.sub(r'\s+', ' ', clean_query)
        encoded = urllib.parse.quote_plus(clean_query)
        # Direct official JioMart search route: zero redirect notice, loads product results directly
        return f"https://www.jiomart.com/products/?q={encoded}"

    # --- ALL OTHER PLATFORMS: RETURN AS-IS WITHOUT MODIFICATION ---
    return raw_url


def generate_store_outbound_url(
    platform_id: str,
    query: str,
    verified_pdp_url: Optional[str] = None
) -> Tuple[str, str]:
    """Generate outbound URL routing through resolve_store_url for Zepto & JioMart."""
    p_id = platform_id.lower().strip()
    if "zepto" in p_id or "jiomart" in p_id:
        final_url = resolve_store_url(p_id, query, verified_pdp_url)
        clean_q = re.sub(r'[/\\#?&%+]', ' ', query).strip()
        encoded = urllib.parse.quote_plus(clean_q)
        if "zepto" in p_id:
            deep = f"zepto://search?query={encoded}" if "search" in final_url else f"zepto://product/{final_url.split('/')[-1]}"
        else:
            sku = final_url.split('/')[-1] if "/product/" in final_url else "search"
            deep = f"jiomart://product/{sku}"
        return final_url, deep

    return _generate_store_outbound_url(platform_id, query, verified_pdp_url)
