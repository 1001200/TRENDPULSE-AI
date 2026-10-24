import pandas as pd
import numpy as np

from data_engine.utils import clean_number  # noqa: F401


# ============================================================
# TRENDPULSE INTELLIGENT PROFILER V3
# ============================================================

def profile_data(df: pd.DataFrame):
    """
    Generate an advanced intelligent profile of a DataFrame.

    V3 includes everything from V2 plus:

    Dataset
        - rows
        - columns
        - total cells
        - missing cells
        - duplicate rows

    Column Intelligence
        - dtype
        - missingness
        - uniqueness
        - cardinality
        - identifier detection

    Numeric
        - descriptive statistics
        - quartiles
        - IQR
        - skewness
        - coefficient of variation
        - zero count
        - negative count
        - outliers
        - distribution shape
        - variability

    Categorical
        - top values
        - dominant value
        - entropy
        - rare values
        - imbalance

    Datetime
        - minimum
        - maximum
        - range

    Relationships
        - Pearson correlation
        - correlation strength
        - direction
        - outlier-aware correlation warning

    Intelligence
        - automatic column signals
        - automatic dataset insights
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            "profile_data expects a pandas DataFrame."
        )

    data = df.copy()

    # ========================================================
    # DATASET OVERVIEW
    # ========================================================

    rows = len(data)
    columns = len(data.columns)

    total_cells = rows * columns

    missing_cells = int(
        data.isna().sum().sum()
    )

    duplicate_rows = int(
        data.duplicated().sum()
    )

    if total_cells > 0:
        missing_percentage = round(
            (missing_cells / total_cells) * 100,
            2
        )
    else:
        missing_percentage = 0.0

    # ========================================================
    # COLUMN GROUPS
    # ========================================================

    numeric_columns = [
        str(column)
        for column in data.columns
        if pd.api.types.is_numeric_dtype(
            data[column]
        )
    ]

    datetime_columns = [
        str(column)
        for column in data.columns
        if pd.api.types.is_datetime64_any_dtype(
            data[column]
        )
    ]

    categorical_columns = [
        str(column)
        for column in data.columns
        if (
            pd.api.types.is_object_dtype(
                data[column]
            )
            or
            pd.api.types.is_string_dtype(
                data[column]
            )
            or
            isinstance(
                data[column].dtype,
                pd.CategoricalDtype
            )
        )
    ]

    # ========================================================
    # COLUMN PROFILES
    # ========================================================

    column_profiles = {}

    for column in data.columns:

        column_name = str(column)
        series = data[column]

        non_null = series.dropna()

        non_null_count = int(
            series.notna().sum()
        )

        missing_count = int(
            series.isna().sum()
        )

        unique_count = int(
            series.nunique(
                dropna=True
            )
        )

        if rows > 0:

            missing_percent = round(
                (
                    missing_count / rows
                ) * 100,
                2
            )

            unique_percent = round(
                (
                    unique_count / rows
                ) * 100,
                2
            )

        else:

            missing_percent = 0.0
            unique_percent = 0.0

        profile = {

            "dtype":
                str(series.dtype),

            "non_null_count":
                non_null_count,

            "missing_count":
                missing_count,

            "missing_percent":
                missing_percent,

            "unique_count":
                unique_count,

            "unique_percent":
                unique_percent,

            "cardinality":
                classify_cardinality(
                    unique_count,
                    rows
                ),

            "intelligence":
                profile_column_intelligence(
                    column_name,
                    series,
                    unique_count,
                    rows,
                    missing_percent
                )
        }

        # ====================================================
        # NUMERIC
        # ====================================================

        if column_name in numeric_columns:

            numeric = pd.to_numeric(
                series,
                errors="coerce"
            ).dropna()

            profile["numeric"] = (
                profile_numeric_column(
                    numeric
                )
            )

            profile["intelligence"].update(
                numeric_intelligence(
                    numeric
                )
            )

        # ====================================================
        # DATETIME
        # ====================================================

        elif column_name in datetime_columns:

            profile["date"] = (
                profile_datetime_column(
                    series
                )
            )

            profile["intelligence"].update(
                datetime_intelligence(
                    series
                )
            )

        # ====================================================
        # CATEGORICAL
        # ====================================================

        else:

            profile["categorical"] = (
                profile_categorical_column(
                    non_null
                )
            )

            profile["intelligence"].update(
                categorical_intelligence(
                    column_name,
                    non_null,
                    unique_count,
                    rows
                )
            )

        column_profiles[column_name] = profile

    # ========================================================
    # RELATIONSHIPS
    # ========================================================

    relationship_result = analyze_relationships(
        data,
        numeric_columns
    )

    # ========================================================
    # DATASET INTELLIGENCE
    # ========================================================

    dataset_signals = generate_dataset_signals(
        data,
        column_profiles,
        relationship_result
    )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    return {

        "column_names": [str(c) for c in data.columns],

        "dataset": {

            "rows":
                rows,

            "columns":
                columns,

            "total_cells":
                total_cells,

            "missing_cells":
                missing_cells,

            "missing_percentage":
                missing_percentage,

            "duplicate_rows":
                duplicate_rows
        },

        "column_groups": {

            "numeric":
                numeric_columns,

            "categorical":
                categorical_columns,

            "datetime":
                datetime_columns
        },

        "column_profiles":
            column_profiles,

        "relationships": {

            "numeric_correlations":
                relationship_result[
                    "numeric_correlations"
                ],

            "correlation_details":
                relationship_result[
                    "correlation_details"
                ],

            "outlier_warnings":
                relationship_result[
                    "outlier_warnings"
                ]
        },

        "intelligence": {

            "dataset_signals":
                dataset_signals,

            "insights":
                generate_insights(
                    data,
                    column_profiles,
                    relationship_result
                )
        }
    }


# ============================================================
# NUMERIC PROFILE
# ============================================================

def profile_numeric_column(numeric):

    if len(numeric) == 0:
        return {}

    minimum = numeric.min()
    maximum = numeric.max()
    mean = numeric.mean()
    median = numeric.median()

    std = numeric.std()

    variance = numeric.var()

    q1 = numeric.quantile(
        0.25
    )

    q3 = numeric.quantile(
        0.75
    )

    iqr = q3 - q1

    # --------------------------------------------------------
    # Skewness
    # --------------------------------------------------------

    if len(numeric) >= 3:
        skewness = numeric.skew()
    else:
        skewness = np.nan

    # --------------------------------------------------------
    # Coefficient of Variation
    # --------------------------------------------------------

    if mean != 0:

        coefficient_of_variation = (
            std / abs(mean)
        ) * 100

    else:

        coefficient_of_variation = np.nan

    # --------------------------------------------------------
    # IQR Outliers
    # --------------------------------------------------------

    lower_bound = (
        q1 - (1.5 * iqr)
    )

    upper_bound = (
        q3 + (1.5 * iqr)
    )

    outliers = numeric[
        (numeric < lower_bound)
        |
        (numeric > upper_bound)
    ]

    outlier_count = int(
        len(outliers)
    )

    outlier_percentage = round(
        (
            outlier_count
            / len(numeric)
        ) * 100,
        2
    )

    # --------------------------------------------------------
    # Classifications
    # --------------------------------------------------------

    distribution_shape = (
        classify_distribution(
            skewness
        )
    )

    variability = (
        classify_variability(
            coefficient_of_variation
        )
    )

    # --------------------------------------------------------
    # Return
    # --------------------------------------------------------

    return {

        "min":
            clean_number(
                minimum
            ),

        "max":
            clean_number(
                maximum
            ),

        "mean":
            clean_number(
                mean
            ),

        "median":
            clean_number(
                median
            ),

        "std":
            clean_number(
                std
            ),

        "variance":
            clean_number(
                variance
            ),

        "q1":
            clean_number(
                q1
            ),

        "q3":
            clean_number(
                q3
            ),

        "iqr":
            clean_number(
                iqr
            ),

        "skewness":
            clean_number(
                skewness
            ),

        "coefficient_of_variation":
            clean_number(
                coefficient_of_variation
            ),

        "zero_count":
            int(
                (numeric == 0).sum()
            ),

        "negative_count":
            int(
                (numeric < 0).sum()
            ),

        "outlier_count":
            outlier_count,

        "outlier_percentage":
            outlier_percentage,

        "iqr_lower_bound":
            clean_number(
                lower_bound
            ),

        "iqr_upper_bound":
            clean_number(
                upper_bound
            ),

        "distribution_shape":
            distribution_shape,

        "variability":
            variability
    }


# ============================================================
# NUMERIC INTELLIGENCE
# ============================================================

def numeric_intelligence(numeric):

    if len(numeric) == 0:
        return {
            "signals": []
        }

    signals = []

    q1 = numeric.quantile(0.25)
    q3 = numeric.quantile(0.75)

    iqr = q3 - q1

    lower_bound = q1 - (1.5 * iqr)
    upper_bound = q3 + (1.5 * iqr)

    outlier_count = int(
        (
            (numeric < lower_bound)
            |
            (numeric > upper_bound)
        ).sum()
    )

    if outlier_count > 0:

        signals.append(
            "contains_outliers"
        )

    if len(numeric) >= 3:

        skewness = numeric.skew()

        if abs(skewness) > 1:

            signals.append(
                "highly_skewed"
            )

        elif abs(skewness) > 0.5:

            signals.append(
                "moderately_skewed"
            )

    mean = numeric.mean()
    std = numeric.std()

    if mean != 0:

        cv = (
            std / abs(mean)
        ) * 100

        if cv > 100:

            signals.append(
                "extremely_high_variability"
            )

        elif cv > 50:

            signals.append(
                "high_variability"
            )

    if int((numeric == 0).sum()) > 0:

        signals.append(
            "contains_zero_values"
        )

    if int((numeric < 0).sum()) > 0:

        signals.append(
            "contains_negative_values"
        )

    return {
        "signals": signals
    }


# ============================================================
# DISTRIBUTION CLASSIFICATION
# ============================================================

def classify_distribution(skewness):

    if pd.isna(skewness):
        return "unknown"

    value = float(skewness)

    absolute_value = abs(value)

    if absolute_value <= 0.5:

        return "approximately_symmetric"

    if absolute_value <= 1.0:

        if value > 0:
            return "moderately_right_skewed"

        return "moderately_left_skewed"

    if value > 0:
        return "highly_right_skewed"

    return "highly_left_skewed"


# ============================================================
# VARIABILITY CLASSIFICATION
# ============================================================

def classify_variability(
    coefficient_of_variation
):

    if pd.isna(
        coefficient_of_variation
    ):

        return "unknown"

    value = abs(
        float(
            coefficient_of_variation
        )
    )

    if value < 20:
        return "low"

    if value <= 50:
        return "moderate"

    return "high"


# ============================================================
# CATEGORICAL PROFILE
# ============================================================

def profile_categorical_column(
    non_null
):

    if len(non_null) == 0:

        return {

            "top_values": [],

            "dominant_value": None,

            "dominant_percentage": 0.0,

            "entropy": 0.0,

            "rare_values": [],

            "imbalance": "unknown"
        }

    values = (
        non_null
        .astype(str)
    )

    value_counts = (
        values.value_counts()
    )

    total = len(values)

    # --------------------------------------------------------
    # Top Values
    # --------------------------------------------------------

    top_values = []

    for value, count in (
        value_counts
        .head(5)
        .items()
    ):

        top_values.append({

            "value":
                str(value),

            "count":
                int(count),

            "percentage":
                round(
                    (
                        count
                        / total
                    ) * 100,
                    2
                )
        })

    # --------------------------------------------------------
    # Dominant Value
    # --------------------------------------------------------

    dominant_value = str(
        value_counts.index[0]
    )

    dominant_count = int(
        value_counts.iloc[0]
    )

    dominant_percentage = round(
        (
            dominant_count
            / total
        ) * 100,
        2
    )

    # --------------------------------------------------------
    # Entropy
    # --------------------------------------------------------

    probabilities = (
        value_counts
        / total
    )

    entropy = -float(
        (
            probabilities
            * np.log2(
                probabilities
            )
        ).sum()
    )

    # --------------------------------------------------------
    # Rare Values
    # --------------------------------------------------------

    rare_values = []

    # A value appearing in <= 1% of the data
    # is considered rare.
    #
    # For small datasets, minimum threshold is 1.
    rare_threshold = max(
        1,
        int(
            total * 0.01
        )
    )

    for value, count in (
        value_counts.items()
    ):

        if count <= rare_threshold:

            rare_values.append({

                "value":
                    str(value),

                "count":
                    int(count),

                "percentage":
                    round(
                        (
                            count
                            / total
                        ) * 100,
                        2
                    )
            })

    # --------------------------------------------------------
    # Imbalance
    # --------------------------------------------------------

    imbalance = (
        classify_imbalance(
            dominant_percentage
        )
    )

    return {

        "top_values":
            top_values,

        "dominant_value":
            dominant_value,

        "dominant_percentage":
            dominant_percentage,

        "entropy":
            round(
                entropy,
                6
            ),

        "rare_values":
            rare_values,

        "imbalance":
            imbalance
    }


# ============================================================
# CATEGORICAL IMBALANCE
# ============================================================

def classify_imbalance(
    dominant_percentage
):

    if dominant_percentage <= 50:
        return "balanced"

    if dominant_percentage <= 80:
        return "moderately_imbalanced"

    return "highly_imbalanced"


# ============================================================
# CATEGORICAL INTELLIGENCE
# ============================================================

def categorical_intelligence(
    column_name,
    non_null,
    unique_count,
    row_count
):

    signals = []

    if row_count == 0:

        return {
            "signals": signals
        }

    unique_ratio = (
        unique_count / row_count
    )

    lower_name = (
        column_name
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )

    # --------------------------------------------------------
    # Identifier detection
    # --------------------------------------------------------

    identifier_keywords = [
        "id",
        "identifier",
        "uuid",
        "customer_number",
        "customer_no",
        "order_number",
        "order_no",
        "transaction_id"
    ]

    identifier_detected = False

    for keyword in identifier_keywords:

        if (
            lower_name == keyword
            or lower_name.endswith(
                "_" + keyword
            )
            or lower_name.startswith(
                keyword + "_"
            )
        ):

            identifier_detected = True
            break

    if unique_ratio >= 0.80:

        signals.append(
            "high_cardinality"
        )

    if identifier_detected:

        signals.append(
            "likely_identifier"
        )

    elif unique_ratio >= 0.95:

        signals.append(
            "possible_identifier"
        )

    # --------------------------------------------------------
    # Constant column
    # --------------------------------------------------------

    if unique_count <= 1:

        signals.append(
            "constant_column"
        )

    return {

        "signals":
            signals,

        "likely_identifier":
            identifier_detected
            or unique_ratio >= 0.95
    }


# ============================================================
# DATETIME PROFILE
# ============================================================

def profile_datetime_column(
    series
):

    dates = series.dropna()

    if len(dates) == 0:
        return {}

    minimum = dates.min()
    maximum = dates.max()

    return {

        "min":
            str(
                minimum
            ),

        "max":
            str(
                maximum
            ),

        "range_days":
            int(
                (
                    maximum
                    - minimum
                ).days
            )
    }


# ============================================================
# DATETIME INTELLIGENCE
# ============================================================

def datetime_intelligence(series):

    dates = series.dropna()

    signals = []

    if len(dates) == 0:

        return {
            "signals": signals
        }

    minimum = dates.min()
    maximum = dates.max()

    range_days = (
        maximum - minimum
    ).days

    if range_days == 0:

        signals.append(
            "single_day_dataset"
        )

    elif range_days <= 7:

        signals.append(
            "short_time_range"
        )

    elif range_days >= 365:

        signals.append(
            "long_time_range"
        )

    # --------------------------------------------------------
    # Date continuity
    # --------------------------------------------------------

    unique_dates = (
        dates
        .dt.normalize()
        .drop_duplicates()
        .sort_values()
    )

    if len(unique_dates) >= 2:

        gaps = (
            unique_dates
            .diff()
            .dropna()
            .dt.days
        )

        if len(gaps) > 0:

            if gaps.max() > 1:

                signals.append(
                    "contains_date_gaps"
                )

    return {
        "signals": signals
    }


# ============================================================
# RELATIONSHIP ANALYSIS
# ============================================================

def analyze_relationships(
    data,
    numeric_columns
):

    if len(numeric_columns) < 2:

        return {

            "numeric_correlations": {},

            "correlation_details": {},

            "outlier_warnings": []
        }

    numeric_data = data[
        numeric_columns
    ]

    correlation_matrix = (
        numeric_data
        .corr(
            method="pearson"
        )
    )

    correlations = {}

    correlation_details = {}

    outlier_warnings = []

    for i, column_a in enumerate(
        numeric_columns
    ):

        for column_b in (
            numeric_columns[
                i + 1:
            ]
        ):

            value = (
                correlation_matrix
                .loc[
                    column_a,
                    column_b
                ]
            )

            if pd.isna(value):
                continue

            correlation = float(
                value
            )

            key = (
                f"{column_a}__{column_b}"
            )

            correlations[key] = round(
                correlation,
                6
            )

            strength = (
                classify_correlation_strength(
                    correlation
                )
            )

            direction = (
                "positive"
                if correlation > 0
                else
                "negative"
                if correlation < 0
                else
                "none"
            )

            details = {

                "correlation":
                    round(
                        correlation,
                        6
                    ),

                "strength":
                    strength,

                "direction":
                    direction
            }

            # ------------------------------------------------
            # Outlier-aware correlation
            # ------------------------------------------------

            outlier_warning = (
                detect_outlier_driven_correlation(
                    numeric_data[column_a],
                    numeric_data[column_b],
                    correlation
                )
            )

            if outlier_warning:

                details[
                    "outlier_warning"
                ] = outlier_warning

                outlier_warnings.append({

                    "columns":
                        [
                            column_a,
                            column_b
                        ],

                    "message":
                        outlier_warning
                })

            correlation_details[
                key
            ] = details

    return {

        "numeric_correlations":
            correlations,

        "correlation_details":
            correlation_details,

        "outlier_warnings":
            outlier_warnings
    }


# ============================================================
# CORRELATION STRENGTH
# ============================================================

def classify_correlation_strength(
    correlation
):

    absolute_value = abs(
        correlation
    )

    if absolute_value < 0.20:
        return "very_weak"

    if absolute_value < 0.40:
        return "weak"

    if absolute_value < 0.60:
        return "moderate"

    if absolute_value < 0.80:
        return "strong"

    return "very_strong"


# ============================================================
# OUTLIER-DRIVEN CORRELATION
# ============================================================

def detect_outlier_driven_correlation(
    series_a,
    series_b,
    original_correlation
):

    clean = pd.concat(
        [
            pd.to_numeric(
                series_a,
                errors="coerce"
            ),
            pd.to_numeric(
                series_b,
                errors="coerce"
            )
        ],
        axis=1
    ).dropna()

    if len(clean) < 5:
        return None

    column_a = clean.columns[0]
    column_b = clean.columns[1]

    # --------------------------------------------------------
    # Detect IQR outliers independently
    # --------------------------------------------------------

    outlier_mask = pd.Series(
        False,
        index=clean.index
    )

    for column in [
        column_a,
        column_b
    ]:

        q1 = clean[column].quantile(
            0.25
        )

        q3 = clean[column].quantile(
            0.75
        )

        iqr = q3 - q1

        lower = q1 - (1.5 * iqr)
        upper = q3 + (1.5 * iqr)

        column_outliers = (
            (clean[column] < lower)
            |
            (clean[column] > upper)
        )

        outlier_mask = (
            outlier_mask
            |
            column_outliers
        )

    outlier_count = int(
        outlier_mask.sum()
    )

    if outlier_count == 0:
        return None

    # Need enough normal observations
    # to make a comparison meaningful.
    if (
        len(clean) - outlier_count
        < 4
    ):
        return None

    normal_data = clean[
        ~outlier_mask
    ]

    normal_correlation = (
        normal_data
        .corr(method="pearson")
        .iloc[0, 1]
    )

    if pd.isna(
        normal_correlation
    ):
        return None

    correlation_change = abs(
        original_correlation
        - normal_correlation
    )

    # Strong original correlation,
    # materially weaker after removing outliers.
    if (
        abs(original_correlation) >= 0.80
        and abs(normal_correlation) < 0.60
        and correlation_change >= 0.30
    ):

        return (
            "Strong correlation may be "
            "driven by shared outliers. "
            f"Original correlation="
            f"{original_correlation:.3f}, "
            f"correlation without outliers="
            f"{normal_correlation:.3f}."
        )

    return None


# ============================================================
# COLUMN INTELLIGENCE
# ============================================================

def profile_column_intelligence(
    column_name,
    series,
    unique_count,
    row_count,
    missing_percent
):

    signals = []

    if missing_percent >= 50:

        signals.append(
            "high_missingness"
        )

    elif missing_percent > 0:

        signals.append(
            "contains_missing_values"
        )

    if row_count > 0:

        unique_ratio = (
            unique_count
            / row_count
        )

        if unique_ratio >= 0.95:

            signals.append(
                "high_uniqueness"
            )

    if unique_count <= 1 and row_count > 0:

        signals.append(
            "constant_column"
        )

    return {

        "signals":
            signals
    }


# ============================================================
# DATASET SIGNALS
# ============================================================

def generate_dataset_signals(
    data,
    column_profiles,
    relationship_result
):

    signals = []

    # --------------------------------------------------------
    # Missing data
    # --------------------------------------------------------

    missing_columns = []

    for column, profile in (
        column_profiles.items()
    ):

        if (
            profile[
                "missing_percent"
            ] > 0
        ):

            missing_columns.append(
                column
            )

    if missing_columns:

        signals.append({

            "type":
                "missing_data",

            "severity":
                "warning",

            "message":
                (
                    f"{len(missing_columns)} "
                    "column(s) contain "
                    "missing values."
                ),

            "columns":
                missing_columns
        })

    # --------------------------------------------------------
    # Duplicate rows
    # --------------------------------------------------------

    duplicate_rows = int(
        data.duplicated().sum()
    )

    if duplicate_rows > 0:

        signals.append({

            "type":
                "duplicates",

            "severity":
                "warning",

            "message":
                (
                    f"{duplicate_rows} "
                    "duplicate row(s) "
                    "detected."
                )
        })

    # --------------------------------------------------------
    # Numeric outliers
    # --------------------------------------------------------

    outlier_columns = []

    for column, profile in (
        column_profiles.items()
    ):

        numeric_profile = (
            profile.get(
                "numeric"
            )
        )

        if numeric_profile:

            if (
                numeric_profile[
                    "outlier_count"
                ] > 0
            ):

                outlier_columns.append(
                    column
                )

    if outlier_columns:

        signals.append({

            "type":
                "outliers",

            "severity":
                "warning",

            "message":
                (
                    f"{len(outlier_columns)} "
                    "numeric column(s) "
                    "contain outliers."
                ),

            "columns":
                outlier_columns
        })

    # --------------------------------------------------------
    # Identifier columns
    # --------------------------------------------------------

    identifier_columns = []

    for column, profile in (
        column_profiles.items()
    ):

        intelligence = (
            profile.get(
                "intelligence",
                {}
            )
        )

        if intelligence.get(
            "likely_identifier",
            False
        ):

            identifier_columns.append(
                column
            )

    if identifier_columns:

        signals.append({

            "type":
                "identifier_columns",

            "severity":
                "info",

            "message":
                (
                    "Columns likely behaving "
                    "as identifiers were detected."
                ),

            "columns":
                identifier_columns
        })

    # --------------------------------------------------------
    # Correlation warnings
    # --------------------------------------------------------

    correlation_warnings = (
        relationship_result.get(
            "outlier_warnings",
            []
        )
    )

    if correlation_warnings:

        signals.append({

            "type":
                "outlier_driven_correlation",

            "severity":
                "warning",

            "message":
                (
                    "Some strong correlations "
                    "may be influenced by "
                    "outliers."
                )
        })

    return signals


# ============================================================
# AUTOMATIC INSIGHTS
# ============================================================

def generate_insights(
    data,
    column_profiles,
    relationship_result
):

    insights = []

    # --------------------------------------------------------
    # Numeric insights
    # --------------------------------------------------------

    for column, profile in (
        column_profiles.items()
    ):

        numeric = profile.get(
            "numeric"
        )

        if not numeric:
            continue

        outlier_count = numeric.get(
            "outlier_count",
            0
        )

        if outlier_count > 0:

            insights.append({

                "type":
                    "outlier",

                "column":
                    column,

                "severity":
                    "warning",

                "message":
                    (
                        f"{column} contains "
                        f"{outlier_count} "
                        "statistical outlier(s)."
                    )
            })

        distribution = numeric.get(
            "distribution_shape"
        )

        if distribution in [
            "highly_right_skewed",
            "highly_left_skewed"
        ]:

            insights.append({

                "type":
                    "distribution",

                "column":
                    column,

                "severity":
                    "info",

                "message":
                    (
                        f"{column} is "
                        f"{distribution.replace('_', ' ')}."
                    )
            })

        variability = numeric.get(
            "variability"
        )

        if variability == "high":

            insights.append({

                "type":
                    "variability",

                "column":
                    column,

                "severity":
                    "info",

                "message":
                    (
                        f"{column} has high "
                        "relative variability."
                    )
            })

    # --------------------------------------------------------
    # Identifier insights
    # --------------------------------------------------------

    for column, profile in (
        column_profiles.items()
    ):

        intelligence = profile.get(
            "intelligence",
            {}
        )

        if intelligence.get(
            "likely_identifier",
            False
        ):

            insights.append({

                "type":
                    "identifier",

                "column":
                    column,

                "severity":
                    "info",

                "message":
                    (
                        f"{column} appears to "
                        "behave like an identifier."
                    )
            })

    # --------------------------------------------------------
    # Correlation insights
    # --------------------------------------------------------

    correlation_details = (
        relationship_result.get(
            "correlation_details",
            {}
        )
    )

    for key, details in (
        correlation_details.items()
    ):

        correlation = details.get(
            "correlation"
        )

        strength = details.get(
            "strength"
        )

        if (
            correlation is not None
            and abs(correlation) >= 0.80
        ):

            insights.append({

                "type":
                    "correlation",

                "columns":
                    key.split("__"),

                "severity":
                    "info",

                "message":
                    (
                        f"{key.replace('__', ' and ')} "
                        f"have a {strength} "
                        f"{details['direction']} "
                        "correlation."
                    )
            })

        if details.get(
            "outlier_warning"
        ):

            insights.append({

                "type":
                    "correlation_warning",

                "columns":
                    key.split("__"),

                "severity":
                    "warning",

                "message":
                    details[
                        "outlier_warning"
                    ]
            })

    # --------------------------------------------------------
    # Duplicate insight
    # --------------------------------------------------------

    duplicate_rows = int(
        data.duplicated().sum()
    )

    if duplicate_rows > 0:

        insights.append({

            "type":
                "duplicates",

            "severity":
                "warning",

            "message":
                (
                    f"Dataset contains "
                    f"{duplicate_rows} "
                    "duplicate row(s)."
                )
        })

    return insights


# ============================================================
# CARDINALITY
# ============================================================

def classify_cardinality(
    unique_count,
    row_count
):

    if unique_count == 0:
        return "empty"

    if row_count == 0:
        return "empty"

    unique_ratio = (
        unique_count
        / row_count
    )

    if unique_ratio <= 0.10:
        return "low"

    if unique_ratio <= 0.50:
        return "medium"

    return "high"


# Backward-compatible file-path profiling API.
def profile_dataset(file_path):
    """Load CSV/XLSX and profile it without mutating the source."""
    from pathlib import Path
    path = Path(file_path)
    if path.suffix.lower() == ".csv":
        frame = pd.read_csv(path)
    elif path.suffix.lower() in {".xlsx", ".xls"}:
        frame = pd.read_excel(path)
    else:
        raise ValueError("Unsupported file type. Use CSV or Excel.")
    return profile_data(frame)
