"""
Comprehensive Integration Tests for the TrendPulse FastAPI Backend & Database.

Tests:
    - Root & Health endpoints
    - User Authentication (Registration, Login, JWT verification)
    - Dataset Upload (CSV ingestion, processing, DB persistence)
    - Analytics Endpoints (Trust Score, PVM Decomposition, Customer RFM, Affinity)
    - Apparel Intelligence Endpoints (Size Curves, Broken Runs, Colorways, Fits)
    - Data Export Endpoints (Clean CSV download, JSON report download)
    - Dataset Deletion & Cleanup
"""

import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database.connection import Base, get_db
from backend.app.main import app

# In-memory SQLite database specifically for test isolation
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_database():
    """Create fresh in-memory database tables for each test run."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_csv_file():
    """Returns an in-memory CSV file representing multi-period apparel sales."""
    csv_content = (
        "Order Date,Product Name,Category,Qty,Selling Price,Customer ID,Order ID\n"
        "2026-07-01,Oversized Vintage Tee - Vintage Black / M,T-Shirt,10,699,C001,ORD01\n"
        "2026-07-01,Slim Fit Denim Jeans - Indigo / 32,Jeans,5,1299,C001,ORD01\n"
        "2026-07-15,French Terry Hoodie - Charcoal / L,Hoodie,8,999,C002,ORD02\n"
        "2026-08-01,Oversized Vintage Tee - Vintage Black / L,T-Shirt,15,699,C001,ORD03\n"
        "2026-08-10,Cropped Linen Top - Sage Green / S,Tops,6,899,C003,ORD04\n"
    )
    return io.BytesIO(csv_content.encode("utf-8"))


# ============================================================
# 1. System Health & Root Tests
# ============================================================

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "version" in data


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# ============================================================
# 2. Authentication & User Profile Tests
# ============================================================

def test_user_registration_and_login():
    # 1. Register User
    reg_payload = {
        "email": "fashion_founder@brand.com",
        "password": "SecurePassword2026!",
        "full_name": "Fashion Founder",
        "organization_name": "Aesthetic Apparel Co",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    user_data = reg_res.json()
    assert user_data["email"] == "fashion_founder@brand.com"
    assert user_data["full_name"] == "Fashion Founder"

    # 2. Duplicate registration fails
    dup_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert dup_res.status_code == 400

    # 3. Login
    login_payload = {
        "email": "fashion_founder@brand.com",
        "password": "SecurePassword2026!",
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 4. Access protected profile endpoint
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "fashion_founder@brand.com"


# ============================================================
# 3. Dataset Upload & Ingestion Tests
# ============================================================

def test_dataset_upload_and_pipeline_execution(sample_csv_file):
    files = {"file": ("clothing_sales_july_august.csv", sample_csv_file, "text/csv")}
    res = client.post("/api/v1/datasets/upload", files=files)

    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "completed"
    assert data["rows_received"] == 5
    assert data["rows_cleaned"] == 5
    assert data["dataset_id"] > 0
    assert data["trust_score"] is not None
    assert data["trust_score"]["composite_score"] >= 80.0

    dataset_id = data["dataset_id"]

    # List datasets
    list_res = client.get("/api/v1/datasets/")
    assert list_res.status_code == 200
    datasets = list_res.json()
    assert len(datasets) >= 1
    assert datasets[0]["id"] == dataset_id

    # Get dataset details with full snapshot
    detail_res = client.get(f"/api/v1/datasets/{dataset_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["result"] is not None
    assert "insights" in detail["result"]
    assert "apparel_intelligence" in detail["result"]


# ============================================================
# 4. Analytics & Diagnostics API Tests
# ============================================================

def test_analytics_endpoints(sample_csv_file):
    # Upload dataset first
    files = {"file": ("sales_data.csv", sample_csv_file, "text/csv")}
    upload_res = client.post("/api/v1/datasets/upload", files=files)
    dataset_id = upload_res.json()["dataset_id"]

    # 1. Trust score endpoint
    ts_res = client.get(f"/api/v1/analytics/{dataset_id}/trust-score")
    assert ts_res.status_code == 200
    assert "composite_score" in ts_res.json()
    assert "dimensions" in ts_res.json()

    # 2. Revenue decomposition endpoint
    rd_res = client.get(f"/api/v1/analytics/{dataset_id}/revenue-decomposition")
    assert rd_res.status_code == 200
    assert "decomposition" in rd_res.json()

    # 3. Performance drivers endpoint
    dr_res = client.get(f"/api/v1/analytics/{dataset_id}/performance-drivers")
    assert dr_res.status_code == 200
    assert "top_revenue_drivers" in dr_res.json()

    # 4. Customer analytics endpoint
    cust_res = client.get(f"/api/v1/analytics/{dataset_id}/customer-analytics")
    assert cust_res.status_code == 200
    assert "overview" in cust_res.json()

    # 5. Product affinity endpoint
    aff_res = client.get(f"/api/v1/analytics/{dataset_id}/product-affinity")
    assert aff_res.status_code == 200
    assert "top_product_pairs" in aff_res.json()


# ============================================================
# 5. Apparel Domain Intelligence API Tests
# ============================================================

def test_apparel_domain_endpoints(sample_csv_file):
    files = {"file": ("apparel_sales.csv", sample_csv_file, "text/csv")}
    upload_res = client.post("/api/v1/datasets/upload", files=files)
    dataset_id = upload_res.json()["dataset_id"]

    # Full apparel intel
    app_res = client.get(f"/api/v1/apparel/{dataset_id}")
    assert app_res.status_code == 200
    assert "size_intelligence" in app_res.json()
    assert "color_intelligence" in app_res.json()

    # Size curves
    sc_res = client.get(f"/api/v1/apparel/{dataset_id}/size-curves")
    assert sc_res.status_code == 200
    assert "overall_size_curve" in sc_res.json()

    # Colorways
    col_res = client.get(f"/api/v1/apparel/{dataset_id}/colorways")
    assert col_res.status_code == 200
    assert "top_colorways" in col_res.json()

    # Fits
    fit_res = client.get(f"/api/v1/apparel/{dataset_id}/fits")
    assert fit_res.status_code == 200
    assert len(fit_res.json()) > 0


# ============================================================
# 6. ML Predictive Intelligence Endpoints Tests
# ============================================================

def test_ml_intelligence_endpoints(sample_csv_file):
    files = {"file": ("ml_test.csv", sample_csv_file, "text/csv")}
    upload_res = client.post("/api/v1/datasets/upload", files=files)
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["dataset_id"]

    # Demand forecast endpoint
    df_res = client.get(f"/api/v1/ml/{dataset_id}/demand-forecast")
    assert df_res.status_code == 200
    df_data = df_res.json()
    assert df_data["prediction_type"] == "demand_forecast"
    assert "predictions" in df_data

    # Product lifecycle endpoint
    lc_res = client.get(f"/api/v1/ml/{dataset_id}/product-lifecycle")
    assert lc_res.status_code == 200
    lc_data = lc_res.json()
    assert lc_data["prediction_type"] == "product_lifecycle"
    assert "predictions" in lc_data

    # Stockout predictions endpoint
    so_res = client.get(f"/api/v1/ml/{dataset_id}/stockout-predictions")
    assert so_res.status_code == 200
    so_data = so_res.json()
    assert so_data["prediction_type"] == "stockout_prediction"
    assert "predictions" in so_data

    # Price elasticity endpoint
    pe_res = client.get(f"/api/v1/ml/{dataset_id}/price-elasticity")
    assert pe_res.status_code == 200
    pe_data = pe_res.json()
    assert pe_data["prediction_type"] == "price_elasticity"
    assert "predictions" in pe_data

    # Customer predictions endpoint
    cp_res = client.get(f"/api/v1/ml/{dataset_id}/customer-predictions")
    assert cp_res.status_code == 200
    cp_data = cp_res.json()
    assert cp_data["prediction_type"] == "customer_predictions"
    assert "predictions" in cp_data

    # Decision center endpoint
    dc_res = client.get(f"/api/v1/ml/{dataset_id}/decision-center")
    assert dc_res.status_code == 200
    dc_data = dc_res.json()
    assert "decision_center" in dc_data
    assert "ranked_threats" in dc_data["decision_center"]
    assert "action_feed" in dc_data["decision_center"]

    # What-If Price Simulation endpoint
    if pe_data.get("predictions"):
        target_product = pe_data["predictions"][0]["entity_id"]
        sim_res = client.post(
            f"/api/v1/ml/{dataset_id}/simulate-price",
            json={"product": target_product, "new_price": 599.0},
        )
        assert sim_res.status_code == 200
        sim_data = sim_res.json()
        assert sim_data["product"] == target_product
        assert "projected_revenue_change_percentage" in sim_data
        assert "commercial_verdict" in sim_data

    # Model registry endpoint
    reg_res = client.get(f"/api/v1/ml/{dataset_id}/model-registry")
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert "registry" in reg_data

    # Summary endpoint
    sum_res = client.get(f"/api/v1/ml/{dataset_id}/summary")
    assert sum_res.status_code == 200
    sum_data = sum_res.json()
    assert "ml_status" in sum_data
    assert "suite_coverage" in sum_data
    assert "critical_highlights" in sum_data


# ============================================================
# 7. Export & Deletion Tests
# ============================================================

def test_export_and_deletion(sample_csv_file):
    files = {"file": ("export_test.csv", sample_csv_file, "text/csv")}
    upload_res = client.post("/api/v1/datasets/upload", files=files)
    dataset_id = upload_res.json()["dataset_id"]

    # Export clean CSV
    csv_res = client.get(f"/api/v1/export/{dataset_id}/clean-csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "std_size" in csv_res.text  # Verified enriched columns present

    # Export report JSON
    json_res = client.get(f"/api/v1/export/{dataset_id}/report-json")
    assert json_res.status_code == 200
    assert "application/json" in json_res.headers["content-type"]

    # Delete dataset
    del_res = client.delete(f"/api/v1/datasets/{dataset_id}")
    assert del_res.status_code == 204

    # Verify not found after delete
    get_res = client.get(f"/api/v1/datasets/{dataset_id}")
    assert get_res.status_code == 404
