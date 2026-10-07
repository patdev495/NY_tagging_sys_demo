from datetime import datetime

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.database import seed_erro_data
from src.core.models import Base, Carton, Product
from src.features.carton import schemas as carton_schemas
from src.features.carton import service as carton_service
from src.features.product.service import get_next_sn


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def test_erro_05_get_next_sn_endpoint(db_session):
    seed_erro_data(db_session)
    db_session.commit()

    p = (
        db_session.query(Product)
        .filter(Product.template_type == "erro_05")
        .first()
    )
    assert p is not None

    sn_info = get_next_sn(p.id, db_session)
    assert sn_info["next_seq"] == 50001
    now = datetime.now()
    expected_prefix = f"{p.pkg_prefix}2{now.strftime('%y')}{now.isocalendar()[1]:02d}50001"
    assert sn_info["next_sn"] == expected_prefix


def test_erro_05_weigh_pack_empty_po_and_batch(db_session):
    seed_erro_data(db_session)
    db_session.commit()

    p = (
        db_session.query(Product)
        .filter(Product.factory_item_code == "1HWU3023C1XX02NN9")
        .first()
    )
    assert p is not None
    assert p.packing_mode == "weight_scale"

    # Weigh pack with empty PO and empty Batch (bypass modal)
    req = carton_schemas.CartonWeighPackCreate(
        product_id=p.id,
        weight=5.0,
        po_number="",
        lot_number="",
        printer_name="ZDesigner",
    )
    carton, btxml = carton_service.weigh_pack_carton(req, db_session)
    now = datetime.now()
    yyww = f"{now.strftime('%y')}{now.isocalendar()[1]:02d}"
    lot_ymd = now.strftime("%Y%m%d")

    assert carton.carton_sn.startswith("MC220TW12")
    assert carton.carton_sn.endswith("50001")
    assert carton.date_code == yyww
    assert carton.lot_number == lot_ymd

    # Verify saved carton in DB
    saved_carton = db_session.query(Carton).filter(Carton.carton_sn == carton.carton_sn).first()
    assert saved_carton is not None
    assert saved_carton.weight == 5.0
    assert saved_carton.po_number is None or saved_carton.po_number == ""


def test_erro_05_weigh_pack_monotonic_sequence(db_session):
    seed_erro_data(db_session)
    db_session.commit()

    p1 = db_session.query(Product).filter(Product.factory_item_code == "1CAU0002M2WH07NX9").first()
    p2 = db_session.query(Product).filter(Product.factory_item_code == "1HWU3023C1XX02NN9").first()

    # Pack carton 1 with product 1
    req1 = carton_schemas.CartonWeighPackCreate(product_id=p1.id, weight=5.0)
    c1, _ = carton_service.weigh_pack_carton(req1, db_session)
    assert c1.carton_sn.endswith("50001")

    # Pack carton 2 with product 2 (shared sequence across erro_05 products)
    req2 = carton_schemas.CartonWeighPackCreate(product_id=p2.id, weight=5.0)
    c2, _ = carton_service.weigh_pack_carton(req2, db_session)
    assert c2.carton_sn.endswith("50002")

    # Pack carton 3 with product 1 again
    req3 = carton_schemas.CartonWeighPackCreate(product_id=p1.id, weight=5.0)
    c3, _ = carton_service.weigh_pack_carton(req3, db_session)
    assert c3.carton_sn.endswith("50003")


def test_erro_05_weigh_pack_weight_tolerance_rejection(db_session):
    seed_erro_data(db_session)
    db_session.commit()

    p = db_session.query(Product).filter(Product.template_type == "erro_05").first()
    p.min_weight = 4.5
    p.max_weight = 5.5
    p.target_weight = 5.0
    db_session.commit()

    # Underweight
    with pytest.raises(HTTPException) as exc_under:
        carton_service.weigh_pack_carton(
            carton_schemas.CartonWeighPackCreate(product_id=p.id, weight=4.0),
            db_session,
        )
    assert exc_under.value.status_code == 400

    # Overweight
    with pytest.raises(HTTPException) as exc_over:
        carton_service.weigh_pack_carton(
            carton_schemas.CartonWeighPackCreate(product_id=p.id, weight=6.0),
            db_session,
        )
    assert exc_over.value.status_code == 400
