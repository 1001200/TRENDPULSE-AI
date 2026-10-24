"""
Unified Pipeline Orchestrator for AutoAnalyst.

Coordinates Type Inference, Reversible Cleaning, Statistical & ML Mining,
Visual Grammar Chart Synthesis, and Executive Briefing into a single frictionless pipeline.
"""

from __future__ import annotations

import io
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union
import pandas as pd

from data_engine.auto_analyst.chart_synthesizer import synthesize_dashboard
from data_engine.auto_analyst.narrative_engine import generate_executive_narrative
from data_engine.auto_analyst.pattern_miner import mine_patterns
from data_engine.auto_analyst.smart_cleaner import clean_dataset
from data_engine.auto_analyst.type_inferrer import infer_column_types


def load_dataframe_safely(file_source: Union[str, Path, bytes, io.BytesIO]) -> Tuple[pd.DataFrame, str]:
    """
    Load any spreadsheet-style file safely with delimiter and encoding sniffing.
    """
    if isinstance(file_source, (str, Path)):
        p = Path(file_source)
        ext = p.suffix.lower()
        if ext in [".xlsx", ".xls"]:
            return pd.read_excel(p), p.name
        
        # Sniff encoding and separator for text/csv
        for enc in ["utf-8", "latin-1", "cp1252"]:
            try:
                # Try standard comma
                return pd.read_csv(p, encoding=enc, sep=None, engine="python"), p.name
            except Exception:
                continue
        # Fallback
        return pd.read_csv(p, encoding="utf-8", errors="replace"), p.name

    elif isinstance(file_source, bytes):
        bio = io.BytesIO(file_source)
        try:
            return pd.read_excel(bio), "uploaded_file.xlsx"
        except Exception:
            bio.seek(0)
            for enc in ["utf-8", "latin-1", "cp1252"]:
                try:
                    return pd.read_csv(bio, encoding=enc, sep=None, engine="python"), "uploaded_file.csv"
                except Exception:
                    bio.seek(0)
            return pd.read_csv(bio, encoding="utf-8", errors="replace"), "uploaded_file.csv"

    elif isinstance(file_source, io.BytesIO):
        try:
            return pd.read_excel(file_source), "uploaded_file.xlsx"
        except Exception:
            file_source.seek(0)
            return pd.read_csv(file_source, sep=None, engine="python"), "uploaded_file.csv"

    raise ValueError("Unsupported file source type")


class AutoAnalystEngine:
    def __init__(self):
        pass

    def run(
        self,
        source: Union[str, Path, bytes, io.BytesIO, pd.DataFrame],
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute the full autonomous intelligence pipeline.
        Returns a complete, JSON-serializable intelligence payload.
        """
        start_time = time.time()

        # 1. Ingestion
        if isinstance(source, pd.DataFrame):
            raw_df = source.copy()
            fname = filename or "in_memory_dataset.csv"
        else:
            raw_df, detected_name = load_dataframe_safely(source)
            fname = filename or detected_name

        raw_rows = len(raw_df)
        raw_cols = len(raw_df.columns)

        # 2. Stage 1: Zero-Shot Type Inference
        schema = infer_column_types(raw_df)

        # 3. Stage 2: Smart Reversible Cleaning & Audit
        clean_result = clean_dataset(raw_df, schema)
        cleaned_df = clean_result.cleaned_df
        clean_dict = clean_result.to_dict()

        # 4. Stage 3: ML & Pattern Mining
        pattern_result = mine_patterns(cleaned_df, clean_result.schema)
        patterns_dict = pattern_result.to_dict()

        # 5. Stage 4: Adaptive Chart Synthesis
        top_corr = patterns_dict["correlations"][0] if patterns_dict["correlations"] else None
        dashboard = synthesize_dashboard(
            df=cleaned_df,
            num_cols=pattern_result.numeric_columns,
            cat_cols=pattern_result.categorical_columns,
            dt_cols=pattern_result.date_columns,
            top_correlation=top_corr,
        )

        # 6. Stage 5: Plain-Language Executive Narrative
        narrative = generate_executive_narrative(
            clean_result_dict=clean_dict,
            patterns_dict=patterns_dict,
            kpis=dashboard["kpi_cards"],
        )

        elapsed_ms = int((time.time() - start_time) * 1000)

        # 7. Sample records for UI Data Explorer
        sample_records = []
        preview_df = cleaned_df.head(50)
        # Convert any timestamps to ISO string for JSON serialization
        for _, row in preview_df.iterrows():
            rec = {}
            for col in preview_df.columns:
                val = row[col]
                if pd.isna(val):
                    rec[col] = None
                elif hasattr(val, "strftime"):
                    rec[col] = val.strftime("%Y-%m-%d %H:%M")
                elif isinstance(val, (int, float, bool, str)):
                    rec[col] = val
                else:
                    rec[col] = str(val)
            sample_records.append(rec)

        # Complete Enterprise Payload
        return {
            "metadata": {
                "filename": fname,
                "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "rows_raw": raw_rows,
                "rows_cleaned": len(cleaned_df),
                "columns_count": len(cleaned_df.columns),
                "processing_time_ms": elapsed_ms,
            },
            "schema": clean_result.schema,
            "quality": clean_dict,
            "dashboard": dashboard,
            "patterns": patterns_dict,
            "narrative": narrative,
            "sample_data": sample_records,
            "_cleaned_df": cleaned_df,  # kept for internal export
        }
