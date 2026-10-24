"""
TrendPulse end-to-end data intelligence processor.

This is the integration boundary used by the backend. Every downstream
module receives the same cleaned canonical DataFrame and the result contains
raw evidence, audit information, statistical evidence, profiling and
business intelligence.

No stage silently mutates the caller's DataFrame.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from data_engine.mapper import apply_column_mapping
from data_engine.cleaner import clean_data_with_audit, clean_data
from data_engine.validator import validate_data
from data_engine.anomaly_detector import detect_anomalies
from data_engine.profiler import profile_data
from data_engine.report import create_quality_report
from data_engine.insight_engine import generate_insights_report
from data_engine.llm_layer import analyze_dataset, openai_client_from_environment
from data_engine.trust_score import calculate_trust_score
from data_engine.analytics import (
    analyze_period_over_period,
    analyze_customers,
    analyze_product_affinity,
    aggregate_time_series,
    decompose_revenue,
    analyze_performance_drivers,
    diagnose_anomalies,
)
from data_engine.apparel import (
    enrich_apparel_data,
    analyze_apparel_domain,
)
from data_engine.social_curation import (
    analyze_aesthetic_velocity,
    analyze_drop_velocity,
    generate_sourcing_recommendations,
    analyze_social_attribution,
)
from data_engine.economics import (
    analyze_unit_economics,
    analyze_inventory_health,
)
from data_engine.ml import run_ml_intelligence


PROCESSOR_VERSION = "5.0"


def load_file(file_path) -> pd.DataFrame:
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension == ".csv":
        return pd.read_csv(path)
    if extension in {".xlsx", ".xls"}:
        return pd.read_excel(path)

    raise ValueError(
        "Unsupported file type. Only CSV and Excel files are supported."
    )


def _json_safe(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return str(value)


def process_dataframe(
    df: pd.DataFrame,
    *,
    llm_client=None,
    enable_llm: bool = True,
) -> dict:
    """Run the complete pipeline on an already-loaded DataFrame."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("process_dataframe expects a pandas DataFrame.")

    source = df.copy(deep=True)
    rows_received = len(source)

    mapped_df, mapping, unmatched, mapping_details, mapping_conflicts = (
        apply_column_mapping(source)
    )

    cleaned_df, cleaning_audit, cleaning_summary = clean_data_with_audit(
        mapped_df
    )

    # Apparel Domain Enrichment (Size, Color, Gender, Fit, Fabric, Category)
    enriched_df, apparel_audit, apparel_summary = enrich_apparel_data(cleaned_df)

    validation = validate_data(enriched_df)

    anomaly_result = detect_anomalies(enriched_df)
    anomalies = anomaly_result["anomalies"]
    anomaly_summary = anomaly_result["summary"]

    profiler = profile_data(enriched_df)

    trust_score = calculate_trust_score(
        enriched_df,
        validation=validation,
        anomaly_summary=anomaly_summary,
    )

    quality_report = create_quality_report(
        validation,
        rows_received,
        anomaly_summary,
    )

    insight_report = generate_insights_report(
        enriched_df,
        anomaly_summary=anomaly_summary,
        profiler=profiler,
        anomalies=anomalies,
    )

    # Phase 2 Descriptive Intelligence layers
    period_comparison = analyze_period_over_period(enriched_df)
    customer_analytics = analyze_customers(enriched_df)
    product_affinity = analyze_product_affinity(enriched_df)
    time_aggregation = aggregate_time_series(enriched_df)

    # Phase 3 Diagnostic Intelligence layers
    revenue_decomposition = decompose_revenue(enriched_df)
    performance_drivers = analyze_performance_drivers(enriched_df)
    anomaly_diagnostics = diagnose_anomalies(
        enriched_df,
        anomalies=anomalies,
        anomaly_summary=anomaly_summary,
    )

    # Apparel Domain Intelligence (Size Curves, Colorways, Broken Runs, Fits)
    apparel_intelligence = analyze_apparel_domain(enriched_df)

    # Social-First & Curation Intelligence (Aesthetic Velocity, Drop Speed, Thrift Sourcing, Attribution)
    social_curation = {
        "aesthetic_velocity": analyze_aesthetic_velocity(enriched_df),
        "drop_velocity": analyze_drop_velocity(enriched_df),
        "sourcing_recommendations": generate_sourcing_recommendations(enriched_df),
        "social_attribution": analyze_social_attribution(enriched_df),
    }

    # Fashion Unit Economics & Inventory Health (Margins, Discount Bleed, STR, WOS)
    fashion_economics = {
        "unit_economics": analyze_unit_economics(enriched_df),
        "inventory_health": analyze_inventory_health(enriched_df),
    }

    # Phase 4: ML Predictive Intelligence (Demand Forecast, Lifecycle, Stockout)
    try:
        ml_intelligence = run_ml_intelligence(
            enriched_df,
            horizon_days=30,
            include_sizes=True,
        )
    except Exception as exc:
        ml_intelligence = {
            "status": "ml_pipeline_error",
            "error": str(exc),
            "demand_forecast": [],
            "product_lifecycle": [],
            "stockout_predictions": [],
            "model_registry": {"total_models": 0, "models": []},
        }

    llm_analysis = None
    if enable_llm:
        if llm_client is None:
            llm_client = openai_client_from_environment()
        llm_analysis = analyze_dataset(
            profile=profiler,
            anomalies=anomaly_result,
            mapping={
                "mapping": mapping,
                "unmatched_columns": unmatched,
                "mapping_details": mapping_details,
                "mapping_conflicts": mapping_conflicts,
            },
            client=llm_client,
        )

    result = {
        "version": PROCESSOR_VERSION,
        "status": "success",
        "rows_received": rows_received,
        "rows_after_cleaning": len(cleaned_df),
        "column_mapping": mapping,
        "mapping_details": mapping_details,
        "mapping_conflicts": mapping_conflicts,
        "unmatched_columns": unmatched,
        "cleaning_summary": cleaning_summary,
        "cleaning_audit": cleaning_audit,
        "apparel_enrichment_summary": apparel_summary,
        "apparel_audit": apparel_audit,
        "validation": validation,
        "anomalies": anomalies,
        "anomaly_summary": anomaly_summary,
        "profiler": profiler,
        "quality_report": quality_report,
        "trust_score": trust_score,
        "insights": insight_report,
        "period_comparison": period_comparison,
        "customer_analytics": customer_analytics,
        "product_affinity": product_affinity,
        "time_aggregation": time_aggregation,
        "revenue_decomposition": revenue_decomposition,
        "performance_drivers": performance_drivers,
        "anomaly_diagnostics": anomaly_diagnostics,
        "apparel_intelligence": apparel_intelligence,
        "social_curation": social_curation,
        "fashion_economics": fashion_economics,
        "ml_intelligence": ml_intelligence,
        "llm_analysis": llm_analysis,
        # Keep the DataFrame for Python callers. API layers should serialize it.
        "processed_data": enriched_df,
    }

    return result


def process_file(
    file_path,
    *,
    llm_client=None,
    enable_llm: bool = True,
) -> dict:
    return process_dataframe(
        load_file(file_path),
        llm_client=llm_client,
        enable_llm=enable_llm,
    )


def result_to_json_safe(result: dict) -> dict:
    """Convert a processor result into a JSON-safe representation."""
    output = dict(result)
    frame = output.pop("processed_data", None)
    if isinstance(frame, pd.DataFrame):
        output["processed_data"] = frame.where(frame.notna(), None).to_dict(
            orient="records"
        )
    return _json_safe(output)


def process_file_json(
    file_path,
    *,
    llm_client=None,
    enable_llm: bool = True,
) -> dict:
    return result_to_json_safe(
        process_file(
            file_path,
            llm_client=llm_client,
            enable_llm=enable_llm,
        )
    )


__all__ = [
    "load_file",
    "process_dataframe",
    "process_file",
    "process_file_json",
    "result_to_json_safe",
]
