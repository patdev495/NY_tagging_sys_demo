from typing import cast

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.models import Base, Carton, Customer, Product
from src.features.print.service import reprint_carton


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def erro_product(db_session):
    customer = Customer(code="ERRO", name="Erro")
    db_session.add(customer)
    db_session.flush()

    product = Product(
        customer_id=customer.id,
        item_name="840-00092",
        packed_qty=190,
        packing_mode="weight_scale",
        target_weight=12.500,
        min_weight=12.300,
        max_weight=12.700,
        weight_unit="kg",
        mfr_pn="NYS5998",
        pkg_prefix="VHK0010237",
        revision="B",
        template_type="erro_01",
        template_path=r"D:\PAT\Template\erro_01.btw",
    )
    db_session.add(product)
    db_session.commit()
    return product


@pytest.fixture
def ui_product(db_session):
    customer = Customer(code="UI", name="Universal Instruments")
    db_session.add(customer)
    db_session.flush()

    product = Product(
        customer_id=customer.id,
        item_name="UACC-Cable",
        packed_qty=20,
        packing_mode="item_scan",
        start_part="CN",
        middle_part="11",
        template_type="standard",
        template_path=r"D:\PAT\Template\carton.btw",
    )
    db_session.add(product)
    db_session.commit()
    return product


def test_reprint_erro_carton_is_allowed_for_admin_workflow(db_session, erro_product):
    """ADR 0009 permits a reprint record for an Erro carton."""
    orig = Carton(
        product_id=erro_product.id,
        carton_sn="VHK00102372608000081",
        weight=12.480,
        po_number="PO-ORIG-100",
        lot_number="LOT-ORIG-200",
        date_code="2634",
        status="SUCCESS",
        carton_origin="VN",
        packed_by="TSC_TTP_244_Pro",
        is_reprint=0,
    )
    db_session.add(orig)
    db_session.commit()

    reprinted = reprint_carton(
        carton_id=cast(int, orig.id),
        printer_name="TSC_TTP_244_Pro",
        db=db_session,
    )

    assert cast(int, reprinted.id) != cast(int, orig.id)
    assert str(reprinted.carton_sn) == "VHK00102372608000081"
    assert cast(int, reprinted.is_reprint) == 1


def test_reprint_ui_carton_still_allowed(db_session, ui_product):
    """
    UI customer retains reprint functionality.
    """
    orig = Carton(
        product_id=ui_product.id,
        carton_sn="CN26081100001",
        job_order="JO-12345",
        status="SUCCESS",
        carton_origin="VN",
        packed_by="TSC_TTP_244_Pro",
        is_reprint=0,
    )
    db_session.add(orig)
    db_session.commit()

    reprinted = reprint_carton(
        carton_id=cast(int, orig.id),
        printer_name="TSC_TTP_244_Pro",
        db=db_session,
    )

    assert cast(int, reprinted.id) != cast(int, orig.id)
    assert str(reprinted.carton_sn) == "CN26081100001"
    assert cast(int, reprinted.is_reprint) == 1


def test_weigh_pack_erro_rejects_custom_sn(db_session, erro_product):
    """
    ADR 0005: Customer Erro strictly forbids manual sequence manipulation.
    Passing custom_sn must be rejected by the API.
    """
    from src.features.carton.schemas import CartonWeighPackCreate
    from src.features.carton.service import weigh_pack_carton

    weigh_in = CartonWeighPackCreate(
        product_id=cast(int, erro_product.id),
        weight=12.500,
        po_number="PO-12345",
        lot_number="LOT-9999",
        custom_sn=99,  # Manual attempt to override sequence
    )

    with pytest.raises(HTTPException) as exc_info:
        weigh_pack_carton(weigh_in, db_session)

    assert exc_info.value.status_code == 400
    assert "thủ công" in exc_info.value.detail or "manual" in exc_info.value.detail.lower() or "ERRO" in exc_info.value.detail


def test_weigh_pack_erro_damaged_label_sop_sequential_increment(db_session, erro_product):
    """
    SOP for Damaged Label:
    If a label is torn/damaged, worker prints the next sequence (F9).
    The system allocates N then N+1 without conflict.
    """
    from src.features.carton.schemas import CartonWeighPackCreate
    from src.features.carton.service import weigh_pack_carton

    weigh_1 = CartonWeighPackCreate(
        product_id=cast(int, erro_product.id),
        weight=12.500,
        po_number="PO-12345",
        lot_number="LOT-9999",
    )
    carton_1, _ = weigh_pack_carton(weigh_1, db_session)

    # Label 1 is damaged physically, worker prints next label:
    weigh_2 = CartonWeighPackCreate(
        product_id=cast(int, erro_product.id),
        weight=12.500,
        po_number="PO-12345",
        lot_number="LOT-9999",
    )
    carton_2, _ = weigh_pack_carton(weigh_2, db_session)

    assert str(carton_1.carton_sn) != str(carton_2.carton_sn)
    seq_1 = int(str(carton_1.carton_sn)[-6:])
    seq_2 = int(str(carton_2.carton_sn)[-6:])
    assert seq_2 == seq_1 + 1

