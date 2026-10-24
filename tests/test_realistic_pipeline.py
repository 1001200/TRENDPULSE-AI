import pandas as pd

from data_engine.processor import process_file


def test_realistic_clothing_brand_pipeline(tmp_path):
    """
    End-to-end integration test for a realistic
    small clothing-brand dataset.

    Pipeline under test:

        CSV
        -> injection
        -> mapping
        -> cleaning
        -> validation
        -> anomaly detection
        -> final processed output
    """

    data = pd.DataFrame({
        "Order Date": [
            "2026-08-20",
            "2026/08/21",
            "August 22, 2026",
            "2026-08-23",
            "2026-08-24",
            "2026-08-25",
            "2026-08-26",
            "2026-08-27",
            "2026-08-28",
            "2026-08-29",
        ],

        "Product Name": [
            "Black Oversized Tee",
            "Blue Jeans",
            "White Hoodie",
            "Black Oversized Tee",
            "Blue Jeans",
            "White Hoodie",
            "Black Oversized Tee",
            "Blue Jeans",
            "White Hoodie",
            "Luxury Product",
        ],

        "Category": [
            "T-Shirt",
            "Jeans",
            "Hoodie",
            "T-Shirt",
            "Jeans",
            "Hoodie",
            "T-Shirt",
            "Jeans",
            "Hoodie",
            "Luxury",
        ],

        "Qty Sold": [
            "5 units",
            "6",
            "4",
            "5",
            "7",
            "6",
            "5",
            "4",
            "6",
            "500",
        ],

        "Selling Price": [
            "₹699",
            "749",
            "$799.00",
            "699",
            "749",
            "₹799",
            "699",
            "749",
            "799",
            "999999",
        ],

        "Customer ID": [
            "C001",
            "C002",
            "C003",
            "C004",
            "C005",
            "C006",
            "C007",
            "C008",
            "C009",
            "C010",
        ],
    })

    input_file = tmp_path / "clothing_brand.csv"

    data.to_csv(
        input_file,
        index=False
    )

    result = process_file(
        str(input_file)
    )

    print("\n")
    print("=" * 70)
    print("TRENDPULSE REALISTIC CLOTHING BRAND PIPELINE")
    print("=" * 70)

    print("\nResult type:")
    print(type(result))

    print("\nResult:")
    print(result)

    assert result is not None

    # --------------------------------------------------------
    # Basic pipeline success
    # --------------------------------------------------------

    if isinstance(result, dict):

        status = result.get(
            "status"
        )

        print("\nPipeline status:")
        print(status)

        if status is not None:
            assert status == "success"

    # --------------------------------------------------------
    # Find processed dataframe
    # --------------------------------------------------------

    processed = None

    if isinstance(result, dict):

        possible_keys = [
            "data",
            "processed_data",
            "processed",
            "cleaned_data",
            "dataframe",
        ]

        for key in possible_keys:

            value = result.get(key)

            if isinstance(
                value,
                pd.DataFrame
            ):

                processed = value

                print(
                    f"\nProcessed DataFrame found under key: {key}"
                )

                break

    # --------------------------------------------------------
    # If the processor returns a DataFrame directly
    # --------------------------------------------------------

    if isinstance(
        result,
        pd.DataFrame
    ):

        processed = result

    # --------------------------------------------------------
    # We need a processed DataFrame
    # --------------------------------------------------------

    assert processed is not None

    print("\nProcessed columns:")
    print(
        processed.columns.tolist()
    )

    print("\nProcessed data:")
    print(processed)

    # --------------------------------------------------------
    # Required canonical columns
    # --------------------------------------------------------

    required_columns = {
        "date",
        "product",
        "category",
        "quantity",
        "price",
        "customer_id",
    }

    assert required_columns.issubset(
        set(processed.columns)
    )

    # --------------------------------------------------------
    # Data cleaning expectations
    # --------------------------------------------------------

    assert processed["quantity"].dtype != object

    assert processed["price"].dtype != object

    # --------------------------------------------------------
    # Currency / numeric normalization
    # --------------------------------------------------------

    assert processed["price"].iloc[0] == 699

    assert processed["price"].iloc[1] == 749

    assert processed["price"].iloc[2] == 799

    # --------------------------------------------------------
    # Quantity normalization
    # --------------------------------------------------------

    assert processed["quantity"].iloc[0] == 5

    assert processed["quantity"].iloc[1] == 6

    # --------------------------------------------------------
    # Date normalization
    # --------------------------------------------------------

    assert pd.api.types.is_datetime64_any_dtype(
        processed["date"]
    )

    # --------------------------------------------------------
    # Anomaly should survive into the processed dataset
    # --------------------------------------------------------

    assert (
        processed["quantity"].max()
        == 500
    )

    assert (
        processed["price"].max()
        == 999999
    )

    print("\n")
    print("=" * 70)
    print("REALISTIC PIPELINE TEST PASSED")
    print("=" * 70)