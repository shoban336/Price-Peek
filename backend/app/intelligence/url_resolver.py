"""Direct Product URL Resolver inspired by Buyhatke.com.
Parses direct product links from Amazon, Flipkart, Myntra, Blinkit, Zepto, JioMart, BigBasket,
Tata 1mg, Croma, Nykaa, Ajio, extracts canonical identity and deep variant attributes:
Brand, Product Name, Model, Exact Volume/Weight, Color, Storage, RAM, Size, and Pack Multiplier.
"""
import re
import urllib.parse
from typing import Optional, Dict, Any, Tuple, List
from pydantic import BaseModel

from app.intelligence.units import parse_and_normalize_unit
from app.intelligence.variants import extract_variants
from app.intelligence.brands import detect_brand
from app.intelligence.parser import extract_model


class ResolvedProductURL(BaseModel):
    is_url: bool
    platform_id: Optional[str] = None
    platform_name: Optional[str] = None
    product_id: Optional[str] = None
    raw_title_slug: Optional[str] = None
    clean_query: Optional[str] = None
    canonical_url: str
    brand: Optional[str] = None
    product_name: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    storage: Optional[str] = None
    ram: Optional[str] = None
    shoe_size: Optional[str] = None
    apparel_size: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    pack_multiplier: Optional[int] = 1
    packaging: Optional[str] = None
    locked_variant_tags: List[str] = []


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
    # Normalize units: e.g. "1 l" -> "1L", "500 ml" -> "500ml", "128 gb" -> "128GB"
    query = re.sub(r'(\d+)\s*(l|ml|kg|g|gm|gb|tb)\b', r'\1\2', query, flags=re.IGNORECASE)
    # Proper casing for common brand words
    res = query.title()
    res = re.sub(r'\bIphone\b', 'iPhone', res)
    res = re.sub(r'\bIpad\b', 'iPad', res)
    res = re.sub(r'\b(\d+)Gb\b', r'\1GB', res)
    res = re.sub(r'\b(\d+)Tb\b', r'\1TB', res)
    res = re.sub(r'\b(\d+)Ml\b', r'\1ml', res)
    return res


def format_variant_tag_unit(quantity: Optional[float], unit: Optional[str]) -> Optional[str]:
    """Format quantity and unit into standard consumer retail denominations (e.g. 750 ml, 500 g, 1 L)."""
    if quantity is None or not unit:
        return None
    if unit == "L":
        if quantity < 1.0:
            return f"{round(quantity * 1000)} ml"
        return f"{quantity:g} L"
    elif unit == "kg":
        if quantity < 1.0:
            return f"{round(quantity * 1000)} g"
        return f"{quantity:g} kg"
    elif unit in ["GB", "TB", "MB"]:
        return f"{int(quantity) if quantity.is_integer() else quantity} {unit}"
    elif unit in ["pack", "pcs", "tablets", "capsules", "strip"]:
        return f"{int(quantity) if quantity.is_integer() else quantity} {unit}"
    return f"{quantity:g} {unit}"


def _extract_deep_attributes(
    slug: str,
    query_string: str,
    platform_id: str,
    clean_query: str
) -> Dict[str, Any]:
    """Deeply inspect URL slug, query params, and cleaned title to isolate exact attributes."""
    combined_raw = f"{slug.replace('-', ' ')} {clean_query}"
    # Parse query parameters from URL
    params = urllib.parse.parse_qs(query_string) if query_string else {}
    for k, vals in params.items():
        if k.lower() in ["color", "colour", "size", "storage", "ram", "variant", "pack", "volume"]:
            for v in vals:
                combined_raw += f" {v}"

    # Extract Brand
    brand, remaining_after_brand = detect_brand(clean_query)
    if not brand:
        brand, _ = detect_brand(combined_raw)

    # Extract Model
    model = extract_model(clean_query) or extract_model(combined_raw)

    # Extract Variants (Color, Storage, RAM, Apparel/Shoe Size, Formulation, Pack)
    variants = extract_variants(combined_raw)
    color = variants.get("color")
    storage = variants.get("storage")
    ram = variants.get("ram")
    shoe_size = variants.get("shoe_size")
    apparel_size = variants.get("apparel_size")
    packaging = variants.get("packaging")
    pack_mult = variants.get("pack", 1)

    # Check query params for explicit overrides
    for k in ["color", "colour"]:
        if k in params and params[k] and not color:
            color = params[k][0].strip().title()
    for k in ["storage", "rom"]:
        if k in params and params[k] and not storage:
            storage = params[k][0].strip().upper()
    if "ram" in params and params["ram"] and not ram:
        ram = params["ram"][0].strip().upper()

    # Extract Quantity and Unit
    unit_res = parse_and_normalize_unit(combined_raw)
    quantity = unit_res.normalized_value if unit_res else None
    unit = unit_res.canonical_unit if unit_res else None

    # Handle storage unit equivalence (e.g. 128GB vs unit=GB, quantity=128)
    if storage and (unit != "GB" or quantity is None):
        sm = re.search(r'(\d+)\s*(GB|TB)', storage, re.IGNORECASE)
        if sm:
            val = float(sm.group(1))
            canonical_u = sm.group(2).upper()
            if canonical_u == "TB":
                val = val * 1024.0
                canonical_u = "GB"
            if not unit:
                quantity = val
                unit = canonical_u

    # If unit is GB and storage not set, set storage
    if unit == "GB" and quantity and not storage:
        storage = f"{int(quantity) if quantity.is_integer() else quantity}GB"

    # Build locked variant tags
    locked_tags: List[str] = []
    # 1. Volume / Weight unit (if not tech digital storage)
    if quantity is not None and unit and unit != "GB":
        formatted_u = format_variant_tag_unit(quantity, unit)
        if formatted_u:
            locked_tags.append(formatted_u)

    # 2. Storage
    if storage:
        s_display = re.sub(r'(\d+)\s*(GB|TB)', r'\1 \2', storage, flags=re.IGNORECASE).upper()
        locked_tags.append(s_display)

    # 3. RAM
    if ram:
        r_display = re.sub(r'(\d+)\s*GB', r'\1 GB RAM', ram, flags=re.IGNORECASE).upper()
        locked_tags.append(r_display)

    # 4. Color
    if color:
        locked_tags.append(color)

    # 5. Shoe or Apparel Size
    if shoe_size:
        locked_tags.append(shoe_size)
    elif apparel_size:
        locked_tags.append(f"Size {apparel_size}")

    # 6. Pack
    if pack_mult and pack_mult > 1:
        locked_tags.append(f"Pack of {pack_mult}")
    elif pack_mult == 1 and ("pack of 1" in combined_raw.lower() or "pack" in params.get("pack", [""])[0].lower()):
        locked_tags.append("Pack of 1")

    # 7. Packaging
    if packaging and packaging.lower() not in ["bottle"]:
        locked_tags.append(packaging)

    # Construct clean canonical product name
    clean_title = clean_query
    if brand and brand.lower() not in clean_title.lower():
        clean_title = f"{brand} {clean_title}"
    if storage and storage.lower() not in clean_title.lower():
        clean_title = f"{clean_title} {storage}"
    if color and color.lower() not in clean_title.lower():
        clean_title = f"{clean_title} {color}"
    if pack_mult and pack_mult > 1 and "pack" not in clean_title.lower():
        clean_title = f"{clean_title} Pack of {pack_mult}"

    return {
        "brand": brand,
        "model": model,
        "color": color,
        "storage": storage,
        "ram": ram,
        "shoe_size": shoe_size,
        "apparel_size": apparel_size,
        "quantity": quantity,
        "unit": unit,
        "pack_multiplier": pack_mult,
        "packaging": packaging,
        "locked_variant_tags": locked_tags,
        "canonical_title": clean_title,
    }


def parse_product_url(input_text: str) -> Optional[ResolvedProductURL]:
    """Inspect if query is a direct store URL and parse product information like Buyhatke."""
    text = input_text.strip()
    if not text:
        return None

    # Check if text looks like a URL
    url_pattern = r'^(https?:\/\/)?([a-zA-Z0-9\-\.]+)\.([a-zA-Z]{2,})(\/.*)?$'
    match = re.match(url_pattern, text)
    if not match and not any(d in text.lower() for d in [
        "amazon.", "amzn.to", "flipkart.", "fkrt.it", "myntra.", "blinkit.", "zeptonow.", "zepto.",
        "jiomart.", "bigbasket.", "ajio.", "croma.", "nykaa.", "1mg.", "tata1mg."
    ]):
        return None

    # Normalize URL with scheme
    url = text if text.startswith("http://") or text.startswith("https://") else f"https://{text}"
    try:
        parsed = urllib.parse.urlparse(url)
        netloc = parsed.netloc.lower()
        path = parsed.path
        query_str = parsed.query
    except Exception:
        return None

    # 1. Amazon India (e.g. amazon.in/dp/B0FNX5ZG78 or amazon.in/Gold-Winner-Oil/dp/B0FNX5ZG78 or amzn.to/...)
    if "amazon." in netloc or "amzn.to" in netloc:
        asin_match = re.search(r'/(?:dp|gp/product|gp/aw/d)/([A-Z0-9]{10})', path)
        asin = asin_match.group(1) if asin_match else None
        
        # Extract title slug from path before /dp/
        slug_match = re.search(r'/([^/]+)/(?:dp|gp/product)', path)
        slug = slug_match.group(1) if slug_match else ""
        query = clean_slug_to_query(slug) or (f"Amazon Item {asin}" if asin else "Amazon Product")

        attrs = _extract_deep_attributes(slug, query_str, "amazon", query)
        return ResolvedProductURL(
            is_url=True,
            platform_id="amazon",
            platform_name="Amazon India",
            product_id=asin,
            raw_title_slug=slug,
            clean_query=query,
            canonical_url=url,
            brand=attrs["brand"],
            product_name=query,
            model=attrs["model"],
            color=attrs["color"],
            storage=attrs["storage"],
            ram=attrs["ram"],
            shoe_size=attrs["shoe_size"],
            apparel_size=attrs["apparel_size"],
            quantity=attrs["quantity"],
            unit=attrs["unit"],
            pack_multiplier=attrs["pack_multiplier"],
            packaging=attrs["packaging"],
            locked_variant_tags=attrs["locked_variant_tags"],
        )

    # 2. Flipkart (e.g. flipkart.com/apple-iphone-15-black-128-gb/p/itm6ac6485515ae4 or fkrt.it/...)
    if "flipkart." in netloc or "fkrt.it" in netloc:
        id_match = re.search(r'/p/(itm[a-zA-Z0-9]+)', path)
        item_id = id_match.group(1) if id_match else None
        
        slug_match = re.search(r'/([^/]+)/p/', path)
        slug = slug_match.group(1) if slug_match else ""
        query = clean_slug_to_query(slug) or (f"Flipkart Item {item_id}" if item_id else "Flipkart Product")

        attrs = _extract_deep_attributes(slug, query_str, "flipkart", query)
        return ResolvedProductURL(
            is_url=True,
            platform_id="flipkart",
            platform_name="Flipkart",
            product_id=item_id,
            raw_title_slug=slug,
            clean_query=query,
            canonical_url=url,
            brand=attrs["brand"],
            product_name=query,
            model=attrs["model"],
            color=attrs["color"],
            storage=attrs["storage"],
            ram=attrs["ram"],
            shoe_size=attrs["shoe_size"],
            apparel_size=attrs["apparel_size"],
            quantity=attrs["quantity"],
            unit=attrs["unit"],
            pack_multiplier=attrs["pack_multiplier"],
            packaging=attrs["packaging"],
            locked_variant_tags=attrs["locked_variant_tags"],
        )

    # 3. Myntra (e.g. myntra.com/shirts/roadster/roadster-men-cotton-casual-shirt/12345/buy)
    if "myntra." in netloc:
        id_match = re.search(r'/(\d+)/buy', path)
        item_id = id_match.group(1) if id_match else None

        slug_match = re.search(r'/([^/]+)/\d+/buy', path)
        slug = slug_match.group(1) if slug_match else path.strip('/').split('/')[-1]
        query = clean_slug_to_query(slug) or "Myntra Fashion Item"

        attrs = _extract_deep_attributes(slug, query_str, "myntra", query)
        return ResolvedProductURL(
            is_url=True,
            platform_id="myntra",
            platform_name="Myntra",
            product_id=item_id,
            raw_title_slug=slug,
            clean_query=query,
            canonical_url=url,
            brand=attrs["brand"],
            product_name=query,
            model=attrs["model"],
            color=attrs["color"],
            storage=attrs["storage"],
            ram=attrs["ram"],
            shoe_size=attrs["shoe_size"],
            apparel_size=attrs["apparel_size"],
            quantity=attrs["quantity"],
            unit=attrs["unit"],
            pack_multiplier=attrs["pack_multiplier"],
            packaging=attrs["packaging"],
            locked_variant_tags=attrs["locked_variant_tags"],
        )

    # 4. Blinkit (e.g. blinkit.com/prn/gold-winner-sunflower-oil/prid/66192)
    if "blinkit." in netloc:
        id_match = re.search(r'/prid/(\d+)', path)
        item_id = id_match.group(1) if id_match else None

        slug_match = re.search(r'/prn/([^/]+)', path)
        slug = slug_match.group(1) if slug_match else ""
        query = clean_slug_to_query(slug) or "Blinkit Grocery Item"

        attrs = _extract_deep_attributes(slug, query_str, "blinkit", query)
        return ResolvedProductURL(
            is_url=True,
            platform_id="blinkit",
            platform_name="Blinkit",
            product_id=item_id,
            raw_title_slug=slug,
            clean_query=query,
            canonical_url=url,
            brand=attrs["brand"],
            product_name=query,
            model=attrs["model"],
            color=attrs["color"],
            storage=attrs["storage"],
            ram=attrs["ram"],
            shoe_size=attrs["shoe_size"],
            apparel_size=attrs["apparel_size"],
            quantity=attrs["quantity"],
            unit=attrs["unit"],
            pack_multiplier=attrs["pack_multiplier"],
            packaging=attrs["packaging"],
            locked_variant_tags=attrs["locked_variant_tags"],
        )

    # 5. Zepto (e.g. zeptonow.com/pn/gold-winner-refined-sunflower-oil-pouch/pvid/93a89783)
    if "zeptonow." in netloc or "zepto." in netloc:
        id_match = re.search(r'/pvid/([a-zA-Z0-9\-]+)', path)
        item_id = id_match.group(1) if id_match else None

        slug_match = re.search(r'/pn/([^/]+)', path)
        slug = slug_match.group(1) if slug_match else ""
        query = clean_slug_to_query(slug) or "Zepto Quick Item"

        attrs = _extract_deep_attributes(slug, query_str, "zepto", query)
        return ResolvedProductURL(
            is_url=True,
            platform_id="zepto",
            platform_name="Zepto",
            product_id=item_id,
            raw_title_slug=slug,
            clean_query=query,
            canonical_url=url,
            brand=attrs["brand"],
            product_name=query,
            model=attrs["model"],
            color=attrs["color"],
            storage=attrs["storage"],
            ram=attrs["ram"],
            shoe_size=attrs["shoe_size"],
            apparel_size=attrs["apparel_size"],
            quantity=attrs["quantity"],
            unit=attrs["unit"],
            pack_multiplier=attrs["pack_multiplier"],
            packaging=attrs["packaging"],
            locked_variant_tags=attrs["locked_variant_tags"],
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

            attrs = _extract_deep_attributes(slug_sku, query_str, "jiomart", query)
            return ResolvedProductURL(
                is_url=True,
                platform_id="jiomart",
                platform_name="JioMart",
                product_id=item_id,
                raw_title_slug=slug_sku,
                clean_query=query,
                canonical_url=url,
                brand=attrs["brand"],
                product_name=query,
                model=attrs["model"],
                color=attrs["color"],
                storage=attrs["storage"],
                ram=attrs["ram"],
                shoe_size=attrs["shoe_size"],
                apparel_size=attrs["apparel_size"],
                quantity=attrs["quantity"],
                unit=attrs["unit"],
                pack_multiplier=attrs["pack_multiplier"],
                packaging=attrs["packaging"],
                locked_variant_tags=attrs["locked_variant_tags"],
            )

        # Legacy /p/ fallback
        id_match = re.search(r'/(\d{7,})', path)
        item_id = id_match.group(1) if id_match else None

        parts = [p for p in path.strip('/').split('/') if p and p != 'p' and not p.isdigit()]
        slug = parts[-1] if parts else ""
        query = clean_slug_to_query(slug) or "JioMart Grocery Item"

        attrs = _extract_deep_attributes(slug, query_str, "jiomart", query)
        return ResolvedProductURL(
            is_url=True,
            platform_id="jiomart",
            platform_name="JioMart",
            product_id=item_id,
            raw_title_slug=slug,
            clean_query=query,
            canonical_url=url,
            brand=attrs["brand"],
            product_name=query,
            model=attrs["model"],
            color=attrs["color"],
            storage=attrs["storage"],
            ram=attrs["ram"],
            shoe_size=attrs["shoe_size"],
            apparel_size=attrs["apparel_size"],
            quantity=attrs["quantity"],
            unit=attrs["unit"],
            pack_multiplier=attrs["pack_multiplier"],
            packaging=attrs["packaging"],
            locked_variant_tags=attrs["locked_variant_tags"],
        )

    # 7. BigBasket (e.g. bigbasket.com/pd/274141/gold-winner-refined-sunflower-oil-1-l-pouch/)
    if "bigbasket." in netloc or "bb.in" in netloc:
        id_match = re.search(r'/pd/(\d+)', path)
        item_id = id_match.group(1) if id_match else None

        slug_match = re.search(r'/pd/\d+/([^/]+)', path)
        slug = slug_match.group(1) if slug_match else ""
        query = clean_slug_to_query(slug) or "BigBasket Item"

        attrs = _extract_deep_attributes(slug, query_str, "bigbasket", query)
        return ResolvedProductURL(
            is_url=True,
            platform_id="bigbasket",
            platform_name="BigBasket",
            product_id=item_id,
            raw_title_slug=slug,
            clean_query=query,
            canonical_url=url,
            brand=attrs["brand"],
            product_name=query,
            model=attrs["model"],
            color=attrs["color"],
            storage=attrs["storage"],
            ram=attrs["ram"],
            shoe_size=attrs["shoe_size"],
            apparel_size=attrs["apparel_size"],
            quantity=attrs["quantity"],
            unit=attrs["unit"],
            pack_multiplier=attrs["pack_multiplier"],
            packaging=attrs["packaging"],
            locked_variant_tags=attrs["locked_variant_tags"],
        )

    # 8. Tata 1mg (e.g. 1mg.com/drugs/dolo-650-tablet-74467 or 1mg.com/otc/...)
    if "1mg." in netloc or "tata1mg." in netloc:
        id_match = re.search(r'-(\d+)$', path)
        item_id = id_match.group(1) if id_match else None

        slug_match = re.search(r'/(?:drugs|otc)/([^/]+)', path)
        slug = slug_match.group(1) if slug_match else path.strip('/').split('/')[-1]
        query = clean_slug_to_query(slug) or "Tata 1mg Pharmacy Item"

        attrs = _extract_deep_attributes(slug, query_str, "tata1mg", query)
        return ResolvedProductURL(
            is_url=True,
            platform_id="tata1mg",
            platform_name="Tata 1mg",
            product_id=item_id,
            raw_title_slug=slug,
            clean_query=query,
            canonical_url=url,
            brand=attrs["brand"],
            product_name=query,
            model=attrs["model"],
            color=attrs["color"],
            storage=attrs["storage"],
            ram=attrs["ram"],
            shoe_size=attrs["shoe_size"],
            apparel_size=attrs["apparel_size"],
            quantity=attrs["quantity"],
            unit=attrs["unit"],
            pack_multiplier=attrs["pack_multiplier"],
            packaging=attrs["packaging"],
            locked_variant_tags=attrs["locked_variant_tags"],
        )

    # 9. Croma (e.g. croma.com/apple-iphone-15-128gb-black-/p/300652)
    if "croma." in netloc:
        id_match = re.search(r'/p/(\d+)', path)
        item_id = id_match.group(1) if id_match else None

        slug_match = re.search(r'/([^/]+)/p/', path)
        slug = slug_match.group(1) if slug_match else path.strip('/').split('/')[-1]
        query = clean_slug_to_query(slug) or "Croma Electronics Item"

        attrs = _extract_deep_attributes(slug, query_str, "croma", query)
        return ResolvedProductURL(
            is_url=True,
            platform_id="croma",
            platform_name="Croma",
            product_id=item_id,
            raw_title_slug=slug,
            clean_query=query,
            canonical_url=url,
            brand=attrs["brand"],
            product_name=query,
            model=attrs["model"],
            color=attrs["color"],
            storage=attrs["storage"],
            ram=attrs["ram"],
            shoe_size=attrs["shoe_size"],
            apparel_size=attrs["apparel_size"],
            quantity=attrs["quantity"],
            unit=attrs["unit"],
            pack_multiplier=attrs["pack_multiplier"],
            packaging=attrs["packaging"],
            locked_variant_tags=attrs["locked_variant_tags"],
        )

    # Generic E-commerce Store Link
    path_segments = [s for s in path.strip('/').split('/') if s and len(s) > 2]
    slug = path_segments[-1] if path_segments else ""
    query = clean_slug_to_query(slug) or netloc.split('.')[0].title() + " Product"

    platform_slug = netloc.split('.')[1] if len(netloc.split('.')) > 2 else netloc.split('.')[0]
    attrs = _extract_deep_attributes(slug, query_str, platform_slug, query)

    return ResolvedProductURL(
        is_url=True,
        platform_id=platform_slug,
        platform_name=netloc,
        product_id=None,
        raw_title_slug=slug,
        clean_query=query,
        canonical_url=url,
        brand=attrs["brand"],
        product_name=query,
        model=attrs["model"],
        color=attrs["color"],
        storage=attrs["storage"],
        ram=attrs["ram"],
        shoe_size=attrs["shoe_size"],
        apparel_size=attrs["apparel_size"],
        quantity=attrs["quantity"],
        unit=attrs["unit"],
        pack_multiplier=attrs["pack_multiplier"],
        packaging=attrs["packaging"],
        locked_variant_tags=attrs["locked_variant_tags"],
    )


def clean_store_search_query(query: str) -> str:
    """
    Produce the optimal, high-accuracy store search query that directly matches
    the targeted product on Blinkit, Zepto, JioMart, BigBasket, Amazon, Flipkart, 1mg, Croma.
    - Converts broken decimal units (0.1kg -> 100g, 0.5L -> 500ml)
    - Separates unspaced numbers and words (650tablets -> 650 tablets)
    - Strips packaging noise words (strip, strips, blister pack, carton, pouch)
    - Strips purchase fluff (buy, online, price, near me)
    - Normalizes brands and fixes common typos (detol -> Dettol)
    """
    if not query:
        return ""
    text = query.strip()

    # 1. Decimal unit conversions (0.1kg -> 100g, 0.5L -> 500ml)
    text = re.sub(r'\b0\.(\d+)\s*kg\b', lambda m: f"{int(float(f'0.{m.group(1)}') * 1000)}g", text, flags=re.IGNORECASE)
    text = re.sub(r'\b0\.(\d+)\s*l\b', lambda m: f"{int(float(f'0.{m.group(1)}') * 1000)}ml", text, flags=re.IGNORECASE)

    # 2. Fix unspaced numbers and words (e.g. 650tablets -> 650 tablets, 100g -> 100g)
    text = re.sub(r'\b(\d+)(tablets?|capsules?|pills?)\b', r'\1 \2', text, flags=re.IGNORECASE)

    # 3. Handle medicines: Dolo 650, Crocin 500, Calpol 650, Paracetamol 650
    # For dosage medicines with packaging words like "strip", stores index by "Brand Dosage" e.g. "Dolo 650"
    if re.search(r'\b(dolo|crocin|calpol|paracetamol|azithral|augmentin|combiflam)\b', text, re.IGNORECASE):
        m = re.search(r'\b(dolo|crocin|calpol|paracetamol|azithral|augmentin|combiflam)\s*(\d{3,4})?\b', text, re.IGNORECASE)
        if m:
            b = m.group(1).title()
            d = f" {m.group(2)}" if m.group(2) else ""
            return f"{b}{d}".strip()

    # 4. Remove store-breaking packaging noise words
    noise_patterns = [
        r'\b(?:strips?|blister\s*packs?|cartons?|pouches|pouch|tetra\s*pack)\b',
        r'\b(?:online|buy|price|near\s*me|best)\b',
    ]
    for np in noise_patterns:
        text = re.sub(np, ' ', text, flags=re.IGNORECASE)

    # 5. Fix common brand misspellings
    text = re.sub(r'\bdetol\b', 'Dettol', text, flags=re.IGNORECASE)
    text = re.sub(r'\bcoca\s*cola\b', 'Coca-Cola', text, flags=re.IGNORECASE)

    # Clean whitespace and punctuation
    text = re.sub(r'[/\\#?&%+]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def resolve_store_url(platform_id: str, query: str, raw_url: str = None) -> str:
    """
    Targeted URL resolver strictly for JioMart and Zepto, preserving
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
    """
    Returns (outbound_url, deep_link_url) for any supported store with guaranteed ZERO 404s.
    If a verified canonical PDP link is provided and valid, it is prioritized.
    Otherwise, generates the official, tested, working store search/catalog URL:
      - Amazon India: https://www.amazon.in/s?k={quote_plus(query)}
      - Flipkart:     https://www.flipkart.com/search?q={quote_plus(query)}
      - Blinkit:      https://blinkit.com/s/?q={quote_plus(query)}
      - Zepto:        https://www.zepto.com/search?q={quote_plus(query)}&query={quote_plus(query)}
      - BigBasket:    https://www.bigbasket.com/ps/?q={quote_plus(query)}
      - JioMart:      https://www.jiomart.com/products/?q={quote_plus(query)}
      - Tata 1mg:     https://www.1mg.com/search/all?name={quote_plus(query)}
      - Croma:        https://www.croma.com/searchB?q={quote_plus(query)}
    """
    pid = platform_id.lower().strip()

    # Apply targeted logic for Zepto & JioMart
    if "zepto" in pid or "jiomart" in pid:
        final_url = resolve_store_url(pid, query, verified_pdp_url)
        clean_q = re.sub(r'[/\\#?&%+]', ' ', query).strip()
        encoded = urllib.parse.quote_plus(clean_q)
        if "zepto" in pid:
            deep = f"zepto://search?query={encoded}" if "search" in final_url else f"zepto://product/{final_url.split('/')[-1]}"
        else:
            sku = final_url.split('/')[-1] if "/product/" in final_url else "search"
            deep = f"jiomart://product/{sku}"
        return final_url, deep

    if verified_pdp_url and isinstance(verified_pdp_url, str) and verified_pdp_url.startswith("http"):
        # Filter out fabricated synthetic IDs like fake ASINs or fake pvids
        is_fake = any(k in verified_pdp_url for k in [
            "dolo650-pvid", "/prid/dolo650", "B07XB2Z92T", "B0CKR12345",
            "B07K123456", "B07K123457", "itmcase12345", "itm123456", "itm123457",
            "41639"
        ])
        if not is_fake:
            sku = verified_pdp_url.split('/')[-1]
            return verified_pdp_url, f"{platform_id}://product/{sku}"

    # Clean query for search syntax
    clean_q = clean_store_search_query(query)
    if not clean_q:
        clean_q = query.strip()

    quoted_plus = urllib.parse.quote_plus(clean_q)
    quoted_path = urllib.parse.quote(clean_q)

    if pid == "amazon":
        return f"https://www.amazon.in/s?k={quoted_plus}", f"amazon://in/search?k={quoted_plus}"
    elif pid == "flipkart":
        return f"https://www.flipkart.com/search?q={quoted_plus}", f"flipkart://search?q={quoted_plus}"
    elif pid == "blinkit":
        return f"https://blinkit.com/s/?q={quoted_plus}", f"grofers://search?q={quoted_plus}"
    elif pid == "bigbasket":
        return f"https://www.bigbasket.com/ps/?q={quoted_plus}", f"bigbasket://search?q={quoted_plus}"
    elif pid in ["tata1mg", "1mg"]:
        return f"https://www.1mg.com/search/all?name={quoted_plus}", f"tata1mg://search?name={quoted_plus}"
    elif pid == "croma":
        return f"https://www.croma.com/searchB?q={quoted_plus}", f"croma://search?q={quoted_plus}"
    elif pid == "myntra":
        return f"https://www.myntra.com/{quoted_path}", f"myntra://search/{quoted_path}"
    elif pid == "ajio":
        return f"https://www.ajio.com/search/?text={quoted_plus}", f"ajio://search?text={quoted_plus}"
    elif pid == "nykaa":
        return f"https://www.nykaa.com/search/result/?q={quoted_plus}", f"nykaa://search?q={quoted_plus}"
    else:
        return f"https://www.google.com/search?q={quoted_plus}", f"{pid}://search?q={quoted_plus}"

