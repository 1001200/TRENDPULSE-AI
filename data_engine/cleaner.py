import re

import pandas as pd


# ============================================================
# Configuration
# ============================================================

NUMERIC_COLUMNS = [
    "quantity",
    "price",
    "discount"
]


# ============================================================
# Audit Helper
# ============================================================

def add_audit_entry(
    audit_log,
    row_index,
    column,
    before,
    after,
    action
):
    """
    Record one cleaning operation.
    """

    audit_log.append({
        "row": row_index,
        "column": column,
        "before": before,
        "after": after,
        "action": action
    })


# ============================================================
# Column Name Cleaning
# ============================================================

def clean_column_names(
    df: pd.DataFrame,
    audit_log=None
) -> pd.DataFrame:

    df = df.copy()

    cleaned_columns = []

    for column in df.columns:

        original = str(column)

        cleaned = original.strip().lower()

        cleaned = re.sub(
            r"[^a-z0-9]+",
            "_",
            cleaned
        )

        cleaned = cleaned.strip("_")

        cleaned_columns.append(cleaned)

        if (
            audit_log is not None
            and original != cleaned
        ):
            add_audit_entry(
                audit_log,
                None,
                original,
                original,
                cleaned,
                "column name normalization"
            )

    df.columns = cleaned_columns

    return df


# ============================================================
# Text Cleaning
# ============================================================

def clean_text_columns(
    df: pd.DataFrame,
    audit_log=None
) -> pd.DataFrame:

    df = df.copy()

    text_columns = df.select_dtypes(
        include=["object", "string"]
    ).columns

    for column in text_columns:

        for index in df.index:

            value = df.at[
                index,
                column
            ]

            if pd.isna(value):
                continue

            original = str(value)

            cleaned = original.strip()

            cleaned = re.sub(
                r"\s+",
                " ",
                cleaned
            )

            if cleaned == "":

                df.at[
                    index,
                    column
                ] = pd.NA

                if audit_log is not None:
                    add_audit_entry(
                        audit_log,
                        index,
                        column,
                        original,
                        pd.NA,
                        "empty text converted to missing"
                    )

                continue

            df.at[
                index,
                column
            ] = cleaned

            if (
                audit_log is not None
                and original != cleaned
            ):
                add_audit_entry(
                    audit_log,
                    index,
                    column,
                    original,
                    cleaned,
                    "text normalization"
                )

    return df


# ============================================================
# Numeric Value Normalization
# ============================================================

def normalize_numeric_value(
    value
):
    """
    Convert messy numeric values into a numeric value.

    Examples:

        "1,299"   -> 1299.0
        "₹1,299"  -> 1299.0
        "$699"    -> 699.0
        "5 units" -> 5.0
        "10%"     -> 10.0
    """

    if pd.isna(value):
        return None

    # If pandas already knows this is numeric,
    # preserve it directly.
    if isinstance(
        value,
        (int, float)
    ) and not isinstance(
        value,
        bool
    ):

        if pd.isna(value):
            return None

        return float(value)

    value = str(value).strip()

    if value == "":
        return None

    # Remove commas
    value = value.replace(
        ",",
        ""
    )

    # Remove currency symbols
    value = re.sub(
        r"[₹$€£¥]",
        "",
        value
    )

    # Remove percentage symbol
    value = value.replace(
        "%",
        ""
    )

    # Extract numeric portion
    match = re.search(
        r"-?\d+(?:\.\d+)?",
        value
    )

    if not match:
        return None

    try:

        return float(
            match.group()
        )

    except (
        ValueError,
        TypeError
    ):

        return None


# ============================================================
# Numeric Cleaning
# ============================================================

def clean_numeric_columns(
    df: pd.DataFrame,
    audit_log=None
) -> pd.DataFrame:

    df = df.copy()

    for column in NUMERIC_COLUMNS:

        if column not in df.columns:
            continue

        cleaned_values = []

        for index in df.index:

            original = df.at[
                index,
                column
            ]

            if pd.isna(original):

                cleaned_values.append(
                    None
                )

                continue

            numeric_value = (
                normalize_numeric_value(
                    original
                )
            )

            if numeric_value is None:

                cleaned_values.append(
                    None
                )

                if audit_log is not None:

                    add_audit_entry(
                        audit_log,
                        index,
                        column,
                        original,
                        pd.NA,
                        "invalid numeric value"
                    )

                continue

            # Keep integer-looking values as integers
            if numeric_value.is_integer():

                final_value = int(
                    numeric_value
                )

            else:

                final_value = numeric_value

            cleaned_values.append(
                final_value
            )

            # Record only actual transformations.
            original_string = str(
                original
            ).strip()

            if (
                audit_log is not None
                and original_string
                != str(final_value)
            ):

                add_audit_entry(
                    audit_log,
                    index,
                    column,
                    original,
                    final_value,
                    "numeric normalization"
                )

        # IMPORTANT:
        #
        # Build the complete numeric Series first.
        # This avoids pandas dtype problems caused by
        # assigning mixed values into string columns.

        df[column] = pd.to_numeric(
            pd.Series(
                cleaned_values,
                index=df.index
            ),
            errors="coerce"
        )

    return df


# ============================================================
# Date Parsing
# ============================================================

def parse_date_value(
    value
):
    """
    Parse a single date value.

    Supports:

        2026-08-20
        2026/08/21
        August 22, 2026
        22 August 2026
    """

    if pd.isna(value):
        return pd.NaT

    value = str(
        value
    ).strip()

    if value == "":
        return pd.NaT

    parsed = pd.to_datetime(
        value,
        errors="coerce"
    )

    if not pd.isna(parsed):
        return parsed

    parsed = pd.to_datetime(
        value,
        format="%d/%m/%Y",
        errors="coerce"
    )

    if not pd.isna(parsed):
        return parsed

    parsed = pd.to_datetime(
        value,
        format="%m/%d/%Y",
        errors="coerce"
    )

    if not pd.isna(parsed):
        return parsed

    return pd.NaT


# ============================================================
# Date Cleaning
# ============================================================

def clean_dates(
    df: pd.DataFrame,
    audit_log=None
) -> pd.DataFrame:

    df = df.copy()

    if "date" not in df.columns:
        return df

    original_values = df[
        "date"
    ].copy()

    parsed_values = []

    for index in df.index:

        original = original_values.loc[
            index
        ]

        parsed = parse_date_value(
            original
        )

        parsed_values.append(
            parsed
        )

        if pd.isna(original):
            continue

        if pd.isna(parsed):

            if audit_log is not None:

                add_audit_entry(
                    audit_log,
                    index,
                    "date",
                    original,
                    pd.NaT,
                    "invalid date"
                )

            continue

        original_string = str(
            original
        ).strip()

        parsed_string = parsed.strftime(
            "%Y-%m-%d"
        )

        if (
            audit_log is not None
            and original_string != parsed_string
        ):

            add_audit_entry(
                audit_log,
                index,
                "date",
                original,
                parsed_string,
                "date normalization"
            )

    df["date"] = pd.to_datetime(
        pd.Series(
            parsed_values,
            index=df.index
        ),
        errors="coerce"
    )

    return df


# ============================================================
# Identifier Cleaning
# ============================================================

def clean_identifier_columns(
    df: pd.DataFrame,
    audit_log=None
) -> pd.DataFrame:

    df = df.copy()

    identifier_columns = [
        "customer_id",
        "order_id"
    ]

    for column in identifier_columns:

        if column not in df.columns:
            continue

        for index in df.index:

            original = df.at[
                index,
                column
            ]

            if pd.isna(original):
                continue

            cleaned = str(
                original
            ).strip()

            if cleaned == "":

                df.at[
                    index,
                    column
                ] = pd.NA

                if audit_log is not None:

                    add_audit_entry(
                        audit_log,
                        index,
                        column,
                        original,
                        pd.NA,
                        "empty identifier converted to missing"
                    )

                continue

            df.at[
                index,
                column
            ] = cleaned

            if (
                audit_log is not None
                and str(original) != cleaned
            ):

                add_audit_entry(
                    audit_log,
                    index,
                    column,
                    original,
                    cleaned,
                    "identifier normalization"
                )

    return df


# ============================================================
# Product / Category Normalization
# ============================================================

def normalize_product_text(
    df: pd.DataFrame,
    audit_log=None
) -> pd.DataFrame:

    df = df.copy()

    columns = [
        "product",
        "category"
    ]

    for column in columns:

        if column not in df.columns:
            continue

        for index in df.index:

            original = df.at[
                index,
                column
            ]

            if pd.isna(original):
                continue

            cleaned = re.sub(
                r"\s+",
                " ",
                str(original).strip()
            )

            df.at[
                index,
                column
            ] = cleaned

            if (
                audit_log is not None
                and str(original) != cleaned
            ):

                add_audit_entry(
                    audit_log,
                    index,
                    column,
                    original,
                    cleaned,
                    "product text normalization"
                )

    return df


# ============================================================
# Empty Row Removal
# ============================================================

def remove_empty_rows(
    df: pd.DataFrame,
    audit_log=None
) -> pd.DataFrame:

    df = df.copy()

    empty_indices = df.index[
        df.isna().all(axis=1)
    ].tolist()

    if audit_log is not None:

        for index in empty_indices:

            add_audit_entry(
                audit_log,
                index,
                None,
                "entire row",
                None,
                "empty row removed"
            )

    df = df.dropna(
        how="all"
    )

    return df


# ============================================================
# Duplicate Removal
# ============================================================

def remove_duplicate_rows(
    df: pd.DataFrame,
    audit_log=None
) -> pd.DataFrame:

    df = df.copy()

    duplicate_mask = df.duplicated(
        keep="first"
    )

    duplicate_indices = df.index[
        duplicate_mask
    ].tolist()

    if audit_log is not None:

        for index in duplicate_indices:

            add_audit_entry(
                audit_log,
                index,
                None,
                "duplicate row",
                None,
                "duplicate row removed"
            )

    df = df[
        ~duplicate_mask
    ]

    return df


# ============================================================
# Cleaning Summary
# ============================================================

def build_cleaning_summary(
    original_df,
    cleaned_df,
    audit_log
):
    """
    Create summary statistics for the cleaning process.
    """

    action_counts = {}

    for entry in audit_log:

        action = entry[
            "action"
        ]

        action_counts[action] = (
            action_counts.get(
                action,
                0
            ) + 1
        )

    return {

        "rows_before":
            len(original_df),

        "rows_after":
            len(cleaned_df),

        "rows_removed":
            len(original_df)
            - len(cleaned_df),

        "changes_made":
            len(audit_log),

        "actions":
            action_counts
    }


# ============================================================
# Clean Data With Audit
# ============================================================

def clean_data_with_audit(
    df: pd.DataFrame
):
    """
    Run the complete cleaning pipeline.

    Returns:

        cleaned_df
        audit_log
        cleaning_summary
    """

    original_df = df.copy()

    audit_log = []

    # Step 1
    df = remove_empty_rows(
        df,
        audit_log
    )

    # Step 2
    df = clean_column_names(
        df,
        audit_log
    )

    # Step 3
    df = clean_text_columns(
        df,
        audit_log
    )

    # Step 4
    df = clean_identifier_columns(
        df,
        audit_log
    )

    # Step 5
    df = normalize_product_text(
        df,
        audit_log
    )

    # Step 6
    df = clean_numeric_columns(
        df,
        audit_log
    )

    # Step 7
    df = clean_dates(
        df,
        audit_log
    )

    # Step 8
    df = remove_duplicate_rows(
        df,
        audit_log
    )

    # Summary
    summary = build_cleaning_summary(
        original_df,
        df,
        audit_log
    )

    return (
        df,
        audit_log,
        summary
    )


# ============================================================
# Backwards-Compatible Clean Function
# ============================================================

def clean_data(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Existing processor-compatible function.

    Returns only the cleaned DataFrame.
    """

    cleaned_df, _, _ = (
        clean_data_with_audit(
            df
        )
    )

    return cleaned_df