from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from src.core.database import get_db
from src.core.models import Base, Customer, Product, ProductInternalFactoryPartNumber


def _setup_test_env():
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

    p = Product(
        customer_id=customer.id,
        item_name="840-00092",
        packed_qty=190,
        template_type="erro_01",
        template_path="templates/erro_01.btw",
        packing_mode="weight_scale",
        min_weight=5.5,
        max_weight=5.9,
    )
    db.add(p)
    db.flush()

    m = ProductInternalFactoryPartNumber(
        product_id=p.id,
        customer_id=customer.id,
        internal_factory_part_number="1LAE0091C2U005MAAS",
        source_drawing_code="PD014736",
    )
    db.add(m)
    db.commit()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    return client, db, customer, p, m


def test_resolve_erro_job_order_tracer_bullet_success():
    client, db, customer, product, mapping = _setup_test_env()
    try:
        mock_erp_return = {
            "job_order": "1259487",
            "product_code": "1LAE0091C2U005MAAS",
            "customer_ref": "840-00092",
            "quantity": 22800,
        }
        with patch("src.features.job_order.service.get_job_order_from_erp", return_value=mock_erp_return):
            response = client.get(
                "/api/v1/job-orders/resolve-erro-job-order",
                params={"job_order": "1259487"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["job_order"] == "1259487"
            assert data["factory_part_number"] == "1LAE0091C2U005MAAS"
            assert data["customer_ref"] == "840-00092"
            assert data["total_qty"] == 22800
            assert data["planned_cartons"] == 120  # ceil(22800 / 190) = 120
            assert data["name_mismatch"] is False
            assert data["lot_number_default"] and len(data["lot_number_default"]) == 8
            assert data["product"]["id"] == product.id
            assert data["product"]["item_name"] == "840-00092"
            assert data["product"]["template_type"] == "erro_01"
    finally:
        client.close()
        app.dependency_overrides.clear()
        db.close()


def test_resolve_erro_job_order_unmapped_factory_pn_returns_404():
    client, db, customer, product, mapping = _setup_test_env()
    try:
        mock_erp_return = {
            "job_order": "9999999",
            "product_code": "1LAENONEXISTENT",
            "customer_ref": "UNKNOWN-ITEM",
            "quantity": 1000,
        }
        with patch("src.features.job_order.service.get_job_order_from_erp", return_value=mock_erp_return):
            response = client.get(
                "/api/v1/job-orders/resolve-erro-job-order",
                params={"job_order": "9999999"},
            )
            assert response.status_code == 404
            err_msg = response.json().get("error") or response.json().get("detail")
            assert "chưa được cấu hình cho khách hàng Erro" in err_msg
    finally:
        client.close()
        app.dependency_overrides.clear()
        db.close()


def test_resolve_erro_job_order_reject_non_erro_customer():
    client, db, customer, product, mapping = _setup_test_env()
    try:
        # Create a non-erro customer and product
        ui_cust = Customer(code="UI", name="Universal Instruments")
        db.add(ui_cust)
        db.flush()
        ui_prod = Product(customer_id=ui_cust.id, item_name="UI-PROD-01", packed_qty=100)
        db.add(ui_prod)
        db.flush()
        ui_map = ProductInternalFactoryPartNumber(
            product_id=ui_prod.id,
            customer_id=ui_cust.id,
            internal_factory_part_number="1LAEUI0001",
            source_drawing_code="PD_UI",
        )
        db.add(ui_map)
        db.commit()

        mock_erp_return = {
            "job_order": "1234567",
            "product_code": "1LAEUI0001",
            "customer_ref": "UI-PROD-01",
            "quantity": 500,
        }
        with patch("src.features.job_order.service.get_job_order_from_erp", return_value=mock_erp_return):
            response = client.get(
                "/api/v1/job-orders/resolve-erro-job-order",
                params={"job_order": "1234567"},
            )
            # Since resolve_erro_product_by_internal_factory_part_number specifically filters Customer.code == "ERRO",
            # a UI product mapping won't be resolved as an Erro product, returning 404
            assert response.status_code in (400, 404)
    finally:
        client.close()
        app.dependency_overrides.clear()
        db.close()



def test_resolve_erro_job_order_detects_name_mismatch():
    client, db, customer, product, mapping = _setup_test_env()
    try:
        mock_erp_return = {
            "job_order": "1259487",
            "product_code": "1LAE0091C2U005MAAS",
            "customer_ref": "DIFFERENT_NAME_FROM_ERP",
            "quantity": 1900,
        }
        with patch("src.features.job_order.service.get_job_order_from_erp", return_value=mock_erp_return):
            response = client.get(
                "/api/v1/job-orders/resolve-erro-job-order",
                params={"job_order": "1259487"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["name_mismatch"] is True
            assert data["customer_ref"] == "DIFFERENT_NAME_FROM_ERP"
            assert data["product"]["item_name"] == "840-00092"
    finally:
        client.close()
        app.dependency_overrides.clear()
        db.close()


def test_resolve_erro_job_order_counts_existing_cartons():
    client, db, customer, product, mapping = _setup_test_env()
    try:
        from src.core.models import Carton
        # Seed existing cartons
        c1 = Carton(product_id=product.id, job_order="1259487", carton_sn="SN001", status="SUCCESS", is_reprint=0)
        c2 = Carton(product_id=product.id, job_order="1259487", carton_sn="SN002", status="SUCCESS", is_reprint=0)
        c3 = Carton(product_id=product.id, job_order="1259487", carton_sn="SN003", status="FAILED", is_reprint=0)  # failed, not counted
        c4 = Carton(product_id=product.id, job_order="1259487", carton_sn="SN001", status="SUCCESS", is_reprint=1)  # reprint, not counted
        db.add_all([c1, c2, c3, c4])
        db.commit()

        mock_erp_return = {
            "job_order": "1259487",
            "product_code": "1LAE0091C2U005MAAS",
            "customer_ref": "840-00092",
            "quantity": 1900,
        }
        with patch("src.features.job_order.service.get_job_order_from_erp", return_value=mock_erp_return):
            response = client.get(
                "/api/v1/job-orders/resolve-erro-job-order",
                params={"job_order": "1259487"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["packed_cartons_count"] == 2
            assert data["planned_cartons"] == 10  # 1900 / 190 = 10
    finally:
        client.close()
        app.dependency_overrides.clear()
        db.close()
