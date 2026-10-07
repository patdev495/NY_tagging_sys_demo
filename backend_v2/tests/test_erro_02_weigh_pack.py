from datetime import datetime
from typing import cast

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.models import Base, Customer, Product
from src.features.carton import schemas as carton_schemas
from src.features.carton import service as carton_service


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def tem2_product(db_session):
    customer = Customer(code="ERRO", name="Erro")
    db_session.add(customer)
    db_session.commit()

    product = Product(
        customer_id=customer.id,
        item_name="G012C1B",
        asin="B08G9M4HXS",
        product_desc="ASSY,BAND WRAPPED,CAT5E ETHERNET CABLE 4.0mm OD:91CM,WHITE,RUBBER BAND",
        packed_qty=190,
        packing_mode="weight_scale",
        template_type="erro_02",
        template_path=r"D:\PAT\Templates\erro_02.btw",
        mfr_pn="NYS5998",
        upc="852582006785",
        pkg_prefix="37033907",
        min_weight=5.0,
        max_weight=7.0,
        target_weight=6.0,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


def test_weigh_pack_tem2_assigns_the_generation_date_as_lot(db_session, tem2_product):
    payload = carton_schemas.CartonWeighPackCreate(
        product_id=cast(int, tem2_product.id),
        weight=6.050,
        po_number=None,
        lot_number=None,
    )
    carton, btxml = carton_service.weigh_pack_carton(payload, db_session)

    assert carton.id is not None
    assert carton.po_number is None
    assert carton.lot_number == datetime.now().strftime("%Y%m%d")
    assert carton.carton_sn == "03703390700000013"
    assert len(carton.carton_sn) == 17  # 1 (0) + 8 (prefix) + 7 (seq) + 1 (cd)

    assert btxml is not None
    assert "SSCC_Text" in btxml
    assert "SSCC_CD" in btxml
    assert "(00) 0 37033907 0000001" in btxml
    assert "NYS5998" in btxml
    assert "B08G9M4HXS" in btxml


def test_weigh_pack_tem2_rejects_underweight(db_session, tem2_product):
    payload = carton_schemas.CartonWeighPackCreate(
        product_id=cast(int, tem2_product.id),
        weight=4.950,
    )
    with pytest.raises(HTTPException) as exc:
        carton_service.weigh_pack_carton(payload, db_session)
    assert exc.value.status_code == 400
    assert "below minimum tolerance" in exc.value.detail


def test_weigh_pack_tem2_rejects_overweight(db_session, tem2_product):
    payload = carton_schemas.CartonWeighPackCreate(
        product_id=cast(int, tem2_product.id),
        weight=7.100,
    )
    with pytest.raises(HTTPException) as exc:
        carton_service.weigh_pack_carton(payload, db_session)
    assert exc.value.status_code == 400
    assert "above maximum tolerance" in exc.value.detail


def test_weigh_pack_tem2_strictly_forbids_manual_sequence(db_session, tem2_product):
    payload = carton_schemas.CartonWeighPackCreate(
        product_id=cast(int, tem2_product.id),
        weight=6.000,
        custom_sn=999,
    )
    with pytest.raises(HTTPException) as exc:
        carton_service.weigh_pack_carton(payload, db_session)
    assert exc.value.status_code == 400
    assert "không cho phép chỉnh sửa số thứ tự" in exc.value.detail


def test_weigh_pack_tem2_increments_sscc_monotonically(db_session, tem2_product):
    payload1 = carton_schemas.CartonWeighPackCreate(
        product_id=cast(int, tem2_product.id),
        weight=6.100,
    )
    carton1, _ = carton_service.weigh_pack_carton(payload1, db_session)
    assert carton1.carton_sn == "03703390700000013"

    payload2 = carton_schemas.CartonWeighPackCreate(
        product_id=cast(int, tem2_product.id),
        weight=6.200,
    )
    carton2, _ = carton_service.weigh_pack_carton(payload2, db_session)
    assert carton2.carton_sn == "03703390700000020"
