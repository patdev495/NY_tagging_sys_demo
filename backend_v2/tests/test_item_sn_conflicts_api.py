from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from src.core.database import Base, get_db
from src.core.models import Carton, CartonItem, Customer, JobOrderCartonSlot, Product


def test_item_sn_conflicts_returns_only_ui_cartons_and_excludes_the_rescan_target():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        db = session_factory()
        ui = Customer(code="UI", name="Universal Instruments")
        erro = Customer(code="ERRO", name="Erro")
        db.add_all([ui, erro])
        db.flush()
        ui_product = Product(customer_id=ui.id, item_name="UI Cable", packed_qty=40)
        erro_product = Product(customer_id=erro.id, item_name="Erro Cable", packed_qty=40)
        db.add_all([ui_product, erro_product])
        db.flush()
        first_ui_carton = Carton(product_id=ui_product.id, carton_sn="UI-001", job_order="JO-1", status="SUCCESS")
        second_ui_carton = Carton(product_id=ui_product.id, carton_sn="UI-002", job_order="JO-2", status="FAILED")
        erro_carton = Carton(product_id=erro_product.id, carton_sn="ERRO-001", status="SUCCESS")
        db.add_all([first_ui_carton, second_ui_carton, erro_carton])
        db.flush()
        db.add_all([
            CartonItem(carton_id=first_ui_carton.id, item_sn="ITEM-DUP"),
            CartonItem(carton_id=second_ui_carton.id, item_sn="ITEM-DUP"),
            CartonItem(carton_id=erro_carton.id, item_sn="ITEM-DUP"),
        ])
        db.commit()

        with TestClient(app) as client:
            response = client.get("/api/v1/cartons/item-sn-conflicts", params={"item_sn": "ITEM-DUP"})
            excluded_response = client.get(
                "/api/v1/cartons/item-sn-conflicts",
                params={"item_sn": "ITEM-DUP", "exclude_carton_id": first_ui_carton.id},
            )
            empty_response = client.get("/api/v1/cartons/item-sn-conflicts", params={"item_sn": "ITEM-NEW"})

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["item_sn"] == "ITEM-DUP"
        assert {carton["carton_sn"] for carton in body["conflicts"]} == {"UI-001", "UI-002"}
        assert all("items" not in carton and "btxml" not in carton for carton in body["conflicts"])

        assert excluded_response.status_code == 200
        assert [carton["carton_sn"] for carton in excluded_response.json()["conflicts"]] == ["UI-002"]
        assert empty_response.status_code == 200
        assert empty_response.json() == {"item_sn": "ITEM-NEW", "conflicts": []}
    finally:
        app.dependency_overrides.clear()


def test_create_carton_rejects_an_item_sn_owned_by_another_ui_carton():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        db = session_factory()
        ui = Customer(code="UI", name="Universal Instruments")
        db.add(ui)
        db.flush()
        product = Product(customer_id=ui.id, item_name="UI Cable", packed_qty=1, allow_partial=0)
        db.add(product)
        db.flush()
        owner = Carton(product_id=product.id, carton_sn="UI-OWNER", status="SUCCESS")
        slot = JobOrderCartonSlot(
            job_order="JO-NEW", product_id=product.id, carton_number=1, carton_sn="UI-NEW", status="PENDING"
        )
        db.add_all([owner, slot])
        db.flush()
        db.add(CartonItem(carton_id=owner.id, item_sn="ITEM-OWNED"))
        db.commit()

        with TestClient(app) as client:
            response = client.post(
                "/api/v1/cartons",
                json={
                    "product_id": product.id,
                    "job_order": "JO-NEW",
                    "slot_id": slot.id,
                    "items": ["ITEM-OWNED"],
                },
            )

        assert response.status_code == 409, response.text
        assert response.json()["code"] == "ITEM_SN_CONFLICT"
        assert response.json()["error"]["conflicts"]["ITEM-OWNED"][0]["carton_sn"] == "UI-OWNER"
    finally:
        app.dependency_overrides.clear()
