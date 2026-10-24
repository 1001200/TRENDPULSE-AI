import re
import difflib

import pandas as pd

from data_engine.semantic_mapper import find_semantic_match


# ============================================================
# TrendPulse Column Aliases
# ============================================================

COLUMN_ALIASES = {

    "date": [
        "date",
        "order date",
        "sale date",
        "sales date",
        "purchase date",
        "transaction date",
        "order dt",
        "sale dt"
    ],

    "product": [
        "product",
        "product name",
        "item",
        "item name",
        "product title",
        "item title",
        "product description"
    ],

    "category": [
        "category",
        "product category",
        "item category",
        "type",
        "product type"
    ],

    "subcategory": [
        "subcategory",
        "sub category",
        "product subcategory",
        "sub type",
        "product sub type"
    ],

    "quantity": [
        "quantity",
        "qty",
        "units",
        "units sold",
        "number of units",
        "sold quantity",
        "pieces sold",
        "items sold",
        "qty sold",
        "quantity sold"
    ],

    "price": [
        "price",
        "selling price",
        "sale price",
        "unit price",
        "selling amount",
        "sale amount",
        "amount",
        "revenue per unit"
    ],

    "customer_id": [
        "customer id",
        "customer_id",
        "customer number",
        "customer no",
        "buyer id",
        "buyer number"
    ],

    "order_id": [
        "order id",
        "order_id",
        "order number",
        "order no",
        "transaction id",
        "transaction number"
    ],

    "discount": [
        "discount",
        "discount %",
        "discount percentage",
        "discount amount",
        "discount rate"
    ],

    "size": [
        "size",
        "product size",
        "item size",
        "garment size"
    ],

    "color": [
        "color",
        "colour",
        "product color",
        "product colour",
        "item color",
        "item colour"
    ],

    "sku": [
        "sku",
        "stock keeping unit",
        "product sku",
        "item sku",
        "product code",
        "item code",
        "barcode"
    ],

    "cost_price": [
        "cost price",
        "cost",
        "purchase price",
        "unit cost",
        "buying price",
        "cogs",
        "cost of goods"
    ],

    "stock": [
        "stock",
        "inventory",
        "units in stock",
        "quantity in stock",
        "stock quantity",
        "available stock",
        "on hand"
    ],

    "revenue": [
        "revenue",
        "total revenue",
        "sales revenue",
        "total sales",
        "total amount",
        "line total"
    ]
}



# ============================================================
# Configuration
# ============================================================

FUZZY_THRESHOLD = 0.75


# ============================================================
# Normalize Column Name
# ============================================================

def normalize_column_name(column_name):
    """
    Convert different column naming styles
    into a common comparison format.
    """

    column_name = str(
        column_name
    ).strip().lower()

    # Replace special characters with spaces
    column_name = re.sub(
        r"[^a-z0-9]+",
        " ",
        column_name
    )

    # Remove extra spaces
    column_name = " ".join(
        column_name.split()
    )

    return column_name


# ============================================================
# Build Normalized Aliases
# ============================================================

def build_normalized_aliases():
    """
    Normalize all aliases so they can be
    compared consistently.
    """

    normalized_aliases = {}

    for standard_name, aliases in COLUMN_ALIASES.items():

        normalized_aliases[standard_name] = [
            normalize_column_name(alias)
            for alias in aliases
        ]

    return normalized_aliases


# ============================================================
# Exact / Alias Match
# ============================================================

def find_exact_match(
    normalized_column,
    normalized_aliases
):
    """
    Find an exact match against known aliases.
    """

    for standard_name, aliases in normalized_aliases.items():

        if normalized_column in aliases:

            return standard_name

    return None


# ============================================================
# Fuzzy Match
# ============================================================

def find_fuzzy_match(
    normalized_column,
    normalized_aliases
):
    """
    Find the closest canonical field using
    string similarity.
    """

    best_match = None
    best_score = 0.0

    for standard_name, aliases in normalized_aliases.items():

        for alias in aliases:

            score = difflib.SequenceMatcher(
                None,
                normalized_column,
                alias
            ).ratio()

            if score > best_score:

                best_score = score
                best_match = standard_name

    if best_score >= FUZZY_THRESHOLD:

        return (
            best_match,
            round(best_score, 4)
        )

    return (
        None,
        round(best_score, 4)
    )


# ============================================================
# Confidence Classification
# ============================================================

def classify_confidence(
    score,
    method
):
    """
    Convert numeric confidence into
    a human-readable level.
    """

    if method == "exact":

        return "high"

    if score >= 0.90:

        return "high"

    if score >= 0.75:

        return "medium"

    return "low"


# ============================================================
# Main Column Mapping
# ============================================================

def map_columns(columns):
    """
    Map uploaded columns using:

    1. Exact / alias matching
    2. Fuzzy matching
    3. Semantic matching
    4. Conflict detection
    5. Safe rejection of uncertain mappings

    A canonical column can only be assigned once.
    """

    normalized_aliases = (
        build_normalized_aliases()
    )

    mapping = {}

    unmatched = []

    mapping_details = []

    mapping_conflicts = {}

    # Tracks which canonical fields have
    # already been assigned.
    assigned_targets = {}

    # ========================================================
    # Process every uploaded column
    # ========================================================

    for original_column in columns:

        normalized_column = (
            normalize_column_name(
                original_column
            )
        )

        # ====================================================
        # STEP 1 — EXACT / ALIAS MATCH
        # ====================================================

        exact_match = find_exact_match(
            normalized_column,
            normalized_aliases
        )

        if exact_match is not None:

            # ------------------------------------------------
            # Check whether target already exists
            # ------------------------------------------------

            if exact_match in assigned_targets:

                existing_column = (
                    assigned_targets[
                        exact_match
                    ]
                )

                mapping_conflicts.setdefault(
                    exact_match,
                    [existing_column]
                )

                if (
                    original_column
                    not in mapping_conflicts[
                        exact_match
                    ]
                ):

                    mapping_conflicts[
                        exact_match
                    ].append(
                        original_column
                    )

                mapping_details.append({

                    "original_column":
                        original_column,

                    "standard_column":
                        None,

                    "proposed_standard_column":
                        exact_match,

                    "method":
                        "conflict",

                    "confidence":
                        1.0,

                    "confidence_level":
                        "high",

                    "reason":
                        "canonical column already assigned",

                    "conflicting_column":
                        existing_column
                })

                continue

            # ------------------------------------------------
            # Accept exact mapping
            # ------------------------------------------------

            mapping[
                original_column
            ] = exact_match

            assigned_targets[
                exact_match
            ] = original_column

            mapping_details.append({

                "original_column":
                    original_column,

                "standard_column":
                    exact_match,

                "proposed_standard_column":
                    exact_match,

                "method":
                    "exact",

                "confidence":
                    1.0,

                "confidence_level":
                    "high"
            })

            continue

        # ====================================================
        # STEP 2 — FUZZY MATCH
        # ====================================================

        fuzzy_match, fuzzy_score = (
            find_fuzzy_match(
                normalized_column,
                normalized_aliases
            )
        )

        if fuzzy_match is not None:

            confidence_level = (
                classify_confidence(
                    fuzzy_score,
                    "fuzzy"
                )
            )

            # ------------------------------------------------
            # Target already assigned?
            # ------------------------------------------------

            if fuzzy_match in assigned_targets:

                existing_column = (
                    assigned_targets[
                        fuzzy_match
                    ]
                )

                mapping_conflicts.setdefault(
                    fuzzy_match,
                    [existing_column]
                )

                if (
                    original_column
                    not in mapping_conflicts[
                        fuzzy_match
                    ]
                ):

                    mapping_conflicts[
                        fuzzy_match
                    ].append(
                        original_column
                    )

                mapping_details.append({

                    "original_column":
                        original_column,

                    "standard_column":
                        None,

                    "proposed_standard_column":
                        fuzzy_match,

                    "method":
                        "conflict",

                    "confidence":
                        fuzzy_score,

                    "confidence_level":
                        confidence_level,

                    "reason":
                        "canonical column already assigned",

                    "conflicting_column":
                        existing_column
                })

                continue

            # ------------------------------------------------
            # Accept fuzzy mapping
            # ------------------------------------------------

            mapping[
                original_column
            ] = fuzzy_match

            assigned_targets[
                fuzzy_match
            ] = original_column

            mapping_details.append({

                "original_column":
                    original_column,

                "standard_column":
                    fuzzy_match,

                "proposed_standard_column":
                    fuzzy_match,

                "method":
                    "fuzzy",

                "confidence":
                    fuzzy_score,

                "confidence_level":
                    confidence_level
            })

            continue

        # ====================================================
        # STEP 3 — SEMANTIC MATCH
        # ====================================================

        # IMPORTANT:
        #
        # Semantic matching considers ALL canonical fields.
        #
        # We do NOT remove already-used fields here because
        # we need to know when a semantic match creates a
        # conflict.

        semantic_result = find_semantic_match(
            original_column,
            candidate_columns=list(
                normalized_aliases.keys()
            )
        )

        semantic_match = (
            semantic_result["match"]
        )

        semantic_score = (
            semantic_result["score"]
        )

        semantic_confidence = (
            semantic_result["confidence"]
        )

        # ----------------------------------------------------
        # Semantic match found
        # ----------------------------------------------------

        if (
            semantic_match is not None
            and semantic_confidence
            in ["medium", "high"]
        ):

            # ------------------------------------------------
            # Semantic target already assigned
            # ------------------------------------------------

            if semantic_match in assigned_targets:

                existing_column = (
                    assigned_targets[
                        semantic_match
                    ]
                )

                mapping_conflicts.setdefault(
                    semantic_match,
                    [existing_column]
                )

                if (
                    original_column
                    not in mapping_conflicts[
                        semantic_match
                    ]
                ):

                    mapping_conflicts[
                        semantic_match
                    ].append(
                        original_column
                    )

                mapping_details.append({

                    "original_column":
                        original_column,

                    "standard_column":
                        None,

                    "proposed_standard_column":
                        semantic_match,

                    "method":
                        "conflict",

                    "confidence":
                        semantic_score,

                    "confidence_level":
                        semantic_confidence,

                    "matched_phrase":
                        semantic_result[
                            "matched_phrase"
                        ],

                    "semantic_margin":
                        semantic_result[
                            "margin"
                        ],

                    "reason":
                        "canonical column already assigned",

                    "conflicting_column":
                        existing_column
                })

                continue

            # ------------------------------------------------
            # Accept semantic mapping
            # ------------------------------------------------

            mapping[
                original_column
            ] = semantic_match

            assigned_targets[
                semantic_match
            ] = original_column

            mapping_details.append({

                "original_column":
                    original_column,

                "standard_column":
                    semantic_match,

                "proposed_standard_column":
                    semantic_match,

                "method":
                    "semantic",

                "confidence":
                    semantic_score,

                "confidence_level":
                    semantic_confidence,

                "matched_phrase":
                    semantic_result[
                        "matched_phrase"
                    ],

                "semantic_margin":
                    semantic_result[
                        "margin"
                    ]
            })

            continue

        # ====================================================
        # STEP 4 — UNMATCHED
        # ====================================================

        unmatched.append(
            original_column
        )

        mapping_details.append({

            "original_column":
                original_column,

            "standard_column":
                None,

            "proposed_standard_column":
                None,

            "method":
                "unmatched",

            "confidence":
                semantic_score,

            "confidence_level":
                "low",

            "matched_phrase":
                semantic_result[
                    "matched_phrase"
                ],

            "semantic_margin":
                semantic_result[
                    "margin"
                ]
        })

    # ========================================================
    # Return Mapping Results
    # ========================================================

    return (
        mapping,
        unmatched,
        mapping_details,
        mapping_conflicts
    )


# ============================================================
# Apply Mapping to DataFrame
# ============================================================

def apply_column_mapping(
    df: pd.DataFrame
):
    """
    Apply the detected mapping to the DataFrame.

    Duplicate canonical columns are prevented because
    conflicting columns are NOT renamed.
    """

    (
        mapping,
        unmatched,
        mapping_details,
        mapping_conflicts
    ) = map_columns(
        df.columns
    )

    mapped_df = df.rename(
        columns=mapping
    )

    return (
        mapped_df,
        mapping,
        unmatched,
        mapping_details,
        mapping_conflicts
    )