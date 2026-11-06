"""FastAPI foundation and API v1 endpoints test suite."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify root endpoint returns service info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "PricePeek"
    assert data["status"] == "operational"
    assert data["docs_url"] == "/docs"


def test_health_endpoint():
    """Verify health check reports healthy database and application status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"]["status"] == "healthy"
    assert data["database"]["engine"] == "sqlite"


def test_swagger_docs_accessible():
    """Verify OpenAPI Swagger documentation UI is available."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower() or "PricePeek" in response.text


def test_platforms_list_endpoint():
    """Verify registry platforms listing returns registered stores."""
    response = client.get("/api/v1/platforms")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert data["total"] >= 7
    platform_ids = [p["id"] for p in data["platforms"]]
    assert "amazon" in platform_ids
    assert "blinkit" in platform_ids
    assert "zepto" in platform_ids


def test_get_platform_by_id():
    """Verify retrieving a specific platform by identifier."""
    response = client.get("/api/v1/platforms/amazon")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "amazon"
    assert data["name"] == "Amazon India"
    assert data["domain"] == "amazon.in"


def test_register_new_platform():
    """Verify plug-and-play platform registration endpoint."""
    new_platform = {
        "id": "meesho",
        "name": "Meesho",
        "category": "fashion",
        "domain": "meesho.com",
        "enabled": True,
        "status": "AVAILABLE",
        "requires_pin": True,
        "supported_regions": ["IN"],
        "logo_url": "https://meesho.com/favicon.ico",
        "app_scheme": "com.meesho.supply",
        "description": "Value e-commerce platform"
    }
    response = client.post("/api/v1/platforms", json=new_platform)
    assert response.status_code == 201
    created = response.json()
    assert created["id"] == "meesho"

    # Verify presence in list
    check = client.get("/api/v1/platforms/meesho")
    assert check.status_code == 200
    assert check.json()["name"] == "Meesho"


def test_search_endpoint_contract():
    """Verify search endpoint responds with valid SearchResponse schema."""
    response = client.get("/api/v1/search?q=Gold+Winner+Sunflower+Oil+1L&pin_code=560001")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "Gold Winner Sunflower Oil 1L"
    assert data["delivery_pin"] == "560001"
    assert "parsed_query" in data
    assert data["parsed_query"]["normalized_unit"] == "L"
    assert data["parsed_query"]["normalized_quantity"] == 1.0


def test_history_endpoint_contract():
    """Verify price history endpoint responds with valid schema."""
    response = client.get("/api/v1/history/sunflower-oil-1l")
    assert response.status_code == 200
    data = response.json()
    assert data["product_identifier"] == "sunflower-oil-1l"
    assert data["total_data_points"] > 0
    assert isinstance(data["history"], list)
