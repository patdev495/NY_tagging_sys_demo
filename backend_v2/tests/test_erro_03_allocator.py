import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.database import Base
from src.core.models import Carton, Product
from src.features.carton.erro_03_sn_allocator import (
    format_erro_03_carton_sn,
    next_erro_03_sequence,
    parse_erro_03_sequence,
    plan_next_erro_03_carton_sn,
)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_format_erro_03_carton_sn():
    sn = format_erro_03_carton_sn("1012665", "260911", 1)
    assert sn == "10126652609110001"
    assert len(sn) == 17

    sn_large = format_erro_03_carton_sn("1012665", "260911", 2209)
    assert sn_large == "10126652609112209"
    assert len(sn_large) == 17


def test_parse_erro_03_sequence():
    assert parse_erro_03_sequence("10126652609110001", "1012665", "26") == 1
    assert parse_erro_03_sequence("10126652609112209", "1012665", "26") == 2209
    # Mismatched year should return 0
    assert parse_erro_03_sequence("10126652609110001", "1012665", "25") == 0


def test_next_erro_03_sequence_yearly_reset(db_session):
    product = Product(
        id=1,
        item_name="2M21-00508-0004H",
        template_type="erro_03",
        pkg_prefix="1012665",
        packed_qty=190,
    )
    db_session.add(product)
    db_session.commit()

    # Day 1 in 2026: 260911 -> First carton sequence should be 1
    seq1 = next_erro_03_sequence(db_session, "1012665", "260911", product_id=product.id)
    assert seq1 == 1

    # Simulate saving carton 1 on day 1
    c1 = Carton(product_id=product.id, carton_sn="10126652609110001", is_reprint=0)
    db_session.add(c1)
    db_session.commit()

    # Day 2 in 2026: 260912 -> Sequence continues as 2 (DOES NOT RESET DAILY)
    plan_day2 = plan_next_erro_03_carton_sn(db_session, product, custom_yymmdd="260912")
    assert plan_day2.sequence == 2
    assert plan_day2.carton_sn == "10126652609120002"

    # Year 2027: 270101 -> Sequence resets to 1
    plan_year27 = plan_next_erro_03_carton_sn(db_session, product, custom_yymmdd="270101")
    assert plan_year27.sequence == 1
    assert plan_year27.carton_sn == "10126652701010001"


def test_plan_next_erro_03_carton_sn(db_session):
    product = Product(
        id=2,
        item_name="2M21-00508-0004H",
        template_type="erro_03",
        pkg_prefix="1012665",
        packed_qty=190,
    )
    db_session.add(product)
    db_session.commit()

    plan = plan_next_erro_03_carton_sn(db_session, product, custom_yymmdd="260911")
    assert plan.supplier_code == "1012665"
    assert plan.yymmdd == "260911"
    assert plan.sequence == 1
    assert plan.carton_sn == "10126652609110001"
    assert len(plan.carton_sn) == 17
