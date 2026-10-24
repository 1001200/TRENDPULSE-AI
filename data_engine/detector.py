SALES_COLUMNS = {
    "order_id",
    "order_date",
    "product",
    "product_name",
    "quantity",
    "price",
    "selling_price",
    "customer_id"
}


INVENTORY_COLUMNS = {
    "sku",
    "product",
    "product_name",
    "stock",
    "quantity_in_stock",
    "reorder_level",
    "warehouse"
}


CUSTOMER_COLUMNS = {
    "customer_id",
    "customer_name",
    "name",
    "email",
    "phone",
    "city",
    "address"
}


PRODUCT_COLUMNS = {
    "product_id",
    "sku",
    "product",
    "product_name",
    "category",
    "price",
    "cost_price"
}


RETURN_COLUMNS = {
    "return_id",
    "order_id",
    "product",
    "quantity",
    "return_date",
    "reason"
}


EXPENSE_COLUMNS = {
    "expense_id",
    "expense_date",
    "category",
    "amount",
    "description"
}


DATASET_RULES = {
    "sales": SALES_COLUMNS,
    "inventory": INVENTORY_COLUMNS,
    "customers": CUSTOMER_COLUMNS,
    "products": PRODUCT_COLUMNS,
    "returns": RETURN_COLUMNS,
    "expenses": EXPENSE_COLUMNS
}


def normalize_column_name(column):
    """
    Convert a column name into a simple comparable format.
    """

    return (
        str(column)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def calculate_match_score(columns, expected_columns):
    """
    Calculate how strongly a dataset matches
    a particular dataset type.
    """

    normalized_columns = {
        normalize_column_name(column)
        for column in columns
    }

    matched_columns = (
        normalized_columns & expected_columns
    )

    if not expected_columns:
        return 0.0

    score = (
        len(matched_columns)
        / len(expected_columns)
    ) * 100

    return round(score, 2)


def detect_dataset_type(columns):
    """
    Determine the most likely business dataset type.
    """

    scores = {}

    for dataset_type, expected_columns in DATASET_RULES.items():

        scores[dataset_type] = calculate_match_score(
            columns,
            expected_columns
        )

    best_type = max(
        scores,
        key=scores.get
    )

    best_score = scores[best_type]

    # Require a minimum amount of evidence.
    if best_score < 20:
        best_type = "unknown"

    return {
        "dataset_type": best_type,
        "confidence": best_score,
        "scores": scores
    }