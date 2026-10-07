import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.models import Base, Carton, Customer, Product
from src.features.carton.sscc_allocator import (
    calculate_gs1_check_digit,
    format_sscc_18,
    format_sscc_display_text,
    next_sscc_sequence,
    parse_sscc_sequence,
    plan_next_sscc_carton_sn,
)


def test_calculate_gs1_check_digit_standard_cases():
    # Test case from drawing page 2: 0370339071000286 -> 1
    assert calculate_gs1_check_digit("0370339071000286") == 1

    # Test case from template 第2.btw: 0370339070000001 -> 3
    assert calculate_gs1_check_digit("0370339070000001") == 3

    # Check non-digit characters stripped
    assert calculate_gs1_check_digit("0-37033907-0000001") == 3


def test_format_sscc_18():
    sscc_code = format_sscc_18("37033907", 1)
    assert sscc_code == "03703390700000013"
    assert len(sscc_code) == 17

    sscc_sample2 = format_sscc_18("37033907", 1000286)
    assert sscc_sample2 == "03703390710002861"
    assert len(sscc_sample2) == 17


def test_format_sscc_display_text():
    display = format_sscc_display_text("37033907", 1)
    assert display == "(00) 0 37033907 0000001"


def test_parse_sscc_sequence():
    assert parse_sscc_sequence("03703390700000013", "37033907") == 1
    assert parse_sscc_sequence("03703390710002861", "37033907") == 1000286
    assert parse_sscc_sequence("INVALID", "37033907") == 0


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def erro_02_product(db_session):
    customer = Customer(code="ERRO", name="Erro")
    db_session.add(customer)
    db_session.flush()

    product = Product(
        customer_id=customer.id,
        item_name="G012C1B",
        packed_qty=190,
        packing_mode="weight_scale",
        target_weight=6.000,
        min_weight=5.000,
        max_weight=7.000,
        weight_unit="kg",
        mfr_pn="NYS5998",
        template_type="erro_02",
        template_path=r"D:\PAT\Templates\erro_02.btw",
    )
    db_session.add(product)
    db_session.commit()
    return product


def test_next_sscc_sequence_starts_at_1_when_empty(db_session):
    seq = next_sscc_sequence(db_session, "37033907")
    assert seq == 1


def test_next_sscc_sequence_increments_across_cartons(db_session, erro_02_product):
    c1 = Carton(
        product_id=erro_02_product.id,
        carton_sn="03703390700000013",
        status="SUCCESS",
        is_reprint=0,
    )
    db_session.add(c1)
    db_session.commit()

    seq = next_sscc_sequence(db_session, "37033907")
    assert seq == 2


def test_plan_next_sscc_carton_sn(db_session, erro_02_product):
    plan = plan_next_sscc_carton_sn(db_session, erro_02_product)
    assert plan.sequence == 1
    assert plan.check_digit == 3
    assert plan.carton_sn == "03703390700000013"
    assert plan.sscc_text == "(00) 0 37033907 0000001"
