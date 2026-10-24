import json
from data_engine.auto_analyst.pipeline import AutoAnalystEngine

def test_healthcare_pipeline():
    engine = AutoAnalystEngine()
    result = engine.run("data/raw/sample_healthcare_clinic.csv")
    assert result["metadata"]["rows_cleaned"] > 0
    assert result["quality"]["health_score"] > 80
    assert len(result["dashboard"]["kpi_cards"]) > 0
    assert len(result["dashboard"]["charts"]) > 0
    assert len(result["narrative"]["executive_summary"]) > 0
    print("[SUCCESS] Healthcare Dataset Processed:")
    print("  Rows Cleaned:", result["metadata"]["rows_cleaned"])
    print("  Health Score:", result["quality"]["health_score"])
    print("  Charts Synthesized:", len(result["dashboard"]["charts"]))
    print("  Executive Summary:", result["narrative"]["executive_summary"])
    if result["patterns"]["clusters"].get("enabled"):
        print("  Clusters:", [p["name"] for p in result["patterns"]["clusters"]["profiles"]])

def test_marketing_pipeline():
    engine = AutoAnalystEngine()
    result = engine.run("data/raw/sample_marketing_campaigns.csv")
    assert result["metadata"]["rows_cleaned"] > 0
    assert result["quality"]["health_score"] > 80
    assert len(result["dashboard"]["charts"]) > 0
    print("\n[SUCCESS] Marketing Dataset Processed:")
    print("  Rows Cleaned:", result["metadata"]["rows_cleaned"])
    print("  Health Score:", result["quality"]["health_score"])
    print("  Charts Synthesized:", len(result["dashboard"]["charts"]))
    print("  Top Outliers Detected:", result["patterns"]["anomalies"]["outlier_count"])
    print("  Executive Summary:", result["narrative"]["executive_summary"])

if __name__ == "__main__":
    test_healthcare_pipeline()
    test_marketing_pipeline()
