"""
TrendPulse Fashion Economics & Inventory Intelligence.
"""

from data_engine.economics.margins import analyze_unit_economics
from data_engine.economics.inventory_health import analyze_inventory_health

__all__ = [
    "analyze_unit_economics",
    "analyze_inventory_health",
]
