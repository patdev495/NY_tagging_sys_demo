import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.models import Base, Carton, Customer, Product
from src.features.carton.erro_01_sn_allocator import (
    current_iso_date_code,
    format_erro_01_carton_sn,
    plan_next_erro_01_carton_sn,
)
from src.features.carton.schemas import AdminCartonCreate
from src.features.carton.service import create_admin_erro_carton


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
    )
    db_session.add(product)
    db_session.commit()
    return product


def test_current_iso_date_code():
    # Test format YYWW
    now = datetime.datetime.now()
    expected_yy = now.strftime("%y")
    expected_ww = f"{now.isocalendar()[1]:02d}"
    expected = f"{expected_yy}{expected_ww}"
    
    assert current_iso_date_code() == expected
    assert len(current_iso_date_code()) == 4


def test_format_erro_01_carton_sn():
    sn = format_erro_01_carton_sn("VHK0010237", "2608", 81)
    assert sn == "VHK00102372608000081"
    assert len(sn) == len("VHK0010237") + 4 + 6


def test_plan_next_erro_01_carton_sn_first_in_year(db_session, erro_01_product):
    plan = plan_next_erro_01_carton_sn(db_session, erro_01_product, custom_yymm="2608")
    assert plan.sequence == 1
    assert plan.carton_sn == "VHK00102372608000001"
    assert plan.date_code == current_iso_date_code()


def test_plan_next_erro_01_carton_sn_sequential_increment_across_months(db_session, erro_01_product):
    # Existing carton in month 08
    c1 = Carton(
        product_id=erro_01_product.id,
        carton_sn="VHK00102372608000080",
        weight=12.45,
        status="SUCCESS",
        is_reprint=0,
    )
    db_session.add(c1)
    db_session.commit()

    # Next carton in month 09 of the same year 26 should be sequence 81
    plan = plan_next_erro_01_carton_sn(db_session, erro_01_product, custom_yymm="2609")
    assert plan.sequence == 81
    assert plan.carton_sn == "VHK00102372609000081"


def test_plan_next_erro_01_carton_sn_resets_on_new_year(db_session, erro_01_product):
    # Existing carton in year 25
    c_prev_year = Carton(
        product_id=erro_01_product.id,
        carton_sn="VHK00102372512000999",
        weight=12.45,
        status="SUCCESS",
        is_reprint=0,
    )
    db_session.add(c_prev_year)
    db_session.commit()

    # In year 26, sequence should reset to 1
    plan = plan_next_erro_01_carton_sn(db_session, erro_01_product, custom_yymm="2601")
    assert plan.sequence == 1
    assert plan.carton_sn == "VHK00102372601000001"


def test_plan_next_erro_01_carton_sn_ignores_reprints(db_session, erro_01_product):
    c_orig = Carton(
        product_id=erro_01_product.id,
        carton_sn="VHK00102372608000005",
        status="SUCCESS",
        is_reprint=0,
    )
    c_reprint = Carton(
        product_id=erro_01_product.id,
        carton_sn="VHK00102372608000005",
        status="SUCCESS",
        is_reprint=1,
    )
    db_session.add_all([c_orig, c_reprint])
    db_session.commit()

    plan = plan_next_erro_01_carton_sn(db_session, erro_01_product, custom_yymm="2608")
    assert plan.sequence == 6
    assert plan.carton_sn == "VHK00102372608000006"


def test_plan_next_erro_01_carton_sn_is_independent_per_product(db_session, erro_01_product):
    # Create product B with same customer and same pkg_prefix
    prod_b = Product(
        customer_id=erro_01_product.customer_id,
        item_name="840-00091",
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
    )
    db_session.add(prod_b)
    db_session.commit()

    # Create cartons for product A reaching sequence 50
    db_session.add(Carton(
        product_id=erro_01_product.id,
        carton_sn="VHK00102372608000050",
        status="SUCCESS",
        is_reprint=0,
    ))
    db_session.commit()

    # Tem 1 maintains a sequence namespace per Product, even with the same prefix.
    plan_b = plan_next_erro_01_carton_sn(db_session, prod_b, custom_yymm="2608")
    assert plan_b.sequence == 1
    assert plan_b.carton_sn == "VHK00102372608000001"

    # Product A continues from its own high-water mark.
    plan_a = plan_next_erro_01_carton_sn(db_session, erro_01_product, custom_yymm="2608")
    assert plan_a.sequence == 51
    assert plan_a.carton_sn == "VHK00102372608000051"


def test_admin_can_create_the_same_erro_01_carton_sn_for_different_products(db_session, erro_01_product):
    product_b = Product(
        customer_id=erro_01_product.customer_id,
        item_name="840-00091",
        packed_qty=190,
        packing_mode="weight_scale",
        target_weight=12.5,
        min_weight=12.3,
        max_weight=12.7,
        pkg_prefix="VHK0010237",
        template_type="erro_01",
        template_path="erro_01.btw",
    )
    db_session.add(product_b)
    db_session.commit()

    common = dict(sequence=3, reason="Khởi tạo", weight=12.5, job_order="JO-01")
    carton_a, _ = create_admin_erro_carton(AdminCartonCreate(product_id=erro_01_product.id, **common), "admin", db_session)
    carton_b, _ = create_admin_erro_carton(AdminCartonCreate(product_id=product_b.id, **common), "admin", db_session)

    assert carton_a.carton_sn == carton_b.carton_sn == "VHK0010237" + datetime.datetime.now().strftime("%y%m") + "000003"
