import tempfile
from pathlib import Path

import pandas as pd

from data_engine.processor import process_file


# ============================================================
# Create Test Dataset
# ============================================================

df = pd.DataFrame({

    "Order Date": [
        "2026-08-20",
        "2026-08-21",
        "2026-08-22",
        "2026-08-23",
        "2026-08-24",
        "2026-08-25",
        "2026-08-26",
        "2026-08-27",
        "2026-08-28",
        "2026-08-29"
    ],

    "Product Name": [
        "Black Tee",
        "Blue Jeans",
        "White Hoodie",
        "Black Tee",
        "Blue Jeans",
        "White Hoodie",
        "Black Tee",
        "Blue Jeans",
        "White Hoodie",
        "Luxury Product"
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
        "Luxury"
    ],

    "Qty": [
        5,
        6,
        4,
        5,
        7,
        6,
        5,
        4,
        6,
        500
    ],

    "Selling Price": [
        699,
        749,
        799,
        699,
        749,
        799,
        699,
        749,
        799,
        999999
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
        "C010"
    ]
})


# ============================================================
# Save Temporary CSV
# ============================================================

with tempfile.TemporaryDirectory() as temp_dir:

    file_path = Path(
        temp_dir
    ) / "anomaly_test.csv"

    df.to_csv(
        file_path,
        index=False
    )

    # --------------------------------------------------------
    # Process through COMPLETE pipeline
    # --------------------------------------------------------

    result = process_file(
        file_path
    )


# ============================================================
# Display Result
# ============================================================

print("\n======================================")
print("   TRENDPULSE END-TO-END ANOMALY TEST")
print("======================================")


print("\nPipeline Status:")

print(
    result["status"]
)


print("\nRows:")

print(
    f"Received: "
    f"{result['rows_received']}"
)

print(
    f"After cleaning: "
    f"{result['rows_after_cleaning']}"
)


print("\nMapping:")

for original, standard in (
    result["column_mapping"].items()
):

    print(
        f"{original} -> {standard}"
    )


print("\nValidation:")

print(
    result["validation"]
)


print("\nAnomaly Summary:")

print(
    result["anomaly_summary"]
)


print("\nDetected Anomalies:")

if not result["anomalies"]:

    print(
        "No anomalies detected."
    )

else:

    for anomaly in result["anomalies"]:

        print(
            f"Row={anomaly['row']} | "
            f"Column={anomaly['column']} | "
            f"Value={anomaly['value']} | "
            f"Method={anomaly['method']} | "
            f"Severity={anomaly['severity']} | "
            f"Direction={anomaly['direction']}"
        )


print("\nQuality Report:")

print(
    result["quality_report"]
)


print("\nProcessed Data:")

print(
    result["processed_data"]
)