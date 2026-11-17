# 🔍 PricePeek – Universal Cross-Platform Price Comparison Engine

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-0.111.0-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-18.3.1-61DAFB.svg?style=for-the-badge&logo=react&logoColor=black" alt="React 18" />
  <img src="https://img.shields.io/badge/Vite-5.2.11-646CFF.svg?style=for-the-badge&logo=vite&logoColor=white" alt="Vite" />
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" />
  <img src="https://img.shields.io/badge/Tests-96%20Passed-brightgreen.svg?style=for-the-badge" alt="Tests" />
</p>

---

## 📌 Overview

**PricePeek** is an intelligent, full-stack universal product price comparison platform engineered specifically for the Indian e-commerce, quick-commerce, electronics, and retail ecosystem.

Instead of browsing across multiple apps, PricePeek lets shoppers:
1. **Search dynamically by name:** Type any product across any vertical (*"Google Pixel 10a Obsidian 256GB"*, *"Dolo 650 tablets strip"*, *"Gold Winner Sunflower Oil 1L"*, *"Apple iPhone 15 Black 128GB"*).
2. **Paste any direct product URL:** Paste a link from Amazon, Flipkart, JioMart, Blinkit, Zepto, BigBasket, Croma, or Tata 1mg to automatically resolve the exact product and compare it across all competing stores.

PricePeek automatically filters delivery options by user pincode (e.g. `560001`), identifies the cheapest price, calculates savings, and provides **guaranteed non-404 direct-to-cart checkout links**.

---

## 🌟 Key Features

* **🧠 Deep Natural Language Query & URL Parsing:**
  * Extracts brand names, models, quantities, and metric units (`1000ml` $\rightarrow$ `1L`, `500g` $\rightarrow$ `0.5kg`).
  * Deep variant extraction from pasted store links (identifies exact phone storage, RAM, color, and pack multiplier from URL slugs and tracking queries).

* **🛡️ Zero-Tolerance Strict Variant Separation:**
  * Eliminates false comparisons: Never merges a 128GB phone with a 256GB phone, an Obsidian Black color with Lavender, or a 500ml pouch with a 1L bottle.
  * Discards mismatched models, single-token accessory fallbacks, and dummy/fake product IDs.

* **⚡ Dynamic Multi-Platform Connector Registry:**
  * Modular, plug-and-play connector architecture covering **20+ major retail platforms** and **Official Brand D2C Storefronts** (Apple, Samsung, Sony, boAt, Puma, etc.).
  * Concurrent asynchronous scraping powered by `HTTPX`, `asyncio`, and `BeautifulSoup4`.

* **🔗 Guaranteed Working Outbound Links (Zero 404s):**
  * Prioritizes verified direct product detail pages (`/product/...`, `/dp/...`, `/pd/...`).
  * Automatically strips Google redirect wrappers (`google.com/url` and `btnI=1`), un-breaks outdated legacy search syntax, and routes to official search catalog endpoints.

* **📊 Real-Time Statistical Pricing & Savings Engine:**
  * Uses **Pandas** and **NumPy** to calculate market averages, identify the cheapest platform, compute maximum savings percentages, and sort results.

* **💾 Blazing-Fast Local Persistence:**
  * Zero-block local storage using **SQLite** (`pricepeek.db`) via **SQLAlchemy ORM** for sub-2ms cached retrieval of previous search results.

---

## 🏪 Supported Platforms by Category

| Category | Supported Platforms & Official Stores |
| :--- | :--- |
| **Electronics & Mobiles** | Amazon India, Flipkart, Croma, Reliance Digital, Vijay Sales, Sangeetha Mobiles, Tata CLiQ, Samsung Official, Apple Official, Sony Official, boAt, OnePlus |
| **Quick Commerce (10–15 Mins)** | Blinkit, Zepto, Swiggy Instamart, Flipkart Minutes |
| **Groceries & Essentials** | JioMart, BigBasket, Amazon Fresh |
| **Pharmacy & Healthcare** | Tata 1mg, PharmEasy, Apollo Pharmacy, Netmeds |
| **Fashion & Apparel** | Myntra, AJIO, Tata CLiQ Fashion, Nykaa Fashion, Puma Official |
| **Beauty & Personal Care** | Nykaa, Tira Beauty, Purplle |

---

## 🏗️ System Architecture

```
                                  USER BROWSER
                         (React 18 + Vite on Port 5173)
                                       │
                                       │ REST API (fetch)
                                       ▼
                       FASTAPI APPLICATION SERVER
                             (Uvicorn on Port 8000)
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
        ▼                              ▼                              ▼
  [ Query & URL ]              [ Connector Registry ]         [ Persistence Layer ]
  Intelligence Engine          Parallel Scraper Engine         SQLite (pricepeek.db)
  • Natural Language Parser    • HTTPX Async Client            • SQLAlchemy 2.0 ORM
  • Deep Slug Resolver         • BeautifulSoup4 / LXML         • Product & Listing Cache
  • Strict Variant Guards      • 20+ Store Connectors          • Price History & Alerts
        │                              │                              │
        └──────────────────────────────┼──────────────────────────────┘
                                       │
                                       ▼
                     [ Comparison & Ranking Engine ]
                     • RapidFuzz Title Similarity Matching
                     • Pandas / NumPy Statistical Spread
                     • Lowest Price Badge & Savings Computation
                     • Verified Direct Outbound Link Router
                                       │
                                       ▼
                                 JSON Response
```

---

## 💻 Tech Stack Breakdown

### Backend
* **Language:** Python 3.11+
* **Web Framework:** [FastAPI](https://fastapi.tiangolo.com/) (REST API routing, request validation, OpenAPI/Swagger docs)
* **Server:** [Uvicorn](https://www.uvicorn.org/) (Lightning-fast ASGI server)
* **Data Validation:** [Pydantic v2](https://docs.pydantic.dev/) & Pydantic-Settings
* **Database & ORM:** [SQLite](https://sqlite.org/) with [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
* **Web Scraping:** [HTTPX](https://www.python-httpx.org/) (async requests), [BeautifulSoup4](https://beautiful-soup-4.readthedocs.io/), [LXML](https://lxml.de/)
* **Matching & Analysis:** [RapidFuzz](https://github.com/maxbachmann/RapidFuzz), [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/)
* **Testing:** [Pytest](https://docs.pytest.org/) & [Pytest-Asyncio](https://github.com/pytest-dev/pytest-asyncio) (96 automated tests)

### Frontend
* **Library:** [React 18](https://react.dev/) (Functional components, hooks, Virtual DOM)
* **Build Tool:** [Vite 5](https://vitejs.dev/) (Hot Module Replacement, fast bundling)
* **Icons:** [Lucide React](https://lucide.dev/)
* **Styling:** Custom modern CSS3 (CSS Grid, Flexbox, responsive `@media` queries, CSS custom properties)

---

## 📁 Repository Structure

```text
Pricepeek/
├── pricepeek.db                     # Local SQLite database storing cached listings & history
├── pytest.ini                       # Pytest test configuration
├── README.md                        # Project documentation
├── .gitignore                       # Git ignore rules for Python, Node, DB, and logs
│
├── backend/                         # FastAPI Python Backend
│   ├── requirements.txt             # Python package dependencies
│   ├── app/
│   │   ├── main.py                  # FastAPI app entry point & CORS configuration
│   │   ├── api/
│   │   │   ├── routes.py            # Central API router
│   │   │   └── endpoints/           # Endpoints: /search, /autocomplete, /platforms, /health
│   │   ├── comparison/              # Pandas/NumPy comparator and savings calculator
│   │   ├── config/                  # Settings (.env loader) and database session factory
│   │   ├── connectors/              # 20+ Store connectors (Amazon, Flipkart, JioMart, Zepto, etc.)
│   │   ├── intelligence/            # Query parser, brand dictionary, and URL resolver
│   │   ├── matching/                # RapidFuzz string matcher and strict unit guards
│   │   ├── models/                  # SQLAlchemy ORM models (Product, Platform, Listing, Alert)
│   │   ├── registry/                # Dynamic connector registry manager
│   │   ├── schemas/                 # Pydantic schemas (SearchResponse, ProductListing)
│   │   └── services/                # Search service, database service, autocomplete service
│   └── tests/                       # 96 Unit and integration tests
│
└── frontend/                        # React 18 + Vite Frontend
    ├── index.html                   # Single-page HTML5 entry point
    ├── vite.config.js               # Vite configuration and backend API proxy
    ├── package.json                 # Frontend dependencies and npm scripts
    └── src/
        ├── main.jsx                 # React root mount
        ├── App.jsx                  # Main dashboard state coordinator
        ├── components/              # SearchBar, ProductListingCard, PriceComparisonTable, etc.
        ├── services/                # api.js REST API client
        └── styles/                  # App.css custom responsive stylesheet
```

---

## 🚀 Getting Started Locally

### Prerequisites
* **Python 3.11+**
* **Node.js 18+** and **npm**
* **Git**

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/shoban336/Price-Peek.git
cd Price-Peek
```

---

### Step 2: Set Up and Run the Backend

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   * **Windows (PowerShell):**
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   * **macOS / Linux:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. Install the backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

* Backend runs at: `http://localhost:8000`
* Interactive API Documentation (Swagger UI): `http://localhost:8000/docs`
* Health Check: `http://localhost:8000/api/v1/health`

---

### Step 3: Set Up and Run the Frontend

Open a **new, separate terminal window**:

1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```

2. Install npm dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```

* Open your browser and navigate to: `http://localhost:5173`

---

## 🧪 Running Automated Tests

PricePeek includes a comprehensive automated test suite verifying URL parsing, connector resilience, zero-404 link generation, and strict variant matching:

```powershell
# From the project root with backend venv activated:
pytest backend/tests/ -v
```

```text
============================== 96 passed in 109.60s ==============================
```

---

## 📡 REST API Reference

### 1. Universal Product Search
```http
GET /api/v1/search?q={query}&pin_code={pin_code}&sort_by={sort_by}
```
* **Query Parameters:**
  * `q` *(required)*: Product name keyword or direct pasted product URL.
  * `pin_code` *(optional, default: `560001`)*: 6-digit Indian delivery PIN code.
  * `sort_by` *(optional, default: `price_asc`)*: `price_asc`, `price_desc`, or `fastest_delivery`.

### 2. Live Search Autocomplete
```http
GET /api/v1/search/autocomplete?q={prefix}&limit={limit}
```
* Returns instant matching search suggestions.

### 3. Active Platforms
```http
GET /api/v1/platforms?category={category}
```
* Lists all enabled store connectors and categories.

### 4. Health Diagnostics
```http
GET /api/v1/health
```
* Returns system health status and active database connection state.

---

## 🛡️ License

This project is licensed under the **MIT License** — feel free to use and adapt it for your own projects.
