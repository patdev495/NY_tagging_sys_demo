import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.core.database import get_db, seed_erro_data
from src.core.models import Base, Customer, Product
from src.features.auth.service import seed_default_users
from src.features.product import schemas
from src.features.product import service as product_service


def _erro_04_payload(**overrides):
    payload = {
        "customer_id": 1,
        "item_name": "G111A1A",
        "upc": "840268939793",
        "packed_qty": 120,
        "template_type": "erro_04",
        "template_path": "erro_04.btw",
        "packing_mode": "weight_scale",
        "mfr_pn": "NYS5896",
        "product_desc": "Accessory, Ethernet Cable CAT6a, 15cm, Black, 1PK, Basic Box",
        "internal_factory_part_number": "1LAX0015C2U001MAAR",
        "factory_item_code": "115-00020",
        "carton_id_prefix": "H",
        "revision": "B",
        "min_weight": 0.0,
        "max_weight": 10.0,
        "target_weight": 5.0,
    }
    payload.update(overrides)
    return payload


def test_erro_04_product_schema_requires_complete_label_metadata():
    product = schemas.ProductCreate(**_erro_04_payload())
    assert product.carton_id_prefix == "H"
    assert product.factory_item_code == "115-00020"

    with pytest.raises(ValidationError, match="carton_id_prefix"):
        schemas.ProductCreate(**_erro_04_payload(carton_id_prefix="X"))

    with pytest.raises(ValidationError, match="revision"):
        schemas.ProductCreate(**_erro_04_payload(revision=""))

    with pytest.raises(ValidationError, match="factory_item_code"):
        schemas.ProductCreate(**_erro_04_payload(factory_item_code=None))


def test_seed_erro_data_adds_exactly_the_16_complete_erro_04_products():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        seed_erro_data(db)
        erro = db.query(Customer).filter_by(code="ERRO").one()
        products = db.query(Product).filter_by(customer_id=erro.id, template_type="erro_04").all()

        assert len(products) == 16
        assert {product.item_name for product in products} == {
            "G111A1A", "G111B1A", "G111C1A", "G111D1A", "G111F1A",
            "G111A1B", "G111B1B", "G111C1B", "G111D1B", "G111F1B",
            "G111A1C", "G111B1C", "G111C1C", "G111D1C", "G111F1C", "G011C1B",
        }
        assert db.query(Product).filter_by(customer_id=erro.id, item_name="NYS6248").count() == 0

        reference = db.query(Product).filter_by(customer_id=erro.id, item_name="G111A1A").one()
        assert reference.upc == "840268939793"
        assert reference.mfr_pn == "NYS5896"
        assert reference.factory_item_code == "115-00020"
        assert reference.carton_id_prefix == "H"
        assert reference.packed_qty == 120
        assert reference.min_weight == 0.0
        assert reference.max_weight == 10.0
        assert reference.target_weight == 5.0

        seed_erro_data(db)
        assert db.query(Product).filter_by(customer_id=erro.id, template_type="erro_04").count() == 16
    finally:
        db.close()


def test_get_next_sn_returns_configured_erro_04_prefix_and_pd027032_id():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        seed_erro_data(db)
        product = db.query(Product).filter_by(item_name="G011C1B", template_type="erro_04").one()

        next_sn = product_service.get_next_sn(product.id, db)

        assert next_sn["next_seq"] == 1
        assert next_sn["next_sn"].startswith("K")
        assert next_sn["next_sn"].endswith("0001")
        assert next_sn["carton_id_prefix"] == "K"
    finally:
        db.close()


def test_product_api_creates_and_rejects_invalid_erro_04_metadata():
    from main import app

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    customer = Customer(code="ERRO", name="Erro")
    db.add(customer)
    seed_default_users(db)
    db.commit()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    try:
        login = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        payload = _erro_04_payload(customer_id=customer.id)

        created = client.post("/api/v1/products", json=payload, headers=headers)
        assert created.status_code == 200
        assert created.json()["carton_id_prefix"] == "H"
        assert created.json()["factory_item_code"] == "115-00020"

        invalid = client.post("/api/v1/products", json={**payload, "revision": ""}, headers=headers)
        assert invalid.status_code == 422

        update = client.put(f"/api/v1/products/{created.json()['id']}", json={"carton_id_prefix": "X"}, headers=headers)
        assert update.status_code == 422
    finally:
        app.dependency_overrides.clear()
        db.close()
