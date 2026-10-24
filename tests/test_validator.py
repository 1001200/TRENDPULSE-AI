import pandas as pd

from data_engine.validator import validate_data


# Sample clothing business data
data = {
    "date": [
        "2026-08-20",
        "2026-08-21",
        "2026-08-21",
        "2026-08-22"
    ],

    "product": [
        "Black Oversized Tee",
        "Blue Jeans",
        "Black Oversized Tee",
        "Black Oversized Tee"
    ],

    "category": [
        "T-Shirt",
        "Jeans",
        "T-Shirt",
        "T-Shirt"
    ],

    "quantity": [
        5,
        2,
        8,
        "wrong"
    ],

    "price": [
        699,
        1299,
        699,
        699
    ]
}


df = pd.DataFrame(data)

report = validate_data(df)

print("\n===== TRENDPULSE VALIDATION REPORT =====")

print("Empty dataset:", report["is_empty"])

print("Missing columns:", report["missing_columns"])

print(
    "Invalid quantity rows:",
    report["invalid_quantity_rows"]
)

print(
    "Invalid price rows:",
    report["invalid_price_rows"]
)

print(
    "Duplicate rows:",
    report["duplicate_rows"]
)