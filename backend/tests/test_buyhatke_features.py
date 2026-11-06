"""Unit & integration test suite for Buyhatke.com reverse-engineered capabilities:
1. Direct Product URL Resolver (Amazon, Flipkart, Myntra, Blinkit, etc.)
2. Price History & Verdict Engine
3. Price Drop Alert System
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.intelligence.url_resolver import parse_product_url, clean_slug_to_query

client = TestClient(app)


def test_url_resolver_slug_cleaner():
    """Verify clean_slug_to_query extracts human-readable product names."""
    slug = "gold-winner-refined-sunflower-oil-1-l-pouch"
    cleaned = clean_slug_to_query(slug)
    assert "Gold Winner" in cleaned
    assert "Sunflower Oil" in cleaned
    assert "1L" in cleaned


@pytest.mark.parametrize("url,expected_platform,expected_keyword", [
    (
        "https://www.amazon.in/Gold-Winner-Refined-Sunflower-Oil/dp/B0FNX5ZG78",
        "amazon",
        "Gold Winner"
    ),
    (
        "https://www.flipkart.com/apple-iphone-15-black-128-gb/p/itm6ac6485515ae4",
        "flipkart",
        "Apple Iphone"
    ),
    (
        "https://blinkit.com/prn/gold-winner-sunflower-oil/prid/66192",
        "blinkit",
        "Gold Winner"
    ),
    (
        "https://www.bigbasket.com/pd/274141/gold-winner-refined-sunflower-oil-1-l-pouch/",
        "bigbasket",
        "Gold Winner"
    ),
])
def test_direct_url_parsing(url, expected_platform, expected_keyword):
    """Verify parse_product_url extracts platform ID and keywords."""
    res = parse_product_url(url)
    assert res is not None
    assert res.is_url is True
    assert res.platform_id == expected_platform
    assert expected_keyword.lower() in res.clean_query.lower()


def test_resolve_url_endpoint():
    """Verify POST /api/v1/search/resolve-url endpoint contract."""
    payload = {
        "url": "https://www.amazon.in/Gold-Winner-Refined-Sunflower-Oil/dp/B0FNX5ZG78",
        "pin_code": "560001"
    }
    response = client.post("/api/v1/search/resolve-url", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_url"] is True
    assert data["platform_id"] == "amazon"
    assert "Gold Winner" in data["clean_query"]
    assert "search_results" in data
    assert len(data["search_results"]["listings"]) > 0


def test_price_history_verdict_analytics():
    """Verify Buyhatke Price Verdict and fluctuation stats in /api/v1/history."""
    response = client.get("/api/v1/history/Gold-Winner-Sunflower-Oil-1L?days=30")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    summary = data["summary"]
    assert "lowest_price" in summary
    assert "highest_price" in summary
    assert "average_price" in summary
    assert "verdict" in summary
    assert summary["verdict"]["verdict"] in ["Great Time to Buy!", "Wait for Price Drop", "Fair Price"]
    assert summary["verdict"]["badge"] in ["good", "wait", "fair"]
    assert summary["lowest_price"] <= summary["average_price"] <= summary["highest_price"]


def test_price_drop_alert_lifecycle():
    """Verify creating, listing, and deleting a Price Drop Alert."""
    test_email = "shopper_test@pricepeek.io"
    
    # 1. Create alert
    payload = {
        "product_name": "Apple iPhone 15 128GB",
        "target_price": 54999.0,
        "current_price": 58499.0,
        "email": test_email
    }
    res_create = client.post("/api/v1/alerts", json=payload)
    assert res_create.status_code == 201
    created = res_create.json()
    alert_id = created["id"]
    assert created["product_name"] == "Apple iPhone 15 128GB"
    assert created["status"] == "active"

    # 2. List alerts
    res_list = client.get(f"/api/v1/alerts?email={test_email}")
    assert res_list.status_code == 200
    alert_list = res_list.json()
    assert alert_list["total_alerts"] >= 1
    assert any(a["id"] == alert_id for a in alert_list["alerts"])

    # 3. Delete alert
    res_del = client.delete(f"/api/v1/alerts/{alert_id}")
    assert res_del.status_code == 204
