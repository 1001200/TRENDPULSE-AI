"""
TrendPulse Apparel & Fashion Domain Intelligence Engine.

Specialized clothing-specific normalization, taxonomy extraction,
and commercial analytics (Size Curves, Colorways, Fits, Fabrics, Broken Runs).

Modules
-------
size_normalizer   : Alpha & numeric size parsing, size curves, broken runs.
color_engine      : 150+ apparel colors mapped to base colors and color families.
taxonomy          : Natural language apparel attribute extraction from titles.
apparel_cleaner   : Auditable dataset enrichment with standard clothing fields.
apparel_analytics : Specialized fashion commercial intelligence reports.
"""

from data_engine.apparel.size_normalizer import (
    normalize_size,
    extract_size_from_title,
    calculate_size_curves,
    detect_broken_size_runs,
)
from data_engine.apparel.color_engine import (
    normalize_color,
    extract_color_from_title,
    analyze_colorways,
)
from data_engine.apparel.taxonomy import (
    extract_apparel_attributes,
)
from data_engine.apparel.apparel_cleaner import (
    enrich_apparel_data,
)
from data_engine.apparel.apparel_analytics import (
    analyze_apparel_domain,
)


__all__ = [
    "normalize_size",
    "extract_size_from_title",
    "calculate_size_curves",
    "detect_broken_size_runs",
    "normalize_color",
    "extract_color_from_title",
    "analyze_colorways",
    "extract_apparel_attributes",
    "enrich_apparel_data",
    "analyze_apparel_domain",
]
