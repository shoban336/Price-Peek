"""Test suite for Live Search Autocomplete with Thumbnails (Blinkit style)."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_autocomplete_endpoint_contract():
    """Verify endpoint exists, returns 200 and valid schema."""
    response = client.get("/api/v1/search/autocomplete?q=milk")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    
    first = data[0]
    assert "id" in first
    assert "name" in first
    assert "imageUrl" in first
    assert "category" in first
    assert "pack_size" in first
    assert "milk" in first["name"].lower()
    assert first["imageUrl"].startswith("http")


@pytest.mark.parametrize("query,expected_keyword", [
    ("milk", "milk"),
    ("apple", "apple"),
    ("lays", "lay"),
    ("tomato", "tomato"),
    ("oil", "oil"),
    ("dettol", "dettol"),
])
def test_universal_autocomplete_queries(query, expected_keyword):
    """Verify live search autocomplete works for all quick-commerce staples."""
    response = client.get(f"/api/v1/search/autocomplete?q={query}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    names_combined = " ".join([item["name"].lower() for item in data])
    assert expected_keyword in names_combined


def test_autocomplete_empty_query():
    """Verify empty query returns 422 or empty list cleanly."""
    response = client.get("/api/v1/search/autocomplete?q=")
    assert response.status_code in [200, 422]


def test_autocomplete_arbitrary_query():
    """Verify arbitrary unlisted product generates a smart dynamic suggestion."""
    response = client.get("/api/v1/search/autocomplete?q=Dragonfruit+500g")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "Dragonfruit" in data[0]["name"]
    assert data[0]["imageUrl"] is not None
