from datetime import datetime
from typing import cast

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.database import seed_erro_data
from src.core.models import Base, Customer, Product
from src.core.utils import TemplateResolver
from src.features.product import schemas
from src.features.product import service as product_service


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_template_resolver_supports_erro_03():
    canonical = TemplateResolver.get_canonical_template_filename("erro_03")
    assert canonical == "erro_03.btw"

    found = [t for t in TemplateResolver.ALL_CANONICAL_TEMPLATES if t["type"] == "erro_03"]
    assert len(found) == 1
    assert found[0]["filename"] == "erro_03.btw"
    assert found[0]["customer"] == "ERRO"


def test_product_schema_supports_tem3_fields():
    data = {
        "item_name": "2M21-00508-0004H",
        "pkg_prefix": "1012665",
        "revision": "/",
        "product_desc": "CAT5E ETHERNET CABLE",
        "customer_project": "Andy Town/ Firefly",
        "production_stage": "MP",
        "luxshare_part_number": "LLERJ014-NC-R",
        "packed_qty": 190,
        "customer_id": 1,
        "packing_mode": "weight_scale",
        "template_type": "erro_03",
        "template_path": r"D:\PAT\Templates\erro_03.btw",
        "min_weight": 5.0,
        "max_weight": 7.0,
        "target_weight": 6.0,
    }
    schema = schemas.ProductCreate(**data)
    assert schema.item_name == "2M21-00508-0004H"
    assert schema.pkg_prefix == "1012665"
    assert schema.revision == "/"
    assert schema.template_type == "erro_03"


def test_product_service_creates_and_searches_tem3(db_session):
    customer = Customer(code="ERRO", name="Erro")
    db_session.add(customer)
    db_session.commit()

    prod_in = schemas.ProductCreate(
        customer_id=cast(int, customer.id),
        item_name="2M21-00508-0004H",
        pkg_prefix="1012665",
        revision="/",
        product_desc="CAT5E ETHERNET CABLE",
        customer_project="Andy Town/ Firefly",
        production_stage="MP",
        luxshare_part_number="LLERJ014-NC-R",
        packed_qty=190,
        packing_mode="weight_scale",
        template_type="erro_03",
        template_path=r"D:\PAT\Templates\erro_03.btw",
        min_weight=5.0,
        max_weight=7.0,
        target_weight=6.0,
    )
    created = product_service.create_product(db_session, prod_in)
    assert created.id is not None
    assert created.template_type == "erro_03"

    results = product_service.get_all_products(db_session, search="2M21-00508-0004H")
    assert len(results) == 1
    assert results[0].item_name == "2M21-00508-0004H"


def test_seed_erro_data_seeds_erro_03_product(db_session):
    seed_erro_data(db_session)

    p_tem3 = db_session.query(Product).filter(Product.item_name == "2M21-00508-0004H").first()
    assert p_tem3 is not None
    assert p_tem3.template_type == "erro_03"
    assert p_tem3.pkg_prefix == "1012665"
    assert p_tem3.packed_qty == 190
    assert p_tem3.packing_mode == "weight_scale"
    assert p_tem3.template_path == r"D:\PAT\Templates\erro_03.btw"
    assert p_tem3.revision == "/"
    assert p_tem3.target_weight == 6.0


def test_get_next_sn_returns_tem3_carton_sn(db_session):
    seed_erro_data(db_session)
    p_tem3 = db_session.query(Product).filter(Product.item_name == "2M21-00508-0004H").first()
    assert p_tem3 is not None
    sn_info = product_service.get_next_sn(cast(int, p_tem3.id), db_session)
    assert sn_info["next_seq"] == 1
    today_yymmdd = datetime.now().strftime("%y%m%d")
    expected_sn = f"1012665{today_yymmdd}0001"
    assert sn_info["next_sn"] == expected_sn
    assert sn_info["supplier_code"] == "1012665"
    assert sn_info["yymmdd"] == today_yymmdd
