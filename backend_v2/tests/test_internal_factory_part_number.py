from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from src.core.database import get_db
from src.core.models import Base, Customer, Product
from src.features.auth.service import seed_default_users


def _client_with_erro_product(internal_factory_part_number: str = "1LAE0009D2U004MAAR"):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    db = session_factory()
    customer = Customer(code="ERRO", name="Erro")
    db.add(customer)
    db.flush()
    db.add(Product(
        customer_id=customer.id,
        item_name="G012C1B",
        internal_factory_part_number=internal_factory_part_number,
        packed_qty=190,
        template_type="erro_02",
        template_path="erro_02.btw",
        packing_mode="weight_scale",
    ))
    db.commit()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), db


def test_packing_station_resolves_erro_product_from_internal_factory_part_number():
    client, db = _client_with_erro_product()
    try:
        response = client.get(
            "/api/v1/products/resolve-internal-factory-part-number",
            params={"value": "  1lae0009d2u004maar  "},
        )

        assert response.status_code == 200
        product = response.json()
        assert product["item_name"] == "G012C1B"
        assert product["template_type"] == "erro_02"
        assert product["internal_factory_part_number"] == "1LAE0009D2U004MAAR"
    finally:
        client.close()
        app.dependency_overrides.clear()
        db.close()


def test_packing_station_rejects_unconfigured_internal_factory_part_number():
    client, db = _client_with_erro_product()
    try:
        response = client.get(
            "/api/v1/products/resolve-internal-factory-part-number",
            params={"value": "1LAEUNKNOWN"},
        )

        assert response.status_code == 404
        assert response.json()["error"] == "Factory P/N chưa được cấu hình cho khách hàng Erro."
    finally:
        client.close()
        app.dependency_overrides.clear()
        db.close()


def test_admin_can_create_erro_product_without_or_reject_duplicate_internal_factory_part_number():
    client, db = _client_with_erro_product()
    try:
        seed_default_users(db)
        db.commit()
        login = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        payload = {
            "customer_id": 1,
            "item_name": "840-00083",
            "packed_qty": 190,
            "template_type": "erro_01",
            "template_path": "erro_01.btw",
            "packing_mode": "weight_scale",
        }

        # 1. Product Erro can be created without Factory P/N (0 mappings initially allowed)
        created_no_pn = client.post("/api/v1/products", json=payload, headers=headers)
        assert created_no_pn.status_code == 200

        # 2. Product Erro with duplicate Factory P/N is rejected with 409
        duplicate = client.post(
            "/api/v1/products",
            json={**payload, "item_name": "840-00091", "internal_factory_part_number": "1LAE0009D2U004MAAR"},
            headers=headers,
        )

        assert duplicate.status_code == 409
        assert duplicate.json()["error"] == "Factory P/N đã được gán cho một Product Erro khác."
    finally:
        client.close()
        app.dependency_overrides.clear()
        db.close()

