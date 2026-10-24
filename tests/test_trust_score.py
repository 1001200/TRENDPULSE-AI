"""
Tests for the TrendPulse Multi-Dimensional Data Trust Score.
"""

import pandas as pd
import pytest

from data_engine.trust_score import (
    calculate_trust_score,
    score_completeness,
    score_validity,
    score_consistency,
    score_timeliness,
    score_uniqueness,
    classify_trust_level,
)


# ============================================================
# Fixtures
# ============================================================

def make_clean_df():
    """A clean, complete clothing sales DataFrame."""
    return pd.DataFrame({
        "date": pd.to_datetime([
            "2026-08-20", "2026-08-21", "2026-08-22",
            "2026-08-23", "2026-08-24",
        ]),
        "product": [
            "Black Tee", "Blue Jeans", "White Hoodie",
            "Red Dress", "Green Jacket",
        ],
        "category": ["T-Shirt", "Jeans", "Hoodie", "Dress", "Jacket"],
        "quantity": [5, 2, 8, 3, 4],
        "price": [699, 1299, 999, 1599, 2499],
        "customer_id": ["C001", "C002", "C003", "C004", "C005"],
        "order_id": ["O001", "O002", "O003", "O004", "O005"],
        "discount": [0, 10, 0, 15, 5],
    })


def make_dirty_df():
    """A messy DataFrame with multiple quality problems."""
    return pd.DataFrame({
        "date": ["2026-08-20", None, "invalid-date", "2026-08-23", "2026-08-24"],
        "product": ["Black Tee", None, "White Hoodie", "", "Green Jacket"],
        "category": ["T-Shirt", "Jeans", None, "Dress", "Jacket"],
        "quantity": [5, -2, "abc", 3, 3],
        "price": [699, 1299, 999, None, 2499],
    })


def make_duplicate_df():
    """A DataFrame with duplicate rows."""
    base = make_clean_df()
    return pd.concat([base, base.iloc[:2]], ignore_index=True)


# ============================================================
# Completeness Tests
# ============================================================

class TestCompleteness:

    def test_clean_data_high_completeness(self):
        result = score_completeness(make_clean_df())
        assert result["score"] >= 85.0
        assert result["missing_required"] == []

    def test_empty_dataframe(self):
        result = score_completeness(pd.DataFrame())
        assert result["score"] == 0.0

    def test_missing_required_columns(self):
        df = pd.DataFrame({"product": ["Tee"], "quantity": [5]})
        result = score_completeness(df)
        assert "date" in result["missing_required"]
        assert "price" in result["missing_required"]
        assert result["score"] < 85.0

    def test_null_values_reduce_completeness(self):
        df = make_clean_df()
        df.loc[0, "quantity"] = None
        df.loc[1, "price"] = None
        result = score_completeness(df)
        assert result["cell_completeness"] < 100.0

    def test_row_completeness(self):
        df = make_dirty_df()
        result = score_completeness(df)
        assert result["row_completeness"] < 100.0


# ============================================================
# Validity Tests
# ============================================================

class TestValidity:

    def test_clean_data_high_validity(self):
        result = score_validity(make_clean_df())
        # No validation issues passed → high score
        assert result["score"] >= 90.0

    def test_with_validation_errors(self):
        validation = {
            "issues": [
                {"row": 0, "severity": "error", "issue": "negative_quantity"},
                {"row": 1, "severity": "error", "issue": "invalid_price"},
                {"row": 2, "severity": "warning", "issue": "zero_quantity"},
            ]
        }
        result = score_validity(make_clean_df(), validation=validation)
        assert result["error_count"] == 2
        assert result["warning_count"] == 1
        assert result["score"] < 100.0

    def test_empty_dataframe(self):
        result = score_validity(pd.DataFrame())
        assert result["score"] == 0.0

    def test_no_validation_report(self):
        result = score_validity(make_clean_df(), validation=None)
        assert result["score"] == 100.0


# ============================================================
# Consistency Tests
# ============================================================

class TestConsistency:

    def test_clean_data_high_consistency(self):
        result = score_consistency(make_clean_df())
        assert result["score"] >= 85.0
        assert result["type_consistency"] == 100.0

    def test_anomalies_reduce_consistency(self):
        summary = {
            "total_anomalies": 10,
            "affected_rows": 5,
        }
        result = score_consistency(make_clean_df(), anomaly_summary=summary)
        assert result["score"] < 100.0
        assert result["anomaly_ratio"] > 0

    def test_empty_dataframe(self):
        result = score_consistency(pd.DataFrame())
        assert result["score"] == 0.0


# ============================================================
# Timeliness Tests
# ============================================================

class TestTimeliness:

    def test_clean_data_high_timeliness(self):
        result = score_timeliness(make_clean_df())
        assert result["score"] >= 80.0
        assert result["parsable_ratio"] == 100.0

    def test_no_date_column(self):
        df = pd.DataFrame({"product": ["Tee"], "quantity": [5]})
        result = score_timeliness(df)
        # Should still return a score (reduced because no dates)
        assert "score" in result

    def test_unparsable_dates(self):
        df = pd.DataFrame({
            "date": ["not-a-date", "also-bad", "invalid"],
            "product": ["A", "B", "C"],
        })
        result = score_timeliness(df)
        assert result["parsable_ratio"] == 0.0

    def test_future_dates_penalized(self):
        df = pd.DataFrame({
            "date": pd.to_datetime([
                "2099-01-01", "2099-06-01", "2099-12-01",
                "2026-08-01", "2026-08-02",
            ]),
        })
        result = score_timeliness(df)
        assert result["future_ratio"] > 0

    def test_empty_dataframe(self):
        result = score_timeliness(pd.DataFrame())
        assert result["score"] == 50.0


# ============================================================
# Uniqueness Tests
# ============================================================

class TestUniqueness:

    def test_clean_data_high_uniqueness(self):
        result = score_uniqueness(make_clean_df())
        assert result["score"] == 100.0
        assert result["duplicate_count"] == 0

    def test_duplicates_reduce_score(self):
        result = score_uniqueness(make_duplicate_df())
        assert result["score"] < 100.0
        assert result["duplicate_count"] == 2

    def test_empty_dataframe(self):
        result = score_uniqueness(pd.DataFrame())
        assert result["score"] == 100.0


# ============================================================
# Trust Level Classification
# ============================================================

class TestClassifyTrustLevel:

    def test_high(self):
        assert classify_trust_level(90.0) == "high"
        assert classify_trust_level(85.0) == "high"

    def test_medium(self):
        assert classify_trust_level(70.0) == "medium"
        assert classify_trust_level(60.0) == "medium"

    def test_low(self):
        assert classify_trust_level(50.0) == "low"
        assert classify_trust_level(0.0) == "low"


# ============================================================
# Composite Trust Score Tests
# ============================================================

class TestCalculateTrustScore:

    def test_clean_data_composite(self):
        df = make_clean_df()
        result = calculate_trust_score(df)
        assert "composite_score" in result
        assert "trust_level" in result
        assert "dimensions" in result
        assert "assessment" in result
        assert result["composite_score"] >= 0.0
        assert result["composite_score"] <= 100.0
        assert result["trust_level"] in ("high", "medium", "low")

    def test_all_dimensions_present(self):
        result = calculate_trust_score(make_clean_df())
        dims = result["dimensions"]
        for dim in ("completeness", "validity", "consistency", "timeliness", "uniqueness"):
            assert dim in dims
            assert "score" in dims[dim]
            assert "breakdown" in dims[dim]

    def test_dirty_data_lower_score(self):
        clean = calculate_trust_score(make_clean_df())
        dirty_df = make_dirty_df()
        dirty = calculate_trust_score(dirty_df)
        assert dirty["composite_score"] < clean["composite_score"]

    def test_with_validation_and_anomalies(self):
        df = make_clean_df()
        validation = {
            "issues": [
                {"row": 0, "severity": "error", "issue": "negative_quantity"},
            ]
        }
        anomaly_summary = {"total_anomalies": 2, "affected_rows": 2}
        result = calculate_trust_score(
            df, validation=validation, anomaly_summary=anomaly_summary
        )
        assert result["composite_score"] < 100.0

    def test_weights_sum_to_one(self):
        result = calculate_trust_score(make_clean_df())
        total = sum(result["weights"].values())
        assert abs(total - 1.0) < 0.001

    def test_type_error_on_non_dataframe(self):
        with pytest.raises(TypeError):
            calculate_trust_score("not a dataframe")

    def test_json_safe_output(self):
        """Trust score result should be JSON-safe (no pandas/numpy objects)."""
        import json
        result = calculate_trust_score(make_clean_df())
        # This should not raise
        json.dumps(result)

    def test_version_field_present(self):
        result = calculate_trust_score(make_clean_df())
        assert result["version"] == "1.0"

    def test_empty_dataframe(self):
        result = calculate_trust_score(pd.DataFrame())
        assert result["composite_score"] >= 0.0
        assert result["trust_level"] == "low"

    def test_pipeline_integration(self):
        """Trust score should be present in the processor output."""
        from data_engine.processor import process_dataframe
        df = make_clean_df()
        result = process_dataframe(df, enable_llm=False)
        assert "trust_score" in result
        assert "composite_score" in result["trust_score"]
        assert "dimensions" in result["trust_score"]
