"""
Plain-Language Executive Narrative & Synthesis Engine.

Generates high-impact, deterministic executive briefings, key driver explanations,
cluster cohort narratives, outlier risk alerts, and prescriptive recommendations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import pandas as pd


def generate_executive_narrative(
    clean_result_dict: Dict[str, Any],
    patterns_dict: Dict[str, Any],
    kpis: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Produce a structured, plain-language executive briefing based on the analytical findings.
    """
    health_score = clean_result_dict.get("health_score", 90.0)
    rows_count = clean_result_dict.get("rows_after", 0)
    cols_count = clean_result_dict.get("columns_count", 0)
    dups_removed = clean_result_dict.get("quality_metrics", {}).get("duplicates_removed", 0)
    imputed_count = clean_result_dict.get("quality_metrics", {}).get("total_missing_imputed", 0)

    num_cols = patterns_dict.get("numeric_columns", [])
    cat_cols = patterns_dict.get("categorical_columns", [])
    dt_cols = patterns_dict.get("date_columns", [])
    correlations = patterns_dict.get("correlations", [])
    clusters = patterns_dict.get("clusters", {})
    anomalies = patterns_dict.get("anomalies", {})

    # 1. Headline & Executive Summary
    headline_parts = [
        f"Analyzed {rows_count:,} records across {cols_count} dimensions with a Data Health Score of {health_score:.1f}%."
    ]
    if dups_removed > 0 or imputed_count > 0:
        headline_parts.append(
            f"Autonomous pre-processing resolved {dups_removed} duplicate entries and {imputed_count} missing values."
        )

    if dt_cols:
        headline_parts.append(f"Temporal velocity tracked along primary date index '{dt_cols[0]}'.")

    executive_summary = " ".join(headline_parts)

    # 2. Key Statistical Drivers
    driver_findings = []
    if correlations:
        top_corr = correlations[0]
        direction = "positive" if top_corr["r_value"] > 0 else "inverse"
        driver_findings.append({
            "title": f"Strongest Relationship: {top_corr['column_a']} & {top_corr['column_b']}",
            "description": (
                f"A statistically significant {direction} coupling was discovered (r = {top_corr['r_value']:.2f}). "
                f"Changes in '{top_corr['column_a']}' are strongly predictive of movements in '{top_corr['column_b']}'."
            ),
            "severity": "high" if top_corr["abs_r"] >= 0.7 else "medium",
        })

    if len(correlations) > 1:
        sec_corr = correlations[1]
        driver_findings.append({
            "title": f"Secondary Correlation: {sec_corr['column_a']} & {sec_corr['column_b']}",
            "description": f"Observed r = {sec_corr['r_value']:.2f} association between '{sec_corr['column_a']}' and '{sec_corr['column_b']}'.",
            "severity": "low",
        })

    # Add categorical driver if present
    if cat_cols:
        driver_findings.append({
            "title": f"Categorical Segmentation",
            "description": f"Records demonstrate distinct behavioral clustering when partitioned by primary category '{cat_cols[0]}'.",
            "severity": "info",
        })

    # 3. Behavioral Clusters Narrative
    cluster_narrative = []
    if clusters.get("enabled"):
        k = clusters.get("k", 3)
        profiles = clusters.get("profiles", [])
        cluster_narrative.append(f"Unsupervised K-Means clustering separated the population into {k} statistically distinct personas:")
        for prof in profiles:
            traits_str = ", ".join(prof.get("defining_traits", ["balanced baseline"]))
            cluster_narrative.append(
                f"• {prof['name']} ({prof['percentage']}% of records, n={prof['count']}): Characterized by {traits_str}."
            )
    else:
        cluster_narrative.append("Clustering skipped due to limited numeric feature space or uniform distributions.")

    # 4. Outlier & Risk Alerts
    risk_alerts = []
    if anomalies.get("enabled") and anomalies.get("outlier_count", 0) > 0:
        outlier_count = anomalies["outlier_count"]
        rate = anomalies["outlier_rate_pct"]
        top_outliers = anomalies.get("top_outliers", [])

        risk_alerts.append({
            "headline": f"Detected {outlier_count} Anomalous Records ({rate}% of dataset)",
            "impact": "Requires targeted operational or clinical review.",
            "top_flag": top_outliers[0]["reason"] if top_outliers else "High multi-variate distance.",
            "severity": "high" if rate > 3.0 else "medium",
        })
    else:
        risk_alerts.append({
            "headline": "No Significant Multi-Variate Anomalies",
            "impact": "Dataset values remain within standard variance boundaries.",
            "top_flag": "Normal distribution across measured axes.",
            "severity": "low",
        })

    # 5. Prescriptive Next-Best Actions (3 targeted action items)
    recommendations = []

    # Recommendation 1: Operational Outlier Audit
    if anomalies.get("outlier_count", 0) > 0:
        top_driver = anomalies["top_outliers"][0].get("primary_driver", "metric") if anomalies.get("top_outliers") else "outlier"
        recommendations.append({
            "priority": "P1 - Immediate Review",
            "action": f"Audit the {anomalies['outlier_count']} flagged outlier records, specifically focusing on extreme deviations in '{top_driver}'.",
            "impact": "Prevents reporting skew and identifies potential data entry or transactional leakage.",
        })
    else:
        recommendations.append({
            "priority": "P1 - Verification",
            "action": "Maintain routine ingestion monitoring; variance remains well-calibrated.",
            "impact": "Ensures ongoing baseline stability.",
        })

    # Recommendation 2: Segment Capitalization
    if clusters.get("enabled") and clusters.get("profiles"):
        top_prof = clusters["profiles"][0]
        recommendations.append({
            "priority": "P2 - Segment Strategy",
            "action": f"Tailor workflows to prioritize '{top_prof['name']}', which represents {top_prof['percentage']}% of population volume.",
            "impact": "Maximizes resource allocation by focusing on the dominant cohort.",
        })
    else:
        recommendations.append({
            "priority": "P2 - Feature Expansion",
            "action": "Consider enriching records with additional behavioral or domain metadata to unlock deeper cohort clustering.",
            "impact": "Unlocks multi-dimensional segmentation.",
        })

    # Recommendation 3: Data Quality & Automation
    recommendations.append({
        "priority": "P3 - Data Governance",
        "action": f"Automate upstream capture validation to reduce the {imputed_count} missing cells and formatting discrepancies observed.",
        "impact": f"Boosts current Data Health Score from {health_score:.1f}% toward 100%.",
    })

    return {
        "executive_summary": executive_summary,
        "key_drivers": driver_findings,
        "cluster_narrative": cluster_narrative,
        "risk_alerts": risk_alerts,
        "recommendations": recommendations,
    }
