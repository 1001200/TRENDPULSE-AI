import pandas as pd

from data_engine.insight_engine import (
    analyze_anomalies,
    analyze_time,
    create_insight_report,
    generate_insights_report,
)


# ============================================================
# Test Dataset
# ============================================================

def make_test_dataframe():

    return pd.DataFrame({

        "product": [
            "Product A",
            "Product B",
            "Product C",
            "Product D",
            "Product E",
            "Product F",
            "Product G",
            "Product H",
            "Product I",
            "Product J",
            "Product K",
        ],

        "category": [
            "Electronics",
            "Electronics",
            "Electronics",
            "Home",
            "Home",
            "Home",
            "Accessories",
            "Accessories",
            "Accessories",
            "Electronics",
            "Electronics",
        ],

        "quantity": [
            5,
            6,
            4,
            5,
            7,
            6,
            5,
            4,
            6,
            100,
            500,
        ],

        "price": [
            699,
            749,
            699,
            799,
            699,
            749,
            799,
            699,
            749,
            99999,
            999999,
        ],

        "date": [
            "2026-01-01",
            "2026-01-02",
            "2026-01-03",
            "2026-01-04",
            "2026-01-05",
            "2026-01-06",
            "2026-01-07",
            "2026-01-08",
            "2026-01-09",
            "2026-01-10",
            "2026-01-11",
        ],
    })


# ============================================================
# Fake Anomaly Detector Output
# ============================================================

def make_anomalies():

    anomalies = [

        {
            "row": 9,
            "column": "price",
            "value": 99999,
            "method": "iqr",
            "score": 10.0,
            "severity": "warning",
            "direction": "high",
        },

        {
            "row": 10,
            "column": "price",
            "value": 999999,
            "method": "iqr",
            "score": 20.0,
            "severity": "critical",
            "direction": "high",
        },

        {
            "row": 10,
            "column": "quantity",
            "value": 500,
            "method": "iqr",
            "score": 15.0,
            "severity": "critical",
            "direction": "high",
        },
    ]

    summary = {
        "total_anomalies": 3,

        "by_column": {
            "price": 2,
            "quantity": 1,
        },

        "by_method": {
            "iqr": 3,
        },

        "by_severity": {
            "warning": 1,
            "critical": 2,
        },
    }

    return anomalies, summary


# ============================================================
# Tests
# ============================================================

def test_empty_dataframe():

    df = pd.DataFrame()

    report = generate_insights_report(df)

    assert report["version"] == "3.0"
    assert report["insights"] == []
    assert report["opportunities"] == []
    assert report["risks"] == []


def test_invalid_dataframe():

    try:
        generate_insights_report(
            ["not", "a", "dataframe"]
        )

    except TypeError:
        pass

    else:
        raise AssertionError(
            "Expected TypeError."
        )


def test_revenue_calculation():

    df = make_test_dataframe()

    report = generate_insights_report(
        df
    )

    expected_revenue = (
        df["quantity"] * df["price"]
    ).sum()

    assert (
        report["summary"]["observed"][
            "total_revenue"
        ]
        == expected_revenue
    )


def test_input_dataframe_is_not_modified():

    df = make_test_dataframe()

    original = df.copy(deep=True)

    generate_insights_report(
        df
    )

    assert df.equals(original)


def test_anomaly_impact():

    df = make_test_dataframe()

    anomalies, anomaly_summary = (
        make_anomalies()
    )

    report = generate_insights_report(
        df,
        anomaly_summary=anomaly_summary,
        anomalies=anomalies,
    )

    anomaly_analysis = report[
        "anomaly_analysis"
    ]

    assert (
        anomaly_analysis[
            "affected_rows"
        ]
        == 2
    )

    assert (
        anomaly_analysis[
            "anomalous_revenue"
        ]
        > 0
    )

    assert (
        anomaly_analysis[
            "anomalous_revenue_share"
        ]
        > 0
    )

    assert (
        anomaly_analysis[
            "adjusted_revenue"
        ]
        <
        anomaly_analysis[
            "observed_revenue"
        ]
    )


def test_adjusted_summary():

    df = make_test_dataframe()

    anomalies, anomaly_summary = (
        make_anomalies()
    )

    report = generate_insights_report(
        df,
        anomaly_summary=anomaly_summary,
        anomalies=anomalies,
    )

    observed = report[
        "summary"
    ]["observed"]

    adjusted = report[
        "summary"
    ]["adjusted"]

    assert (
        adjusted["excluded_rows"]
        == 2
    )

    assert (
        adjusted["remaining_rows"]
        == len(df) - 2
    )

    assert (
        adjusted["total_revenue"]
        <
        observed["total_revenue"]
    )


def test_anomaly_rows_are_mapped_to_dates():

    df = make_test_dataframe()

    anomalies, anomaly_summary = (
        make_anomalies()
    )

    report = generate_insights_report(
        df,
        anomaly_summary=anomaly_summary,
        anomalies=anomalies,
    )

    dates = report[
        "anomaly_analysis"
    ]["affected_dates"]

    assert "2026-01-10" in dates
    assert "2026-01-11" in dates


def test_time_analysis_adjusted_trend():

    df = make_test_dataframe()

    anomalies, _ = make_anomalies()

    from data_engine.insight_engine import (
        prepare_revenue_data,
    )

    data = prepare_revenue_data(df)

    result = analyze_time(
        data,
        anomalous_indices={9, 10},
    )

    assert (
        result["revenue_trend"]
        is not None
    )

    assert (
        result["revenue_trend"]["observed"]
        is not None
    )

    assert (
        result["revenue_trend"]["adjusted"]
        is not None
    )

    assert (
        result["revenue_trend"]["adjusted"][
            "points"
        ]
        == 9
    )


def test_anomaly_summary_only():

    anomalies, summary = make_anomalies()

    result = analyze_anomalies(
        summary
    )

    assert (
        result["total_anomalies"]
        == 3
    )

    assert (
        result["critical_anomalies"]
        == 2
    )

    assert (
        result["warning_anomalies"]
        == 1
    )

    assert (
        result["affected_columns"]
        == ["price", "quantity"]
    )


def test_full_v3_report():

    df = make_test_dataframe()

    anomalies, anomaly_summary = (
        make_anomalies()
    )

    report = generate_insights_report(
        df,
        anomaly_summary=anomaly_summary,
        anomalies=anomalies,
        profiler=None,
    )

    assert isinstance(
        report,
        dict,
    )

    assert (
        report["version"]
        == "3.0"
    )

    required_sections = [
        "executive_summary",
        "summary",
        "insights",
        "opportunities",
        "risks",
        "product_analysis",
        "category_analysis",
        "time_analysis",
        "concentration",
        "anomaly_analysis",
        "profiler_analysis",
    ]

    for section in required_sections:

        assert section in report


def test_executive_summary():

    df = make_test_dataframe()

    anomalies, anomaly_summary = (
        make_anomalies()
    )

    report = generate_insights_report(
        df,
        anomaly_summary=anomaly_summary,
        anomalies=anomalies,
    )

    executive = report[
        "executive_summary"
    ]

    assert executive["business_health"] in {
        "healthy",
        "caution",
        "critical",
    }

    assert executive["confidence"] in {
        "high",
        "medium",
        "low",
    }

    assert (
        executive["observed_revenue"]
        >
        executive["adjusted_revenue"]
    )

    assert (
        executive[
            "anomalous_revenue_share"
        ]
        > 0
    )


def test_backward_compatibility():

    df = make_test_dataframe()

    anomalies, anomaly_summary = (
        make_anomalies()
    )

    report = create_insight_report(
        df,
        anomaly_summary=anomaly_summary,
        profiler=None,
        anomalies=anomalies,
    )

    assert isinstance(
        report,
        dict,
    )

    assert (
        report["version"]
        == "3.0"
    )


# ============================================================
# Runner
# ============================================================

if __name__ == "__main__":

    tests = [

        test_empty_dataframe,
        test_invalid_dataframe,
        test_revenue_calculation,
        test_input_dataframe_is_not_modified,
        test_anomaly_impact,
        test_adjusted_summary,
        test_anomaly_rows_are_mapped_to_dates,
        test_time_analysis_adjusted_trend,
        test_anomaly_summary_only,
        test_full_v3_report,
        test_executive_summary,
        test_backward_compatibility,
    ]

    print()
    print("==============================================")
    print("       TRENDPULSE INSIGHT ENGINE V3")
    print("==============================================")

    print()

    passed = 0

    for test in tests:

        try:

            test()

            print(
                f"PASS  {test.__name__}"
            )

            passed += 1

        except Exception as exc:

            print(
                f"FAIL  {test.__name__}: "
                f"{exc}"
            )

            raise

    print()
    print("==============================================")
    print(
        f"PASSED: {passed}/{len(tests)}"
    )
    print("==============================================")
    print()