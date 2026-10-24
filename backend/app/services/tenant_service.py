"""
TrendPulse Strict Authorization & Tenant Data Isolation Service.

Enforces server-side authorization and prevents horizontal privilege escalation (IDOR).
Guarantees that a merchant can NEVER access or manipulate another merchant's brand,
datasets, store, drops, items, or customer orders.
"""

from __future__ import annotations

import logging
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.models import User, Store, Drop, DropItem, Order, Dataset

logger = logging.getLogger("trendpulse.security.tenant")


def get_user_dataset(
    db: Session,
    dataset_id: int,
    current_user: User,
) -> Dataset:
    """
    Retrieve dataset strictly verifying ownership.
    Rejects any cross-account data access attempt.
    """
    query = db.query(Dataset).filter(Dataset.id == dataset_id)

    if current_user.role == "admin":
        dataset = query.first()
    elif current_user.organization_id:
        dataset = query.filter(Dataset.organization_id == current_user.organization_id).first()
    else:
        dataset = query.filter(Dataset.user_id == current_user.id).first()

    if not dataset:
        logger.warning(
            f"SECURITY: Unauthorized dataset access attempt. User {current_user.id} ({current_user.email}) "
            f"attempted to access dataset {dataset_id} belonging to another tenant."
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID {dataset_id} not found or access denied.",
        )
    return dataset


def get_user_store(
    db: Session,
    current_user: User,
) -> Store:
    """
    Retrieve store strictly owned by the authenticated user.
    Never falls back to other users' stores.
    """
    store = db.query(Store).filter(Store.user_id == current_user.id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store profile not found. Please complete store onboarding at /setup.",
        )
    return store


def get_user_drop(
    db: Session,
    drop_id: int,
    current_user: User,
) -> Drop:
    """
    Retrieve drop strictly belonging to authenticated user's store.
    """
    store = get_user_store(db, current_user)
    drop = db.query(Drop).filter(Drop.id == drop_id, Drop.store_id == store.id).first()
    if not drop:
        logger.warning(
            f"SECURITY: Unauthorized drop access attempt. User {current_user.id} "
            f"attempted to access drop {drop_id} not owned by their store {store.id}."
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drop with ID {drop_id} not found or access denied.",
        )
    return drop


def get_user_order(
    db: Session,
    order_id: int,
    current_user: User,
) -> Order:
    """
    Retrieve order strictly belonging to authenticated user's drops.
    """
    store = get_user_store(db, current_user)
    order = (
        db.query(Order)
        .join(Drop, Order.drop_id == Drop.id)
        .filter(Order.id == order_id, Drop.store_id == store.id)
        .first()
    )
    if not order:
        logger.warning(
            f"SECURITY: Unauthorized order access attempt. User {current_user.id} "
            f"attempted to access order {order_id}."
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found or access denied.",
        )
    return order
