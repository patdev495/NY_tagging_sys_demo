from typing import cast

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.database import seed_erro_data
from src.core.models import Base, Customer, Product
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


def test_product_schema_supports_tem2_fields():
    data = {
        "item_name": "G012C1B",
        "asin": "B08G9M4HXS",
        "product_desc": "ASSY,BAND WRAPPED,CAT5E ETHERNET CABLE 4.0mm OD:91CM,WHITE,RUBBER BAND",
        "packed_qty": 190,
        "customer_id": 1,
        "packing_mode": "weight_scale",
        "template_type": "erro_02",
        "template_path": r"D:\PAT\Templates\erro_02.btw",
        "mfr_pn": "NYS5998",
        "upc": "852582006785",
        "min_weight": 5.0,
        "max_weight": 7.0,
        "target_weight": 6.0,
    }
    schema = schemas.ProductCreate(**data)
    assert schema.asin == "B08G9M4HXS"
    assert schema.product_desc == "ASSY,BAND WRAPPED,CAT5E ETHERNET CABLE 4.0mm OD:91CM,WHITE,RUBBER BAND"


def test_product_service_creates_and_searches_by_asin(db_session):
    customer = Customer(code="ERRO", name="Erro")
    db_session.add(customer)
    db_session.commit()

    prod_in = schemas.ProductCreate(
        customer_id=cast(int, customer.id),
        item_name="G112C1B",
        asin="B0C32N712K",
        product_desc="ASSY, BAND WRAPPED, CAT6A ETHERNET CABLE 4.7MM OD, 91CM , WHITE,RUBBER BAND",
        packed_qty=190,
        packing_mode="weight_scale",
        template_type="erro_02",
        template_path=r"D:\PAT\Templates\erro_02.btw",
        internal_factory_part_number="1LAE0009D2U002MAAS",
        mfr_pn="NYS5996",
        upc="840268969493",
        min_weight=5.0,
        max_weight=7.0,
        target_weight=6.0,
    )
    created = product_service.create_product(db_session, prod_in)
    assert created.id is not None
    assert created.asin == "B0C32N712K"
    assert created.product_desc.startswith("ASSY, BAND WRAPPED")

    results = product_service.get_all_products(db_session, search="B0C32N712K")
    assert len(results) == 1
    assert results[0].item_name == "G112C1B"


def test_seed_a11_data_seeds_both_tem1_and_tem2(db_session):
    seed_erro_data(db_session)

    # Check Tem 1 products
    p840 = db_session.query(Product).filter(Product.item_name == "840-00083").first()
    assert p840 is not None
    assert p840.template_type == "erro_01"

    # Check Tem 2 products
    g012 = db_session.query(Product).filter(Product.item_name == "G012C1B").first()
    assert g012 is not None
    assert g012.template_type == "erro_02"
    assert g012.asin == "B08G9M4HXS"
    assert g012.mfr_pn == "NYS5998"
    assert g012.upc == "852582006785"
    assert g012.packed_qty == 190
    assert g012.template_path == r"D:\PAT\Templates\erro_02.btw"

    g112 = db_session.query(Product).filter(Product.item_name == "G112C1B").first()
    assert g112 is not None
    assert g112.template_type == "erro_02"
    assert g112.asin == "B0C32N712K"
    assert g112.mfr_pn == "NYS5996"
    assert g112.upc == "840268969493"
    assert g112.packed_qty == 190
    assert g112.template_path == r"D:\PAT\Templates\erro_02.btw"


def test_get_next_sn_returns_sscc_for_a11_tem2(db_session):
    seed_erro_data(db_session)
    g012 = db_session.query(Product).filter(Product.item_name == "G012C1B").first()
    sn_info = product_service.get_next_sn(g012.id, db_session)
    assert sn_info["next_seq"] == 1
    assert sn_info["next_sn"] == "03703390700000013"
    assert sn_info["sscc_text"] == "(00) 0 37033907 0000001"
    assert sn_info["check_digit"] == 3
