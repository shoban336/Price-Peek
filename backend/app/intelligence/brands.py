"""Brand recognition and category classification intelligence.
Rule-based, heuristic, and dynamic keyword extraction.
"""
import re
from typing import Optional, Tuple
from app.schemas.platform_schema import PlatformCategory

# Common high-frequency multi-word and single-word brand prefixes
KNOWN_BRANDS = [
    # Grocery / FMCG
    "Gold Winner", "Fortune", "Tata Sampann", "Tata Salt", "Tata Tea", "Aashirvaad",
    "Amul", "Mother Dairy", "Saffola", "Dhara", "India Gate", "Daawat", "Nestle",
    "Cadbury", "Britannia", "Sunfeast", "Parle", "Haldiram's", "Everest", "MDH",
    # Electronics
    "Apple", "Samsung", "Google Pixel", "OnePlus", "Xiaomi", "Realme", "Vivo", "Oppo",
    "Sony", "HP", "Dell", "Lenovo", "Asus", "Acer", "Boat", "Noise", "JBL", "Bose",
    "LG", "Whirlpool", "Panasonic", "Motorola", "Nothing",
    # Personal Care / Beauty / Pharmacy
    "Dove", "Nivea", "L'Oreal", "Garnier", "Tresemme", "Head & Shoulders", "Pantene",
    "Mamaearth", "Cetaphil", "Neutrogena", "Minimalist", "The Derma Co", "Colgate",
    "Dolo", "Crocin", "Combiflam", "Vicks", "Himalaya", "Dabur", "Baidyanath",
    # Fashion
    "Nike", "Adidas", "Puma", "Reebok", "Under Armour", "Levi's", "Zara", "H&M",
    "Allen Solly", "Peter England", "Louis Philippe", "Van Heusen", "Red Tape", "Bata"
]

CATEGORY_KEYWORDS = {
    PlatformCategory.GROCERY: [
        "oil", "sunflower", "mustard", "atta", "flour", "rice", "dal", "pulses",
        "sugar", "salt", "tea", "coffee", "milk", "butter", "cheese", "ghee",
        "paneer", "masala", "spices", "biscuit", "cookies", "noodles", "ketchup",
        "detergent", "soap bar", "surf excel", "vim"
    ],
    PlatformCategory.ELECTRONICS: [
        "phone", "smartphone", "iphone", "galaxy", "pixel", "laptop", "macbook",
        "notebook", "tablet", "ipad", "headphone", "earbuds", "earphone", "tv",
        "television", "smartwatch", "monitor", "charger", "powerbank", "speaker",
        "camera", "ssd", "ram", "gpu", "processor"
    ],
    PlatformCategory.PHARMACY: [
        "tablet", "tablets", "capsule", "capsules", "syrup", "paracetamol",
        "ointment", "drops", "pain relief", "vitamin", "multivitamin", "strip",
        "bandage", "thermometer", "inhaler", "dolo", "crocin"
    ],
    PlatformCategory.BEAUTY: [
        "shampoo", "conditioner", "facewash", "face wash", "moisturizer",
        "sunscreen", "serum", "lotion", "body wash", "perfume", "deodorant",
        "lipstick", "foundation", "eyeliner", "kajal", "skin cream"
    ],
    PlatformCategory.FASHION: [
        "shoes", "sneakers", "sandals", "t-shirt", "tshirt", "shirt", "jeans",
        "trousers", "jacket", "hoodie", "dress", "kurta", "kurti", "saree",
        "sunglasses", "watch", "handbag", "wallet"
    ]
}


def detect_brand(query: str) -> Tuple[Optional[str], str]:
    """Identify if a brand name appears at the start or within the query.
    
    Returns:
        (detected_brand, query_with_brand_stripped)
    """
    normalized_q = query.strip()
    
    # Check known multi-word and single-word brands (case-insensitive)
    for brand in KNOWN_BRANDS:
        pattern = rf'\b{re.escape(brand)}\b'
        match = re.search(pattern, normalized_q, re.IGNORECASE)
        if match:
            # Strip brand from query for downstream product naming
            cleaned_query = (normalized_q[:match.start()] + " " + normalized_q[match.end():]).strip()
            cleaned_query = re.sub(r'\s+', ' ', cleaned_query)
            return brand, cleaned_query

    # Heuristic fallback: if first token is capitalized or distinct, we can extract it
    tokens = normalized_q.split()
    if len(tokens) >= 2 and tokens[0].isalpha() and len(tokens[0]) > 2:
        # Candidate brand token
        first_token = tokens[0]
        # Skip generic query words
        if first_token.lower() not in {"buy", "best", "cheap", "online", "price", "pack", "new"}:
            remaining = " ".join(tokens[1:])
            return first_token.title(), remaining

    return None, normalized_q


def classify_category(text: str) -> PlatformCategory:
    """Classify product text into a primary platform category."""
    lower_text = text.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if re.search(rf'\b{re.escape(kw)}\b', lower_text):
                return cat
    return PlatformCategory.ECOMMERCE
