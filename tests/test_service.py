import json

import pandas as pd

from data_engine.service import (
    analyze_dataframe,
    analyze_file,
    health_check,
)


def _sample_dataframe():
    return pd.DataFrame(
        {
            "Order Date": [
                "2026-08-20",
                "2026-08-21",
                "2026-08-22",
            ],
            "Product Name": [
                "Black Tee",
                "Blue Jeans",
                "White Hoodie",
            ],
            "Category": [
                "T-Shirt",
                "Jeans",
                "Hoodie",
            ],
            "Qty Sold": [
                5,
                3,
                4,
            ],
            "Selling Price": [
                699,
                1299,
                799,
            ],
            "Customer ID": [
                "C001",
                "C002",
                "C003",
            ],
        }
    )


def test_health_check():
    result = health_check()

    print("\nHEALTH CHECK")
    print(result)

    assert result["service"] == "TrendPulse Data Engine"
    assert result["status"] == "healthy"
    assert result["version"] == "4.0"


def test_analyze_dataframe_returns_json_safe_result():
    df = _sample_dataframe()

    result = analyze_dataframe(
        df,
        enable_llm=False,
    )

    print("\nSERVICE DATAFRAME RESULT")
    print(result)

    assert isinstance(result, dict)
    assert result["status"] == "success"
    assert result["rows_received"] == 3
    assert result["rows_after_cleaning"] == 3

    assert isinstance(result["processed_data"], list)
    assert result["processed_data"][0]["product"] == "Black Tee"

    # Prove the service result can actually cross an HTTP/JSON boundary.
    json_payload = json.dumps(result)

    assert isinstance(json_payload, str)


def test_analyze_dataframe_does_not_modify_input():
    df = _sample_dataframe()
    original = df.copy(deep=True)

    analyze_dataframe(
        df,
        enable_llm=False,
    )

    pd.testing.assert_frame_equal(df, original)


def test_analyze_file_returns_json_safe_result(tmp_path):
    csv_file = tmp_path / "sales.csv"

    csv_file.write_text(
        "Order Date,Product Name,Category,Qty Sold,Selling Price,Customer ID\n"
        "2026-08-20,Black Tee,T-Shirt,5,699,C001\n"
        "2026-08-21,Blue Jeans,Jeans,3,1299,C002\n"
    )

    result = analyze_file(
        csv_file,
        enable_llm=False,
    )

    print("\nSERVICE FILE RESULT")
    print(result)

    assert isinstance(result, dict)
    assert result["status"] == "success"
    assert result["rows_received"] == 2
    assert result["rows_after_cleaning"] == 2

    assert isinstance(result["processed_data"], list)
    assert result["processed_data"][1]["product"] == "Blue Jeans"

    json_payload = json.dumps(result)

    assert isinstance(json_payload, str)