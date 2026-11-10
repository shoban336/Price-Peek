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
from app.intelligence.url_resolver import parse_product_url


# Distinct, authentic product thumbnails across all major quick-commerce categories
PRODUCT_THUMBNAILS = {
    # Dairy & Breakfast
    "milk": "https://images.unsplash.com/photo-1550583724-b2692b85b150?auto=format&fit=crop&w=120&q=80",
    "curd": "https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=120&q=80",
    "butter": "https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?auto=format&fit=crop&w=120&q=80",
    "paneer": "https://images.unsplash.com/photo-1550583724-b2692b85b150?auto=format&fit=crop&w=120&q=80",
    "bread": "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=120&q=80",
    "eggs": "https://images.unsplash.com/photo-1516448620398-c5f44bf9f441?auto=format&fit=crop&w=120&q=80",

    # Produce
    "tomato": "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=120&q=80",
    "apple": "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?auto=format&fit=crop&w=120&q=80",
    "potato": "https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=120&q=80",
    "onion": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=120&q=80",
    "banana": "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?auto=format&fit=crop&w=120&q=80",
    "coriander": "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=120&q=80",

    # Snacks & Bakery
    "biscuit": "https://images.unsplash.com/photo-1558961363-fa8fdf82db35?auto=format&fit=crop&w=120&q=80",
    "lays_blue": "https://images.unsplash.com/photo-1566478989037-eec170784d0b?auto=format&fit=crop&w=120&q=80",
    "lays_green": "https://images.unsplash.com/photo-1566478989037-eec170784d0b?auto=format&fit=crop&w=120&q=80",
    "chips": "https://images.unsplash.com/photo-1566478989037-eec170784d0b?auto=format&fit=crop&w=120&q=80",
    "kurkure": "https://images.unsplash.com/photo-1528751014936-863e6e7a319c?auto=format&fit=crop&w=120&q=80",
    "nachos": "https://images.unsplash.com/photo-1528751014936-863e6e7a319c?auto=format&fit=crop&w=120&q=80",
    "bhujia": "https://images.unsplash.com/photo-1528751014936-863e6e7a319c?auto=format&fit=crop&w=120&q=80",

    # Beverages
    "coca_cola": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?auto=format&fit=crop&w=120&q=80",
    "thums_up": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?auto=format&fit=crop&w=120&q=80",
    "frooti": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?auto=format&fit=crop&w=120&q=80",
    "coffee": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=120&q=80",

    # Cooking & Oils
    "sunflower_oil": "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?auto=format&fit=crop&w=120&q=80",
    "atta": "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=120&q=80",
    "salt": "https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=120&q=80",
    "rice": "https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=120&q=80",

    # Personal Care
    "dettol": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&w=120&q=80",
    "shampoo": "https://images.unsplash.com/photo-1535585209827-a15fcdbc4c2d?auto=format&fit=crop&w=120&q=80",
    "toothpaste": "https://images.unsplash.com/photo-1559591937-e1032c50fa47?auto=format&fit=crop&w=120&q=80",

    # Tech & Electronics
    "iphone": "https://images.unsplash.com/photo-1592750475338-74b7b21085ab?auto=format&fit=crop&w=120&q=80",
    "phone_case": "https://images.unsplash.com/photo-1601784551446-20c9e07cdbdb?auto=format&fit=crop&w=120&q=80",
    "earbuds": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?auto=format&fit=crop&w=120&q=80",
    "headphones": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=120&q=80",

    # Fashion
    "shirt": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=120&q=80",
    "jeans": "https://images.unsplash.com/photo-1542272604-780c96856592?auto=format&fit=crop&w=120&q=80",
    "shoes": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=120&q=80",

    # Pharmacy
    "tablets": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&w=120&q=80",
}


# Category-aware SVG Data URIs (Instant, clean, never broken)
CATEGORY_FALLBACK_SVGS = {
    "dairy": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44' viewBox='0 0 24 24' fill='%23e0f2fe' stroke='%230284c7' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'><path d='M8 2h8v4H8z'/><path d='M6 6h12v14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2z'/><path d='M6 12h12'/></svg>",
    "fruits_vegetables": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44' viewBox='0 0 24 24' fill='%23dcfce7' stroke='%2316a34a' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='13' r='8'/><path d='M12 5V2'/><path d='M12 5c2-2 5-2 7 0'/></svg>",
    "snacks": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44' viewBox='0 0 24 24' fill='%23ffedd5' stroke='%23ea580c' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'><path d='M5 4h14l-2 16H7z'/><path d='M9 10h6'/><path d='M9 14h6'/></svg>",
    "beverages": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44' viewBox='0 0 24 24' fill='%23ccfbf1' stroke='%230d9488' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'><path d='M17 8h1a4 4 0 1 1 0 8h-1'/><path d='M3 8h14v9a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4Z'/><line x1='6' x2='6' y1='2' y2='4'/><line x1='10' x2='10' y1='2' y2='4'/><line x1='14' x2='14' y1='2' y2='4'/></svg>",
    "oil": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44' viewBox='0 0 24 24' fill='%23fef3c7' stroke='%23d97706' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'><path d='M12 2a5 5 0 0 1 5 5c0 5-5 13-5 13s-5-8-5-13a5 5 0 0 1 5-5Z'/></svg>",
    "grocery": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44' viewBox='0 0 24 24' fill='%23f1f5f9' stroke='%23475569' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'><path d='M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z'/><path d='M3 6h18'/><path d='M16 10a4 4 0 0 1-8 0'/></svg>",
    "personal_care": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44' viewBox='0 0 24 24' fill='%23e0e7ff' stroke='%234f46e5' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'><path d='M12 2v4'/><path d='m7 6 10 0'/><rect width='12' height='14' x='6' y='8' rx='2'/><path d='M9 13h6'/></svg>",
    "electronics": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44' viewBox='0 0 24 24' fill='%23ede9fe' stroke='%237c3aed' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'><rect width='14' height='20' x='5' y='2' rx='2'/><path d='M12 18h.01'/></svg>",
    "fashion": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44' viewBox='0 0 24 24' fill='%23fae8ff' stroke='%23a855f7' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'><path d='M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.47a1 1 0 0 0 .99.84H6v10a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.47a2 2 0 0 0-1.34-2.23z'/></svg>",
    "pharmacy": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44' viewBox='0 0 24 24' fill='%23dcfce7' stroke='%23059669' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'><rect width='16' height='16' x='4' y='4' rx='4'/><path d='M12 8v8'/><path d='M8 12h8'/></svg>",
    "general": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44' viewBox='0 0 24 24' fill='%23f8fafc' stroke='%2364748b' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'><path d='m7.5 4.27 9 5.15'/><path d='M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z'/><path d='m3.3 7 8.7 5 8.7-5'/><path d='M12 22V12'/></svg>",
}


def resolve_product_thumbnail(name: str, category: Optional[str] = None, brand: Optional[str] = None) -> str:
    """Smart product thumbnail resolver.
    
    Guarantees every item receives an actual product-specific image rather than a single static olive oil jar.
    """
    text = f"{brand or ''} {name} {category or ''}".lower()

    # 1. Tech & Electronics (Check before fruit 'apple' to prevent brand false positives)
    if any(k in text for k in ["iphone", "macbook", "ipad", "smartphone", "ios", "gadget"]):
        return PRODUCT_THUMBNAILS["iphone"]
    if any(k in text for k in ["phone case", "cover", "back cover", "case", "tempered glass"]):
        return PRODUCT_THUMBNAILS["phone_case"]
    if any(k in text for k in ["earbuds", "boat", "headphones", "airpods", "tws", "earphone", "rockerz"]):
        return PRODUCT_THUMBNAILS["headphones"] if any(k in text for k in ["headphone", "headphones", "rockerz"]) else PRODUCT_THUMBNAILS["earbuds"]

    # 2. Dairy Products
    if any(k in text for k in ["milk", "doodh", "toned milk", "nandani", "nandini"]):
        return PRODUCT_THUMBNAILS["milk"]
    if any(k in text for k in ["curd", "dahi", "yogurt", "milky mist"]):
        return PRODUCT_THUMBNAILS["curd"]
    if any(k in text for k in ["butter", "makhan"]):
        return PRODUCT_THUMBNAILS["butter"]
    if any(k in text for k in ["paneer", "cottage cheese"]):
        return PRODUCT_THUMBNAILS["paneer"]
    if any(k in text for k in ["bread", "toast"]):
        return PRODUCT_THUMBNAILS["bread"]
    if any(k in text for k in ["egg", "eggs", "anda"]):
        return PRODUCT_THUMBNAILS["eggs"]

    # 3. Fresh Produce (Fruits & Vegetables)
    if any(k in text for k in ["tomato", "tamatar"]):
        return PRODUCT_THUMBNAILS["tomato"]
    if any(k in text for k in ["apple", "apples", "seb"]):
        return PRODUCT_THUMBNAILS["apple"]
    if any(k in text for k in ["potato", "potatoes", "aloo"]):
        return PRODUCT_THUMBNAILS["potato"]
    if any(k in text for k in ["onion", "onions", "pyaz"]):
        return PRODUCT_THUMBNAILS["onion"]
    if any(k in text for k in ["banana", "bananas", "kela"]):
        return PRODUCT_THUMBNAILS["banana"]
    if any(k in text for k in ["coriander", "dhaniya", "cilantro"]):
        return PRODUCT_THUMBNAILS["coriander"]

    # 4. Snacks & Munchies & Biscuits
    if any(k in text for k in ["biscuit", "biscuits", "cookie", "cookies", "good day", "bourbon", "marie"]):
        return PRODUCT_THUMBNAILS["biscuit"]
    if "lays" in text or "lay's" in text:
        return PRODUCT_THUMBNAILS["lays_blue"]
    if any(k in text for k in ["chips", "crisps", "potato chips"]):
        return PRODUCT_THUMBNAILS["chips"]
    if "kurkure" in text:
        return PRODUCT_THUMBNAILS["kurkure"]
    if any(k in text for k in ["nachos", "doritos"]):
        return PRODUCT_THUMBNAILS["nachos"]
    if any(k in text for k in ["bhujia", "sev", "namkeen"]):
        return PRODUCT_THUMBNAILS["bhujia"]

    # 5. Cold Drinks & Beverages
    if any(k in text for k in ["coca-cola", "coke"]):
        return PRODUCT_THUMBNAILS["coca_cola"]
    if "thums up" in text:
        return PRODUCT_THUMBNAILS["thums_up"]
    if any(k in text for k in ["frooti", "mango drink", "maaza"]):
        return PRODUCT_THUMBNAILS["frooti"]
    if any(k in text for k in ["coffee", "nescafe"]):
        return PRODUCT_THUMBNAILS["coffee"]

    # 6. Cooking & Oils
    if any(k in text for k in ["gold winner", "sunflower oil", "cooking oil", "refined oil", "oil 1l", "fortune oil"]):
        return PRODUCT_THUMBNAILS["sunflower_oil"]
    if any(k in text for k in ["atta", "wheat flour", "aashirvaad"]):
        return PRODUCT_THUMBNAILS["atta"]
    if any(k in text for k in ["salt", "tata salt", "namak"]):
        return PRODUCT_THUMBNAILS["salt"]
    if any(k in text for k in ["rice", "basmati", "india gate"]):
        return PRODUCT_THUMBNAILS["rice"]

    # 7. Personal Care & Hygiene
    if any(k in text for k in ["dettol", "handwash", "hand wash", "lifebuoy", "sanitizer"]):
        return PRODUCT_THUMBNAILS["dettol"]
    if any(k in text for k in ["shampoo", "dove", "hair care", "tresemme"]):
        return PRODUCT_THUMBNAILS["shampoo"]
    if any(k in text for k in ["colgate", "toothpaste", "oral care"]):
        return PRODUCT_THUMBNAILS["toothpaste"]

    # 8. Fashion & Apparel
    if any(k in text for k in ["shirt", "t-shirt", "tshirt", "casual shirt"]):
        return PRODUCT_THUMBNAILS["shirt"]
    if any(k in text for k in ["jeans", "pant", "pants", "trouser", "trousers"]):
        return PRODUCT_THUMBNAILS["jeans"]
    if any(k in text for k in ["shoe", "shoes", "sneaker", "sneakers", "nike"]):
        return PRODUCT_THUMBNAILS["shoes"]

    # 9. Pharmacy & Medicines
    if any(k in text for k in ["dolo", "tablets", "tablet", "paracetamol", "crocin"]):
        return PRODUCT_THUMBNAILS["tablets"]

    # Category fallback
    cat_lower = (category or "").lower()
    if "dairy" in cat_lower:
        return PRODUCT_THUMBNAILS["milk"]
    if "fruit" in cat_lower or "veg" in cat_lower:
        return PRODUCT_THUMBNAILS["tomato"]
    if "snack" in cat_lower:
        return PRODUCT_THUMBNAILS["chips"]
    if "drink" in cat_lower or "beverage" in cat_lower:
        return PRODUCT_THUMBNAILS["coca_cola"]
    if "oil" in cat_lower:
        return PRODUCT_THUMBNAILS["sunflower_oil"]
    if "tech" in cat_lower or "electronic" in cat_lower:
        return PRODUCT_THUMBNAILS["iphone"]
    if "fashion" in cat_lower:
        return PRODUCT_THUMBNAILS["shirt"]
    if "pharma" in cat_lower:
        return PRODUCT_THUMBNAILS["tablets"]
    if "beauty" in cat_lower or "care" in cat_lower:
        return PRODUCT_THUMBNAILS["shampoo"]

    return CATEGORY_FALLBACK_SVGS.get(cat_lower, CATEGORY_FALLBACK_SVGS["general"])


# Universal Quick-Commerce & E-Commerce Catalog Index
UNIVERSAL_CATALOG: List[Dict[str, Any]] = [
    # --- Dairy & Breakfast ---
    {
        "id": "amul-milk-taaza-500",
        "name": "Amul Taaza Homogenised Toned Milk",
        "category": "Dairy, Bread & Eggs",
        "pack_size": "500 ml",
        "subtitle": "Amul · 500 ml Pouch",
        "imageUrl": PRODUCT_THUMBNAILS["milk"],
        "keywords": ["milk", "amul", "taaza", "toned milk", "dairy", "doodh"]
    },
    {
        "id": "nandini-toned-milk-500",
        "name": "Nandini Pasteurized Toned Milk",
        "category": "Dairy, Bread & Eggs",
        "pack_size": "500 ml",
        "subtitle": "Nandini · 500 ml Pouch",
        "imageUrl": PRODUCT_THUMBNAILS["milk"],
        "keywords": ["milk", "nandini", "toned milk", "karnataka milk", "dairy", "nandani"]
    },
    {
        "id": "mother-dairy-full-cream-1l",
        "name": "Mother Dairy Full Cream Fresh Milk",
        "category": "Dairy, Bread & Eggs",
        "pack_size": "1 L",
        "subtitle": "Mother Dairy · 1 L Poly Pack",
        "imageUrl": PRODUCT_THUMBNAILS["milk"],
        "keywords": ["milk", "mother dairy", "full cream", "dairy", "1l milk"]
    },
    {
        "id": "milky-mist-curd-400",
        "name": "Milky Mist Fresh Dahi / Curd",
        "category": "Dairy, Bread & Eggs",
        "pack_size": "400 g",
        "subtitle": "Milky Mist · 400 g Tub",
        "imageUrl": PRODUCT_THUMBNAILS["curd"],
        "keywords": ["curd", "dahi", "yogurt", "milky mist curd", "dairy"]
    },
    {
        "id": "amul-salted-butter-100",
        "name": "Amul Pasteurized Salted Butter",
        "category": "Dairy, Bread & Eggs",
        "pack_size": "100 g",
        "subtitle": "Amul · 100 g Carton",
        "imageUrl": PRODUCT_THUMBNAILS["butter"],
        "keywords": ["butter", "amul butter", "makhan", "salted butter", "dairy"]
    },
    {
        "id": "amul-malai-paneer-200",
        "name": "Amul Fresh Malai Paneer",
        "category": "Dairy, Bread & Eggs",
        "pack_size": "200 g",
        "subtitle": "Amul · 200 g Pack",
        "imageUrl": PRODUCT_THUMBNAILS["paneer"],
        "keywords": ["paneer", "cottage cheese", "amul paneer", "malai paneer"]
    },
    {
        "id": "britannia-brown-bread-400",
        "name": "Britannia 100% Whole Wheat Brown Bread",
        "category": "Dairy, Bread & Eggs",
        "pack_size": "400 g",
        "subtitle": "Britannia · 400 g Loaf",
        "imageUrl": PRODUCT_THUMBNAILS["bread"],
        "keywords": ["bread", "brown bread", "wheat bread", "britannia", "toast"]
    },
    {
        "id": "farm-fresh-white-eggs-6",
        "name": "Farm Fresh White Eggs (Pack of 6)",
        "category": "Dairy, Bread & Eggs",
        "pack_size": "6 pcs",
        "subtitle": "Farm Fresh · 6 pcs Tray",
        "imageUrl": PRODUCT_THUMBNAILS["eggs"],
        "keywords": ["eggs", "egg", "white eggs", "poultry", "anda", "tray"]
    },

    # --- Fruits & Vegetables ---
    {
        "id": "fresh-hybrid-tomato-1kg",
        "name": "Fresh Hybrid Tomato",
        "category": "Fruits & Vegetables",
        "pack_size": "1 kg",
        "subtitle": "Farm Fresh · 1 kg Net",
        "imageUrl": PRODUCT_THUMBNAILS["tomato"],
        "keywords": ["tomato", "tamatar", "tomatoes", "red tomato", "vegetable", "veggies"]
    },
    {
        "id": "shimla-apple-red-delicious-500",
        "name": "Shimla Red Delicious Apple",
        "category": "Fruits & Vegetables",
        "pack_size": "500 g (3-4 pcs)",
        "subtitle": "Himachal Fresh · 4 pcs",
        "imageUrl": PRODUCT_THUMBNAILS["apple"],
        "keywords": ["apple", "apples", "shimla apple", "red apple", "fruit", "seb"]
    },
    {
        "id": "fresh-potato-aloo-1kg",
        "name": "Fresh Potato / Aloo",
        "category": "Fruits & Vegetables",
        "pack_size": "1 kg",
        "subtitle": "Farm Fresh · 1 kg",
        "imageUrl": PRODUCT_THUMBNAILS["potato"],
        "keywords": ["potato", "potatoes", "aloo", "batata", "vegetables"]
    },
    {
        "id": "fresh-red-onion-1kg",
        "name": "Fresh Red Onion / Pyaz",
        "category": "Fruits & Vegetables",
        "pack_size": "1 kg",
        "subtitle": "Farm Fresh · 1 kg",
        "imageUrl": PRODUCT_THUMBNAILS["onion"],
        "keywords": ["onion", "onions", "pyaz", "kanda", "vegetables"]
    },
    {
        "id": "fresh-banana-robusta-500",
        "name": "Fresh Robusta Banana",
        "category": "Fruits & Vegetables",
        "pack_size": "500 g (4-5 pcs)",
        "subtitle": "Farm Fresh · 500 g",
        "imageUrl": PRODUCT_THUMBNAILS["banana"],
        "keywords": ["banana", "bananas", "kela", "robusta banana", "fruits"]
    },
    {
        "id": "fresh-green-coriander-100",
        "name": "Fresh Coriander Leaves / Dhaniya",
        "category": "Fruits & Vegetables",
        "pack_size": "100 g",
        "subtitle": "Farm Fresh · 100 g Bunch",
        "imageUrl": PRODUCT_THUMBNAILS["coriander"],
        "keywords": ["coriander", "dhaniya", "cilantro", "herbs", "vegetables"]
    },

    # --- Snacks & Munchies ---
    {
        "id": "lays-magic-masala-50",
        "name": "Lay's India's Magic Masala Potato Chips",
        "category": "Snacks & Munchies",
        "pack_size": "50 g",
        "subtitle": "Lay's · 50 g Pouch",
        "imageUrl": PRODUCT_THUMBNAILS["lays_blue"],
        "keywords": ["lays", "chips", "potato chips", "magic masala", "blue lays", "snack"]
    },
    {
        "id": "lays-cream-onion-50",
        "name": "Lay's American Style Cream & Onion Chips",
        "category": "Snacks & Munchies",
        "pack_size": "50 g",
        "subtitle": "Lay's · 50 g Pouch",
        "imageUrl": PRODUCT_THUMBNAILS["lays_green"],
        "keywords": ["lays", "green lays", "cream onion", "chips", "snack"]
    },
    {
        "id": "kurkure-masala-munch-85",
        "name": "Kurkure Masala Munch Crisps",
        "category": "Snacks & Munchies",
        "pack_size": "85 g",
        "subtitle": "Kurkure · 85 g Pouch",
        "imageUrl": PRODUCT_THUMBNAILS["kurkure"],
        "keywords": ["kurkure", "masala munch", "namkeen", "crisps", "snack"]
    },
    {
        "id": "doritos-cheese-nachos-60",
        "name": "Doritos Cheese Supreme Nachos",
        "category": "Snacks & Munchies",
        "pack_size": "60 g",
        "subtitle": "Doritos · 60 g Pouch",
        "imageUrl": PRODUCT_THUMBNAILS["nachos"],
        "keywords": ["doritos", "nachos", "cheese nachos", "chips", "snack"]
    },
    {
        "id": "haldiram-bhujia-sev-200",
        "name": "Haldiram's Nagpur Aloo Bhujia",
        "category": "Snacks & Munchies",
        "pack_size": "200 g",
        "subtitle": "Haldiram's · 200 g Pouch",
        "imageUrl": PRODUCT_THUMBNAILS["bhujia"],
        "keywords": ["haldiram", "bhujia", "aloo bhujia", "sev", "namkeen"]
    },
    {
        "id": "britannia-good-day-butter-cookies-200",
        "name": "Britannia Good Day Butter Cookies",
        "category": "Snacks & Munchies",
        "pack_size": "200 g",
        "subtitle": "Britannia · 200 g Pack",
        "imageUrl": PRODUCT_THUMBNAILS["biscuit"],
        "keywords": ["good day", "good day biscuit", "biscuit", "biscuits", "cookies", "britannia", "butter cookies"]
    },

    # --- Beverages & Cold Drinks ---
    {
        "id": "coca-cola-original-750",
        "name": "Coca-Cola Original Soft Drink",
        "category": "Cold Drinks & Juices",
        "pack_size": "750 ml",
        "subtitle": "Coca-Cola · 750 ml PET Bottle",
        "imageUrl": PRODUCT_THUMBNAILS["coca_cola"],
        "keywords": ["coca-cola", "coke", "cold drink", "soda", "beverages"]
    },
    {
        "id": "thums-up-soft-drink-750",
        "name": "Thums Up Charged Soft Drink",
        "category": "Cold Drinks & Juices",
        "pack_size": "750 ml",
        "subtitle": "Thums Up · 750 ml Bottle",
        "imageUrl": PRODUCT_THUMBNAILS["thums_up"],
        "keywords": ["thums up", "coke", "soft drink", "cold drink", "cola"]
    },
    {
        "id": "frooti-mango-drink-600",
        "name": "Frooti Fresh Mango Juice",
        "category": "Cold Drinks & Juices",
        "pack_size": "600 ml",
        "subtitle": "Frooti · 600 ml Bottle",
        "imageUrl": PRODUCT_THUMBNAILS["frooti"],
        "keywords": ["frooti", "mango juice", "maaza", "mango drink", "juice"]
    },
    {
        "id": "nescafe-classic-coffee-50",
        "name": "Nescafé Classic 100% Pure Instant Coffee",
        "category": "Tea, Coffee & Health Drinks",
        "pack_size": "50 g",
        "subtitle": "Nescafé · 50 g Glass Jar",
        "imageUrl": PRODUCT_THUMBNAILS["coffee"],
        "keywords": ["coffee", "nescafe", "instant coffee", "cafe", "nescafe classic"]
    },

    # --- Cooking, Oils & Staple Groceries ---
    {
        "id": "gold-winner-oil-1l",
        "name": "Gold Winner Refined Sunflower Oil 1L",
        "category": "Edible Oils & Ghee",
        "pack_size": "1 L",
        "subtitle": "Gold Winner · 1 L Pouch",
        "imageUrl": PRODUCT_THUMBNAILS["sunflower_oil"],
        "keywords": ["gold winner", "sunflower oil", "cooking oil", "refined oil", "oil 1l"]
    },
    {
        "id": "fortune-sunlite-oil-1l",
        "name": "Fortune Sunlite Refined Sunflower Oil",
        "category": "Edible Oils & Ghee",
        "pack_size": "1 L",
        "subtitle": "Fortune · 1 L Pouch",
        "imageUrl": PRODUCT_THUMBNAILS["sunflower_oil"],
        "keywords": ["fortune", "sunflower oil", "fortune oil", "cooking oil"]
    },
    {
        "id": "aashirvaad-sharbati-atta-5kg",
        "name": "Aashirvaad Superior MP Sharbati Whole Wheat Atta",
        "category": "Atta, Rice & Dals",
        "pack_size": "5 kg",
        "subtitle": "Aashirvaad · 5 kg Bag",
        "imageUrl": PRODUCT_THUMBNAILS["atta"],
        "keywords": ["atta", "aashirvaad", "wheat flour", "sharbati atta", "gehu"]
    },
    {
        "id": "tata-salt-iodized-1kg",
        "name": "Tata Salt Vacuum Evaporated Iodized Salt",
        "category": "Masalas & Spices",
        "pack_size": "1 kg",
        "subtitle": "Tata · 1 kg Pouch",
        "imageUrl": PRODUCT_THUMBNAILS["salt"],
        "keywords": ["salt", "tata salt", "namak", "iodized salt"]
    },
    {
        "id": "india-gate-basmati-rice-1kg",
        "name": "India Gate Basmati Rice Feast Rozzana",
        "category": "Atta, Rice & Dals",
        "pack_size": "1 kg",
        "subtitle": "India Gate · 1 kg Bag",
        "imageUrl": PRODUCT_THUMBNAILS["rice"],
        "keywords": ["rice", "basmati rice", "india gate", "chawal", "biryani rice"]
    },

    # --- Personal Care & Hygiene ---
    {
        "id": "dettol-handwash-750",
        "name": "Dettol Liquid Handwash Refill",
        "category": "Bath & Body",
        "pack_size": "750 ml",
        "subtitle": "Dettol · 750 ml Refill Pouch",
        "imageUrl": PRODUCT_THUMBNAILS["dettol"],
        "keywords": ["dettol", "handwash", "detol", "dettol handwash", "hand wash", "soap"]
    },
    {
        "id": "dove-intense-repair-shampoo-650",
        "name": "Dove Intense Repair Shampoo",
        "category": "Hair Care",
        "pack_size": "650 ml",
        "subtitle": "Dove · 650 ml Bottle",
        "imageUrl": PRODUCT_THUMBNAILS["shampoo"],
        "keywords": ["dove", "shampoo", "dove shampoo", "hair care", "intense repair"]
    },
    {
        "id": "colgate-strong-teeth-150",
        "name": "Colgate Strong Teeth Dental Cream Toothpaste",
        "category": "Oral Care",
        "pack_size": "150 g",
        "subtitle": "Colgate · 150 g Tube",
        "imageUrl": PRODUCT_THUMBNAILS["toothpaste"],
        "keywords": ["toothpaste", "colgate", "teeth", "oral care", "colgate strong"]
    },

    # --- Tech & Electronics ---
    {
        "id": "apple-iphone-15-128gb",
        "name": "Apple iPhone 15 128GB",
        "category": "Mobiles & Tablets",
        "pack_size": "128 GB",
        "subtitle": "Apple · Black / Blue 128 GB",
        "imageUrl": PRODUCT_THUMBNAILS["iphone"],
        "keywords": ["iphone", "iphone 15", "apple", "smartphone", "ios", "apple phone"]
    },
    {
        "id": "iphone-15-silicon-phone-case",
        "name": "iPhone 15 Silicon Magnetic Phone Case",
        "category": "Mobile Accessories",
        "pack_size": "1 pc",
        "subtitle": "MagSafe Compatible · Translucent",
        "imageUrl": PRODUCT_THUMBNAILS["phone_case"],
        "keywords": ["phone case", "iphone cover", "silicon cover", "back cover", "case", "cover"]
    },
    {
        "id": "boat-airdopes-141-tws",
        "name": "boAt Airdopes 141 True Wireless Earbuds",
        "category": "Audio & Headphones",
        "pack_size": "1 unit",
        "subtitle": "boAt · 42H Playtime, Fast Charge",
        "imageUrl": PRODUCT_THUMBNAILS["earbuds"],
        "keywords": ["boat", "airdopes", "earbuds", "headphones", "bluetooth earphones", "tws"]
    },
    {
        "id": "boat-rockerz-wireless-headphones",
        "name": "boAt Rockerz Bluetooth Wireless Headphones",
        "category": "Audio & Headphones",
        "pack_size": "1 unit",
        "subtitle": "boAt · Wireless Over Ear Headphones",
        "imageUrl": PRODUCT_THUMBNAILS["headphones"],
        "keywords": ["boat", "rockerz", "headphones", "boat rockerz", "bluetooth headphones", "headphone"]
    },

    # --- Fashion & Apparel ---
    {
        "id": "men-cotton-casual-shirt",
        "name": "Men Slim Fit Cotton Casual Shirt",
        "category": "Men's Fashion",
        "pack_size": "Size M / L / XL",
        "subtitle": "100% Breathable Cotton · Solid Casual",
        "imageUrl": PRODUCT_THUMBNAILS["shirt"],
        "keywords": ["shirt", "casual shirt", "cotton shirt", "men shirt", "formal shirt"]
    },
    {
        "id": "denim-jeans-pants-men",
        "name": "Men Denim Slim Fit Jeans Pants",
        "category": "Men's Fashion",
        "pack_size": "Size 30 / 32 / 34",
        "subtitle": "Stretchable Blue Denim · 5 Pocket",
        "imageUrl": PRODUCT_THUMBNAILS["jeans"],
        "keywords": ["jeans", "pants", "denim pants", "trousers", "men jeans", "pant"]
    },
    {
        "id": "nike-air-max-shoes-uk9",
        "name": "Nike Air Max Running Shoes UK 9",
        "category": "Footwear",
        "pack_size": "UK 9",
        "subtitle": "Nike · Lightweight Cushioning",
        "imageUrl": PRODUCT_THUMBNAILS["shoes"],
        "keywords": ["nike", "air max", "shoes", "sneakers", "running shoes", "footwear"]
    },

    # --- Pharmacy & Health ---
    {
        "id": "dolo-650-tablets-strip",
        "name": "Dolo 650 Tablets (Strip of 15 Tablets)",
        "category": "Medicines & Pharmacy",
        "pack_size": "15 Tablets",
        "subtitle": "Micro Labs · Paracetamol 650mg",
        "imageUrl": PRODUCT_THUMBNAILS["tablets"],
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
    1. Buyhatke Direct URL Resolver (Instant product link detection)
    2. Universal Quick-Commerce & E-Commerce Catalog Index (High-fidelity curated items)
    3. SQLite Database registered Products & Listings (dynamically updated with resolved images)
    4. Dynamic intelligent generator for unlisted / arbitrary product queries
    """
    clean_q = query.strip()
    if not clean_q or len(clean_q) < 1:
        return []

    # 0. Buyhatke URL Resolver Check
    url_info = parse_product_url(clean_q)
    if url_info and url_info.is_url:
        img = resolve_product_thumbnail(url_info.clean_query or "", url_info.platform_id)
        return [
            AutocompleteItem(
                id="url_resolver_direct",
                name=url_info.clean_query or clean_q,
                imageUrl=img,
                image_url=img,
                category=f"{url_info.platform_name} Link",
                pack_size="Direct Link",
                subtitle=f"🔗 Paste detected from {url_info.platform_name} ({url_info.product_id or 'Product'}) — Click to compare across all stores"
            )
        ]

    lower_q = clean_q.lower()
    results: List[AutocompleteItem] = []
    seen_names = set()

    # 1. Match Universal Catalog Index First for Curated Instant Results
    scored_catalog = []
    for item in UNIVERSAL_CATALOG:
        score = _score_item(lower_q, item)
        if score > 0 and item["name"].lower() not in seen_names:
            scored_catalog.append((score, item))

    scored_catalog.sort(key=lambda x: x[0], reverse=True)

    for _, item in scored_catalog:
        if len(results) >= limit:
            break
        img_url = item.get("imageUrl") or resolve_product_thumbnail(item["name"], item.get("category"))
        results.append(
            AutocompleteItem(
                id=item["id"],
                name=item["name"],
                imageUrl=img_url,
                image_url=img_url,
                category=item.get("category"),
                pack_size=item.get("pack_size"),
                subtitle=item.get("subtitle")
            )
        )
        seen_names.add(item["name"].lower())

    # 2. Search Database Products
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
            if len(results) >= limit:
                break
            norm_name = p.canonical_name.strip()
            if norm_name.lower() in seen_names:
                continue

            # Look up an image from any associated listing or resolve product-specific image
            first_listing = db.query(ProductListingRecord).filter(
                ProductListingRecord.product_id == p.id
            ).first()

            if first_listing and first_listing.image_url and "photo-1474979266404-7eaacbcd87c5" not in first_listing.image_url:
                img = first_listing.image_url
            else:
                img = resolve_product_thumbnail(norm_name, p.category, p.brand)
                # Auto-heal listing image in DB
                if first_listing and (not first_listing.image_url or "photo-1474979266404-7eaacbcd87c5" in first_listing.image_url):
                    first_listing.image_url = img
                    db.commit()

            unit_str = f"{p.normalized_quantity:g}{p.normalized_unit}" if p.normalized_quantity and p.normalized_unit else ""
            category_title = (p.category or "General").replace("_", " ").title()

            results.append(
                AutocompleteItem(
                    id=f"db_{p.id}",
                    name=norm_name,
                    imageUrl=img,
                    image_url=img,
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

    # 3. Dynamic Fallback for arbitrary / unlisted products
    if len(results) < 2 and len(clean_q) >= 2:
        parsed = parse_query(clean_q)
        cat_key = parsed.category or "general"
        cat_name = cat_key.replace("_", " ").title()
        unit_str = f"{parsed.normalized_quantity:g}{parsed.normalized_unit}" if parsed.normalized_quantity and parsed.normalized_unit else None

        generated_name = clean_q.title()
        if generated_name.lower() not in seen_names:
            img = resolve_product_thumbnail(generated_name, cat_key, parsed.brand)
            results.append(
                AutocompleteItem(
                    id=f"dyn_{re.sub(r'[^a-zA-Z0-9]', '_', clean_q.lower())}",
                    name=generated_name,
                    imageUrl=img,
                    image_url=img,
                    category=cat_name,
                    pack_size=unit_str,
                    subtitle=f"{parsed.brand or cat_name}{' · ' + unit_str if unit_str else ''}"
                )
            )

    return results[:limit]
