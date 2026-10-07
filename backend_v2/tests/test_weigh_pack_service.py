from typing import cast

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.models import Base, Customer, Product
from src.features.carton import service as carton_service
from src.features.carton.schemas import CartonWeighPackCreate


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def erro_01_product(db_session):
    customer = Customer(code="ERRO", name="Erro")
    db_session.add(customer)
    db_session.flush()

    product = Product(
        customer_id=customer.id,
        item_name="840-00083",
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
        template_path=r"D:\PAT\Template\第1.btw",
    )
    db_session.add(product)
    db_session.commit()
    return product


def test_weigh_pack_rejects_underweight(db_session, erro_01_product):
    payload = CartonWeighPackCreate(
        product_id=cast(int, erro_01_product.id),
        weight=12.100,  # Below min_weight 12.300
        po_number="PO12345",
        lot_number="LOT67890",
        printer_name="TSC_TTP_244_Pro",
    )

    with pytest.raises(HTTPException) as exc_info:
        carton_service.weigh_pack_carton(payload, db_session)
    assert exc_info.value.status_code == 400
    assert "below minimum tolerance" in exc_info.value.detail


def test_weigh_pack_rejects_overweight(db_session, erro_01_product):
    payload = CartonWeighPackCreate(
        product_id=cast(int, erro_01_product.id),
        weight=12.900,  # Above max_weight 12.700
        po_number="PO12345",
        lot_number="LOT67890",
        printer_name="TSC_TTP_244_Pro",
    )

    with pytest.raises(HTTPException) as exc_info:
        carton_service.weigh_pack_carton(payload, db_session)
    assert exc_info.value.status_code == 400
    assert "above maximum tolerance" in exc_info.value.detail


def test_weigh_pack_success(db_session, erro_01_product):
    payload = CartonWeighPackCreate(
        product_id=cast(int, erro_01_product.id),
        weight=12.500,
        po_number="PO-9999",
        lot_number="LOT-8888",
        printer_name="TSC_TTP_244_Pro",
        station_id="192.168.1.100",
    )

    carton, btxml = carton_service.weigh_pack_carton(payload, db_session)
    assert carton.id is not None
    assert carton.carton_sn.startswith("VHK0010237")
    assert carton.weight == 12.500
    assert carton.po_number == "PO-9999"
    assert carton.lot_number == "LOT-8888"
    assert carton.station_id == "192.168.1.100"
    assert carton.is_reprint == 0
    assert "第1.btw</Format>" in btxml
    assert "<NamedSubString Name=\"CPN\"><Value>840-00083</Value></NamedSubString>" in btxml
    assert "<NamedSubString Name=\"PONo\"><Value>PO-9999</Value></NamedSubString>" in btxml
    assert "<NamedSubString Name=\"LotNo\"><Value>LOT-8888</Value></NamedSubString>" in btxml


def test_weigh_pack_sequential_sn(db_session, erro_01_product):
    p1 = CartonWeighPackCreate(
        product_id=cast(int, erro_01_product.id),
        weight=12.450,
        po_number="PO-1",
        lot_number="LOT-1",
    )
    p2 = CartonWeighPackCreate(
        product_id=cast(int, erro_01_product.id),
        weight=12.550,
        po_number="PO-1",
        lot_number="LOT-1",
    )

    c1, _ = carton_service.weigh_pack_carton(p1, db_session)
    c2, _ = carton_service.weigh_pack_carton(p2, db_session)

    sn1_seq = int(str(c1.carton_sn)[-6:])
    sn2_seq = int(str(c2.carton_sn)[-6:])
    assert sn2_seq == sn1_seq + 1


def test_weigh_pack_saves_job_order(db_session, erro_01_product):
    payload = CartonWeighPackCreate(
        product_id=cast(int, erro_01_product.id),
        weight=12.500,
        job_order="1259487",
        po_number="PO-123",
        lot_number="LOT-456",
    )
    carton, _ = carton_service.weigh_pack_carton(payload, db_session)
    assert carton.job_order == "1259487"

