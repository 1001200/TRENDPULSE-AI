"""
AutoAnalyst: Zero-Shot Automated Insight & Dashboard Engine.
"""

from data_engine.auto_analyst.pipeline import AutoAnalystEngine, load_dataframe_safely
from data_engine.auto_analyst.type_inferrer import infer_column_types
from data_engine.auto_analyst.smart_cleaner import clean_dataset
from data_engine.auto_analyst.pattern_miner import mine_patterns
from data_engine.auto_analyst.chart_synthesizer import synthesize_dashboard
from data_engine.auto_analyst.narrative_engine import generate_executive_narrative

__all__ = [
    "AutoAnalystEngine",
    "load_dataframe_safely",
    "infer_column_types",
    "clean_dataset",
    "mine_patterns",
    "synthesize_dashboard",
    "generate_executive_narrative",
]
