from dataclasses import dataclass
from typing import Optional


@dataclass
class SalesRecord:
    """
    Standard format for one clothing business sales record.

    Required fields
    ---------------
    date, product, category, quantity, price

    Optional fields
    ---------------
    customer_id, order_id, discount — original V4 fields
    size, color, subcategory, sku    — clothing-domain fields
    cost_price, stock, revenue       — extended analytics fields
    """

    date: str
    product: str
    category: str
    quantity: float
    price: float

    # Original optional fields
    customer_id: Optional[str] = None
    order_id: Optional[str] = None
    discount: float = 0.0

    # Clothing-domain fields
    size: Optional[str] = None
    color: Optional[str] = None
    subcategory: Optional[str] = None
    sku: Optional[str] = None

    # Extended analytics fields
    cost_price: Optional[float] = None
    stock: Optional[float] = None
    revenue: Optional[float] = None