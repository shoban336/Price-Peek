# PricePeek – Universal Product Price Comparison Platform

PricePeek is a universal product price comparison platform that enables users to query any product (e.g., *"Gold Winner Sunflower Oil 1L"*, *"iPhone 15 128GB"*, *"Dove shampoo"*) across all active shopping platforms (E-Commerce, Quick-Commerce, Electronics, Fashion, Pharmacy, and Grocery), filtered by delivery PIN code.

## Key Features

- **Universal Query Intelligence:** Parses unstructured user searches into structured attributes (brand, product title, model, normalized units, variant).
- **Strict Unit & Variant Separation:** Distinguishes between package sizes and tech variants (e.g., `1000ml` matches `1L`, but rejects `500ml`; `128GB` does not merge with `256GB`).
- **Dynamic Platform Registry:** Independent, plug-and-play connectors registered dynamically without modifying core engine logic.
- **Ethical & Permitted Data Ingestion:** Adheres to `robots.txt` and polite web standards with clean status tracking (`AVAILABLE`, `RESTRICTED_BY_ROBOTS`, `UNAVAILABLE`).
- **Mandatory Direct Product Links:** Guarantees direct URLs to listing pages with deep linking support.
- **Zero Paid APIs:** Built with Python, FastAPI, Pandas, NumPy, RapidFuzz, BeautifulSoup4, and SQLAlchemy 2.0.
- **Dual-Database Support:** Instant zero-block development on SQLite with production-ready MySQL compatibility via configuration.

## Folder Structure

```text
pricepeek/
├── .gitignore
├── .env.example
├── README.md
├── PROJECT_SOP.md
├── docs/
│   └── architecture.md
├── backend/
│   ├── requirements.txt
│   ├── .env
│   ├── app/
│   └── tests/
└── frontend/
```

## Quick Start (Backend)

1. **Activate Python Environment:**
   ```powershell
   cd backend
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Run Server:**
   ```powershell
   uvicorn app.main:app --reload --port 8000
   ```

3. **Interactive Documentation:**
   Visit `http://localhost:8000/docs` for Swagger UI.
