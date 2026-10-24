import pandas as pd

from data_engine.profiler import profile_data


# ============================================================
# TEST DATASET
# ============================================================

df = pd.DataFrame({

    "product": [
        "Black Tee",
        "Blue Jeans",
        "White Hoodie",
        "Black Tee",
        "Blue Jeans",
        "White Hoodie",
        "Black Tee",
        "Blue Jeans",
        "White Hoodie",
        "Black Tee"
    ],

    "category": [
        "T-Shirt",
        "Jeans",
        "Hoodie",
        "T-Shirt",
        "Jeans",
        "Hoodie",
        "T-Shirt",
        "Jeans",
        "Hoodie",
        "T-Shirt"
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
        100
    ],

    "price": [
        699,
        749,
        799,
        699,
        749,
        799,
        699,
        749,
        799,
        99999
    ],

    "customer_id": [
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
    ],

    "date": pd.to_datetime([
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
    ])
})


# ============================================================
# RUN PROFILER
# ============================================================

profile = profile_data(
    df
)


# ============================================================
# HEADER
# ============================================================

print(
    "\n======================================"
)

print(
    "   TRENDPULSE INTELLIGENT PROFILER V3"
)

print(
    "======================================"
)


# ============================================================
# DATASET OVERVIEW
# ============================================================

print(
    "\nDataset Overview:"
)

print(
    profile["dataset"]
)


# ============================================================
# COLUMN GROUPS
# ============================================================

print(
    "\nColumn Groups:"
)

print(
    profile["column_groups"]
)


# ============================================================
# COLUMN PROFILES
# ============================================================

print(
    "\nColumn Profiles:"
)

for column, details in (
    profile["column_profiles"].items()
):

    print(
        f"\n{column}:"
    )

    print(
        details
    )


# ============================================================
# RELATIONSHIPS
# ============================================================

print(
    "\nRelationships:"
)

print(
    profile["relationships"]
)


# ============================================================
# DATASET INTELLIGENCE
# ============================================================

print(
    "\nDataset Intelligence:"
)

print(
    profile["intelligence"]["dataset_signals"]
)


# ============================================================
# AUTOMATIC INSIGHTS
# ============================================================

print(
    "\nAutomatic Insights:"
)

for insight in (
    profile["intelligence"]["insights"]
):

    print(
        insight
    )