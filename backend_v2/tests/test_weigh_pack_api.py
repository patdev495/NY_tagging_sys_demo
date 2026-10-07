from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from src.core.database import Base, get_db
from src.core.models import Customer, Product


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Seed Erro Product
    db = TestingSessionLocal()
    customer = Customer(code="ERRO", name="Erro")
    db.add(customer)
    db.flush()

    product = Product(
        customer_id=customer.id,
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
        template_path=r"D:\PAT\Template\第1.btw",
    )
    db.add(product)
    db.commit()
    db.close()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_weigh_pack_api_success(client):
    res = client.post("/api/v1/cartons/weigh-pack", json={
        "product_id": 1,
        "weight": 12.520,
        "po_number": "PO-API-123",
        "lot_number": "LOT-API-456",
        "printer_name": "TSC_Printer"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["carton_sn"].startswith("VHK0010237")
    assert data["weight"] == 12.520
    assert data["po_number"] == "PO-API-123"
    assert data["lot_number"] == datetime.now().strftime("%Y%m%d")
    assert data["btxml"] is not None
    assert "<NamedSubString Name=\"CPN\"><Value>840-00091</Value></NamedSubString>" in data["btxml"]


def test_weigh_pack_api_out_of_tolerance(client):
    res = client.post("/api/v1/cartons/weigh-pack", json={
        "product_id": 1,
        "weight": 12.000,
        "po_number": "PO-API-123",
        "lot_number": "LOT-API-456",
    })
    assert res.status_code == 400
    assert "below minimum tolerance" in res.json()["error"]


def test_weigh_pack_api_assigns_generation_date_when_erro_01_lot_is_blank(client):
    res = client.post("/api/v1/cartons/weigh-pack", json={
        "product_id": 1,
        "weight": 12.520,
        "po_number": "PO-API-123",
        "lot_number": " ",
    })
    assert res.status_code == 200
    assert res.json()["lot_number"].isdigit()
    assert len(res.json()["lot_number"]) == 8
