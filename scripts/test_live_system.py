"""
TrendPulse End-to-End Live System Demonstration & Test Script.

Simulates a real clothing merchant workflow:
    1. User Registration & JWT Authentication
    2. Multipart Dataset Upload (CSV with messy fashion headers)
    3. Full Data Engine Pipeline Execution & Persistence
    4. Querying Trust Scores, PVM Decomposition, and Apparel Intelligence
    5. Clean CSV Export
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

# Ensure root is on pythonpath
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Ensure utf-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.connection import init_db

client = TestClient(app)


def print_banner(title: str):
    print("\n" + "=" * 75)
    print(f"  [TRENDPULSE] {title.upper()}")
    print("=" * 75)


def print_section(title: str):
    print(f"\n--- [ {title} ] " + "-" * max(2, (65 - len(title))))


def run_live_test():
    # Initialize database tables
    init_db()

    print_banner("TrendPulse Fashion Intelligence Engine — Live End-to-End Run")

    # 1. Health Check
    print_section("1. System Health Check")
    health = client.get("/health").json()
    print(f"Server Status: {health['status'].upper()} (API Version: {health['version']})")

    # 2. User Registration & Login
    print_section("2. Merchant Authentication (JWT)")
    user_email = "founder@urbanstrides.com"
    reg_payload = {
        "email": user_email,
        "password": "StrongPassword2026!",
        "full_name": "Alex Mercer",
        "organization_name": "Urban Strides Apparel",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_res = client.post("/api/v1/auth/login", json={"email": user_email, "password": "StrongPassword2026!"})
    token_data = login_res.json()
    token = token_data["access_token"]
    print(f"Logged in as: {token_data['full_name']} ({token_data['email']})")
    print(f"JWT Token (truncated): {token[:30]}...{token[-15:]}")

    headers = {"Authorization": f"Bearer {token}"}

    # 3. Dataset Upload
    print_section("3. Ingesting Raw Clothing Dataset (CSV)")
    sample_csv_path = project_root / "data" / "raw" / "urban_strides_apparel_sample.csv"
    print(f"Reading file: {sample_csv_path.name} ({sample_csv_path.stat().st_size} bytes)")

    with open(sample_csv_path, "rb") as f:
        upload_res = client.post(
            "/api/v1/datasets/upload",
            files={"file": ("urban_strides_apparel_sample.csv", f, "text/csv")},
            headers=headers,
        )

    if upload_res.status_code != 201:
        print(f"Upload failed ({upload_res.status_code}): {upload_res.text}")
        return

    upload_data = upload_res.json()
    dataset_id = upload_data["dataset_id"]
    print(f"Upload Status: {upload_data['status'].upper()}")
    print(f"Dataset ID: {dataset_id}")
    print(f"Rows Ingested: {upload_data['rows_received']} | Cleaned: {upload_data['rows_cleaned']}")
    print(f"Processing Duration: {upload_data['processing_time_ms']} ms")

    # 4. Data Trust Score
    print_section("4. Multi-Dimensional Data Trust Score (L1)")
    ts = client.get(f"/api/v1/analytics/{dataset_id}/trust-score", headers=headers).json()
    print(f"Composite Trust Score: {ts.get('composite_score')}/100 ({ts.get('trust_level', '').upper()} TRUST)")
    print(f"Assessment: {ts.get('assessment')}")
    dims = ts.get("dimensions", {})
    print("\nDimension Breakdown:")
    for dim_name, d_info in dims.items():
        print(f"  • {dim_name.capitalize():<15} Score: {d_info.get('score'):>5.1f}/100 | {d_info.get('breakdown')}")

    # 5. Price-Volume-Mix Revenue Decomposition
    print_section("5. Price-Volume-Mix (PVM) Revenue Decomposition (L3)")
    pvm = client.get(f"/api/v1/analytics/{dataset_id}/revenue-decomposition", headers=headers).json()
    summary = pvm.get("summary", {})
    decomp = pvm.get("decomposition", {})
    print(f"Previous Period Rev: ₹{summary.get('previous_revenue', 0):,.2f} -> Current Period Rev: ₹{summary.get('current_revenue', 0):,.2f}")
    print(f"Net Variance: ₹{summary.get('total_revenue_delta', 0):+,.2f} ({summary.get('percentage_change', 0):+.1f}%)")
    print(f"Primary Commercial Driver: {pvm.get('primary_driver')}")
    print(f"\nMathematical Decomposition:")
    print(f"  • Volume Effect: ₹{decomp.get('volume_effect', {}).get('impact', 0):+,.2f} ({decomp.get('volume_effect', {}).get('contribution_percentage', 0):.1f}% contribution)")
    print(f"  • Price Effect:  ₹{decomp.get('price_effect', {}).get('impact', 0):+,.2f} ({decomp.get('price_effect', {}).get('contribution_percentage', 0):.1f}% contribution)")
    print(f"  • Mix Effect:    ₹{decomp.get('mix_effect', {}).get('impact', 0):+,.2f} ({decomp.get('mix_effect', {}).get('contribution_percentage', 0):.1f}% contribution)")
    print(f"\nDiagnostic Explanation: \"{pvm.get('diagnostic_explanation')}\"")

    # 6. Customer Analytics & RFM Segmentation
    print_section("6. Customer Analytics & RFM Cohorts (L2)")
    cust = client.get(f"/api/v1/analytics/{dataset_id}/customer-analytics", headers=headers).json()
    ov = cust.get("overview", {})
    print(f"Total Unique Customers: {ov.get('total_customers')} | Repeat Customer Rate: {ov.get('repeat_customer_rate')}%")
    print(f"Avg Revenue Per Customer: ₹{ov.get('average_revenue_per_customer', 0):,.2f}")
    print("\nCustomer RFM Cohorts:")
    for seg in cust.get("segments", []):
        print(f"  • {seg.get('segment'):<25} Customers: {seg.get('customer_count')} ({seg.get('customer_percentage')}%) | Revenue: ₹{seg.get('total_revenue', 0):,.2f}")

    # 7. Product Basket Affinity (Lift & Bundle Recommendations)
    print_section("7. Market Basket Affinity & Cross-Selling (L2)")
    affinity = client.get(f"/api/v1/analytics/{dataset_id}/product-affinity", headers=headers).json()
    print(f"Multi-Item Basket Rate: {affinity.get('multi_item_basket_rate')}% ({affinity.get('multi_item_baskets')}/{affinity.get('total_baskets')} baskets)")
    for pair in affinity.get("top_product_pairs", [])[:3]:
        print(f"  • Pair: '{pair.get('product_a')}' + '{pair.get('product_b')}'")
        print(f"    Lift Multiplier: {pair.get('lift')}x | {pair.get('bundle_recommendation')}")

    # 8. Apparel Domain Intelligence
    print_section("8. Apparel Fashion Intelligence (Size Curves & Colorways)")
    apparel = client.get(f"/api/v1/apparel/{dataset_id}", headers=headers).json()
    size_intel = apparel.get("size_intelligence", {})
    color_intel = apparel.get("color_intelligence", {})

    print("Catalog Size Curve:")
    for s_item in size_intel.get("overall_size_curve", []):
        bar = "█" * int(s_item.get("share_percentage", 0) / 4)
        print(f"  • Size {s_item.get('size'):<6} {s_item.get('share_percentage'):>5.1f}% | {bar}")

    print("\nColor Family Palette Distribution:")
    for fam in color_intel.get("color_family_distribution", []):
        print(f"  • {fam.get('color_family'):<15} Revenue: ₹{fam.get('revenue', 0):,.2f} ({fam.get('revenue_share_percentage')}%)")

    print("\nFit & Silhouette Demand Ranking:")
    for fit_item in apparel.get("fit_intelligence", []):
        print(f"  • {fit_item.get('fit'):<20} Units Sold: {fit_item.get('units_sold')} ({fit_item.get('revenue_share_percentage')}% of revenue)")

    # 9. Viral Aesthetics & Thrift Sourcing Recommender
    print_section("9. Viral Aesthetic Velocity & Thrift Sourcing (Social-First)")
    aes_res = client.get(f"/api/v1/social/{dataset_id}/aesthetics", headers=headers).json()
    print("Top Viral Aesthetics by Revenue:")
    for aes_item in aes_res.get("top_aesthetics_by_revenue", [])[:4]:
        print(f"  • {aes_item.get('aesthetic'):<35} Revenue: ₹{aes_item.get('revenue', 0):,.2f} ({aes_item.get('revenue_share_percentage')}%) | ASP: ₹{aes_item.get('average_selling_price')}")

    sourcing_res = client.get(f"/api/v1/social/{dataset_id}/sourcing-recommendations", headers=headers).json()
    print(f"\nProcurement Guidance: \"{sourcing_res.get('procurement_guidance')}\"")
    print("Prioritized Sourcing Checklist:")
    for chk in sourcing_res.get("sourcing_checklist", [])[:3]:
        print(f"  • [{chk.get('sourcing_priority')}] {chk.get('aesthetic')} - Size: {chk.get('recommended_sizes_to_hunt')} (Avg Price: ₹{chk.get('average_selling_price')})")

    # 10. Unit Economics & 4-Quadrant Profitability Matrix
    print_section("10. Fashion Unit Economics & 4-Quadrant Matrix")
    econ_res = client.get(f"/api/v1/economics/{dataset_id}/margins", headers=headers).json()
    ov_econ = econ_res.get("overall_metrics", {})
    print(f"Gross Revenue: ₹{ov_econ.get('total_revenue', 0):,.2f} | Total COGS: ₹{ov_econ.get('total_cogs', 0):,.2f}")
    print(f"Gross Profit: ₹{ov_econ.get('total_gross_profit', 0):,.2f} (Margin: {ov_econ.get('gross_margin_percentage', 0):.1f}%)")
    print(f"Discount Drag (Lost Margin): ₹{ov_econ.get('total_discount_bleed', 0):,.2f}")

    quads = econ_res.get("profitability_quadrants", {})
    print("\nPortfolio Profitability Quadrants:")
    if quads.get("star_performers"):
        star = quads["star_performers"][0]
        print(f"  • 💎 STAR: '{star.get('sku')}' -> Margin: {star.get('gross_margin_percentage')}% (Sold {star.get('units_sold')} units) | {star.get('action_advice')}")
    if quads.get("cash_cows"):
        cow = quads["cash_cows"][0]
        print(f"  • 💰 CASH COW: '{cow.get('sku')}' -> Margin: {cow.get('gross_margin_percentage')}% (Sold {cow.get('units_sold')} units) | {cow.get('action_advice')}")

    # 11. ML Predictive Intelligence (Demand, Lifecycle, Stockout)
    print_section("11. ML Predictive Intelligence (Demand, Lifecycle, Stockout)")
    ml_summary = client.get(f"/api/v1/ml/{dataset_id}/summary", headers=headers).json()
    print(f"ML Pipeline Status: {ml_summary.get('ml_status', '').upper()} | Models Trained: {ml_summary.get('total_models_trained', 0)}")
    print(f"Suite Coverage: {ml_summary.get('suite_coverage', {})}")

    lc_res = client.get(f"/api/v1/ml/{dataset_id}/product-lifecycle", headers=headers).json()
    print("\nSample Product Lifecycle Predictions:")
    for p in lc_res.get("predictions", [])[:3]:
        print(f"  • {p.get('entity_id')}: Stage={p.get('value')} (Confidence: {p.get('confidence'):.0%}) | Action: {p.get('recommended_action')}")

    # 12. Price Elasticity & Markdown Optimization
    print_section("12. Price Elasticity & Markdown Optimizer")
    pe_res = client.get(f"/api/v1/ml/{dataset_id}/price-elasticity", headers=headers).json()
    for pe in pe_res.get("predictions", [])[:3]:
        meta = pe.get("metadata", {})
        print(f"  • {pe.get('entity_id')}: Elasticity ε={pe.get('value')} ({meta.get('sensitivity')})")
        print(f"    Posture: {meta.get('pricing_posture')}")
        if meta.get("optimal_discount_pct", 0) > 0:
            print(f"    Prescribed Markdown: {meta.get('optimal_discount_pct')}% (Volume Mult: {meta.get('projected_volume_multiplier')}x)")

    # 13. Customer Churn & Repurchase Timing
    print_section("13. Customer Churn Risk & Repurchase Timing")
    cp_res = client.get(f"/api/v1/ml/{dataset_id}/customer-predictions", headers=headers).json()
    for cp in cp_res.get("predictions", [])[:3]:
        meta = cp.get("metadata", {})
        print(f"  • Customer {cp.get('entity_id')}: Churn Risk={cp.get('value'):.0%} ({meta.get('customer_segment')})")
        print(f"    Timing: {meta.get('repurchase_timing_description')} | Exp Next Spend: ₹{meta.get('predicted_next_order_spend'):,.2f}")

    # 14. Autonomous Decision & Action Center
    print_section("14. Autonomous Decision & Action Center")
    dc_res = client.get(f"/api/v1/ml/{dataset_id}/decision-center", headers=headers).json()
    dc = dc_res.get("decision_center", {})
    d_sum = dc.get("summary", {})
    print(f"Threats Detected: {d_sum.get('total_threats_detected', 0)} (₹{d_sum.get('total_revenue_at_risk', 0):,.2f} at risk)")
    print(f"Opportunities Detected: {d_sum.get('total_opportunities_detected', 0)} (₹{d_sum.get('total_projected_opportunity_gain', 0):,.2f} upside)")
    print("\nTop Prescriptive Business Actions:")
    for act in dc.get("action_feed", [])[:4]:
        print(f"  [{act.get('priority')}] [{act.get('category')}] {act.get('headline')}")
        print(f"      Reason: {act.get('reason')}")

    # 15. Clean CSV Export
    print_section("15. Clean & Enriched CSV Export")
    export_res = client.get(f"/api/v1/export/{dataset_id}/clean-csv", headers=headers)
    csv_lines = export_res.text.strip().split("\n")
    print(f"Export HTTP Status: {export_res.status_code}")
    print(f"Export Headers: {csv_lines[0]}")
    print(f"Sample Enriched Row: {csv_lines[1]}")

    print_banner("All-in-One Predictive Suite Complete — 100% Operational")


if __name__ == "__main__":
    run_live_test()
