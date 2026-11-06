# PricePeek Standard Operating Procedures (PROJECT_SOP.md)

## Universal Product Price Comparison Platform – Engineering Guidelines

### 1. Non-Negotiable Core Engineering Rules

1. **Zero Paid APIs:**
   - Under no circumstances shall the system rely on OpenAI, Gemini, ChatGPT, Claude, paid scraping proxies, or paid aggregation APIs.
   - All product intelligence, unit normalization, entity resolution, and parsing must use deterministic, algorithmic, or rule-based processing (e.g., regex, RapidFuzz, Pandas, custom parsing tables).

2. **Universal Scope (No Hardcoding):**
   - Never hardcode fixed product catalogs, specific brand lists as constraints, fabricated product prices, or mock URLs.
   - Never restrict the architecture to a fixed set of 7 or 10 websites. Any shopping platform conforming to the Base Connector specification must be plug-and-play without core engine alterations.

3. **Ethical & Permitted Data Collection:**
   - Always honor `robots.txt` directives and legal terms of service.
   - Never bypass Cloudflare, Akamai, CAPTCHAs, or authentication barriers.
   - If a target storefront blocks automated extraction or does not allow public scraping, the connector status must explicitly report `RESTRICTED_BY_ROBOTS` or `UNAVAILABLE`.
   - Never fabricate live results; fallback to sample/cached reference fixtures must be clearly designated with `is_live=False`.

4. **Mandatory Direct Product Links:**
   - Every returned product item MUST feature its exact, direct web URL (`product_url`) leading directly to that product's item page.
   - App deep links (`deep_link_url`) should be supplied whenever supported (e.g., intent URIs for mobile apps).
   - Never redirect users to a generic home page or root search URL when a product link is expected.

5. **Strict Unit & Variant Separation:**
   - Never group distinct package sizes, volumes, weights, or tech specifications as identical items.
   - Example 1: `1000ml` and `1 Litre` equal `1L`. They match.
   - Example 2: `500ml` vs `1L` are different variants and must NOT be compared as the same product unit.
   - Example 3: `iPhone 15 128GB` and `iPhone 15 256GB` are different storage tiers and must remain separate comparison groups.

6. **Plug-and-Play Connector Modularity:**
   - Adding a new shopping platform requires ONLY adding a connector file in `backend/app/connectors/` that implements `BaseConnector` and registering it in the `PlatformRegistry`.
   - The central query parsing, matching, and price comparison engine remains 100% untouched.

7. **Security & Configuration Hygiene:**
   - No credentials, tokens, or local secrets are hardcoded in source files.
   - Load configuration dynamically via Pydantic Settings and `.env`.
   - Support zero-block local development on SQLite (`sqlite:///./pricepeek.db`), transitioning smoothly to production MySQL (`mysql+pymysql://...`) by modifying only `DATABASE_URL`.
