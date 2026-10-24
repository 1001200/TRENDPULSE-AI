import pandas as pd


# ============================================================
# Required TrendPulse Columns
# ============================================================

REQUIRED_COLUMNS = [
    "date",
    "product",
    "quantity",
    "price"
]


# ============================================================
# Validation Issue Helper
# ============================================================

def add_issue(
    issues,
    row,
    column,
    value,
    issue,
    severity,
    message
):
    """
    Add one structured validation issue.
    """

    issues.append({
        "row": row,
        "column": column,
        "value": value,
        "issue": issue,
        "severity": severity,
        "message": message
    })


# ============================================================
# Empty Dataset Check
# ============================================================

def check_empty_dataset(
    df
):
    """
    Check whether the dataset contains no rows.
    """

    return df.empty


# ============================================================
# Missing Column Check
# ============================================================

def check_missing_columns(
    df
):
    """
    Return required columns that are missing.
    """

    return [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]


# ============================================================
# Quantity Validation
# ============================================================

def validate_quantity(
    df,
    issues
):
    """
    Validate quantity values.

    Rules:

        Missing quantity -> warning
        Non-numeric      -> error
        Zero             -> warning
        Negative         -> error
    """

    if "quantity" not in df.columns:
        return

    for index in df.index:

        value = df.at[
            index,
            "quantity"
        ]

        # Missing
        if pd.isna(value):

            add_issue(
                issues,
                index,
                "quantity",
                value,
                "missing_quantity",
                "warning",
                "Quantity is missing."
            )

            continue

        # Non-numeric
        numeric_value = pd.to_numeric(
            value,
            errors="coerce"
        )

        if pd.isna(numeric_value):

            add_issue(
                issues,
                index,
                "quantity",
                value,
                "invalid_quantity",
                "error",
                "Quantity is not numeric."
            )

            continue

        # Negative
        if numeric_value < 0:

            add_issue(
                issues,
                index,
                "quantity",
                value,
                "negative_quantity",
                "error",
                "Quantity cannot be negative."
            )

            continue

        # Zero
        if numeric_value == 0:

            add_issue(
                issues,
                index,
                "quantity",
                value,
                "zero_quantity",
                "warning",
                "Quantity is zero."
            )


# ============================================================
# Price Validation
# ============================================================

def validate_price(
    df,
    issues
):
    """
    Validate price values.

    Rules:

        Missing price -> warning
        Non-numeric   -> error
        Negative      -> error
        Zero          -> warning
    """

    if "price" not in df.columns:
        return

    for index in df.index:

        value = df.at[
            index,
            "price"
        ]

        # Missing
        if pd.isna(value):

            add_issue(
                issues,
                index,
                "price",
                value,
                "missing_price",
                "warning",
                "Price is missing."
            )

            continue

        numeric_value = pd.to_numeric(
            value,
            errors="coerce"
        )

        # Non-numeric
        if pd.isna(numeric_value):

            add_issue(
                issues,
                index,
                "price",
                value,
                "invalid_price",
                "error",
                "Price is not numeric."
            )

            continue

        # Negative
        if numeric_value < 0:

            add_issue(
                issues,
                index,
                "price",
                value,
                "negative_price",
                "error",
                "Price cannot be negative."
            )

            continue

        # Zero
        if numeric_value == 0:

            add_issue(
                issues,
                index,
                "price",
                value,
                "zero_price",
                "warning",
                "Price is zero."
            )


# ============================================================
# Date Validation
# ============================================================

def validate_dates(
    df,
    issues
):
    """
    Validate dates.

    Rules:

        Missing date -> warning
        Invalid date -> error
        Future date  -> warning
    """

    if "date" not in df.columns:
        return

    today = pd.Timestamp.now().normalize()

    for index in df.index:

        value = df.at[
            index,
            "date"
        ]

        # Missing
        if pd.isna(value):

            add_issue(
                issues,
                index,
                "date",
                value,
                "missing_date",
                "warning",
                "Date is missing."
            )

            continue

        parsed_date = pd.to_datetime(
            value,
            errors="coerce"
        )

        # Invalid
        if pd.isna(parsed_date):

            add_issue(
                issues,
                index,
                "date",
                value,
                "invalid_date",
                "error",
                "Date could not be parsed."
            )

            continue

        # Future
        if parsed_date.normalize() > today:

            add_issue(
                issues,
                index,
                "date",
                value,
                "future_date",
                "warning",
                "Date occurs in the future."
            )


# ============================================================
# Product Validation
# ============================================================

def validate_product(
    df,
    issues
):
    """
    Validate product names.
    """

    if "product" not in df.columns:
        return

    for index in df.index:

        value = df.at[
            index,
            "product"
        ]

        if pd.isna(value):

            add_issue(
                issues,
                index,
                "product",
                value,
                "missing_product",
                "error",
                "Product name is missing."
            )

            continue

        if str(value).strip() == "":

            add_issue(
                issues,
                index,
                "product",
                value,
                "empty_product",
                "error",
                "Product name is empty."
            )


# ============================================================
# Duplicate Validation
# ============================================================

def validate_duplicates(
    df,
    issues
):
    """
    Detect completely duplicated rows.
    """

    duplicate_mask = df.duplicated(
        keep=False
    )

    for index in df.index:

        if duplicate_mask.loc[index]:

            add_issue(
                issues,
                index,
                None,
                None,
                "duplicate_row",
                "warning",
                "Row is duplicated."
            )


# ============================================================
# Main Validation
# ============================================================

def validate_data(
    df
):
    """
    Run complete TrendPulse validation.

    Returns the original validation report
    plus structured validation issues.
    """

    issues = []

    is_empty = check_empty_dataset(
        df
    )

    missing_columns = check_missing_columns(
        df
    )

    # If required columns are missing,
    # validate only the columns that exist.

    validate_quantity(
        df,
        issues
    )

    validate_price(
        df,
        issues
    )

    validate_dates(
        df,
        issues
    )

    validate_product(
        df,
        issues
    )

    validate_duplicates(
        df,
        issues
    )

    # ========================================================
    # Compatibility Counts
    # ========================================================

    invalid_quantity_rows = sum(
        1
        for issue in issues
        if issue["issue"]
        in [
            "invalid_quantity",
            "negative_quantity"
        ]
    )

    invalid_price_rows = sum(
        1
        for issue in issues
        if issue["issue"]
        in [
            "invalid_price",
            "negative_price"
        ]
    )

    duplicate_rows = sum(
        1
        for issue in issues
        if issue["issue"]
        == "duplicate_row"
    )

    return {

        "is_empty":
            is_empty,

        "missing_columns":
            missing_columns,

        "invalid_quantity_rows":
            invalid_quantity_rows,

        "invalid_price_rows":
            invalid_price_rows,

        "duplicate_rows":
            duplicate_rows,

        "issues":
            issues
    }