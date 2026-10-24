"""
TrendPulse Social Curation & Viral Fashion Intelligence.
"""

from data_engine.social_curation.aesthetics import (
    classify_aesthetic,
    analyze_aesthetic_velocity,
    AESTHETIC_RULES,
)
from data_engine.social_curation.drop_velocity import analyze_drop_velocity
from data_engine.social_curation.thrift_sourcing import generate_sourcing_recommendations
from data_engine.social_curation.social_attribution import analyze_social_attribution

__all__ = [
    "classify_aesthetic",
    "analyze_aesthetic_velocity",
    "AESTHETIC_RULES",
    "analyze_drop_velocity",
    "generate_sourcing_recommendations",
    "analyze_social_attribution",
]
