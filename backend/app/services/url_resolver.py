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
    resolve_croma_url,
    resolve_reliance_digital_url,
    resolve_vijay_sales_url,
    resolve_sangeetha_url,
    resolve_tatacliq_url,
    resolve_store_url,
    generate_store_outbound_url as _generate_store_outbound_url,
)


def resolve_store_url(platform_id: str, query: str, raw_url: str = None) -> str:
    """
    Targeted URL resolver specifically for JioMart, Zepto, Croma, and Tata 1mg, preserving
    all other platform URLs completely untouched.
    """
    if raw_url and "google.com/url" in raw_url:
        try:
            parsed_g = urllib.parse.urlparse(raw_url)
            qs = urllib.parse.parse_qs(parsed_g.query)
            if "q" in qs and qs["q"]:
                raw_url = qs["q"][0]
        except Exception:
            raw_url = None

    p_id = platform_id.lower().strip()

    # --- ZEPTO ONLY ---
    if "zepto" in p_id:
        # Keep verified PDP links, but discard fake/broken mock IDs
        if raw_url and raw_url.startswith("http") and not any(fake in raw_url for fake in ["dolo650-pvid", "dummy", "fake"]):
            return raw_url
        clean_query = clean_store_search_query(query) if query else ""
        if not clean_query:
            clean_query = re.sub(r'[/\\#?&%+]', ' ', query).strip() if query else ""
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
        clean_query = clean_store_search_query(query) if query else ""
        if not clean_query:
            clean_query = re.sub(r'[/\\#?&%+]', ' ', query).strip() if query else ""
        clean_query = re.sub(r'\b0\.\d+\s*(kg|l|litre|litres|gm|g|ml)\b', '', clean_query, flags=re.IGNORECASE).strip()
        clean_query = re.sub(r'\s+', ' ', clean_query)
        encoded = urllib.parse.quote_plus(clean_query)
        # Direct official JioMart search route: zero redirect notice, loads product results directly
        return f"https://www.jiomart.com/products/?q={encoded}"

    # --- CROMA ONLY ---
    if "croma" in p_id:
        return resolve_croma_url(query, raw_url)

    # --- TATA 1MG ONLY ---
    if "tata1mg" in p_id or "1mg" in p_id:
        if raw_url and raw_url.startswith("http") and not any(fake in raw_url for fake in ["41639", "dummy"]):
            return raw_url
        clean_query = clean_store_search_query(query) if query else ""
        if not clean_query:
            clean_query = re.sub(r'[/\\#?&%+]', ' ', query).strip() if query else ""
        encoded = urllib.parse.quote_plus(clean_query)
        return f"https://www.1mg.com/search/all?name={encoded}"

    # --- RELIANCE DIGITAL ---
    if "reliance_digital" in p_id or "reliancedigital" in p_id:
        return resolve_reliance_digital_url(query, raw_url)[0]

    # --- VIJAY SALES ---
    if "vijay_sales" in p_id or "vijaysales" in p_id:
        return resolve_vijay_sales_url(query, raw_url)[0]

    # --- SANGEETHA MOBILES ---
    if "sangeetha" in p_id:
        return resolve_sangeetha_url(query, raw_url)[0]

    # --- TATA CLIQ ---
    if "tatacliq" in p_id:
        return resolve_tatacliq_url(query, raw_url)[0]

    # --- BRAND OFFICIAL STORE ---
    if "brand_official" in p_id or "official" in p_id:
        from app.connectors.brand_official_connector import build_brand_official_outbound_url
        from app.intelligence.brands import detect_brand
        brand, _ = detect_brand(query)
        out, _ = build_brand_official_outbound_url(brand, query, raw_url)
        return out

    # --- ALL OTHER PLATFORMS: RETURN AS-IS WITHOUT MODIFICATION ---
    return raw_url


def generate_store_outbound_url(
    platform_id: str,
    query: str,
    verified_pdp_url: Optional[str] = None
) -> Tuple[str, str]:
    """Generate outbound URL routing through resolve_store_url for Zepto, JioMart, Croma, 1mg & Brand Official Store."""
    if verified_pdp_url and "google.com/url" in verified_pdp_url:
        try:
            parsed_g = urllib.parse.urlparse(verified_pdp_url)
            qs = urllib.parse.parse_qs(parsed_g.query)
            if "q" in qs and qs["q"]:
                verified_pdp_url = qs["q"][0]
        except Exception:
            verified_pdp_url = None

    p_id = platform_id.lower().strip()
    if "brand_official" in p_id or "official" in p_id:
        from app.connectors.brand_official_connector import build_brand_official_outbound_url
        from app.intelligence.brands import detect_brand
        brand, _ = detect_brand(query)
        return build_brand_official_outbound_url(brand, query, verified_pdp_url)
    if "croma" in p_id:
        final_url = resolve_croma_url(query, verified_pdp_url)
        sku = final_url.split('/')[-1] if "/p/" in final_url else "search"
        return final_url, f"croma://product/{sku}"

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
