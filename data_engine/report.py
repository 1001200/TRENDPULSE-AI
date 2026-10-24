import pandas as pd

from data_engine.utils import safe_int


# ============================================================
# Quality Score Configuration
# ============================================================

MAX_SCORE = 100.0

# Keep the existing validation scoring behavior:
# one invalid quantity row = -6 points
INVALID_QUANTITY_PENALTY = 6.0

# One invalid price row = -6 points
INVALID_PRICE_PENALTY = 6.0

# Duplicate row penalty
DUPLICATE_ROW_PENALTY = 4.0

# Missing required column penalty
MISSING_COLUMN_PENALTY = 15.0

# Missing-value warning penalty
MISSING_VALUE_PENALTY = 2.0

# Anomaly penalties
ANOMALY_WARNING_PENALTY = 2.0
ANOMALY_CRITICAL_PENALTY = 5.0

# ============================================================
# Validation Penalty
# ============================================================

def calculate_validation_penalty(
    validation_report
):
    """
    Calculate penalties caused by validation problems.

    This preserves the old behavior where:

        1 invalid quantity row = -6
        1 invalid price row    = -6
        1 duplicate row        = -4
        1 missing column       = -15
    """

    invalid_quantity_rows = safe_int(
        validation_report.get(
            "invalid_quantity_rows",
            0
        )
    )

    invalid_price_rows = safe_int(
        validation_report.get(
            "invalid_price_rows",
            0
        )
    )

    duplicate_rows = safe_int(
        validation_report.get(
            "duplicate_rows",
            0
        )
    )

    missing_columns = validation_report.get(
        "missing_columns",
        []
    )

    penalty = 0.0

    penalty += (
        invalid_quantity_rows
        * INVALID_QUANTITY_PENALTY
    )

    penalty += (
        invalid_price_rows
        * INVALID_PRICE_PENALTY
    )

    penalty += (
        duplicate_rows
        * DUPLICATE_ROW_PENALTY
    )

    penalty += (
        len(missing_columns)
        * MISSING_COLUMN_PENALTY
    )

    return penalty


# ============================================================
# Missing Value Penalty
# ============================================================

def calculate_missing_value_penalty(
    validation_report
):
    """
    Calculate a small penalty for missing-value warnings.

    Missing values are treated differently from invalid values.

    Invalid:
        stronger penalty

    Missing:
        smaller penalty
    """

    issues = validation_report.get(
        "issues",
        []
    )

    missing_count = 0

    for issue in issues:

        issue_type = issue.get(
            "issue"
        )

        if issue_type in [
            "missing_quantity",
            "missing_price",
            "missing_date"
        ]:

            missing_count += 1

    return (
        missing_count
        * MISSING_VALUE_PENALTY
    )


# ============================================================
# Anomaly Penalty
# ============================================================

def calculate_anomaly_penalty(
    anomaly_summary
):
    """
    Calculate anomaly penalties.

    Warning:
        -2 points

    Critical:
        -5 points
    """

    if not anomaly_summary:

        return 0.0

    by_severity = anomaly_summary.get(
        "by_severity",
        {}
    )

    warning_count = safe_int(
        by_severity.get(
            "warning",
            0
        )
    )

    critical_count = safe_int(
        by_severity.get(
            "critical",
            0
        )
    )

    penalty = (
        warning_count
        * ANOMALY_WARNING_PENALTY
    )

    penalty += (
        critical_count
        * ANOMALY_CRITICAL_PENALTY
    )

    return penalty


# ============================================================
# Final Score
# ============================================================

def calculate_quality_score(
    validation_report,
    anomaly_summary=None
):
    """
    Calculate the final quality score.

    Score is always bounded between 0 and 100.
    """

    validation_penalty = (
        calculate_validation_penalty(
            validation_report
        )
    )

    missing_value_penalty = (
        calculate_missing_value_penalty(
            validation_report
        )
    )

    anomaly_penalty = (
        calculate_anomaly_penalty(
            anomaly_summary
        )
    )

    total_penalty = (
        validation_penalty
        + missing_value_penalty
        + anomaly_penalty
    )

    score = (
        MAX_SCORE
        - total_penalty
    )

    score = max(
        0.0,
        min(
            MAX_SCORE,
            score
        )
    )

    return round(
        score,
        2
    )


# ============================================================
# Quality Breakdown
# ============================================================

def build_quality_breakdown(
    validation_report,
    anomaly_summary=None
):
    """
    Explain exactly why the quality score has its value.
    """

    validation_penalty = (
        calculate_validation_penalty(
            validation_report
        )
    )

    missing_value_penalty = (
        calculate_missing_value_penalty(
            validation_report
        )
    )

    anomaly_penalty = (
        calculate_anomaly_penalty(
            anomaly_summary
        )
    )

    total_penalty = (
        validation_penalty
        + missing_value_penalty
        + anomaly_penalty
    )

    return {

        "starting_score":
            MAX_SCORE,

        "validation_penalty":
            round(
                validation_penalty,
                2
            ),

        "missing_value_penalty":
            round(
                missing_value_penalty,
                2
            ),

        "anomaly_penalty":
            round(
                anomaly_penalty,
                2
            ),

        "total_penalty":
            round(
                total_penalty,
                2
            ),

        "final_score":
            calculate_quality_score(
                validation_report,
                anomaly_summary
            )
    }


# ============================================================
# Main Quality Report
# ============================================================

def create_quality_report(
    validation_report,
    rows_received,
    anomaly_summary=None
):
    """
    Create the TrendPulse quality report.

    The function remains compatible with the old processor:

        create_quality_report(
            validation_report,
            rows_received
        )

    Anomaly information is optional.
    """

    if anomaly_summary is None:

        anomaly_summary = {
            "total_anomalies": 0,
            "by_column": {},
            "by_method": {},
            "by_severity": {}
        }

    quality_score = calculate_quality_score(
        validation_report,
        anomaly_summary
    )

    quality_breakdown = (
        build_quality_breakdown(
            validation_report,
            anomaly_summary
        )
    )

    return {

        "rows_received":
            rows_received,

        "missing_columns":
            len(
                validation_report.get(
                    "missing_columns",
                    []
                )
            ),

        "duplicate_rows":
            validation_report.get(
                "duplicate_rows",
                0
            ),

        "invalid_quantity_rows":
            validation_report.get(
                "invalid_quantity_rows",
                0
            ),

        "invalid_price_rows":
            validation_report.get(
                "invalid_price_rows",
                0
            ),

        "quality_score":
            quality_score,

        "anomalies":
            anomaly_summary.get(
                "total_anomalies",
                0
            ),

        "anomaly_summary":
            anomaly_summary,

        "quality_breakdown":
            quality_breakdown
    }