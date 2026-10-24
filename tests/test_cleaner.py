import pandas as pd

from data_engine.cleaner import clean_data


# ============================================================
# Messy Test Dataset
# ============================================================

df = pd.DataFrame({

    "Product": [
        "  Black   Oversized Tee  ",
        "Blue Jeans",
        "White Hoodie",
        "Blue Jeans",
        None
    ],

    "Category": [
        " T-Shirt ",
        " Jeans",
        "Hoodie",
        " Jeans",
        None
    ],

    "Quantity": [
        "5 units",
        "2",
        "8",
        "2",
        None
    ],

    "Price": [
        "₹699",
        "1,299",
        "$999.00",
        "1,299",
        None
    ],

    "Customer ID": [
        " C001 ",
        "C002",
        "C003",
        "C002",
        None
    ],

    "Date": [
        "2026-08-20",
        "2026/08/21",
        "August 22, 2026",
        "2026-08-21",
        None
    ]
})


# ============================================================
# Run Cleaner
# ============================================================

cleaned_df = clean_data(
    df
)


# ============================================================
# Display Results
# ============================================================

print("\n======================================")
print("       TRENDPULSE CLEANER")
print("======================================")


print("\nOriginal Data:")

print(df)


print("\nCleaned Data:")

print(cleaned_df)


print("\nColumn Names:")

print(
    list(cleaned_df.columns)
)


print("\nData Types:")

print(
    cleaned_df.dtypes
)


print("\nMissing Values:")

print(
    cleaned_df.isna().sum()
)


print("\nDuplicate Rows:")

print(
    cleaned_df.duplicated().sum()
)