
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core import models
from src.core.database import Base
from src.features.job_order import service
from src.features.print import schemas as print_schemas
from src.features.print import service as print_service
from src.features.product import service as product_service

# Create in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # Create tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop tables
        Base.metadata.drop_all(bind=engine)

def test_find_matching_product(db_session):
    # Setup customer and products
    customer = models.Customer(id=1, code="UI", name="UI Customer")
    db_session.add(customer)
    
    prod1 = models.Product(
        id=1,
        customer_id=1,
        item_name="UACC-Cable-Path-Outdoor-2M-BK",
        upc="810010077400",
        packed_qty=50,
        start_part="CN",
        middle_part="52",
        template_type="standard",
        allow_partial=0
    )
    prod2 = models.Product(
        id=2,
        customer_id=1,
        item_name="U-Cable-Patch-RJ45",
        upc="810010075765",
        packed_qty=100,
        start_part="CN",
        middle_part="9",
        template_type="standard",
        allow_partial=0
    )
    db_session.add_all([prod1, prod2])
    db_session.commit()

    # Test exact match
    p = service.find_matching_product(db_session, "U-Cable-Patch-RJ45", "123")
    assert p is not None
    assert p.id == 2

    # Test case insensitive
    p = service.find_matching_product(db_session, "u-cable-patch-rj45", "123")
    assert p is not None
    assert p.id == 2

    # Test Patch to Path typo mapping
    p = service.find_matching_product(db_session, "UACC-Cable-Patch-Outdoor-2M-BK", "1CAD2420D2BK01NX9")
    assert p is not None
    assert p.id == 1

    # Test Path to Patch typo mapping
    p = service.find_matching_product(db_session, "U-Cable-Path-RJ45", "123")
    assert p is not None
    assert p.id == 2

    # Test None handling (prevents AttributeError: 'NoneType' object has no attribute 'lower')
    assert service.find_matching_product(db_session, None, None) is None
    assert service.find_matching_product(db_session, "", None) is None
    assert service.find_matching_product(db_session, None, "UNKNOWN_CODE") is None


def test_get_last_carton_for_job_order_does_not_resume_a_different_job_order(db_session):
    customer = models.Customer(code="UI", name="UI Customer")
    db_session.add(customer)
    db_session.flush()
    product = models.Product(
        customer_id=customer.id,
        item_name="U-Cable-Patch-Outdoor-2M-W",
        upc="810010077356",
        packed_qty=20,
        start_part="CN",
        middle_part="52",
        template_type="standard",
        allow_partial=0,
    )
    db_session.add(product)
    db_session.flush()

    resume_carton = models.Carton(
        product_id=product.id,
        carton_sn="CN26095200001",
        job_order="JO-CURRENT",
        status="PRINTED",
    )
    unrelated_newer_carton = models.Carton(
        product_id=product.id,
        carton_sn="CN26095200002",
        job_order="JO-OTHER",
        status="PRINTED",
    )
    db_session.add_all([resume_carton, unrelated_newer_carton])
    db_session.commit()

    carton = product_service.get_last_carton(product.id, db_session, job_order="JO-CURRENT")

    assert carton is not None
    assert carton.id == resume_carton.id


def test_get_last_carton_for_job_order_ignores_newer_reprints(db_session):
    customer = models.Customer(code="UI", name="UI Customer")
    db_session.add(customer)
    db_session.flush()
    product = models.Product(
        customer_id=customer.id,
        item_name="U-Cable-Patch-Outdoor-2M-W",
        packed_qty=20,
    )
    db_session.add(product)
    db_session.flush()

    original = models.Carton(
        product_id=product.id,
        carton_sn="CN26095200001",
        job_order="WO-CURRENT",
        status="SUCCESS",
        is_reprint=0,
    )
    newer_reprint = models.Carton(
        product_id=product.id,
        carton_sn="CN26095200001",
        job_order="WO-CURRENT",
        status="SUCCESS",
        is_reprint=1,
    )
    db_session.add_all([original, newer_reprint])
    db_session.commit()

    carton = product_service.get_last_carton(product.id, db_session, job_order="WO-CURRENT")

    assert carton is not None
    assert carton.id == original.id

def test_get_or_create_job_order_slots(db_session):
    # Setup product
    customer = models.Customer(id=1, code="UI", name="UI Customer")
    db_session.add(customer)
    
    product = models.Product(
        id=1,
        customer_id=1,
        item_name="UACC-Cable-Path-Outdoor-2M-BK",
        upc="810010077400",
        packed_qty=50,
        start_part="CN",
        middle_part="52",
        template_type="standard",
        allow_partial=0
    )
    db_session.add(product)
    db_session.commit()

    # Call service (mock ERP will return 15 * 50 = 750 qty => 15 cartons)
    res = service.get_or_create_job_order_slots(db_session, "1232225")
    
    assert res.job_order == "1232225"
    assert res.total_cartons == 15
    assert len(res.slots) == 15
    
    # Check slots saved in DB
    slots_in_db = db_session.query(models.JobOrderCartonSlot).filter_by(job_order="1232225").all()
    assert len(slots_in_db) == 15
    assert slots_in_db[0].carton_number == 1
    assert slots_in_db[14].carton_number == 15
    assert slots_in_db[0].status == "PENDING"
    
    # Check Carton SN generation sequentiality
    sn0 = slots_in_db[0].carton_sn
    sn1 = slots_in_db[1].carton_sn
    assert int(sn1[-5:]) == int(sn0[-5:]) + 1


def test_get_job_order_details_rejects_erro_without_allocating_slots(db_session):
    """Erro uses the weighing flow and must never receive Job Order Carton Slots."""
    customer = models.Customer(code="ERRO", name="Erro")
    db_session.add(customer)
    db_session.flush()
    product = models.Product(
        customer_id=customer.id,
        item_name="840-00092",
        upc="000000000001",
        packed_qty=190,
        packing_mode="weight_scale",
        template_type="erro_01",
    )
    db_session.add(product)
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        service.get_or_create_job_order_slots(db_session, "ERRO-WO-001")

    assert getattr(exc_info.value, "status_code", None) == 400
    assert "ERRO" in str(exc_info.value.detail)
    assert db_session.query(models.JobOrderCartonSlot).filter_by(job_order="ERRO-WO-001").count() == 0

def test_sequence_generator_collision_avoidance(db_session):
    # Setup product
    customer = models.Customer(id=1, code="UI", name="UI Customer")
    db_session.add(customer)
    
    product = models.Product(
        id=1,
        customer_id=1,
        item_name="UACC-Cable-Path-Outdoor-2M-BK",
        upc="810010077400",
        packed_qty=50,
        start_part="CN",
        middle_part="52",
        template_type="standard",
        allow_partial=0
    )
    db_session.add(product)
    db_session.commit()

    import datetime
    yymm = datetime.datetime.now().strftime("%y%m")
    prefix = f"CN{yymm}52"
    
    # 1. Simulate an existing Carton in DB with SN ...00010
    carton = models.Carton(
        product_id=1,
        carton_sn=f"{prefix}00010",
        status="SUCCESS",
        job_order="OTHER_JO"
    )
    db_session.add(carton)
    db_session.commit()
    
    # 2. Call service for new Job Order slots. It should start at ...00011
    res1 = service.get_or_create_job_order_slots(db_session, "JO-NEW-1")
    assert res1.slots[0].carton_sn == f"{prefix}00011"
    assert res1.slots[14].carton_sn == f"{prefix}00025" # 15 cartons
    
    # 3. Call service for another new Job Order. It should start at ...00026 (based on slots table max)
    res2 = service.get_or_create_job_order_slots(db_session, "JO-NEW-2")
    assert res2.slots[0].carton_sn == f"{prefix}00026"

def test_update_status_updates_slot(db_session):
    # Setup product and slot
    customer = models.Customer(id=1, code="UI", name="UI Customer")
    db_session.add(customer)
    
    product = models.Product(
        id=1,
        customer_id=1,
        item_name="UACC-Cable-Path-Outdoor-2M-BK",
        upc="810010077400",
        packed_qty=50,
        start_part="CN",
        middle_part="52",
        template_type="standard",
        allow_partial=0
    )
    db_session.add(product)
    db_session.commit()
    
    import datetime
    yymm = datetime.datetime.now().strftime("%y%m")
    carton_sn = f"CN{yymm}5200001"
    
    slot = models.JobOrderCartonSlot(
        job_order="1232225",
        product_id=1,
        carton_number=1,
        carton_sn=carton_sn,
        status="PENDING"
    )
    carton = models.Carton(
        id=10,
        product_id=1,
        carton_sn=carton_sn,
        status="PRINTED",
        job_order="1232225"
    )
    db_session.add_all([slot, carton])
    db_session.commit()

    # Call update_status to SUCCESS
    status_update = print_schemas.CartonStatusUpdate(status="SUCCESS")
    print_service.update_status(10, status_update, db_session)

    # Verify slot is updated to SCANNED
    db_session.refresh(slot)
    assert slot.status == "SCANNED"
    assert slot.carton_id == 10
    assert slot.scanned_at is not None

def test_multiple_job_orders_allocation_order(db_session):
    # Setup product
    customer = models.Customer(id=1, code="UI", name="UI Customer")
    db_session.add(customer)
    
    product = models.Product(
        id=1,
        customer_id=1,
        item_name="UACC-Cable-Path-Outdoor-2M-BK",
        upc="810010077400",
        packed_qty=50,
        start_part="CN",
        middle_part="52",
        template_type="standard",
        allow_partial=0
    )
    db_session.add(product)
    db_session.commit()

    import datetime
    yymm = datetime.datetime.now().strftime("%y%m")
    prefix = f"CN{yymm}52"

    # 1. First Job Order (JO-1) is entered first. It should get slots starting at 00001
    res1 = service.get_or_create_job_order_slots(db_session, "JO-1")
    assert res1.slots[0].carton_sn == f"{prefix}00001"
    assert res1.slots[-1].carton_sn == f"{prefix}00015"  # 15 cartons
 
    # 2. Second Job Order (JO-2) is entered second. It should get slots starting at 00016
    res2 = service.get_or_create_job_order_slots(db_session, "JO-2")
    assert res2.slots[0].carton_sn == f"{prefix}00016"
    assert res2.slots[-1].carton_sn == f"{prefix}00030"  # 15 cartons

    # 3. Query JO-1 again. It should return its original slots (00001 -> 00015), not changing sequence
    res1_retry = service.get_or_create_job_order_slots(db_session, "JO-1")
    assert res1_retry.slots[0].carton_sn == f"{prefix}00001"
    assert res1_retry.slots[-1].carton_sn == f"{prefix}00015"
