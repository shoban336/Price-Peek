"""Fast, scalable rich autocomplete suggestion service for quick commerce & universal e-commerce.
Provides sub-5ms search as you type with product titles, square image thumbnails,
categories, pack sizes, and dynamic catalog matching (Blinkit / Zepto style).
"""
import re
from typing import List, Dict, Any, Optional
from sqlalchemy import or_
from app.config.database import SessionLocal
from app.models.product_model import Product
from app.models.listing_model import ProductListingRecord
from app.schemas.search_schema import AutocompleteItem
from app.intelligence.parser import parse_query


# Default high-quality category thumbnail fallbacks
CATEGORY_DEFAULT_THUMBNAILS = {
    "dairy": "https://images.unsplash.com/photo-1550583724-b2692b85b150?auto=format&fit=crop&w=120&q=80",
    "fruits_vegetables": "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=120&q=80",
    "snacks": "https://images.unsplash.com/photo-1566478989037-eec170784d0b?auto=format&fit=crop&w=120&q=80",
    "beverages": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?auto=format&fit=crop&w=120&q=80",
    "grocery": "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?auto=format&fit=crop&w=120&q=80",
    "personal_care": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&w=120&q=80",
    "electronics": "https://images.unsplash.com/photo-1592750475338-74b7b21085ab?auto=format&fit=crop&w=120&q=80",
    "fashion": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=120&q=80",
    "pharmacy": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&w=120&q=80",
    "general": "https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=120&q=80",
}


# Universal Quick-Commerce & E-Commerce Catalog Index
UNIVERSAL_CATALOG: List[Dict[str, Any]] = [
    # --- Dairy & Breakfast ---
    {
        "id": "amul-milk-taaza-500",
        "name": "Amul Taaza Homogenised Toned Milk",
        "category": "Dairy, Bread & Eggs",
        "pack_size": "500 ml",
        "subtitle": "Amul · 500 ml Pouch",
        "imageUrl": "https://images.unsplash.com/photo-1550583724-b2692b85b150?auto=format&fit=crop&w=120&q=80",
        "keywords": ["milk", "amul", "taaza", "toned milk", "dairy", "doodh"]
    },
    {
        "id": "nandini-toned-milk-500",
        "name": "Nandini Pasteurized Toned Milk",
        "category": "Dairy, Bread & Eggs",
        "pack_size": "500 ml",
        "subtitle": "Nandini · 500 ml Pouch",
        "imageUrl": "https://images.unsplash.com/photo-1550583724-b2692b85b150?auto=format&fit=crop&w=120&q=80",
        "keywords": ["milk", "nandini", "toned milk", "karnataka milk", "dairy"]
    },
    {
        "id": "mother-dairy-full-cream-1l",
        "name": "Mother Dairy Full Cream Fresh Milk",
        "category": "Dairy, Bread & Eggs",
        "pack_size": "1 L",
        "subtitle": "Mother Dairy · 1 L Poly Pack",
        "imageUrl": "https://images.unsplash.com/photo-1550583724-b2692b85b150?auto=format&fit=crop&w=120&q=80",
        "keywords": ["milk", "mother dairy", "full cream", "dairy", "1l milk"]
    },
    {
        "id": "amul-salted-butter-100",
        "name": "Amul Pasteurized Salted Butter",
        "category": "Dairy, Bread & Eggs",
        "pack_size": "100 g",
        "subtitle": "Amul · 100 g Carton",
        "imageUrl": "https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?auto=format&fit=crop&w=120&q=80",
        "keywords": ["butter", "amul butter", "makhan", "salted butter", "dairy"]
    },
    {
        "id": "amul-malai-paneer-200",
        "name": "Amul Fresh Malai Paneer",
        "category": "Dairy, Bread & Eggs",
        "pack_size": "200 g",
        "subtitle": "Amul · 200 g Pack",
        "imageUrl": "https://images.unsplash.com/photo-1550583724-b2692b85b150?auto=format&fit=crop&w=120&q=80",
        "keywords": ["paneer", "cottage cheese", "amul paneer", "malai paneer"]
    },
    {
        "id": "milky-mist-curd-400",
        "name": "Milky Mist Fresh Dahi / Curd",
        "category": "Dairy, Bread & Eggs",
        "pack_size": "400 g",
        "subtitle": "Milky Mist · 400 g Tub",
        "imageUrl": "https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=120&q=80",
        "keywords": ["curd", "dahi", "yogurt", "milky mist curd", "dairy"]
    },
    {
        "id": "britannia-brown-bread-400",
        "name": "Britannia 100% Whole Wheat Brown Bread",
        "category": "Dairy, Bread & Eggs",
        "pack_size": "400 g",
        "subtitle": "Britannia · 400 g Loaf",
        "imageUrl": "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=120&q=80",
        "keywords": ["bread", "brown bread", "wheat bread", "britannia", "toast"]
    },
    {
        "id": "farm-fresh-white-eggs-6",
        "name": "Farm Fresh White Eggs (Pack of 6)",
        "category": "Dairy, Bread & Eggs",
        "pack_size": "6 pcs",
        "subtitle": "Farm Fresh · 6 pcs Tray",
        "imageUrl": "https://images.unsplash.com/photo-1516448620398-c5f44bf9f441?auto=format&fit=crop&w=120&q=80",
        "keywords": ["eggs", "egg", "white eggs", "poultry", "anda", "tray"]
    },

    # --- Fruits & Vegetables ---
    {
        "id": "fresh-hybrid-tomato-1kg",
        "name": "Fresh Hybrid Tomato",
        "category": "Fruits & Vegetables",
        "pack_size": "1 kg",
        "subtitle": "Farm Fresh · 1 kg Net",
        "imageUrl": "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=120&q=80",
        "keywords": ["tomato", "tamatar", "tomatoes", "red tomato", "vegetable", "veggies"]
    },
    {
        "id": "shimla-apple-red-delicious-500",
        "name": "Shimla Red Delicious Apple",
        "category": "Fruits & Vegetables",
        "pack_size": "500 g (3-4 pcs)",
        "subtitle": "Himachal Fresh · 4 pcs",
        "imageUrl": "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?auto=format&fit=crop&w=120&q=80",
        "keywords": ["apple", "apples", "shimla apple", "red apple", "fruit", "seb"]
    },
    {
        "id": "fresh-potato-aloo-1kg",
        "name": "Fresh Potato / Aloo",
        "category": "Fruits & Vegetables",
        "pack_size": "1 kg",
        "subtitle": "Farm Fresh · 1 kg",
        "imageUrl": "https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=120&q=80",
        "keywords": ["potato", "potatoes", "aloo", "batata", "vegetables"]
    },
    {
        "id": "fresh-red-onion-1kg",
        "name": "Fresh Red Onion / Pyaz",
        "category": "Fruits & Vegetables",
        "pack_size": "1 kg",
        "subtitle": "Farm Fresh · 1 kg",
        "imageUrl": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=120&q=80",
        "keywords": ["onion", "onions", "pyaz", "kanda", "vegetables"]
    },
    {
        "id": "fresh-banana-robusta-500",
        "name": "Fresh Robusta Banana",
        "category": "Fruits & Vegetables",
        "pack_size": "500 g (4-5 pcs)",
        "subtitle": "Farm Fresh · 500 g",
        "imageUrl": "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?auto=format&fit=crop&w=120&q=80",
        "keywords": ["banana", "bananas", "kela", "robusta banana", "fruits"]
    },
    {
        "id": "fresh-green-coriander-100",
        "name": "Fresh Coriander Leaves / Dhaniya",
        "category": "Fruits & Vegetables",
        "pack_size": "100 g",
        "subtitle": "Farm Fresh · 100 g Bunch",
        "imageUrl": "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=120&q=80",
        "keywords": ["coriander", "dhaniya", "cilantro", "herbs", "vegetables"]
    },

    # --- Snacks & Munchies ---
    {
        "id": "lays-magic-masala-50",
        "name": "Lay's India's Magic Masala Potato Chips",
        "category": "Snacks & Munchies",
        "pack_size": "50 g",
        "subtitle": "Lay's · 50 g Pouch",
        "imageUrl": "https://images.unsplash.com/photo-1566478989037-eec170784d0b?auto=format&fit=crop&w=120&q=80",
        "keywords": ["lays", "chips", "potato chips", "magic masala", "blue lays", "snack"]
    },
    {
        "id": "lays-cream-onion-50",
        "name": "Lay's American Style Cream & Onion Chips",
        "category": "Snacks & Munchies",
        "pack_size": "50 g",
        "subtitle": "Lay's · 50 g Pouch",
        "imageUrl": "https://images.unsplash.com/photo-1566478989037-eec170784d0b?auto=format&fit=crop&w=120&q=80",
        "keywords": ["lays", "green lays", "cream onion", "chips", "snack"]
    },
    {
        "id": "kurkure-masala-munch-85",
        "name": "Kurkure Masala Munch Crisps",
        "category": "Snacks & Munchies",
        "pack_size": "85 g",
        "subtitle": "Kurkure · 85 g Pouch",
        "imageUrl": "https://images.unsplash.com/photo-1528751014936-863e6e7a319c?auto=format&fit=crop&w=120&q=80",
        "keywords": ["kurkure", "masala munch", "namkeen", "crisps", "snack"]
    },
    {
        "id": "doritos-cheese-nachos-60",
        "name": "Doritos Cheese Supreme Nachos",
        "category": "Snacks & Munchies",
        "pack_size": "60 g",
        "subtitle": "Doritos · 60 g Pouch",
        "imageUrl": "https://images.unsplash.com/photo-1528751014936-863e6e7a319c?auto=format&fit=crop&w=120&q=80",
        "keywords": ["doritos", "nachos", "cheese nachos", "chips", "snack"]
    },
    {
        "id": "haldiram-bhujia-sev-200",
        "name": "Haldiram's Nagpur Aloo Bhujia",
        "category": "Snacks & Munchies",
        "pack_size": "200 g",
        "subtitle": "Haldiram's · 200 g Pouch",
        "imageUrl": "https://images.unsplash.com/photo-1528751014936-863e6e7a319c?auto=format&fit=crop&w=120&q=80",
        "keywords": ["haldiram", "bhujia", "aloo bhujia", "sev", "namkeen"]
    },

    # --- Beverages & Cold Drinks ---
    {
        "id": "coca-cola-original-750",
        "name": "Coca-Cola Original Soft Drink",
        "category": "Cold Drinks & Juices",
        "pack_size": "750 ml",
        "subtitle": "Coca-Cola · 750 ml PET Bottle",
        "imageUrl": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?auto=format&fit=crop&w=120&q=80",
        "keywords": ["coca-cola", "coke", "cold drink", "soda", "beverages"]
    },
    {
        "id": "thums-up-soft-drink-750",
        "name": "Thums Up Charged Soft Drink",
        "category": "Cold Drinks & Juices",
        "pack_size": "750 ml",
        "subtitle": "Thums Up · 750 ml Bottle",
        "imageUrl": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?auto=format&fit=crop&w=120&q=80",
        "keywords": ["thums up", "coke", "soft drink", "cold drink", "cola"]
    },
    {
        "id": "frooti-mango-drink-600",
        "name": "Frooti Fresh Mango Juice",
        "category": "Cold Drinks & Juices",
        "pack_size": "600 ml",
        "subtitle": "Frooti · 600 ml Bottle",
        "imageUrl": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?auto=format&fit=crop&w=120&q=80",
        "keywords": ["frooti", "mango juice", "maaza", "mango drink", "juice"]
    },
    {
        "id": "nescafe-classic-coffee-50",
        "name": "Nescafé Classic 100% Pure Instant Coffee",
        "category": "Tea, Coffee & Health Drinks",
        "pack_size": "50 g",
        "subtitle": "Nescafé · 50 g Glass Jar",
        "imageUrl": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=120&q=80",
        "keywords": ["coffee", "nescafe", "instant coffee", "cafe", "nescafe classic"]
    },

    # --- Cooking, Oils & Staple Groceries ---
    {
        "id": "gold-winner-oil-1l",
        "name": "Gold Winner Refined Sunflower Oil 1L",
        "category": "Edible Oils & Ghee",
        "pack_size": "1 L",
        "subtitle": "Gold Winner · 1 L Pouch",
        "imageUrl": "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?auto=format&fit=crop&w=120&q=80",
        "keywords": ["gold winner", "sunflower oil", "cooking oil", "refined oil", "oil 1l"]
    },
    {
        "id": "fortune-sunlite-oil-1l",
        "name": "Fortune Sunlite Refined Sunflower Oil",
        "category": "Edible Oils & Ghee",
        "pack_size": "1 L",
        "subtitle": "Fortune · 1 L Pouch",
        "imageUrl": "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?auto=format&fit=crop&w=120&q=80",
        "keywords": ["fortune", "sunflower oil", "fortune oil", "cooking oil"]
    },
    {
        "id": "aashirvaad-sharbati-atta-5kg",
        "name": "Aashirvaad Superior MP Sharbati Whole Wheat Atta",
        "category": "Atta, Rice & Dals",
        "pack_size": "5 kg",
        "subtitle": "Aashirvaad · 5 kg Bag",
        "imageUrl": "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=120&q=80",
        "keywords": ["atta", "aashirvaad", "wheat flour", "sharbati atta", "gehu"]
    },
    {
        "id": "tata-salt-iodized-1kg",
        "name": "Tata Salt Vacuum Evaporated Iodized Salt",
        "category": "Masalas & Spices",
        "pack_size": "1 kg",
        "subtitle": "Tata · 1 kg Pouch",
        "imageUrl": "https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=120&q=80",
        "keywords": ["salt", "tata salt", "namak", "iodized salt"]
    },
    {
        "id": "india-gate-basmati-rice-1kg",
        "name": "India Gate Basmati Rice Feast Rozzana",
        "category": "Atta, Rice & Dals",
        "pack_size": "1 kg",
        "subtitle": "India Gate · 1 kg Bag",
        "imageUrl": "https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=120&q=80",
        "keywords": ["rice", "basmati rice", "india gate", "chawal", "biryani rice"]
    },

    # --- Personal Care & Hygiene ---
    {
        "id": "dettol-handwash-750",
        "name": "Dettol Liquid Handwash Refill",
        "category": "Bath & Body",
        "pack_size": "750 ml",
        "subtitle": "Dettol · 750 ml Refill Pouch",
        "imageUrl": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&w=120&q=80",
        "keywords": ["dettol", "handwash", "detol", "dettol handwash", "hand wash", "soap"]
    },
    {
        "id": "dove-intense-repair-shampoo-650",
        "name": "Dove Intense Repair Shampoo",
        "category": "Hair Care",
        "pack_size": "650 ml",
        "subtitle": "Dove · 650 ml Bottle",
        "imageUrl": "https://images.unsplash.com/photo-1535585209827-a15fcdbc4c2d?auto=format&fit=crop&w=120&q=80",
        "keywords": ["dove", "shampoo", "dove shampoo", "hair care", "intense repair"]
    },
    {
        "id": "colgate-strong-teeth-150",
        "name": "Colgate Strong Teeth Dental Cream Toothpaste",
        "category": "Oral Care",
        "pack_size": "150 g",
        "subtitle": "Colgate · 150 g Tube",
        "imageUrl": "https://images.unsplash.com/photo-1559591937-e1032c50fa47?auto=format&fit=crop&w=120&q=80",
        "keywords": ["toothpaste", "colgate", "teeth", "oral care", "colgate strong"]
    },

    # --- Tech & Electronics ---
    {
        "id": "apple-iphone-15-128gb",
        "name": "Apple iPhone 15 128GB",
        "category": "Mobiles & Tablets",
        "pack_size": "128 GB",
        "subtitle": "Apple · Black / Blue 128 GB",
        "imageUrl": "https://images.unsplash.com/photo-1592750475338-74b7b21085ab?auto=format&fit=crop&w=120&q=80",
        "keywords": ["iphone", "iphone 15", "apple", "smartphone", "ios", "apple phone"]
    },
    {
        "id": "iphone-15-silicon-phone-case",
        "name": "iPhone 15 Silicon Magnetic Phone Case",
        "category": "Mobile Accessories",
        "pack_size": "1 pc",
        "subtitle": "MagSafe Compatible · Translucent",
        "imageUrl": "https://images.unsplash.com/photo-1601784551446-20c9e07cdbdb?auto=format&fit=crop&w=120&q=80",
        "keywords": ["phone case", "iphone cover", "silicon cover", "back cover", "case", "cover"]
    },
    {
        "id": "boat-airdopes-141-tws",
        "name": "boAt Airdopes 141 True Wireless Earbuds",
        "category": "Audio & Headphones",
        "pack_size": "1 unit",
        "subtitle": "boAt · 42H Playtime, Fast Charge",
        "imageUrl": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?auto=format&fit=crop&w=120&q=80",
        "keywords": ["boat", "airdopes", "earbuds", "headphones", "bluetooth earphones", "tws"]
    },

    # --- Fashion & Apparel ---
    {
        "id": "men-cotton-casual-shirt",
        "name": "Men Slim Fit Cotton Casual Shirt",
        "category": "Men's Fashion",
        "pack_size": "Size M / L / XL",
        "subtitle": "100% Breathable Cotton · Solid Casual",
        "imageUrl": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=120&q=80",
        "keywords": ["shirt", "casual shirt", "cotton shirt", "men shirt", "formal shirt"]
    },
    {
        "id": "denim-jeans-pants-men",
        "name": "Men Denim Slim Fit Jeans Pants",
        "category": "Men's Fashion",
        "pack_size": "Size 30 / 32 / 34",
        "subtitle": "Stretchable Blue Denim · 5 Pocket",
        "imageUrl": "https://images.unsplash.com/photo-1542272604-780c96856592?auto=format&fit=crop&w=120&q=80",
        "keywords": ["jeans", "pants", "denim pants", "trousers", "men jeans", "pant"]
    },
    {
        "id": "nike-air-max-shoes-uk9",
        "name": "Nike Air Max Running Shoes UK 9",
        "category": "Footwear",
        "pack_size": "UK 9",
        "subtitle": "Nike · Lightweight Cushioning",
        "imageUrl": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=120&q=80",
        "keywords": ["nike", "air max", "shoes", "sneakers", "running shoes", "footwear"]
    },

    # --- Pharmacy & Health ---
    {
        "id": "dolo-650-tablets-strip",
        "name": "Dolo 650 Tablets (Strip of 15 Tablets)",
        "category": "Medicines & Pharmacy",
        "pack_size": "15 Tablets",
        "subtitle": "Micro Labs · Paracetamol 650mg",
        "imageUrl": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&w=120&q=80",
        "keywords": ["dolo", "dolo 650", "paracetamol", "fever", "tablets", "medicine"]
    },
]


def _score_item(query: str, item: Dict[str, Any]) -> int:
    """Calculate matching score for ranking autocomplete results."""
    q = query.lower().strip()
    name = item["name"].lower()
    cat = item.get("category", "").lower()
    keywords = [k.lower() for k in item.get("keywords", [])]

    # Exact name prefix match -> Highest priority
    if name.startswith(q):
        return 120

    # Individual word in name starts with query -> High priority
    words = re.split(r'[\s\-_]+', name)
    if any(w.startswith(q) for w in words):
        return 100

    # Any keyword starts with query -> Strong priority (e.g. "lay" -> "lays")
    if any(k.startswith(q) for k in keywords):
        return 90

    # Keyword contains query
    if any(q in k for k in keywords):
        return 75

    # Name contains query substring
    if q in name:
        return 60

    # Category matches
    if q in cat:
        return 40

    return 0


def get_autocomplete_suggestions(query: str, limit: int = 8) -> List[AutocompleteItem]:
    """Return top matched suggestions with thumbnails for live search autocomplete.
    
    Searches:
    1. SQLite Database registered Products & Listings
    2. Universal Quick-Commerce & E-Commerce Catalog Index
    3. Dynamic intelligent generator for unlisted / arbitrary product queries
    """
    clean_q = query.strip()
    if not clean_q or len(clean_q) < 1:
        return []

    lower_q = clean_q.lower()
    results: List[AutocompleteItem] = []
    seen_names = set()

    # 1. Search Database Products
    try:
        db = SessionLocal()
        search_pattern = f"%{clean_q}%"
        db_products = db.query(Product).filter(
            or_(
                Product.canonical_name.ilike(search_pattern),
                Product.brand.ilike(search_pattern),
                Product.category.ilike(search_pattern)
            )
        ).limit(limit).all()

        for p in db_products:
            norm_name = p.canonical_name.strip()
            if norm_name.lower() in seen_names:
                continue

            # Look up an image from any associated listing
            img = None
            first_listing = db.query(ProductListingRecord).filter(
                ProductListingRecord.product_id == p.id
            ).first()
            if first_listing and first_listing.image_url:
                img = first_listing.image_url
            else:
                img = CATEGORY_DEFAULT_THUMBNAILS.get(p.category or "", CATEGORY_DEFAULT_THUMBNAILS["general"])

            unit_str = f"{p.normalized_quantity:g}{p.normalized_unit}" if p.normalized_quantity and p.normalized_unit else ""
            category_title = (p.category or "General").replace("_", " ").title()

            results.append(
                AutocompleteItem(
                    id=f"db_{p.id}",
                    name=norm_name,
                    imageUrl=img,
                    category=category_title,
                    pack_size=unit_str or None,
                    subtitle=f"{p.brand or category_title} · {unit_str}".strip(" · ") if unit_str else p.brand or category_title
                )
            )
            seen_names.add(norm_name.lower())
        db.close()
    except Exception:
        # Resilient to any DB lock or connection issue
        pass

    # 2. Match Universal Catalog Index
    scored_catalog = []
    for item in UNIVERSAL_CATALOG:
        score = _score_item(lower_q, item)
        if score > 0 and item["name"].lower() not in seen_names:
            scored_catalog.append((score, item))

    # Sort catalog matches by score descending
    scored_catalog.sort(key=lambda x: x[0], reverse=True)

    for _, item in scored_catalog:
        if len(results) >= limit:
            break
        results.append(
            AutocompleteItem(
                id=item["id"],
                name=item["name"],
                imageUrl=item.get("imageUrl"),
                category=item.get("category"),
                pack_size=item.get("pack_size"),
                subtitle=item.get("subtitle")
            )
        )
        seen_names.add(item["name"].lower())

    # 3. Dynamic Fallback for arbitrary / unlisted products
    # If the user is typing something not yet in the catalog (e.g. "dragon fruit", "green tea")
    if len(results) < 2 and len(clean_q) >= 2:
        parsed = parse_query(clean_q)
        cat_key = parsed.category or "general"
        cat_name = cat_key.replace("_", " ").title()
        fallback_img = CATEGORY_DEFAULT_THUMBNAILS.get(cat_key, CATEGORY_DEFAULT_THUMBNAILS["general"])
        unit_str = f"{parsed.normalized_quantity:g}{parsed.normalized_unit}" if parsed.normalized_quantity and parsed.normalized_unit else None

        generated_name = clean_q.title()
        if generated_name.lower() not in seen_names:
            results.append(
                AutocompleteItem(
                    id=f"dyn_{re.sub(r'[^a-zA-Z0-9]', '_', clean_q.lower())}",
                    name=generated_name,
                    imageUrl=fallback_img,
                    category=cat_name,
                    pack_size=unit_str,
                    subtitle=f"{parsed.brand or cat_name}{' · ' + unit_str if unit_str else ''}"
                )
            )

    return results[:limit]
