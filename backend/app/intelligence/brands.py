"""Brand recognition and category classification intelligence.
Rule-based, heuristic, and dynamic keyword extraction.
"""
import re
from typing import Optional, Tuple
from app.schemas.platform_schema import PlatformCategory

# Common high-frequency multi-word and single-word brand prefixes
KNOWN_BRANDS = [
    # Grocery / FMCG / Hygiene / Beverages
    "Coca-Cola", "Coca Cola", "Coke", "Good Day", "Pepsi", "Thums Up", "Sprite", "Fanta", "Limca", "Frooti", "Maaza",
    "Gold Winner", "Fortune", "Tata Sampann", "Tata Salt", "Tata Tea", "Aashirvaad",
    "Amul", "Mother Dairy", "Saffola", "Dhara", "India Gate", "Daawat", "Nestle",
    "Cadbury", "Britannia", "Sunfeast", "Parle", "Oreo", "Bourbon", "Haldiram's", "Haldiram", "Everest", "MDH",
    "Lay's", "Lays", "Kurkure", "Doritos", "Bingo",
    "Dettol", "Lifebuoy", "Savlon", "Godrej", "Cinthol", "Pears", "Lux", "Surf Excel",
    "Ariel", "Vim", "Pril", "Harpic", "Lizol", "Colin",
    # Electronics & Audio
    "Apple", "Samsung", "Google Pixel", "OnePlus", "Xiaomi", "Redmi", "Realme", "Vivo", "Oppo", "Poco", "iQOO",
    "Boat", "boAt", "Noise", "Fire-Boltt", "Boult", "JBL", "Sony", "Bose", "Sennheiser", "Zebronics", "Portronics",
    "HP", "Dell", "Lenovo", "Asus", "Acer", "LG", "Whirlpool", "Panasonic", "Motorola", "Nothing", "Spigen",
    # Personal Care / Beauty / Pharmacy
    "Dove", "Nivea", "L'Oreal", "Garnier", "Tresemme", "Head & Shoulders", "Pantene",
    "Mamaearth", "Cetaphil", "Neutrogena", "Minimalist", "The Derma Co", "Colgate",
    "Dolo", "Crocin", "Calpol", "Combiflam", "Vicks", "Strepsils", "Otrivin", "Volini", "Moov", "Iodex", "Band-Aid",
    "Himalaya", "Dabur", "Baidyanath", "Nykaa", "Eno", "Digene",
    # Fashion
    "Nike", "Adidas", "Puma", "Reebok", "Under Armour", "Levi's", "Zara", "H&M",
    "Allen Solly", "Peter England", "Louis Philippe", "Van Heusen", "Red Tape", "Bata",
    "Roadster", "HRX", "Highlander", "U.S. Polo", "Wrangler", "Flying Machine"
]

CATEGORY_KEYWORDS = {
    PlatformCategory.PHARMACY: [
        "tablet", "tablets", "capsule", "capsules", "syrup", "paracetamol",
        "dolo", "dolo 650", "crocin", "calpol", "combiflam", "strip",
        "ointment", "drops", "pain relief", "vitamin", "multivitamin",
        "bandage", "band-aid", "thermometer", "inhaler", "medicine",
        "balm", "spray", "cough", "fever", "digene", "eno", "ors", "vicks", "volini", "moov"
    ],
    PlatformCategory.GROCERY: [
        "biscuit", "biscuits", "cookie", "cookies", "good day", "marie", "bourbon", "oreo", "parle",
        "drink", "drinks", "soft drink", "cold drink", "cola", "coke", "coca-cola", "coca cola",
        "pepsi", "thums up", "sprite", "fanta", "mirinda", "limca", "frooti", "maaza", "slice",
        "juice", "beverage", "soda", "oil", "sunflower", "mustard", "refined oil", "cooking oil",
        "ghee", "atta", "wheat", "flour", "rice", "basmati", "dal", "pulses", "sugar", "salt",
        "tea", "coffee", "milk", "butter", "cheese", "paneer", "curd", "dahi", "egg", "eggs",
        "bread", "toast", "chips", "crisps", "lays", "kurkure", "nachos", "namkeen", "bhujia",
        "noodles", "maggi", "pasta", "sauce", "ketchup", "masala", "spices", "chocolate", "cadbury",
        "detergent", "soap bar", "surf excel", "vim", "handwash", "hand wash", "dettol", "savlon",
        "sanitizer", "dishwash", "floor cleaner", "vegetable", "vegetables", "fruit", "fruits",
        "tomato", "potato", "onion"
    ],
    PlatformCategory.ELECTRONICS: [
        "phone", "smartphone", "iphone", "galaxy", "pixel", "laptop", "macbook",
        "notebook", "tablet", "ipad", "headphone", "headphones", "earbuds", "earbud",
        "earphone", "earphones", "tws", "airpods", "neckband", "rockerz", "boat", "noise",
        "tv", "television", "smartwatch", "watch", "monitor", "charger", "powerbank", "power bank",
        "speaker", "soundbar", "camera", "ssd", "ram", "gpu", "processor", "case", "phone case",
        "back cover", "cover", "tempered glass", "screen guard", "cable", "adapter", "mouse", "keyboard"
    ],
    PlatformCategory.BEAUTY: [
        "shampoo", "conditioner", "facewash", "face wash", "moisturizer",
        "sunscreen", "serum", "lotion", "body wash", "perfume", "deodorant",
        "lipstick", "foundation", "eyeliner", "kajal", "skin cream", "hair oil"
    ],
    PlatformCategory.FASHION: [
        "shoes", "sneakers", "sandals", "slippers", "footwear", "t-shirt", "tshirt",
        "tee", "shirt", "shirts", "jeans", "pant", "pants", "trousers", "trouser",
        "cargo", "shorts", "jacket", "hoodie", "dress", "kurta", "kurti", "saree",
        "blazer", "suit", "trackpant", "sunglasses", "handbag", "wallet", "belt"
    ]
}


BRAND_CORRECTIONS = {
    "detol": "Dettol",
    "iphne": "Apple",
    "nik": "Nike",
    "adiddas": "Adidas",
    "samsng": "Samsung"
}


def detect_brand(query: str) -> Tuple[Optional[str], str]:
    """Identify if a brand name appears at the start or within the query.
    
    Returns:
        (detected_brand, query_with_brand_stripped)
    """
    normalized_q = query.strip()
    
    # Check common spelling typos and map to canonical brand
    for typo, canonical in BRAND_CORRECTIONS.items():
        pattern = rf'\b{re.escape(typo)}\b'
        match = re.search(pattern, normalized_q, re.IGNORECASE)
        if match:
            cleaned_query = (normalized_q[:match.start()] + " " + normalized_q[match.end():]).strip()
            cleaned_query = re.sub(r'\s+', ' ', cleaned_query)
            return canonical, cleaned_query

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
