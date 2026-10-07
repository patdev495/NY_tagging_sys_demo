import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.core import models
from src.core.database import Base
from src.features.history import service


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_filter_cartons_by_date_range_inclusive(db_session):
    """Test filtering cartons by start_date and end_date (inclusive of entire days)."""
    customer = models.Customer(code="UI", name="Universal Instruments")
    db_session.add(customer)
    db_session.commit()

    product = models.Product(customer_id=customer.id, item_name="Cable A", packed_qty=10)
    db_session.add(product)
    db_session.commit()

    # Carton 1: 2026-08-31 23:59:00 (outside)
    c1 = models.Carton(
        product_id=product.id, carton_sn="SN-0831", status="SUCCESS",
        created_at=datetime.datetime(2026, 8, 31, 23, 59, 0)
    )
    # Carton 2: 2026-09-01 01:00:00 (inside)
    c2 = models.Carton(
        product_id=product.id, carton_sn="SN-0901", status="SUCCESS",
        created_at=datetime.datetime(2026, 9, 1, 1, 0, 0)
    )
    # Carton 3: 2026-09-02 23:45:00 (inside end_date)
    c3 = models.Carton(
        product_id=product.id, carton_sn="SN-0902", status="SUCCESS",
        created_at=datetime.datetime(2026, 9, 2, 23, 45, 0)
    )
    # Carton 4: 2026-09-03 00:01:00 (outside)
    c4 = models.Carton(
        product_id=product.id, carton_sn="SN-0903", status="SUCCESS",
        created_at=datetime.datetime(2026, 9, 3, 0, 1, 0)
    )
    db_session.add_all([c1, c2, c3, c4])
    db_session.commit()

    result = service.get_cartons(
        db_session,
        start_date="2026-09-01",
        end_date="2026-09-02"
    )

    sns = [item.carton_sn for item in result["items"]]
    assert result["total"] == 2
    assert "SN-0901" in sns
    assert "SN-0902" in sns
    assert "SN-0831" not in sns
    assert "SN-0903" not in sns

def test_filter_cartons_by_customer(db_session):
    """Test filtering cartons by customer_id."""
    c_ui = models.Customer(code="UI", name="Universal Instruments")
    c_a11 = models.Customer(code="A11", name="Customer A11")
    db_session.add_all([c_ui, c_a11])
    db_session.commit()

    p_ui = models.Product(customer_id=c_ui.id, item_name="Product UI", packed_qty=10)
    p_a11 = models.Product(customer_id=c_a11.id, item_name="Product A11", packed_qty=20)
    db_session.add_all([p_ui, p_a11])
    db_session.commit()

    carton_ui = models.Carton(product_id=p_ui.id, carton_sn="SN-UI-01", status="SUCCESS")
    carton_a11 = models.Carton(product_id=p_a11.id, carton_sn="SN-A11-01", status="SUCCESS")
    db_session.add_all([carton_ui, carton_a11])
    db_session.commit()

    result_ui = service.get_cartons(db_session, customer_id=c_ui.id)
    assert result_ui["total"] == 1
    assert result_ui["items"][0].carton_sn == "SN-UI-01"

    result_a11 = service.get_cartons(db_session, customer_id=c_a11.id)
    assert result_a11["total"] == 1
    assert result_a11["items"][0].carton_sn == "SN-A11-01"

def test_filter_cartons_by_job_order_and_po(db_session):
    """Test filtering cartons by job_order and po_number."""
    customer = models.Customer(code="CUST", name="Customer")
    db_session.add(customer)
    db_session.commit()

    product = models.Product(customer_id=customer.id, item_name="Product 1", packed_qty=10)
    db_session.add(product)
    db_session.commit()

    c_jo = models.Carton(product_id=product.id, carton_sn="SN-JO", job_order="JO-9988", status="SUCCESS")
    c_po = models.Carton(product_id=product.id, carton_sn="SN-PO", po_number="PO-4455", status="SUCCESS")
    db_session.add_all([c_jo, c_po])
    db_session.commit()

    # Match by job_order
    res_jo = service.get_cartons(db_session, job_order="9988")
    assert res_jo["total"] == 1
    assert res_jo["items"][0].carton_sn == "SN-JO"

    # Match by po_number
    res_po = service.get_cartons(db_session, po_number="4455")
    assert res_po["total"] == 1
    assert res_po["items"][0].carton_sn == "SN-PO"
