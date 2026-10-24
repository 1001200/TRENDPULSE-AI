import pandas as pd

from data_engine.mapper import apply_column_mapping


# ============================================================
# Test Dataset
# ============================================================

df = pd.DataFrame({

    "Order Date": [
        "2026-08-20",
        "2026-08-21"
    ],

    "Product Name": [
        "Black Tee",
        "Blue Jeans"
    ],

    "Qty Sold": [
        5,
        3
    ],

    "Selling Price": [
        699,
        1299
    ],

    "Custmer ID": [
        "C001",
        "C002"
    ],

    # This should conflict with Qty Sold -> quantity
    "Items Moved": [
        5,
        3
    ],

    "Something Completely Unrelated": [
        "A",
        "B"
    ]
})


# ============================================================
# Run Mapper
# ============================================================

(
    mapped_df,
    mapping,
    unmatched,
    mapping_details,
    conflicts
) = apply_column_mapping(df)


# ============================================================
# Display Mapping
# ============================================================

print("\n======================================")
print("       TRENDPULSE SMART MAPPER")
print("======================================")


print("\nMapping:")

for original_column, standard_column in mapping.items():

    print(
        f"{original_column}"
        f" -> "
        f"{standard_column}"
    )


# ============================================================
# Unmatched
# ============================================================

print("\nUnmatched:")

if unmatched:

    for column in unmatched:

        print(
            f"- {column}"
        )

else:

    print("None")


# ============================================================
# Mapping Details
# ============================================================

print("\nMapping Details:")

for detail in mapping_details:

    print(
        f'{detail["original_column"]}'
        f' -> '
        f'{detail["standard_column"]}'
        f' | '
        f'method={detail["method"]}'
        f' | '
        f'confidence={detail["confidence"]}'
        f' | '
        f'level={detail["confidence_level"]}'
    )

    if "proposed_standard_column" in detail:

        print(
            f'  Proposed: '
            f'{detail["proposed_standard_column"]}'
        )


# ============================================================
# Conflicts
# ============================================================

print("\nMapping Conflicts:")

if conflicts:

    for standard_column, original_columns in conflicts.items():

        print(
            f"{standard_column}: "
            f"{original_columns}"
        )

else:

    print("None")


# ============================================================
# Verify No Duplicate Columns
# ============================================================

print("\nMapped DataFrame Columns:")

print(
    list(mapped_df.columns)
)


print("\nDuplicate Columns:")

duplicate_columns = (
    mapped_df.columns[
        mapped_df.columns.duplicated()
    ].tolist()
)

if duplicate_columns:

    print(
        duplicate_columns
    )

else:

    print("None")


# ============================================================
# Final DataFrame
# ============================================================

print("\nMapped DataFrame:")

print(
    mapped_df
)