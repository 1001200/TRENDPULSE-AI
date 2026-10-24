"""
TrendPulse ML Feature Store — Centralized Feature Engineering.

Consumes the enriched DataFrame from ``processor.py`` and generates
leakage-safe, reusable feature matrices for all ML models.

Feature groups:
    TIME       — day_of_week, week_of_year, month, quarter, season, trend
    SALES      — velocity, rolling windows, growth rate, acceleration, CoV
    PRODUCT    — category, size, color, margin, discount, sell-through, WOS
    CUSTOMER   — recency, frequency, monetary, AOV, purchase interval
    INVENTORY  — current stock, DOI, WOS, stockout flags
    SOCIAL     — aesthetic class, velocity score, drop speed
    ECONOMIC   — COGS, gross margin, profitability quadrant

Design rules:
    - Deterministic; zero side-effects on input DataFrame.
    - Leakage-safe: all temporal features respect ``as_of_date``.
    - Every feature function is independently testable.
    - Returns typed FeatureSet with metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


# ─────────────────────────────────────────────────────────────────────
# Feature Set Container
# ─────────────────────────────────────────────────────────────────────

@dataclass
class FeatureSet:
    """Container for an engineered feature matrix with metadata."""
    features: pd.DataFrame
    feature_names: List[str]
    generation_timestamp: str = ""
    data_range: Optional[Dict[str, str]] = None
    n_samples: int = 0
    n_features: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.generation_timestamp:
            self.generation_timestamp = datetime.now(timezone.utc).isoformat()
        self.n_samples = len(self.features)
        self.n_features = len(self.feature_names)


# ─────────────────────────────────────────────────────────────────────
# Feature Engineer
# ─────────────────────────────────────────────────────────────────────

class FeatureEngineer:
    """
    Centralized feature generation that consumes the enriched DataFrame
    from the TrendPulse data engine and produces ML-ready feature matrices.

    Usage::

        fe = FeatureEngineer(enriched_df)
        sku_features = fe.build_sku_features()
        time_series  = fe.build_time_series_features(freq="W")
        customer_features = fe.build_customer_features()
    """

    def __init__(self, df: pd.DataFrame, *, as_of_date: Optional[pd.Timestamp] = None):
        """
        Parameters
        ----------
        df : pd.DataFrame
            The enriched DataFrame from ``processor.py`` (after cleaning,
            validation, and apparel enrichment).
        as_of_date : pd.Timestamp, optional
            Cutoff date for leakage prevention.  Features are computed
            using only rows with ``date <= as_of_date``.  If None, all
            data is used (appropriate for training, NOT for future prediction).
        """
        self._raw = df.copy()
        self._df = self._prepare(self._raw, as_of_date)
        self._as_of_date = as_of_date

    # ── Internal prep ─────────────────────────────────────────────

    @staticmethod
    def _prepare(df: pd.DataFrame, as_of_date: Optional[pd.Timestamp] = None) -> pd.DataFrame:
        """Parse dates, ensure numerics, apply leakage cutoff."""
        data = df.copy()

        # Parse date
        if "date" in data.columns:
            data["_date"] = pd.to_datetime(data["date"], errors="coerce")
        else:
            data["_date"] = pd.NaT

        # Apply leakage cutoff
        if as_of_date is not None and data["_date"].notna().any():
            data = data[data["_date"] <= as_of_date].copy()

        # Ensure numeric columns
        for col in ["quantity", "price", "revenue", "cost_price", "stock", "discount"]:
            if col in data.columns:
                data[f"_{col}"] = pd.to_numeric(data[col], errors="coerce").fillna(0.0)
            else:
                data[f"_{col}"] = 0.0

        # Compute revenue if missing
        if data["_revenue"].sum() == 0 and data["_quantity"].sum() > 0:
            data["_revenue"] = data["_quantity"] * data["_price"]

        # Product identifier
        if "product" in data.columns:
            data["_product"] = data["product"].astype(str).str.strip()
        else:
            data["_product"] = "unknown"

        # Category
        if "category" in data.columns:
            data["_category"] = data["category"].astype(str).str.strip()
        else:
            data["_category"] = "unknown"

        # Size
        if "size" in data.columns:
            data["_size"] = data["size"].astype(str).str.strip().str.upper()
        else:
            data["_size"] = "ONE_SIZE"

        return data

    # ── Time Features ─────────────────────────────────────────────

    def _time_features_for_row(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add per-row temporal features."""
        out = df.copy()
        dates = out["_date"]
        out["day_of_week"] = dates.dt.dayofweek.fillna(0).astype(int)
        out["week_of_year"] = dates.dt.isocalendar().week.astype(int) if dates.notna().any() else 1
        out["month"] = dates.dt.month.fillna(1).astype(int)
        out["quarter"] = dates.dt.quarter.fillna(1).astype(int)
        out["is_weekend"] = (out["day_of_week"] >= 5).astype(int)

        # Season mapping (Northern Hemisphere fashion calendar)
        out["season"] = out["month"].map(
            {1: 0, 2: 0, 3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 3, 11: 3, 12: 0}
        ).fillna(0).astype(int)

        # Days since first sale in dataset
        if dates.notna().any():
            min_date = dates.min()
            out["days_since_start"] = (dates - min_date).dt.days.fillna(0).astype(int)
        else:
            out["days_since_start"] = 0

        return out

    # ── SKU-Level Features ────────────────────────────────────────

    def build_sku_features(self) -> FeatureSet:
        """
        Build one row per SKU (product × size) with aggregated features.

        Features include:
            - total_units, total_revenue, avg_selling_price
            - velocity (units/week), velocity_trend (acceleration)
            - active_weeks, recency_days
            - coefficient_of_variation
            - revenue_share (% of total catalog revenue)
            - margin_pct, avg_discount
            - size_fragmentation_score
        """
        df = self._df.copy()

        if df.empty or df["_date"].isna().all():
            return FeatureSet(features=pd.DataFrame(), feature_names=[], metadata={"status": "no_data"})

        # Group key
        df["_sku"] = df["_product"] + " | " + df["_size"]

        total_rev = df["_revenue"].sum()
        date_range = (df["_date"].max() - df["_date"].min()).days
        total_weeks = max(date_range / 7, 1)

        sku_groups = df.groupby("_sku", sort=False)

        records: List[Dict[str, Any]] = []
        for sku, grp in sku_groups:
            # Basic aggregates
            units = float(grp["_quantity"].sum())
            rev = float(grp["_revenue"].sum())
            avg_price = float(rev / units) if units > 0 else 0.0

            # Time-aware features
            dates = grp["_date"].dropna()
            if dates.empty:
                continue

            first_sale = dates.min()
            last_sale = dates.max()
            active_days = (last_sale - first_sale).days + 1
            active_weeks = max(active_days / 7, 1)
            recency_days = (df["_date"].max() - last_sale).days
            catalog_days = (df["_date"].max() - first_sale).days + 1
            catalog_weeks = max(catalog_days / 7, 1)

            # Velocity (over catalog lifespan so dormant items have true low velocity)
            velocity = units / catalog_weeks
            n_selling_weeks = grp.set_index("_date").resample("W")["_quantity"].sum()
            n_selling_weeks = n_selling_weeks[n_selling_weeks > 0]
            num_active_weeks = len(n_selling_weeks)

            # Velocity trend (acceleration): compare recent half vs earlier half
            if len(n_selling_weeks) >= 4:
                mid = len(n_selling_weeks) // 2
                early_vel = float(n_selling_weeks.iloc[:mid].mean())
                late_vel = float(n_selling_weeks.iloc[mid:].mean())
                velocity_trend = (late_vel - early_vel) / max(early_vel, 0.01)
            else:
                velocity_trend = 0.0

            # Coefficient of variation
            weekly_units = grp.set_index("_date").resample("W")["_quantity"].sum()
            cv = float(weekly_units.std() / weekly_units.mean()) if weekly_units.mean() > 0 else 0.0

            # Revenue share
            rev_share = (rev / total_rev * 100) if total_rev > 0 else 0.0

            # Margin
            cost = float(grp["_cost_price"].sum())
            margin_pct = ((rev - cost) / rev * 100) if rev > 0 and cost > 0 else 0.0

            # Average discount
            avg_discount = float(grp["_discount"].mean())

            # Category / product / size
            product = str(grp["_product"].iloc[0])
            category = str(grp["_category"].iloc[0])
            size = str(grp["_size"].iloc[0])

            records.append({
                "sku": sku,
                "product": product,
                "category": category,
                "size": size,
                "total_units": round(units, 2),
                "total_revenue": round(rev, 2),
                "avg_selling_price": round(avg_price, 2),
                "velocity_units_per_week": round(velocity, 4),
                "velocity_trend": round(velocity_trend, 4),
                "active_weeks": round(active_weeks, 1),
                "num_selling_weeks": num_active_weeks,
                "recency_days": recency_days,
                "coefficient_of_variation": round(cv, 4),
                "revenue_share_pct": round(rev_share, 4),
                "margin_pct": round(margin_pct, 2),
                "avg_discount": round(avg_discount, 2),
                "days_since_first_sale": active_days,
            })

        result_df = pd.DataFrame(records)
        if result_df.empty:
            return FeatureSet(features=result_df, feature_names=[], metadata={"status": "no_data"})

        # Size fragmentation: per product, how many sizes are actively selling?
        if "product" in result_df.columns:
            product_size_counts = result_df.groupby("product")["size"].nunique()
            result_df["size_count"] = result_df["product"].map(product_size_counts).fillna(1).astype(int)
            total_possible_sizes = df["_size"].nunique()
            result_df["size_fragmentation"] = round(
                result_df["size_count"] / max(total_possible_sizes, 1), 4
            )
        else:
            result_df["size_count"] = 1
            result_df["size_fragmentation"] = 1.0

        feature_cols = [
            "total_units", "total_revenue", "avg_selling_price",
            "velocity_units_per_week", "velocity_trend", "active_weeks",
            "num_selling_weeks", "recency_days", "coefficient_of_variation",
            "revenue_share_pct", "margin_pct", "avg_discount",
            "days_since_first_sale", "size_count", "size_fragmentation",
        ]

        # Data range
        data_range = {
            "start": df["_date"].min().isoformat() if df["_date"].notna().any() else "",
            "end": df["_date"].max().isoformat() if df["_date"].notna().any() else "",
        }

        return FeatureSet(
            features=result_df,
            feature_names=feature_cols,
            data_range=data_range,
        )

    # ── Time-Series Features ──────────────────────────────────────

    def build_time_series_features(
        self,
        *,
        group_col: str = "_product",
        freq: str = "W",
    ) -> FeatureSet:
        """
        Build time-series feature matrix for forecasting.

        Returns one row per (group × period) with rolling features,
        trend slopes, and seasonal indicators.

        Parameters
        ----------
        group_col : str
            Column to group by (``"_product"``, ``"_sku"``, ``"_category"``).
        freq : str
            Resampling frequency (``"W"`` for weekly, ``"D"`` for daily).
        """
        df = self._df.copy()

        if df.empty or df["_date"].isna().all():
            return FeatureSet(features=pd.DataFrame(), feature_names=[], metadata={"status": "no_data"})

        # Ensure _sku exists
        if group_col == "_sku" and "_sku" not in df.columns:
            df["_sku"] = df["_product"] + " | " + df["_size"]

        records: List[Dict[str, Any]] = []

        for group_key, grp in df.groupby(group_col, sort=False):
            # Resample to time periods
            ts = (
                grp.set_index("_date")
                .resample(freq)
                .agg({"_quantity": "sum", "_revenue": "sum", "_price": "mean"})
                .fillna(0)
            )

            if len(ts) < 2:
                continue

            # Rolling features
            ts["rolling_4w_qty"] = ts["_quantity"].rolling(4, min_periods=1).mean()
            ts["rolling_4w_rev"] = ts["_revenue"].rolling(4, min_periods=1).mean()
            ts["ewm_qty"] = ts["_quantity"].ewm(span=4, min_periods=1).mean()

            # Growth rate (period-over-period)
            ts["qty_pct_change"] = ts["_quantity"].pct_change().fillna(0).clip(-5, 5)

            # Acceleration (change of change)
            ts["qty_acceleration"] = ts["qty_pct_change"].diff().fillna(0).clip(-5, 5)

            # Trend slope (linear regression over last 8 periods)
            window = min(8, len(ts))
            x = np.arange(window, dtype=float)
            y = ts["_quantity"].values[-window:]
            if len(y) >= 2 and np.std(y) > 0:
                slope = float(np.polyfit(x, y, 1)[0])
            else:
                slope = 0.0

            # Add temporal features for each row
            for i, (idx, row) in enumerate(ts.iterrows()):
                rec = {
                    "group": str(group_key),
                    "period": idx.isoformat() if hasattr(idx, "isoformat") else str(idx),
                    "period_index": i,
                    "quantity": float(row["_quantity"]),
                    "revenue": float(row["_revenue"]),
                    "avg_price": float(row["_price"]),
                    "rolling_4w_qty": float(row["rolling_4w_qty"]),
                    "rolling_4w_rev": float(row["rolling_4w_rev"]),
                    "ewm_qty": float(row["ewm_qty"]),
                    "qty_pct_change": float(row["qty_pct_change"]),
                    "qty_acceleration": float(row["qty_acceleration"]),
                    "trend_slope": round(slope, 6),
                }

                # Seasonal indicators from period
                if hasattr(idx, "month"):
                    rec["month"] = idx.month
                    rec["quarter"] = idx.quarter
                    rec["week_of_year"] = idx.isocalendar()[1]
                else:
                    rec["month"] = 0
                    rec["quarter"] = 0
                    rec["week_of_year"] = 0

                records.append(rec)

        result_df = pd.DataFrame(records)

        feature_cols = [
            "period_index", "quantity", "revenue", "avg_price",
            "rolling_4w_qty", "rolling_4w_rev", "ewm_qty",
            "qty_pct_change", "qty_acceleration", "trend_slope",
            "month", "quarter", "week_of_year",
        ]

        data_range = {
            "start": df["_date"].min().isoformat() if df["_date"].notna().any() else "",
            "end": df["_date"].max().isoformat() if df["_date"].notna().any() else "",
        }

        return FeatureSet(
            features=result_df,
            feature_names=feature_cols,
            data_range=data_range,
        )

    # ── Customer Features ─────────────────────────────────────────

    def build_customer_features(self) -> FeatureSet:
        """
        Build one row per customer with behavioral features.

        Features: recency, frequency, monetary, AOV, purchase_interval,
        category_diversity, size_consistency, days_as_customer.
        """
        df = self._df.copy()

        if df.empty or "customer_id" not in df.columns:
            return FeatureSet(features=pd.DataFrame(), feature_names=[], metadata={"status": "no_customer_data"})

        df["_cust"] = df["customer_id"].astype(str).str.strip()
        df = df[~df["_cust"].isin(["", "nan", "None", "null"])]

        if df.empty:
            return FeatureSet(features=pd.DataFrame(), feature_names=[], metadata={"status": "no_valid_customers"})

        max_date = df["_date"].max()
        records: List[Dict[str, Any]] = []

        for cust_id, grp in df.groupby("_cust", sort=False):
            dates = grp["_date"].dropna().sort_values()
            if dates.empty:
                continue

            # RFM
            recency = (max_date - dates.max()).days
            frequency = len(dates.unique())
            monetary = float(grp["_revenue"].sum())
            aov = monetary / frequency if frequency > 0 else 0.0

            # Purchase intervals
            unique_dates = dates.drop_duplicates().sort_values()
            if len(unique_dates) >= 2:
                intervals = unique_dates.diff().dropna().dt.days
                interval_mean = float(intervals.mean())
                interval_std = float(intervals.std()) if len(intervals) > 1 else 0.0
            else:
                interval_mean = 0.0
                interval_std = 0.0

            # Category diversity
            cat_diversity = grp["_category"].nunique()

            # Size consistency (does customer always buy the same size?)
            sizes = grp["_size"].dropna()
            size_consistency = 1.0 if sizes.nunique() <= 1 else round(1.0 / sizes.nunique(), 4)

            # Customer tenure
            days_as_customer = (dates.max() - dates.min()).days

            records.append({
                "customer_id": str(cust_id),
                "recency_days": recency,
                "frequency": frequency,
                "monetary": round(monetary, 2),
                "avg_order_value": round(aov, 2),
                "purchase_interval_mean": round(interval_mean, 2),
                "purchase_interval_std": round(interval_std, 2),
                "category_diversity": cat_diversity,
                "size_consistency": size_consistency,
                "days_as_customer": days_as_customer,
            })

        result_df = pd.DataFrame(records)

        feature_cols = [
            "recency_days", "frequency", "monetary", "avg_order_value",
            "purchase_interval_mean", "purchase_interval_std",
            "category_diversity", "size_consistency", "days_as_customer",
        ]

        return FeatureSet(
            features=result_df,
            feature_names=feature_cols,
        )

    # ── Size Ratio Features ──────────────────────────────────────

    def build_size_ratios(self) -> Dict[str, Dict[str, float]]:
        """
        Compute observed size distribution ratios per product.

        Returns dict like ``{"Black Tee": {"S": 0.15, "M": 0.35, ...}}``.
        Used by the demand forecaster to allocate aggregate forecasts
        down to individual sizes.
        """
        df = self._df.copy()
        if df.empty:
            return {}

        ratios: Dict[str, Dict[str, float]] = {}
        for product, grp in df.groupby("_product", sort=False):
            size_units = grp.groupby("_size")["_quantity"].sum()
            total = size_units.sum()
            if total > 0:
                ratios[str(product)] = {
                    str(size): round(float(units / total), 4)
                    for size, units in size_units.items()
                }
        return ratios
