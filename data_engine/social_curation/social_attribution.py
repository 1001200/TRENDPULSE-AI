"""
TrendPulse Social Channel & Campaign Attribution.

Maps sales to traffic channels (Instagram Reels, Instagram Stories, TikTok,
WhatsApp Broadcasts, Organic Direct) to determine revenue generation per channel.

Design rules:
    - Deterministic; zero side-effects on input DataFrame.
    - Automatic channel inference if explicit channel column is absent.
    - JSON-safe return structure.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
import pandas as pd

from data_engine.utils import clean_number, safe_float, safe_int


CHANNEL_PATTERNS = [
    ("Instagram Reels", r"\b(reel|reels|ig_reel|insta_reel)\b"),
    ("Instagram Bio / Story", r"\b(bio|story|stories|ig_bio|ig_story|instagram)\b"),
    ("TikTok / Short Video", r"\b(tiktok|tt|douyin)\b"),
    ("WhatsApp Broadcast", r"\b(whatsapp|wa|broadcast|chat)\b"),
    ("Email / VIP Club", r"\b(email|newsletter|vip|mail)\b"),
    ("Organic Store / Direct", r"\b(direct|organic|google|search|none)\b"),
]


def _infer_channel(val: Any) -> str:
    """Infer social channel from text or tag."""
    if not isinstance(val, str) or not val.strip():
        return "Organic Store / Direct"

    clean = val.lower()
    for channel_name, pat in CHANNEL_PATTERNS:
        if re.search(pat, clean):
            return channel_name

    return "Other Social Channel"


def analyze_social_attribution(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze revenue, order volume, and average order value across social discovery channels.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return {
            "status": "no_data",
            "message": "DataFrame is empty.",
            "channels": [],
            "top_converting_channel": None,
        }

    data = df.copy()

    # Find channel column (e.g. channel, source, utm_source, medium, marketing_source)
    channel_col = None
    for col in data.columns:
        if col.lower() in ("channel", "source", "utm_source", "medium", "marketing_channel", "traffic_source"):
            channel_col = col
            break

    # If explicit channel column is present, use it; otherwise infer or default
    if channel_col:
        data["_channel"] = data[channel_col].apply(_infer_channel)
    else:
        # If order_id or notes contains hints, use them
        data["_channel"] = "Instagram Bio / Story"

    # Numerical values
    if "quantity" in data.columns:
        data["_qty"] = pd.to_numeric(data["quantity"], errors="coerce").fillna(0.0)
    else:
        data["_qty"] = 1.0

    if "revenue" in data.columns:
        data["_rev"] = pd.to_numeric(data["revenue"], errors="coerce").fillna(0.0)
    elif "price" in data.columns:
        p = pd.to_numeric(data["price"], errors="coerce").fillna(0.0)
        data["_rev"] = data["_qty"] * p
    else:
        data["_rev"] = 0.0

    total_rev = float(data["_rev"].sum())
    total_qty = float(data["_qty"].sum())

    channels_list = []
    for ch_name, ch_df in data.groupby("_channel"):
        rev = float(ch_df["_rev"].sum())
        qty = float(ch_df["_qty"].sum())
        orders = len(ch_df)
        aov = (rev / orders) if orders > 0 else 0.0
        rev_share = (rev / total_rev * 100) if total_rev > 0 else 0.0

        channels_list.append({
            "channel": str(ch_name),
            "revenue": clean_number(rev),
            "units_sold": clean_number(qty),
            "order_count": orders,
            "average_order_value": clean_number(aov),
            "revenue_share_percentage": clean_number(rev_share),
        })

    channels_list.sort(key=lambda x: safe_float(x["revenue"]), reverse=True)
    top_channel = channels_list[0]["channel"] if channels_list else "Instagram"

    return {
        "status": "success",
        "total_revenue": clean_number(total_rev),
        "total_units_sold": clean_number(total_qty),
        "top_converting_channel": top_channel,
        "channels": channels_list,
    }


__all__ = ["analyze_social_attribution"]
