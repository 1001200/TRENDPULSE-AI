"""
TrendPulse SQLAlchemy Database Models.

Enterprise data models for Users, Multi-tenant Organizations, Datasets,
Trust Score History, Anomaly Logs, and Apparel Intelligence Snapshots.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any, Dict, Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.app.database.connection import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    datasets = relationship("Dataset", back_populates="organization", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="merchant", nullable=False)  # admin, merchant, analyst
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=True, nullable=False)
    onboarding_status = Column(String(30), default="not_started", nullable=False)  # not_started, in_progress, completed
    onboarding_step = Column(Integer, default=1, nullable=False)
    auth_provider = Column(String(50), default="local", nullable=False)  # local, google, apple
    google_sub = Column(String(255), nullable=True, index=True)
    apple_sub = Column(String(255), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    organization = relationship("Organization", back_populates="users")
    datasets = relationship("Dataset", back_populates="user", cascade="all, delete-orphan")
    stores = relationship("Store", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    verification_tokens = relationship("EmailVerificationToken", back_populates="user", cascade="all, delete-orphan")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token_hash = Column(String(255), unique=True, index=True, nullable=False)
    user_agent = Column(String(512), nullable=True)
    ip_address = Column(String(100), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    last_active_at = Column(DateTime, default=utcnow, nullable=False)

    user = relationship("User", back_populates="sessions")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    user = relationship("User", back_populates="reset_tokens")


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    user = relationship("User", back_populates="verification_tokens")


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)

    filename = Column(String(255), nullable=False)
    file_path = Column(String(1024), nullable=False)
    file_size_bytes = Column(Integer, default=0, nullable=False)
    file_extension = Column(String(10), nullable=False)

    # Status: pending, processing, completed, failed
    status = Column(String(50), default="pending", nullable=False, index=True)
    error_message = Column(Text, nullable=True)

    # Processing Metrics
    rows_received = Column(Integer, default=0, nullable=False)
    rows_cleaned = Column(Integer, default=0, nullable=False)
    processing_time_ms = Column(Float, default=0.0, nullable=False)

    created_at = Column(DateTime, default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="datasets")
    organization = relationship("Organization", back_populates="datasets")
    trust_score = relationship("DatasetTrustScore", back_populates="dataset", uselist=False, cascade="all, delete-orphan")
    snapshot = relationship("DatasetSnapshot", back_populates="dataset", uselist=False, cascade="all, delete-orphan")


class DatasetTrustScore(Base):
    __tablename__ = "dataset_trust_scores"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), unique=True, nullable=False)

    composite_score = Column(Float, nullable=False)
    trust_level = Column(String(20), nullable=False)  # high, medium, low
    completeness_score = Column(Float, nullable=False)
    validity_score = Column(Float, nullable=False)
    consistency_score = Column(Float, nullable=False)
    timeliness_score = Column(Float, nullable=False)
    uniqueness_score = Column(Float, nullable=False)
    assessment = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utcnow, nullable=False)

    dataset = relationship("Dataset", back_populates="trust_score")


class DatasetSnapshot(Base):
    __tablename__ = "dataset_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), unique=True, nullable=False)

    # Stores the full JSON payload computed by data_engine.processor
    result_json = Column(Text, nullable=False)

    created_at = Column(DateTime, default=utcnow, nullable=False)

    dataset = relationship("Dataset", back_populates="snapshot")

    def get_result(self) -> Dict[str, Any]:
        """Safely deserialize stored JSON payload."""
        try:
            return json.loads(self.result_json)
        except Exception:
            return {}

    def set_result(self, data: Dict[str, Any]) -> None:
        """Safely serialize JSON payload."""
        self.result_json = json.dumps(data)


class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    instagram_handle = Column(String(100), nullable=False)
    upi_id = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    fulfillment_type = Column(String(20), default="self", nullable=False)  # "self" or "supplier"
    supplier_phone = Column(String(20), nullable=True)
    flat_shipping_fee = Column(Float, default=70.0, nullable=False)
    niche = Column(String(100), default="Curated Vintage Thrift", nullable=True)
    city = Column(String(100), default="Delhi", nullable=True)
    policies = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    user = relationship("User", back_populates="stores")
    drops = relationship("Drop", back_populates="store", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="store", cascade="all, delete-orphan")


class Drop(Base):
    __tablename__ = "drops"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    title = Column(String(255), nullable=False)
    slug = Column(String(100), index=True, nullable=False)
    status = Column(String(20), default="live", nullable=False)  # "draft", "live", "archived"
    created_at = Column(DateTime, default=utcnow, nullable=False)

    store = relationship("Store", back_populates="drops")
    items = relationship("DropItem", back_populates="drop", cascade="all, delete-orphan")


class DropItem(Base):
    __tablename__ = "drop_items"

    id = Column(Integer, primary_key=True, index=True)
    drop_id = Column(Integer, ForeignKey("drops.id"), nullable=False)
    title = Column(String(255), nullable=False)
    aesthetic = Column(String(100), default="Vintage Streetwear", nullable=False)
    category = Column(String(100), default="Apparel", nullable=False)
    size_label = Column(String(50), default="Free Size", nullable=False)
    chest_inches = Column(Float, nullable=True)
    length_inches = Column(Float, nullable=True)
    price_inr = Column(Float, nullable=False)
    condition_score = Column(String(20), default="10/10", nullable=False)
    photo_url = Column(String(1024), nullable=True)
    status = Column(String(20), default="available", nullable=False)  # "available", "reserved", "sold"
    stock_units = Column(Integer, default=1, nullable=False)
    available_units = Column(Integer, default=1, nullable=False)
    reserved_until = Column(DateTime, nullable=True)
    reserved_by_phone = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    drop = relationship("Drop", back_populates="items")
    orders = relationship("Order", back_populates="item", cascade="all, delete-orphan")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("drop_items.id"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    buyer_name = Column(String(255), nullable=False)
    buyer_ig = Column(String(100), nullable=False)
    buyer_phone = Column(String(20), nullable=False)
    address_line = Column(Text, nullable=False)
    pincode = Column(String(6), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    shipping_fee_inr = Column(Float, default=70.0, nullable=False)
    total_amount_inr = Column(Float, nullable=False)
    payment_status = Column(String(30), default="pending_verification", nullable=False)  # "pending_verification", "verified"
    utr_reference = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    item = relationship("DropItem", back_populates="orders")
    store = relationship("Store", back_populates="orders")

