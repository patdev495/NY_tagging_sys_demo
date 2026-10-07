from datetime import datetime
from typing import cast

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.models import Base, Customer, Product
from src.features.carton import schemas as carton_schemas
from src.features.carton import service as carton_service
from src.features.print import service as print_service


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def tem3_product(db_session):
    customer = Customer(code="ERRO", name="Erro")
    db_session.add(customer)
    db_session.commit()

    product = Product(
        customer_id=customer.id,
        item_name="2M21-00508-0004H",
        luxshare_part_number="LLERJ014-NC-R",
        customer_project="Andy Town/ Firefly",
        production_stage="MP",
        product_desc="CAT5E ETHERNET CABLE",
        packed_qty=190,
        packing_mode="weight_scale",
        template_type="erro_03",
        template_path=r"D:\PAT\Templates\erro_03.btw",
        pkg_prefix="1012665",
        revision="/",
        min_weight=5.0,
        max_weight=7.0,
        target_weight=6.0,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


def test_weigh_pack_tem3_assigns_the_generation_date_as_lot(db_session, tem3_product):
    payload = carton_schemas.CartonWeighPackCreate(
        product_id=cast(int, tem3_product.id),
        weight=6.050,
        po_number=None,
        lot_number=None,
    )
    carton, btxml = carton_service.weigh_pack_carton(payload, db_session)

    assert carton.id is not None
    assert carton.po_number is None
    assert carton.lot_number == datetime.now().strftime("%Y%m%d")

    today_yymmdd = datetime.now().strftime("%y%m%d")
    expected_sn = f"1012665{today_yymmdd}0001"
    assert carton.carton_sn == expected_sn
    assert len(carton.carton_sn) == 17

    assert btxml is not None
    assert "erro_03.btw" in btxml
    assert "<NamedSubString Name=\"CartonSN\">" in btxml
    assert f"<Value>{expected_sn}</Value>" in btxml
    assert "<NamedSubString Name=\"SupplierCode\">" in btxml
    assert "<Value>1012665</Value>" in btxml
    assert "<NamedSubString Name=\"LuxsharePartNo\">" in btxml
    assert "<Value>LLERJ014-NC-R</Value>" in btxml
    assert "<NamedSubString Name=\"QTY\">" in btxml
    assert "<Value>190</Value>" in btxml
    assert "<NamedSubString Name=\"PartDesc\">" in btxml
    assert "<Value>CAT5E ETHERNET CABLE</Value>" in btxml
    assert "<NamedSubString Name=\"QRCode_Content\">" in btxml


def test_weigh_pack_tem3_uses_a_new_lot_date_for_the_same_job_order_on_a_new_day(
    db_session, tem3_product, monkeypatch
):
    class FrozenDatetime:
        current = datetime(2026, 10, 1, 8, 0, 0)

        @classmethod
        def now(cls):
            return cls.current

    monkeypatch.setattr(carton_service, "datetime", FrozenDatetime)
    payload = carton_schemas.CartonWeighPackCreate(
        product_id=cast(int, tem3_product.id), weight=6.050, job_order="JO-100"
    )

    first_carton, _ = carton_service.weigh_pack_carton(payload, db_session)
    FrozenDatetime.current = datetime(2026, 10, 2, 8, 0, 0)
    second_carton, _ = carton_service.weigh_pack_carton(payload, db_session)

    assert first_carton.lot_number == "20261001"
    assert second_carton.lot_number == "20261002"
    assert first_carton.carton_sn[7:13] == "261001"
    assert second_carton.carton_sn[7:13] == "261002"


def test_weigh_pack_tem3_increments_sequence_monotonically(db_session, tem3_product):
    today_yymmdd = datetime.now().strftime("%y%m%d")

    payload1 = carton_schemas.CartonWeighPackCreate(
        product_id=cast(int, tem3_product.id),
        weight=6.100,
    )
    carton1, _ = carton_service.weigh_pack_carton(payload1, db_session)
    assert carton1.carton_sn == f"1012665{today_yymmdd}0001"

    payload2 = carton_schemas.CartonWeighPackCreate(
        product_id=cast(int, tem3_product.id),
        weight=6.200,
    )
    carton2, _ = carton_service.weigh_pack_carton(payload2, db_session)
    assert carton2.carton_sn == f"1012665{today_yymmdd}0002"


def test_weigh_pack_tem3_rejects_underweight(db_session, tem3_product):
    payload = carton_schemas.CartonWeighPackCreate(
        product_id=cast(int, tem3_product.id),
        weight=4.950,
    )
    with pytest.raises(HTTPException) as exc:
        carton_service.weigh_pack_carton(payload, db_session)
    assert exc.value.status_code == 400
    assert "below minimum tolerance" in exc.value.detail


def test_weigh_pack_tem3_rejects_overweight(db_session, tem3_product):
    payload = carton_schemas.CartonWeighPackCreate(
        product_id=cast(int, tem3_product.id),
        weight=7.100,
    )
    with pytest.raises(HTTPException) as exc:
        carton_service.weigh_pack_carton(payload, db_session)
    assert exc.value.status_code == 400
    assert "above maximum tolerance" in exc.value.detail


def test_weigh_pack_tem3_strictly_forbids_manual_sequence(db_session, tem3_product):
    payload = carton_schemas.CartonWeighPackCreate(
        product_id=cast(int, tem3_product.id),
        weight=6.000,
        custom_sn=999,
    )
    with pytest.raises(HTTPException) as exc:
        carton_service.weigh_pack_carton(payload, db_session)
    assert exc.value.status_code == 400
    assert "không cho phép chỉnh sửa số thứ tự" in exc.value.detail


def test_tem3_allows_reprint(db_session, tem3_product):
    payload = carton_schemas.CartonWeighPackCreate(
        product_id=cast(int, tem3_product.id),
        weight=6.000,
    )
    carton, _ = carton_service.weigh_pack_carton(payload, db_session)
    assert carton.id is not None

    reprint = print_service.reprint_carton(carton_id=cast(int, carton.id), db=db_session)
    assert reprint.id != carton.id
    assert reprint.carton_sn == carton.carton_sn
    assert reprint.is_reprint == 1
