from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core import models
from src.core.database import Base
from src.features.carton import print_attempts, slot_lifecycle


def make_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return engine, sessionmaker(autocommit=False, autoflush=False, bind=engine)()


def seed_carton_group(db):
    customer = models.Customer(code="CUST", name="Customer")
    db.add(customer)
    db.flush()
    product = models.Product(
        customer_id=customer.id,
        item_name="Product",
        packed_qty=2,
        start_part="CN",
        middle_part="52",
        allow_partial=0,
    )
    db.add(product)
    db.flush()
    original = models.Carton(
        product_id=product.id,
        carton_sn="CN26065200001",
        job_order="JO-001",
        status="SUCCESS",
        is_reprint=0,
    )
    reprint = models.Carton(
        product_id=product.id,
        carton_sn="CN26065200001",
        job_order="JO-001",
        status="PRINTED",
        is_reprint=1,
    )
    other_job_order = models.Carton(
        product_id=product.id,
        carton_sn="CN26065200001",
        job_order="JO-OTHER",
        status="SUCCESS",
        is_reprint=0,
    )
    db.add_all([original, reprint, other_job_order])
    db.flush()
    db.add_all([
        models.CartonItem(carton_id=original.id, item_sn="ITEM-1"),
        models.CartonItem(carton_id=original.id, item_sn="ITEM-2"),
        models.CartonItem(carton_id=reprint.id, item_sn="REPRINT-ITEM"),
    ])
    slot = models.JobOrderCartonSlot(
        job_order=original.job_order,
        product_id=product.id,
        carton_number=1,
        carton_sn=original.carton_sn,
        status="PENDING",
    )
    db.add(slot)
    db.commit()
    return original, reprint, other_job_order, slot


def test_print_attempts_resolves_original_carton_items_for_reprint():
    engine, db = make_db()
    try:
        original, reprint, other_job_order, _slot = seed_carton_group(db)

        item_sns = print_attempts.item_sns_for_attempt(db, reprint)
        attempts = print_attempts.get_carton_attempts(db, reprint)

        assert item_sns == ["ITEM-1", "ITEM-2"]
        assert {attempt.id for attempt in attempts} == {original.id, reprint.id}
        assert other_job_order.id not in {attempt.id for attempt in attempts}
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_print_attempts_successful_reprint_status_follows_original_carton():
    engine, db = make_db()
    try:
        original, reprint, _other_job_order, _slot = seed_carton_group(db)

        assert print_attempts.successful_print_status(db, reprint) == "SUCCESS"

        original.status = "PRINTED"
        db.commit()

        assert print_attempts.successful_print_status(db, reprint) == "PRINTED"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_slot_lifecycle_success_links_reprint_to_original_carton():
    engine, db = make_db()
    try:
        original, reprint, _other_job_order, slot = seed_carton_group(db)

        slot_lifecycle.complete_slot_for_success(db, reprint)
        db.commit()
        db.refresh(slot)

        assert slot.status == "SCANNED"
        assert slot.carton_id == original.id
        assert slot.scanned_at is not None
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_slot_lifecycle_failed_reprint_does_not_release_original_slot():
    engine, db = make_db()
    try:
        original, reprint, _other_job_order, slot = seed_carton_group(db)
        slot.status = "SCANNED"
        slot.carton_id = original.id
        db.commit()

        slot_lifecycle.release_slot_for_failed_original(db, reprint)
        db.commit()
        db.refresh(slot)

        assert slot.status == "SCANNED"
        assert slot.carton_id == original.id
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_slot_lifecycle_release_slots_reopens_original_carton_slot():
    engine, db = make_db()
    try:
        _original, _reprint, _other_job_order, slot = seed_carton_group(db)
        slot.status = "SCANNED"
        slot.carton_id = 1
        db.commit()

        slot_lifecycle.release_slots([slot])
        db.commit()
        db.refresh(slot)

        assert slot.status == "PENDING"
        assert slot.carton_id is None
        assert slot.scanned_at is None
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
