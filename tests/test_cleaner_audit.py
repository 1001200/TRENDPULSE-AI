import pandas as pd

from data_engine.cleaner import clean_data_with_audit


# ============================================================
# Messy Dataset
# ============================================================

df = pd.DataFrame({

    " Product ": [
        "  Black   Tee ",
        "Blue Jeans",
        None,
        "Blue Jeans"
    ],

    "Category": [
        " T-Shirt ",
        " Jeans ",
        None,
        " Jeans "
    ],

    "Quantity": [
        "5 units",
        "2",
        None,
        "2"
    ],

    "Price": [
        "₹699",
        "1,299",
        None,
        "1,299"
    ],

    "Customer ID": [
        " C001 ",
        "C002",
        None,
        "C002"
    ],

    "Date": [
        "2026-08-20",
        "2026/08/21",
        None,
        "2026-08-21"
    ]
})


# ============================================================
# Run Cleaner
# ============================================================

(
    cleaned_df,
    audit_log,
    summary
) = clean_data_with_audit(
    df
)


# ============================================================
# Output
# ============================================================

print("\n======================================")
print("     TRENDPULSE CLEANING AUDIT")
print("======================================")


print("\nCleaned Data:")

print(
    cleaned_df
)


print("\nCleaning Summary:")

for key, value in summary.items():

    print(
        f"{key}: {value}"
    )


print("\nAudit Log:")

if audit_log:

    for entry in audit_log:

        print(
            f"Row={entry['row']} | "
            f"Column={entry['column']} | "
            f"Before={entry['before']} | "
            f"After={entry['after']} | "
            f"Action={entry['action']}"
        )

else:

    print(
        "No cleaning changes detected."
    )