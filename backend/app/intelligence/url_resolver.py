"""Direct Product URL Resolver inspired by Buyhatke.com.
Parses direct product links from Amazon, Flipkart, Myntra, Blinkit, Zepto, JioMart, BigBasket,
extracts platform, product ID/ASIN, title slug, and generates clean search query.
"""
import re
import urllib.parse
from typing import Optional, Dict, Any
from pydantic import BaseModel


class ResolvedProductURL(BaseModel):
    is_url: bool
    platform_id: Optional[str] = None
    platform_name: Optional[str] = None
    product_id: Optional[str] = None
    raw_title_slug: Optional[str] = None
    clean_query: Optional[str] = None
    canonical_url: str


def clean_slug_to_query(slug: str) -> str:
    """Transform URL slug like 'gold-winner-refined-sunflower-oil-1-l-pouch' into 'Gold Winner Refined Sunflower Oil 1L Pouch'."""
    if not slug:
        return ""
    # Remove file extensions or tracking params
    cleaned = re.sub(r'\.(html|htm|php|aspx)$', '', slug, flags=re.IGNORECASE)
    # Replace hyphens and underscores with space
    words = re.split(r'[\-_+]+', cleaned)
    
    # Filter out pure tracking / technical hashes
    meaningful_words = []
    for w in words:
        if not w:
            continue
        # Skip random hex IDs or tracking tokens like 'itmcf3c7d82f3a97' or 'dp' or 'pd'
        if re.match(r'^(itm[a-f0-9]{8,}|pvid|pid|prid|p_\d+|dp|pd)$', w, re.IGNORECASE):
            continue
        # Skip numeric SKU IDs like 7533064, 490000073, 590798548
        if w.isdigit() and len(w) >= 6:
            continue
        # Skip short store SKU hashes / prefixes like mffn5q, mffmsl
        if re.match(r'^(mff[a-z0-9]+|[a-z0-9]{5,8})$', w, re.IGNORECASE) and re.search(r'\d', w) and re.search(r'[a-zA-Z]', w):
            continue
        if re.match(r'^mff[a-z0-9]+$', w, re.IGNORECASE):
            continue
        meaningful_words.append(w)

    query = " ".join(meaningful_words).strip()
    # Normalize units: e.g. "1 l" -> "1L", "500 ml" -> "500ml"
    query = re.sub(r'(\d+)\s*(l|ml|kg|g|gm|gb|tb)\b', r'\1\2', query, flags=re.IGNORECASE)
    return query.title()


def parse_product_url(input_text: str) -> Optional[ResolvedProductURL]:
    """Inspect if query is a direct store URL and parse product information like Buyhatke."""
    text = input_text.strip()
    if not text:
        return None

    # Check if text looks like a URL
    url_pattern = r'^(https?:\/\/)?([a-zA-Z0-9\-\.]+)\.([a-zA-Z]{2,})(\/.*)?$'
    match = re.match(url_pattern, text)
    if not match and not any(d in text.lower() for d in [
        "amazon.", "flipkart.", "myntra.", "blinkit.", "zeptonow.", "jiomart.", "bigbasket.", "ajio.", "croma.", "nykaa.", "1mg."
    ]):
        return None

    # Normalize URL with scheme
    url = text if text.startswith("http://") or text.startswith("https://") else f"https://{text}"
    try:
        parsed = urllib.parse.urlparse(url)
        netloc = parsed.netloc.lower()
        path = parsed.path
    except Exception:
        return None

    # 1. Amazon India (e.g. amazon.in/dp/B0FNX5ZG78 or amazon.in/Gold-Winner-Oil/dp/B0FNX5ZG78)
    if "amazon." in netloc:
        asin_match = re.search(r'/(?:dp|gp/product|gp/aw/d)/([A-Z0-9]{10})', path)
        asin = asin_match.group(1) if asin_match else None
        
        # Extract title slug from path before /dp/
        slug_match = re.search(r'/([^/]+)/(?:dp|gp/product)', path)
        slug = slug_match.group(1) if slug_match else ""
        query = clean_slug_to_query(slug) or (f"Amazon Item {asin}" if asin else "Amazon Product")

        return ResolvedProductURL(
            is_url=True,
            platform_id="amazon",
            platform_name="Amazon India",
            product_id=asin,
            raw_title_slug=slug,
            clean_query=query,
            canonical_url=url
        )

    # 2. Flipkart (e.g. flipkart.com/apple-iphone-15-black-128-gb/p/itm6ac6485515ae4)
    if "flipkart." in netloc:
        id_match = re.search(r'/p/(itm[a-zA-Z0-9]+)', path)
        item_id = id_match.group(1) if id_match else None
        
        slug_match = re.search(r'/([^/]+)/p/', path)
        slug = slug_match.group(1) if slug_match else ""
        query = clean_slug_to_query(slug) or (f"Flipkart Item {item_id}" if item_id else "Flipkart Product")

        return ResolvedProductURL(
            is_url=True,
            platform_id="flipkart",
            platform_name="Flipkart",
            product_id=item_id,
            raw_title_slug=slug,
            clean_query=query,
            canonical_url=url
        )

    # 3. Myntra (e.g. myntra.com/shirts/roadster/roadster-men-cotton-casual-shirt/12345/buy)
    if "myntra." in netloc:
        id_match = re.search(r'/(\d+)/buy', path)
        item_id = id_match.group(1) if id_match else None

        slug_match = re.search(r'/([^/]+)/\d+/buy', path)
        slug = slug_match.group(1) if slug_match else path.strip('/').split('/')[-1]
        query = clean_slug_to_query(slug) or "Myntra Fashion Item"

        return ResolvedProductURL(
            is_url=True,
            platform_id="myntra",
            platform_name="Myntra",
            product_id=item_id,
            raw_title_slug=slug,
            clean_query=query,
            canonical_url=url
        )

    # 4. Blinkit (e.g. blinkit.com/prn/gold-winner-sunflower-oil/prid/66192)
    if "blinkit." in netloc:
        id_match = re.search(r'/prid/(\d+)', path)
        item_id = id_match.group(1) if id_match else None

        slug_match = re.search(r'/prn/([^/]+)', path)
        slug = slug_match.group(1) if slug_match else ""
        query = clean_slug_to_query(slug) or "Blinkit Grocery Item"

        return ResolvedProductURL(
            is_url=True,
            platform_id="blinkit",
            platform_name="Blinkit",
            product_id=item_id,
            raw_title_slug=slug,
            clean_query=query,
            canonical_url=url
        )

    # 5. Zepto (e.g. zeptonow.com/pn/gold-winner-refined-sunflower-oil-pouch/pvid/93a89783)
    if "zeptonow." in netloc or "zepto." in netloc:
        id_match = re.search(r'/pvid/([a-zA-Z0-9\-]+)', path)
        item_id = id_match.group(1) if id_match else None

        slug_match = re.search(r'/pn/([^/]+)', path)
        slug = slug_match.group(1) if slug_match else ""
        query = clean_slug_to_query(slug) or "Zepto Quick Item"

        return ResolvedProductURL(
            is_url=True,
            platform_id="zepto",
            platform_name="Zepto",
            product_id=item_id,
            raw_title_slug=slug,
            clean_query=query,
            canonical_url=url
        )

    # 6. JioMart (e.g. jiomart.com/product/gold-winner-refined-sunflower-oil-1-l-pouch-mffn5q-7533064)
    if "jiomart." in netloc:
        # Match modern /product/<slug-with-sku>
        prod_match = re.search(r'/product/([a-zA-Z0-9\-_]+)', path)
        if prod_match:
            slug_sku = prod_match.group(1)
            id_match = re.search(r'(\d{7,})$', slug_sku)
            item_id = id_match.group(1) if id_match else slug_sku.split('-')[-1]
            query = clean_slug_to_query(slug_sku) or "JioMart Grocery Item"

            return ResolvedProductURL(
                is_url=True,
                platform_id="jiomart",
                platform_name="JioMart",
                product_id=item_id,
                raw_title_slug=slug_sku,
                clean_query=query,
                canonical_url=url
            )

        # Legacy /p/ fallback
        id_match = re.search(r'/(\d{7,})', path)
        item_id = id_match.group(1) if id_match else None

        parts = [p for p in path.strip('/').split('/') if p and p != 'p' and not p.isdigit()]
        slug = parts[-1] if parts else ""
        query = clean_slug_to_query(slug) or "JioMart Grocery Item"

        return ResolvedProductURL(
            is_url=True,
            platform_id="jiomart",
            platform_name="JioMart",
            product_id=item_id,
            raw_title_slug=slug,
            clean_query=query,
            canonical_url=url
        )

    # 7. BigBasket (e.g. bigbasket.com/pd/274141/gold-winner-refined-sunflower-oil-1-l-pouch/)
    if "bigbasket." in netloc:
        id_match = re.search(r'/pd/(\d+)', path)
        item_id = id_match.group(1) if id_match else None

        slug_match = re.search(r'/pd/\d+/([^/]+)', path)
        slug = slug_match.group(1) if slug_match else ""
        query = clean_slug_to_query(slug) or "BigBasket Item"

        return ResolvedProductURL(
            is_url=True,
            platform_id="bigbasket",
            platform_name="BigBasket",
            product_id=item_id,
            raw_title_slug=slug,
            clean_query=query,
            canonical_url=url
        )

    # Generic E-commerce Store Link
    path_segments = [s for s in path.strip('/').split('/') if s and len(s) > 2]
    slug = path_segments[-1] if path_segments else ""
    query = clean_slug_to_query(slug) or netloc.split('.')[0].title() + " Product"

    return ResolvedProductURL(
        is_url=True,
        platform_id=netloc.split('.')[1] if len(netloc.split('.')) > 2 else netloc.split('.')[0],
        platform_name=netloc,
        product_id=None,
        raw_title_slug=slug,
        clean_query=query,
        canonical_url=url
    )
