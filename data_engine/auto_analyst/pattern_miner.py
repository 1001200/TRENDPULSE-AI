"""
Pattern Miner & Unsupervised ML Engine.

Executes correlation discovery, automatic K-Means clustering with persona profiling,
and Isolation Forest anomaly detection with root-cause column attribution.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


class PatternResult:
    def __init__(
        self,
        correlations: List[Dict[str, Any]],
        correlation_matrix: Dict[str, Dict[str, float]],
        clusters: Dict[str, Any],
        anomalies: Dict[str, Any],
        feature_importance: Dict[str, Any],
        numeric_columns: List[str],
        categorical_columns: List[str],
        date_columns: List[str],
    ):
        self.correlations = correlations
        self.correlation_matrix = correlation_matrix
        self.clusters = clusters
        self.anomalies = anomalies
        self.feature_importance = feature_importance
        self.numeric_columns = numeric_columns
        self.categorical_columns = categorical_columns
        self.date_columns = date_columns

    def to_dict(self) -> Dict[str, Any]:
        return {
            "correlations": self.correlations,
            "correlation_matrix": self.correlation_matrix,
            "clusters": self.clusters,
            "anomalies": self.anomalies,
            "feature_importance": self.feature_importance,
            "numeric_columns": self.numeric_columns,
            "categorical_columns": self.categorical_columns,
            "date_columns": self.date_columns,
        }


def compute_correlations(df: pd.DataFrame, num_cols: List[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, float]]]:
    """Compute Pearson correlation matrix and top pairwise relationships."""
    if len(num_cols) < 2 or len(df) < 5:
        return [], {}

    corr_df = df[num_cols].corr().fillna(0.0)
    matrix_dict = {col: {c: round(float(val), 3) for c, val in row.items()} for col, row in corr_df.iterrows()}

    # Extract upper triangle pairs
    pairs = []
    for i in range(len(num_cols)):
        for j in range(i + 1, len(num_cols)):
            col1 = num_cols[i]
            col2 = num_cols[j]
            r = float(corr_df.loc[col1, col2])
            abs_r = abs(r)

            if abs_r >= 0.25:  # meaningful threshold
                direction = "positive" if r > 0 else "negative"
                strength = "strong" if abs_r >= 0.7 else ("moderate" if abs_r >= 0.4 else "slight")
                desc = (
                    f"Strong {direction} coupling between {col1} and {col2} (r = {r:.2f})"
                    if strength == "strong"
                    else f"Moderate {direction} trend between {col1} and {col2} (r = {r:.2f})"
                )

                pairs.append({
                    "column_a": col1,
                    "column_b": col2,
                    "r_value": round(r, 3),
                    "abs_r": round(abs_r, 3),
                    "direction": direction,
                    "strength": strength,
                    "description": desc,
                })

    pairs.sort(key=lambda x: x["abs_r"], reverse=True)
    return pairs[:10], matrix_dict


def run_clustering(df: pd.DataFrame, num_cols: List[str]) -> Dict[str, Any]:
    """
    Perform automatic K-Means clustering with optimal k heuristic and centroid persona labeling.
    """
    if len(num_cols) < 2 or len(df) < 15:
        return {"enabled": False, "reason": "Insufficient numeric variance or row count (<15)"}

    # Use sample if very large dataset
    sub_df = df[num_cols].dropna()
    if len(sub_df) < 15:
        return {"enabled": False, "reason": "Too few non-null rows"}

    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(sub_df)

    # Heuristic for optimal k between 2 and 4
    best_k = 3
    best_score = -1.0

    k_candidates = [2, 3] if len(sub_df) < 40 else [2, 3, 4]
    for k in k_candidates:
        try:
            km = KMeans(n_clusters=k, random_state=42, n_init=5)
            labels = km.fit_predict(scaled_data)
            score = silhouette_score(scaled_data, labels)
            if score > best_score:
                best_score = score
                best_k = k
        except Exception:
            pass

    # Fit best model
    final_km = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    cluster_labels = final_km.fit_predict(scaled_data)
    sub_df_copy = sub_df.copy()
    sub_df_copy["cluster"] = cluster_labels

    global_means = sub_df[num_cols].mean()
    global_stds = sub_df[num_cols].std().replace(0, 1.0)

    cluster_profiles = []
    total_clustered = len(sub_df_copy)

    for c_id in range(best_k):
        c_rows = sub_df_copy[sub_df_copy["cluster"] == c_id]
        c_count = len(c_rows)
        c_pct = round((c_count / total_clustered) * 100, 1)

        c_means = c_rows[num_cols].mean()
        # Compute z-scores of centroid to see defining traits
        z_scores = (c_means - global_means) / global_stds

        top_positive_trait = z_scores.idxmax()
        top_positive_z = float(z_scores[top_positive_trait])

        top_negative_trait = z_scores.idxmin()
        top_negative_z = float(z_scores[top_negative_trait])

        # Auto-name persona
        if top_positive_z > 0.6 and abs(top_negative_z) < 0.5:
            persona = f"High {top_positive_trait.replace('_', ' ').title()} Leaders"
        elif top_negative_z < -0.6 and top_positive_z < 0.5:
            persona = f"Low {top_negative_trait.replace('_', ' ').title()} Baseline"
        elif top_positive_z > 0.5 and top_negative_z < -0.5:
            persona = f"High {top_positive_trait.replace('_', ' ').title()} / Low {top_negative_trait.replace('_', ' ').title()}"
        else:
            persona = f"Balanced Segment {c_id + 1}"

        traits = []
        for col in num_cols:
            diff_pct = ((c_means[col] - global_means[col]) / (global_means[col] + 1e-9)) * 100.0
            if abs(diff_pct) >= 15:
                direction = "higher" if diff_pct > 0 else "lower"
                traits.append(f"{abs(diff_pct):.0f}% {direction} {col.replace('_', ' ')}")

        cluster_profiles.append({
            "cluster_id": int(c_id),
            "name": persona,
            "count": int(c_count),
            "percentage": float(c_pct),
            "defining_traits": traits[:3] if traits else ["Representative baseline metrics"],
            "means": {col: round(float(c_means[col]), 2) for col in num_cols},
        })

    # Prepare 2D sample points for scatter plot visualization
    # Choose top 2 features with highest variance or highest correlation
    x_col = num_cols[0]
    y_col = num_cols[1] if len(num_cols) > 1 else num_cols[0]

    # Sample points for performance if > 500 rows
    sample_vis = sub_df_copy.sample(min(400, len(sub_df_copy)), random_state=42)
    vis_points = []
    for _, row in sample_vis.iterrows():
        vis_points.append({
            "x": round(float(row[x_col]), 2),
            "y": round(float(row[y_col]), 2),
            "cluster": int(row["cluster"]),
        })

    return {
        "enabled": True,
        "k": best_k,
        "x_axis": x_col,
        "y_axis": y_col,
        "profiles": cluster_profiles,
        "visualization_points": vis_points,
    }


def detect_anomalies(df: pd.DataFrame, num_cols: List[str]) -> Dict[str, Any]:
    """
    Isolation Forest anomaly detection with root-cause column attribution.
    """
    if len(num_cols) == 0 or len(df) < 10:
        return {"enabled": False, "outlier_count": 0, "outliers": []}

    sub_df = df[num_cols].fillna(df[num_cols].median())
    scaler = StandardScaler()
    scaled = scaler.fit_transform(sub_df)

    contamination = max(0.01, min(0.05, 5.0 / len(df)))
    iso = IsolationForest(contamination=contamination, random_state=42)
    predictions = iso.fit_predict(scaled)  # -1 for anomaly, 1 for normal
    scores = iso.decision_function(scaled)

    anomaly_indices = np.where(predictions == -1)[0]
    total_anomalies = len(anomaly_indices)

    means = sub_df.mean()
    stds = sub_df.std().replace(0, 1.0)

    outliers = []
    for idx in anomaly_indices:
        row_vals = sub_df.iloc[idx]
        # Calculate z-scores for this row
        z_scores = (row_vals - means).abs() / stds
        top_driver_col = z_scores.idxmax()
        top_driver_z = float(z_scores[top_driver_col])
        actual_val = float(row_vals[top_driver_col])
        avg_val = float(means[top_driver_col])

        # Plain language trigger reason
        reason = f"{top_driver_col.replace('_', ' ').title()} is {top_driver_z:.1f}σ from mean ({actual_val:.2f} vs avg {avg_val:.2f})"

        # Row preview as dict
        full_row_preview = {k: str(v) for k, v in df.iloc[idx].head(8).items()}

        outliers.append({
            "row_index": int(idx) + 1,
            "anomaly_score": round(float(-scores[idx]), 3),
            "primary_driver": top_driver_col,
            "deviation_sigma": round(top_driver_z, 1),
            "reason": reason,
            "row_preview": full_row_preview,
        })

    outliers.sort(key=lambda x: x["anomaly_score"], reverse=True)

    return {
        "enabled": True,
        "outlier_count": total_anomalies,
        "outlier_rate_pct": round((total_anomalies / len(df)) * 100, 2),
        "top_outliers": outliers[:15],
    }


def compute_feature_importance(df: pd.DataFrame, num_cols: List[str]) -> Dict[str, Any]:
    """
    Train a lightweight Random Forest model to compute feature importance on the most informative target.
    """
    if len(num_cols) < 3 or len(df) < 20:
        return {"enabled": False, "reason": "Requires at least 3 numeric features and 20 rows"}

    # Target selection heuristic: choose column containing keywords, or column with highest variance
    sub_df = df[num_cols].dropna()
    if len(sub_df) < 20:
        return {"enabled": False, "reason": "Insufficient non-null records"}

    target_keywords = ["revenue", "cost", "spend", "amount", "price", "stay", "score", "total", "profit"]
    target_col = None
    for col in num_cols:
        col_l = col.lower()
        if any(kw in col_l for kw in target_keywords):
            target_col = col
            break

    if not target_col:
        # Fallback to the last numeric column
        target_col = num_cols[-1]

    feature_cols = [c for c in num_cols if c != target_col]
    if not feature_cols:
        return {"enabled": False, "reason": "No feature columns"}

    try:
        X = sub_df[feature_cols]
        y = sub_df[target_col]

        rf = RandomForestRegressor(n_estimators=30, max_depth=5, random_state=42)
        rf.fit(X, y)

        importances = rf.feature_importances_
        ranked = []
        for feat, imp in zip(feature_cols, importances):
            ranked.append({
                "feature": feat.replace("_", " ").title(),
                "importance_pct": round(float(imp) * 100, 1),
            })

        ranked.sort(key=lambda x: x["importance_pct"], reverse=True)

        return {
            "enabled": True,
            "target_metric": target_col.replace("_", " ").title(),
            "drivers": ranked,
        }
    except Exception as exc:
        return {"enabled": False, "reason": str(exc)}


def mine_patterns(df: pd.DataFrame, schema: Dict[str, Dict[str, Any]]) -> PatternResult:
    """Orchestrate all statistical and ML pattern extraction."""
    num_cols = [col for col, info in schema.items() if info.get("inferred_type") == "numeric"]
    cat_cols = [col for col, info in schema.items() if info.get("inferred_type") == "categorical"]
    dt_cols = [col for col, info in schema.items() if info.get("inferred_type") == "datetime"]

    correlations, corr_matrix = compute_correlations(df, num_cols)
    clusters = run_clustering(df, num_cols)
    anomalies = detect_anomalies(df, num_cols)
    feature_importance = compute_feature_importance(df, num_cols)

    return PatternResult(
        correlations=correlations,
        correlation_matrix=corr_matrix,
        clusters=clusters,
        anomalies=anomalies,
        feature_importance=feature_importance,
        numeric_columns=num_cols,
        categorical_columns=cat_cols,
        date_columns=dt_cols,
    )
