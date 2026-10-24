"""
TrendPulse Analytics & Diagnostics sub-package.

Modular analytics & diagnostic capabilities that extend the base insight engine
with descriptive and diagnostic intelligence (L2 & L3) for the clothing business domain.

Modules
-------
period_comparison     : Period-over-period business metric comparisons.
customer              : Customer-level analytics (RFM, retention, segmentation).
product_affinity      : Product co-purchase / basket analysis.
time_aggregation      : Weekly and monthly time-series aggregation.
revenue_decomposition : Price-Volume-Mix (PVM) variance decomposition.
drivers               : Performance driver attribution & Pareto concentration.
anomaly_diagnostics   : Anomaly root-cause investigation & forecasting guidance.
"""

from data_engine.analytics.period_comparison import analyze_period_over_period
from data_engine.analytics.customer import analyze_customers
from data_engine.analytics.product_affinity import analyze_product_affinity
from data_engine.analytics.time_aggregation import aggregate_time_series
from data_engine.analytics.revenue_decomposition import decompose_revenue
from data_engine.analytics.drivers import analyze_performance_drivers
from data_engine.analytics.anomaly_diagnostics import diagnose_anomalies


__all__ = [
    "analyze_period_over_period",
    "analyze_customers",
    "analyze_product_affinity",
    "aggregate_time_series",
    "decompose_revenue",
    "analyze_performance_drivers",
    "diagnose_anomalies",
]
