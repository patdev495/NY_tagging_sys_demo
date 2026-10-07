from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.core.database import get_db, seed_erro_data
from src.core.models import Base, Customer, Product
from src.features.auth.service import seed_default_users


def test_admin_can_configure_erro_03_customer_project_and_production_stage():
    from main import app

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
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
        admin = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
        admin_headers = {"Authorization": f"Bearer {admin.json()['access_token']}"}
        payload = {
            "customer_id": customer.id,
            "item_name": "2M21-00508-0004H",
            "luxshare_part_number": "LLERJ014-NC-R",
            "packed_qty": 190,
                "template_type": "erro_03",
                "template_path": "erro_03.btw",
                "internal_factory_part_number": "1LAE0091C2U011NMES",
                "packing_mode": "weight_scale",
            "pkg_prefix": "1012665",
            "revision": "/",
            "product_desc": "CAT5E ETHERNET CABLE",
            "customer_project": "Andy Town/ Firefly",
            "production_stage": "MP",
        }

        created = client.post("/api/v1/products", json=payload, headers=admin_headers)

        assert created.status_code == 200
        assert created.json()["customer_project"] == "Andy Town/ Firefly"
        assert created.json()["production_stage"] == "MP"
        assert created.json()["luxshare_part_number"] == "LLERJ014-NC-R"

        qa = client.post("/auth/login", json={"username": "qa", "password": "qa123"})
        qa_headers = {"Authorization": f"Bearer {qa.json()['access_token']}"}
        rejected = client.put(
            f"/api/v1/products/{created.json()['id']}",
            json={"production_stage": "QB/CR"},
            headers=qa_headers,
        )
        assert rejected.status_code == 403
    finally:
        app.dependency_overrides.clear()
        db.close()


def test_erro_03_seed_backfills_eero_project_and_mp_production_stage():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        seed_erro_data(db)

        product = db.query(Product).filter_by(template_type="erro_03").one()

        assert product.customer_project == "Andy Town/ Firefly"
        assert product.production_stage == "MP"
        assert product.luxshare_part_number == "LLERJ014-NC-R"
    finally:
        db.close()
