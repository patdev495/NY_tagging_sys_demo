import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.database import seed_erro_data
from src.core.models import Base, Customer, Product


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def test_seed_erro_05_38_products_catalog(db_session):
    # Act: run seed
    seed_erro_data(db_session)
    db_session.commit()

    erro_customer = db_session.query(Customer).filter(Customer.code == "ERRO").first()
    assert erro_customer is not None

    # Query all erro_05 products
    erro_05_prods = (
        db_session.query(Product)
        .filter(
            Product.customer_id == erro_customer.id,
            Product.template_type == "erro_05",
        )
        .all()
    )

    # Must have exactly 38 products from PD016906 Page 3
    assert len(erro_05_prods) == 38

    # Verify uniform defaults
    for p in erro_05_prods:
        assert p.pkg_prefix == "MC220TW1"
        assert p.packed_qty == 1000
        assert p.packing_mode == "weight_scale"
        assert p.template_path == r"D:\PAT\Templates\erro_05.btw"
        assert p.min_weight == 0.0
        assert p.max_weight == 10.0
        assert p.target_weight == 5.0
        assert p.weight_unit == "kg"
        assert p.revision == ""
        assert p.factory_item_code is not None
        assert p.product_desc is not None

    # Verify representative product 1
    p1 = (
        db_session.query(Product)
        .filter(
            Product.customer_id == erro_customer.id,
            Product.factory_item_code == "1CAU0002M2WH07NX9",
        )
        .first()
    )
    assert p1 is not None
    assert p1.item_name == "1401-02BP0W3"
    assert p1.product_desc == "USB2.0 AM TO 90° TYPE-C TPE 2M"

    # Verify representative product 35 (NN9 representative)
    p35 = (
        db_session.query(Product)
        .filter(
            Product.customer_id == erro_customer.id,
            Product.factory_item_code == "1HWU3023C1XX02NN9",
        )
        .first()
    )
    assert p35 is not None
    assert p35.item_name == "1414-0GDA0BV"
    assert p35.product_desc == "X LED CABLE 30AWG 230mm"

    # Verify representative product 38
    p38 = (
        db_session.query(Product)
        .filter(
            Product.customer_id == erro_customer.id,
            Product.factory_item_code == "1MA00PCBAXX045NN9",
        )
        .first()
    )
    assert p38 is not None
    assert p38.item_name == "0A02-02WF0BV"
    assert p38.product_desc == "LED PCBA BOARD NIENYI/NYS6994"

    # Verify 1401-02QK0W9 has 10 distinct variants
    qkow9_variants = (
        db_session.query(Product)
        .filter(
            Product.customer_id == erro_customer.id,
            Product.item_name == "1401-02QK0W9",
        )
        .all()
    )
    assert len(qkow9_variants) == 10
    unique_factory_codes = {v.factory_item_code for v in qkow9_variants}
    assert len(unique_factory_codes) == 10

    # Test idempotency: running seed again should not duplicate products
    seed_erro_data(db_session)
    db_session.commit()

    erro_05_prods_second_run = (
        db_session.query(Product)
        .filter(
            Product.customer_id == erro_customer.id,
            Product.template_type == "erro_05",
        )
        .all()
    )
    assert len(erro_05_prods_second_run) == 38


def test_admin_update_erro_05_product(db_session):
    from src.features.product.schemas import ProductUpdate
    from src.features.product.service import get_all_products, update_product

    seed_erro_data(db_session)
    db_session.commit()

    # Test search by factory_item_code
    searched = get_all_products(db_session, customer_code="ERRO", search="1HWU3023C1XX02NN9")
    assert len(searched) == 1
    assert searched[0].item_name == "1414-0GDA0BV"

    p = searched[0]
    assert p.pkg_prefix == "MC220TW1"
    assert p.packed_qty == 1000

    update_payload = ProductUpdate(
        pkg_prefix="MC220VN2",
        packed_qty=500,
        min_weight=2.0,
        max_weight=4.0,
        target_weight=3.0,
    )

    updated = update_product(db_session, p.id, update_payload)
    assert updated is not None
    assert updated.pkg_prefix == "MC220VN2"
    assert updated.packed_qty == 500
    assert updated.min_weight == 2.0
    assert updated.max_weight == 4.0
    assert updated.target_weight == 3.0


