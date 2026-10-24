import pandas as pd

from data_engine.validator import validate_data


# ============================================================
# Test Dataset
# ============================================================

df = pd.DataFrame({

    "date": [
        "2026-08-20",
        "2026-08-21",
        "2026-08-22",
        "2026-08-23"
    ],

    "product": [
        "Black Tee",
        "Blue Jeans",
        "White Hoodie",
        None
    ],

    "quantity": [
        5,
        -3,
        0,
        10
    ],

    "price": [
        699,
        -100,
        0,
        1299
    ]
})


# ============================================================
# Validate
# ============================================================

report = validate_data(
    df
)


# ============================================================
# Output
# ============================================================

print("\n======================================")
print("   TRENDPULSE ADVANCED VALIDATOR")
print("======================================")


print("\nBasic Report:")

print(
    f"is_empty: "
    f"{report['is_empty']}"
)

print(
    f"missing_columns: "
    f"{report['missing_columns']}"
)

print(
    f"invalid_quantity_rows: "
    f"{report['invalid_quantity_rows']}"
)

print(
    f"invalid_price_rows: "
    f"{report['invalid_price_rows']}"
)

print(
    f"duplicate_rows: "
    f"{report['duplicate_rows']}"
)


print("\nStructured Issues:")

for issue in report["issues"]:

    print(
        f"Row={issue['row']} | "
        f"Column={issue['column']} | "
        f"Value={issue['value']} | "
        f"Issue={issue['issue']} | "
        f"Severity={issue['severity']} | "
        f"{issue['message']}"
    )