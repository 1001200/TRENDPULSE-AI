"""
Automated Test Suite for TrendPulse Drop & DM Closing Engine.

Tests:
- Store & Drop setup
- 30-second quick item listing with auto-aesthetic classifier
- Public drop query & real-time inventory status
- Atomic 10-minute claim lock & collision prevention
- Ship-now checkout with address & UTR
- 1-Click Shiprocket CSV export
- Live sourcing intelligence card
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.database.connection import Base, get_db

@pytest.fixture
def client():
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    old_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    if old_override:
        app.dependency_overrides[get_db] = old_override
    else:
        app.dependency_overrides.pop(get_db, None)

    Base.metadata.drop_all(bind=test_engine)


def test_full_drop_and_checkout_lifecycle(client):
    # 1. Initialize seller store
    store_payload = {
        "name": "Delhi Thrift Co",
        "slug": "delhi-thrift",
        "instagram_handle": "delhithriftco",
        "upi_id": "delhithrift@okaxis",
        "phone": "9876543210",
        "fulfillment_type": "self",
        "flat_shipping_fee": 70.0,
    }
    res = client.post("/api/v1/seller/store", json=store_payload)
    assert res.status_code == 200, res.text
    store_data = res.json()
    assert store_data["slug"] == "delhi-thrift"

    # 2. Create a new Drop
    drop_payload = {
        "title": "Sunday Vintage Grails",
        "slug": "sunday-grails",
    }
    res = client.post("/api/v1/seller/drops", json=drop_payload)
    assert res.status_code == 200, res.text
    drop_data = res.json()
    drop_id = drop_data["id"]
    assert drop_data["title"] == "Sunday Vintage Grails"

    # 3. 30-Second Quick Upload an Item
    item_payload = {
        "title": "Vintage 90s Acid Wash Graphic Tee - Oversized",
        "category": "Tops",
        "size_label": "L (Oversized)",
        "chest_inches": 44.0,
        "length_inches": 29.0,
        "price_inr": 899.0,
        "condition_score": "9/10",
        "photo_url": "https://example.com/photos/tee.jpg",
    }
    res = client.post(f"/api/v1/seller/drops/{drop_id}/items", json=item_payload)
    assert res.status_code == 200, res.text
    item_data = res.json()
    item_id = item_data["id"]
    assert item_data["status"] == "available"
    # Auto-aesthetic classification
    assert item_data["aesthetic"] != ""

    # 4. Public Buyer queries the drop
    res = client.get("/api/v1/public/drop/sunday-grails")
    assert res.status_code == 200, res.text
    public_drop = res.json()
    assert len(public_drop["items"]) == 1
    assert public_drop["items"][0]["status"] == "available"

    # 5. Buyer claims the item (10-minute atomic lock)
    claim_payload = {"buyer_phone": "9988776655"}
    res = client.post(f"/api/v1/public/items/{item_id}/claim", json=claim_payload)
    assert res.status_code == 200, res.text
    claim_data = res.json()
    assert claim_data["success"] is True
    assert claim_data["status"] == "reserved"
    assert claim_data["seconds_remaining"] > 590
    assert "upi://pay" in claim_data["upi_intent_uri"]
    assert "delhithrift@okaxis" in claim_data["upi_intent_uri"]
    assert claim_data["total_amount_inr"] == 899.0 + 70.0

    # 6. Another buyer tries to claim the same item -> must get 409 Conflict
    res_conflict = client.post(
        f"/api/v1/public/items/{item_id}/claim", json={"buyer_phone": "9123456789"}
    )
    assert res_conflict.status_code == 409

    # 7. Buyer completes ship-now checkout with UTR
    checkout_payload = {
        "buyer_name": "Aarav Sharma",
        "buyer_ig": "aarav_vintage",
        "buyer_phone": "9988776655",
        "address_line": "Flat 304, Green Palms, Civil Lines",
        "pincode": "302006",
        "city": "Jaipur",
        "state": "Rajasthan",
        "utr_reference": "428910293812",
    }
    res = client.post(f"/api/v1/public/items/{item_id}/checkout", json=checkout_payload)
    assert res.status_code == 200, res.text
    order_data = res.json()
    assert order_data["total_amount_inr"] == 969.0
    assert order_data["utr_reference"] == "428910293812"

    # 8. Public drop now shows the item as SOLD
    res = client.get("/api/v1/public/drop/sunday-grails")
    assert res.status_code == 200
    assert res.json()["items"][0]["status"] == "sold"

    # 9. Seller checks orders list
    res = client.get("/api/v1/seller/orders")
    assert res.status_code == 200
    orders = res.json()
    assert len(orders) == 1
    assert orders[0]["buyer_name"] == "Aarav Sharma"
    assert orders[0]["pincode"] == "302006"

    # 10. Seller exports Shiprocket CSV
    res = client.get("/api/v1/seller/export/shiprocket")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    csv_content = res.text
    assert "Aarav Sharma" in csv_content
    assert "302006" in csv_content
    assert "ORD-" in csv_content

    # 11. Sourcing intelligence card reflects the sale
    res = client.get("/api/v1/seller/sourcing-card")
    assert res.status_code == 200
    sourcing_card = res.json()
    assert sourcing_card["status"] == "active"
    assert sourcing_card["total_items_sold"] == 1
    assert sourcing_card["total_revenue_inr"] == 899.0
