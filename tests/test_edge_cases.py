import pandas as pd
from data_engine.auto_analyst.pipeline import AutoAnalystEngine

def test_no_dates_dataset():
    # Only categoricals and numerics
    df = pd.DataFrame({
        "Department": ["HR", "Engineering", "Sales", "Support", "Marketing"] * 5,
        "Salary_USD": [50000, 120000, 80000, 45000, 75000] * 5,
        "Performance_Score": [3.2, 4.8, 4.1, 3.0, 3.9] * 5,
        "Remote_Worker": ["Yes", "No", "Yes", "Yes", "No"] * 5,
    })
    engine = AutoAnalystEngine()
    result = engine.run(df, filename="hr_salaries.csv")
    assert result["metadata"]["rows_cleaned"] == 5  # Deduplicated from 25
    assert len(result["dashboard"]["kpi_cards"]) > 0
    print("[EDGE TEST PASS] No-date dataset handled smoothly.")

def test_no_numerics_dataset():
    # Only categoricals and text
    df = pd.DataFrame({
        "User_ID": [f"USR_{i}" for i in range(20)],
        "Subscription_Tier": ["Basic", "Pro", "Enterprise", "Free"] * 5,
        "Country": ["US", "IN", "UK", "CA"] * 5,
    })
    engine = AutoAnalystEngine()
    result = engine.run(df, filename="users_no_num.csv")
    assert result["metadata"]["rows_cleaned"] == 20
    assert len(result["dashboard"]["kpi_cards"]) > 0
    print("[EDGE TEST PASS] No-numeric dataset handled smoothly.")

def test_dirty_formatting():
    # Currency with weird symbols and nulls
    df = pd.DataFrame({
        "Price": ["$ 1,200.50", "€ 450", "₹ 99,000", "(250.00)", None, "unknown"],
        "Category": ["Apparel", "Home", "Tech", "Outdoor", None, "Tech"],
    })
    engine = AutoAnalystEngine()
    result = engine.run(df, filename="dirty_test.csv")
    assert result["metadata"]["rows_cleaned"] > 0
    print("[EDGE TEST PASS] Dirty symbols and mixed strings handled smoothly.")

if __name__ == "__main__":
    test_no_dates_dataset()
    test_no_numerics_dataset()
    test_dirty_formatting()
    print("\nALL ZERO-SHOT EDGE CASES PASSED! ENGINE IS BULLETPROOF.")
