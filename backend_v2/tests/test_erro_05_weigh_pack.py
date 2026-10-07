from datetime import datetime
from typing import cast

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.models import Base, Carton, Customer, Product
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
def erro_05_product(db_session):
    customer = Customer(code="ERRO", name="Erro")
    db_session.add(customer)
    db_session.flush()

    product = Product(
        customer_id=customer.id,
        item_name="1414-0GDA0BV",
        upc="",
        packed_qty=1000,
        template_type="erro_05",
        template_path=r"D:\PAT\Templates\erro_05.btw",
        packing_mode="weight_scale",
        pkg_prefix="MC220TW1",
        product_desc="X LED CABLE 30AWG 230mm",
        factory_item_code="1HWU3023C1XX02NN9",
        min_weight=0.0,
        max_weight=10.0,
        target_weight=5.0,
    )
    db_session.add(product)
    db_session.commit()
    return product


def test_weigh_pack_erro_05_creates_carton_and_btxml(db_session, erro_05_product):
    now = datetime.now()
    yy = now.strftime("%y")
    ww = f"{now.isocalendar()[1]:02d}"

    carton, btxml = carton_service.weigh_pack_carton(
        carton_schemas.CartonWeighPackCreate(
            product_id=cast(int, erro_05_product.id),
            weight=5.0,
            po_number="",
            lot_number="",
        ),
        db_session,
    )

    expected_sn = f"MC220TW12{yy}{ww}50001"
    assert carton.carton_sn == expected_sn
    assert len(carton.carton_sn) == 18
    assert db_session.query(Carton).filter_by(id=carton.id).one().btxml == btxml

    lot_ymd = now.strftime("%Y%m%d")
    date_yyww = f"{yy}{ww}"
    expected_qr = f"{expected_sn},1414-0GDA0BV,,,1000,{date_yyww},{lot_ymd}"

    expected_substrings = {
        "CartonNo": expected_sn,
        "Item": "1414-0GDA0BV",
        "DESC": "X LED CABLE 30AWG 230mm",
        "DateCode": date_yyww,
        "LotCode": lot_ymd,
        "QTY": "1000",
        "QRCode_Content": expected_qr,
        "MPN": "",
        "Rev": getattr(erro_05_product, "revision", "") or "",
        "Config": "",
        "Batch": "",
        "Stage": "",
    }
    for name, value in expected_substrings.items():
        assert f'<NamedSubString Name="{name}"><Value>{value}</Value></NamedSubString>' in btxml, (
            f"Missing substring {name} in btxml"
        )


def test_weigh_pack_erro_05_sequence_increments_within_month(db_session, erro_05_product):
    now = datetime.now()
    yy = now.strftime("%y")
    ww = f"{now.isocalendar()[1]:02d}"

    carton1, _ = carton_service.weigh_pack_carton(
        carton_schemas.CartonWeighPackCreate(
            product_id=cast(int, erro_05_product.id),
            weight=5.0,
        ),
        db_session,
    )
    carton2, _ = carton_service.weigh_pack_carton(
        carton_schemas.CartonWeighPackCreate(
            product_id=cast(int, erro_05_product.id),
            weight=5.0,
        ),
        db_session,
    )

    assert carton1.carton_sn == f"MC220TW12{yy}{ww}50001"
    assert carton2.carton_sn == f"MC220TW12{yy}{ww}50002"


def test_weigh_pack_erro_05_sequence_resets_each_month(db_session, erro_05_product):
    # Simulate a carton created in a previous month (August 2026)
    prev_carton = Carton(
        product_id=erro_05_product.id,
        carton_sn="MC220TW12263250088",
        created_at=datetime(2026, 8, 15, 10, 0, 0),
        status="SUCCESS",
        is_reprint=0,
    )
    db_session.add(prev_carton)
    db_session.commit()

    now = datetime.now()
    yy = now.strftime("%y")
    ww = f"{now.isocalendar()[1]:02d}"

    # Current month (September 2026) should start fresh at 50001
    carton, _ = carton_service.weigh_pack_carton(
        carton_schemas.CartonWeighPackCreate(
            product_id=cast(int, erro_05_product.id),
            weight=5.0,
        ),
        db_session,
    )
    assert carton.carton_sn == f"MC220TW12{yy}{ww}50001"


def test_reprint_allowed_for_erro_05(db_session, erro_05_product):
    carton, _ = carton_service.weigh_pack_carton(
        carton_schemas.CartonWeighPackCreate(
            product_id=cast(int, erro_05_product.id),
            weight=5.0,
        ),
        db_session,
    )
    from src.features.print.service import reprint_carton
    reprint = reprint_carton(
        carton_id=carton.id,
        station_id="STATION_TEST",
        db=db_session,
    )
    assert reprint.id != carton.id
    assert reprint.carton_sn == carton.carton_sn
    assert reprint.is_reprint == 1
