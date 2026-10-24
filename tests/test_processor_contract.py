import json

import pandas as pd
import pytest

from data_engine.processor import (
    load_file,
    process_dataframe,
    result_to_json_safe,
)


def test_processor_does_not_modify_input_dataframe():
    df = pd.DataFrame(
        {
            "Order Date": ["2026-08-20", "2026-08-21"],
            "Product Name": ["Black Tee", "Blue Jeans"],
            "Category": ["T-Shirt", "Jeans"],
            "Qty Sold": ["5 units", "3"],
            "Selling Price": ["₹699", "1299"],
            "Customer ID": ["C001", "C002"],
        }
    )

    original = df.copy(deep=True)

    result = process_dataframe(
        df,
        enable_llm=False,
    )

    print("\nINPUT IMMUTABILITY")
    print("Original:")
    print(df)
    print("\nProcessed:")
    print(result["processed_data"])

    pd.testing.assert_frame_equal(df, original)


def test_empty_dataframe_is_handled():
    df = pd.DataFrame(
        columns=[
            "Order Date",
            "Product Name",
            "Category",
            "Qty Sold",
            "Selling Price",
            "Customer ID",
        ]
    )

    result = process_dataframe(
        df,
        enable_llm=False,
    )

    print("\nEMPTY DATAFRAME")
    print(result)

    assert result["status"] == "success"
    assert result["rows_received"] == 0
    assert result["rows_after_cleaning"] == 0
    assert result["validation"]["is_empty"] is True


def test_missing_required_columns_are_reported():
    df = pd.DataFrame(
        {
            "Order Date": ["2026-08-20"],
            "Product Name": ["Black Tee"],
        }
    )

    result = process_dataframe(
        df,
        enable_llm=False,
    )

    print("\nMISSING REQUIRED COLUMNS")
    print(result["validation"])

    assert result["status"] == "success"
    assert result["validation"]["is_empty"] is False
    assert result["validation"]["missing_columns"]


def test_json_safe_result_contains_no_dataframe():
    df = pd.DataFrame(
        {
            "Order Date": ["2026-08-20"],
            "Product Name": ["Black Tee"],
            "Category": ["T-Shirt"],
            "Qty Sold": [5],
            "Selling Price": [699],
            "Customer ID": ["C001"],
        }
    )

    result = process_dataframe(
        df,
        enable_llm=False,
    )

    safe_result = result_to_json_safe(result)

    print("\nJSON SAFE RESULT")
    print(safe_result)

    assert isinstance(safe_result, dict)
    assert isinstance(safe_result["processed_data"], list)

    json_string = json.dumps(safe_result)

    assert isinstance(json_string, str)
    assert "Black Tee" in json_string


def test_json_safe_processed_data_is_record_oriented():
    df = pd.DataFrame(
        {
            "Order Date": ["2026-08-20"],
            "Product Name": ["Black Tee"],
            "Category": ["T-Shirt"],
            "Qty Sold": [5],
            "Selling Price": [699],
            "Customer ID": ["C001"],
        }
    )

    result = process_dataframe(
        df,
        enable_llm=False,
    )

    safe_result = result_to_json_safe(result)

    processed = safe_result["processed_data"]

    print("\nPROCESSED DATA JSON")
    print(processed)

    assert isinstance(processed, list)
    assert len(processed) == 1
    assert processed[0]["product"] == "Black Tee"
    assert processed[0]["quantity"] == 5
    assert processed[0]["price"] == 699


def test_llm_failure_does_not_fail_processor():
    df = pd.DataFrame(
        {
            "Order Date": ["2026-08-20", "2026-08-21"],
            "Product Name": ["Black Tee", "Blue Jeans"],
            "Category": ["T-Shirt", "Jeans"],
            "Qty Sold": [5, 3],
            "Selling Price": [699, 1299],
            "Customer ID": ["C001", "C002"],
        }
    )

    def broken_llm(payload):
        raise RuntimeError("LLM intentionally unavailable")

    result = process_dataframe(
        df,
        enable_llm=True,
        llm_client=broken_llm,
    )

    print("\nLLM FAILURE PROCESSOR")
    print("Pipeline status:", result["status"])
    print("LLM analysis:", result["llm_analysis"])

    assert result["status"] == "success"
    assert result["processed_data"] is not None

    assert result["llm_analysis"]["enabled"] is False
    assert result["llm_analysis"]["error"] is not None
    assert "LLM intentionally unavailable" in result["llm_analysis"]["error"]


def test_unsupported_file_type_fails_clearly(tmp_path):
    unsupported_file = tmp_path / "sample.txt"
    unsupported_file.write_text("hello TrendPulse")

    with pytest.raises(ValueError, match="Unsupported file type"):
        load_file(unsupported_file)


def test_csv_file_can_be_loaded(tmp_path):
    csv_file = tmp_path / "sales.csv"

    csv_file.write_text(
        "Order Date,Product Name,Category,Qty Sold,Selling Price,Customer ID\n"
        "2026-08-20,Black Tee,T-Shirt,5,699,C001\n"
        "2026-08-21,Blue Jeans,Jeans,3,1299,C002\n"
    )

    df = load_file(csv_file)

    print("\nCSV LOADING")
    print(df)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == [
        "Order Date",
        "Product Name",
        "Category",
        "Qty Sold",
        "Selling Price",
        "Customer ID",
    ]