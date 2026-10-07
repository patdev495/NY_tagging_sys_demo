import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Index,
    String,
    UnicodeText,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    products: Mapped[list["Product"]] = relationship("Product", back_populates="customer")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("customers.id"), index=True, nullable=True)
    item_name: Mapped[str | None] = mapped_column(String(200), index=True, nullable=True)
    upc: Mapped[str | None] = mapped_column(String(50), nullable=True)
    packed_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_part: Mapped[str | None] = mapped_column(String(10), nullable=True)  # E.g., CN (Carton Number)
    middle_part: Mapped[str | None] = mapped_column(String(20), nullable=True)  # e.g. 11, 16, A, B
    template_type: Mapped[str | None] = mapped_column(String(50), default="standard", nullable=True)  # "standard" | "detailed" | "erro_01" ... "erro_03"
    template_path: Mapped[str | None] = mapped_column(String(500), nullable=True)  # E.g. D:\PAT\Template\carton.btw
    allow_partial: Mapped[int | None] = mapped_column(Integer, default=0, nullable=True)  # 0 = must be full | 1 = can be partial

    # Erro Customer & weight-scale additions
    packing_mode: Mapped[str | None] = mapped_column(String(50), default="item_scan", nullable=True)  # "item_scan" | "weight_scale"
    target_weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_unit: Mapped[str | None] = mapped_column(String(10), default="kg", nullable=True)
    mfr_pn: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g. NYS5998
    pkg_prefix: Mapped[str | None] = mapped_column(String(20), nullable=True)  # e.g. VHK0010237 hoặc 37033907
    revision: Mapped[str | None] = mapped_column(String(10), default="B", nullable=True)
    asin: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Amazon ASIN (B08G9M4HXS...)
    product_desc: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Mô tả cáp đầy đủ trên tem 2
    customer_project: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Erro 03 customer project printed on Luxshare label
    production_stage: Mapped[str | None] = mapped_column(String(20), nullable=True)  # Erro 03 production stage printed on Luxshare label
    luxshare_part_number: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Erro 03 Luxshare material number printed as LuxsharePartNo
    internal_factory_part_number: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Legacy Factory P/N reference
    factory_item_code: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Source ITEM code for Erro 04 catalog rows
    carton_id_prefix: Mapped[str | None] = mapped_column(String(1), nullable=True)  # Erro 04 Carton ID prefix: H (CAT6A) or K (CAT5E)

    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="products")
    cartons: Mapped[list["Carton"]] = relationship("Carton", back_populates="product")
    internal_factory_part_numbers: Mapped[list["ProductInternalFactoryPartNumber"]] = relationship(
        "ProductInternalFactoryPartNumber",
        back_populates="product",
        cascade="all, delete-orphan",
    )


class ProductInternalFactoryPartNumber(Base):
    __tablename__ = "product_internal_factory_part_numbers"
    __table_args__ = (
        UniqueConstraint("customer_id", "internal_factory_part_number", name="uq_pifpn_customer_part_no"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    internal_factory_part_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_drawing_code: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, default=datetime.datetime.now, nullable=True)
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, nullable=True)

    product: Mapped["Product"] = relationship("Product", back_populates="internal_factory_part_numbers")
    customer: Mapped["Customer"] = relationship("Customer")


class Carton(Base):
    __tablename__ = "cartons"
    __allow_unmapped__ = True

    # Transient runtime fields attached for API responses
    items_count: int = 0
    reprint_count: int = 0
    print_history: list["Carton"] = []

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("products.id"), index=True, nullable=True)
    carton_sn: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)  # Removed unique=True to allow print attempt logs
    created_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, default=datetime.datetime.now, index=True, nullable=True)
    packed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    job_order: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[str | None] = mapped_column(String(20), default="FAILED", index=True, nullable=True)  # SUCCESS or FAILED
    btxml: Mapped[str | None] = mapped_column(UnicodeText, nullable=True)  # Stores original print data
    is_reprint: Mapped[int | None] = mapped_column(Integer, default=0, nullable=True)  # 0 for Original, 1 for Reprint
    carton_origin: Mapped[str | None] = mapped_column(String(50), default="VN", nullable=True)  # Origin country, e.g. CN (China) or VN (Vietnam)
    station_id: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Station ID derived from MAC address

    # Erro weight-scale additions
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    po_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lot_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    date_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    admin_creation_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    product: Mapped[Optional["Product"]] = relationship("Product", back_populates="cartons")
    items: Mapped[list["CartonItem"]] = relationship("CartonItem", back_populates="carton")


class CartonItem(Base):
    __tablename__ = "carton_items"
    __table_args__ = (Index("ix_carton_items_item_sn_carton_id", "item_sn", "carton_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    carton_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("cartons.id"), index=True, nullable=True)
    item_sn: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)

    carton: Mapped[Optional["Carton"]] = relationship("Carton", back_populates="items")


class UIItemSNClaim(Base):
    """Database-level ownership reservation for a UI Item SN."""
    __tablename__ = "ui_item_sn_claims"

    item_sn: Mapped[str] = mapped_column(String(100), primary_key=True)
    carton_id: Mapped[int] = mapped_column(Integer, ForeignKey("cartons.id"), nullable=False, index=True)


class JobOrderCartonSlot(Base):
    __tablename__ = "job_order_carton_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_order: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), index=True, nullable=False)
    carton_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, ..., N
    carton_sn: Mapped[str] = mapped_column(String(100), index=True, unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True, nullable=False)  # PENDING or SCANNED
    scanned_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    carton_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("cartons.id"), index=True, nullable=True)
    shipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))

    product: Mapped[Optional["Product"]] = relationship("Product")
    carton: Mapped[Optional["Carton"]] = relationship("Carton")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="qa")  # "admin" | "qa"
    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[int | None] = mapped_column(Integer, default=1, nullable=True)
    created_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, default=datetime.datetime.now, nullable=True)
