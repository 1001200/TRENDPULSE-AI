from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.db.session import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String(64), unique=True, index=True)
    product_name = Column(String(255), nullable=False)
    category = Column(String(100), default="Uncategorized", index=True)
    brand = Column(String(100), default="Vintage / Independent")
    aesthetic = Column(String(100), default="Classic", index=True)  # e.g., Y2K, Grunge, Minimalist, 90s Vintage
    size = Column(String(50), default="Free Size")
    condition = Column(String(50), default="Gently Used")  # Like New, Vintage Worn, Gently Used
    cost_price = Column(Float, default=0.0)  # COGS / Wholesale sourcing price
    retail_price = Column(Float, default=0.0)  # Selling price
    source_file = Column(String(255), default="")  # Which upload file created this record
    source_row_idx = Column(Integer, default=0)  # Row index within the source file
    tags = Column(JSON, default=list)  # Freeform tags for flexible categorization
    date_sourced = Column(DateTime, nullable=True)  # When the item was sourced/thrifted
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    sales = relationship("SaleOrder", back_populates="product", cascade="all, delete-orphan")
    inventory = relationship("InventoryItem", back_populates="product", uselist=False, cascade="all, delete-orphan")
    inquiries = relationship("CustomerInquiry", back_populates="product", cascade="all, delete-orphan")


class SaleOrder(Base):
    __tablename__ = "sale_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(64), index=True)
    product_id = Column(String(64), ForeignKey("products.product_id"), nullable=False)
    sale_date = Column(DateTime, default=datetime.utcnow, index=True)
    quantity = Column(Integer, default=1)
    selling_price = Column(Float, nullable=False)
    discount_amount = Column(Float, default=0.0)
    channel = Column(String(50), default="Instagram DM")  # Instagram DM, Story Drop, Shopify, Pop-up
    customer_identifier = Column(String(100), default="Anonymous Buyer")
    inquiry_type = Column(String(50), default="DM")  # DM, comment, story_reply, link_click
    sale_status = Column(String(50), default="completed")  # completed, returned, cancelled
    notes = Column(Text, default="")

    product = relationship("Product", back_populates="sales")


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String(64), ForeignKey("products.product_id"), unique=True, nullable=False)
    quantity_on_hand = Column(Integer, default=1)
    date_stocked = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="Available")  # Available, Reserved, Sold, Deadstock (>45 days)
    location = Column(String(100), default="")  # e.g., "Shelf A", "Storage Bin 3"

    product = relationship("Product", back_populates="inventory")

    @property
    def days_on_hand(self):
        """Compute how many days this item has been in inventory."""
        if self.date_stocked:
            return (datetime.utcnow() - self.date_stocked).days
        return 0


class ContentItem(Base):
    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(String(64), unique=True, index=True)
    platform = Column(String(50), default="Instagram")
    content_type = Column(String(50), default="Reel")  # Reel, Post, Story
    content_url = Column(String(500), default="")
    content_caption = Column(Text, default="")
    hashtags = Column(JSON, default=list)  # List of hashtag strings
    posted_at = Column(DateTime, default=datetime.utcnow)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    saves = Column(Integer, default=0)  # Critical high-intent demand proxy
    shares = Column(Integer, default=0)
    linked_product_ids = Column(JSON, default=list)  # List of product_id strings featured in this video
    product_tags_count = Column(Integer, default=0)  # How many products tagged in this content


class CustomerInquiry(Base):
    """
    Tracks interest-without-purchase: DMs asking about items, saves, comments.
    Feeds Q1 (What are people looking for?) and Q4 (Why are they not buying?).
    """
    __tablename__ = "customer_inquiries"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String(64), ForeignKey("products.product_id"), nullable=True)
    inquiry_date = Column(DateTime, default=datetime.utcnow, index=True)
    inquiry_type = Column(String(50), default="DM")  # "DM", "Comment", "Story Reply", "Save"
    customer_identifier = Column(String(100), default="Anonymous")
    outcome = Column(String(50), default="unknown")  # "purchased", "ghosted", "price_objection", "size_unavailable", "no_response"
    notes = Column(Text, default="")

    product = relationship("Product", back_populates="inquiries")


class DataQualityLog(Base):
    __tablename__ = "data_quality_logs"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(64), unique=True, index=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    source_name = Column(String(255), default="Manual Upload")
    total_rows = Column(Integer, default=0)
    valid_rows = Column(Integer, default=0)
    flagged_rows = Column(Integer, default=0)
    skipped_rows = Column(Integer, default=0)
    mutations_count = Column(Integer, default=0)
    info_count = Column(Integer, default=0)
    warning_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    quality_score = Column(Float, default=100.0)  # 0.0 - 100.0%
    audit_trail_json = Column(JSON, default=list)  # Cell-by-cell audit mutation ledger
    cleaning_rules_applied = Column(JSON, default=list)  # List of rule names used during cleaning


class BusinessProfile(Base):
    """
    Stores authenticated clothing business account details.
    Eliminates fabricated personal identities in favor of dynamic store identity.
    """
    __tablename__ = "business_profiles"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(String(64), unique=True, index=True, default="default_business")
    business_name = Column(String(255), default="Studio Atelier")
    instagram_handle = Column(String(100), default="@studio.atelier")
    account_type = Column(String(50), default="Business Account")
    currency = Column(String(50), default="₹ INR (Indian Rupee)")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

