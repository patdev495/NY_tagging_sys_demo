from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.core import models
from src.core.database import Base, get_db
from src.features.auth.service import seed_default_users
from main import create_app


def test_admin_can_check_an_unscanned_job_orders_slot_allocation():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = testing_session()
    try:
        seed_default_users(db)
        customer = models.Customer(code="UI", name="Universal Instruments")
        db.add(customer)
        db.flush()
        product = models.Product(customer_id=customer.id, item_name="UI Cable", packed_qty=10)
        db.add(product)
        db.flush()
        db.add_all([
            models.JobOrderCartonSlot(
                job_order="1257157", product_id=product.id, carton_number=1,
                carton_sn="CN261000001", status="PENDING",
            ),
            models.JobOrderCartonSlot(
                job_order="1257157", product_id=product.id, carton_number=2,
                carton_sn="CN261000002", status="PENDING",
            ),
        ])
        db.commit()

        app = create_app()

        def override_get_db():
            session = testing_session()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as client:
            login = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
            assert login.status_code == 200
            headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

            response = client.get(
                "/api/v1/admin/production-runs/job-orders/1257157/cancellation-check",
                headers=headers,
            )
            qa_login = client.post("/auth/login", json={"username": "qa", "password": "qa123"})
            assert qa_login.status_code == 200
            qa_response = client.get(
                "/api/v1/admin/production-runs/job-orders/1257157/cancellation-check",
                headers={"Authorization": f"Bearer {qa_login.json()['access_token']}"},
            )

        assert response.status_code == 200
        assert response.json() == {
            "job_order": "1257157",
            "total_slots": 2,
            "scanned_slots": 0,
            "can_cancel": True,
        }
        assert qa_response.status_code == 403
    finally:
        app.dependency_overrides.clear()
        db.close()


def test_admin_can_delete_an_unscanned_job_orders_slot_allocation():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = testing_session()
    try:
        seed_default_users(db)
        customer = models.Customer(code="UI", name="Universal Instruments")
        db.add(customer)
        db.flush()
        product = models.Product(customer_id=customer.id, item_name="UI Cable", packed_qty=10)
        db.add(product)
        db.flush()
        db.add_all([
            models.JobOrderCartonSlot(
                job_order="1257157", product_id=product.id, carton_number=1,
                carton_sn="CN261000001", status="PENDING",
            ),
            models.JobOrderCartonSlot(
                job_order="1257157", product_id=product.id, carton_number=2,
                carton_sn="CN261000002", status="PENDING",
            ),
        ])
        db.commit()

        app = create_app()

        def override_get_db():
            session = testing_session()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as client:
            login = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
            assert login.status_code == 200
            headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

            response = client.delete(
                "/api/v1/admin/production-runs/job-orders/1257157/slots",
                headers=headers,
            )
            check = client.get(
                "/api/v1/admin/production-runs/job-orders/1257157/cancellation-check",
                headers=headers,
            )

        assert response.status_code == 200
        assert response.json() == {"job_order": "1257157", "deleted_slots": 2}
        assert check.status_code == 200
        assert check.json()["total_slots"] == 0
        assert check.json()["can_cancel"] is False
    finally:
        app.dependency_overrides.clear()
        db.close()


def test_admin_cannot_delete_slot_allocation_when_a_job_order_has_a_carton():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = testing_session()
    try:
        seed_default_users(db)
        customer = models.Customer(code="UI", name="Universal Instruments")
        db.add(customer)
        db.flush()
        product = models.Product(customer_id=customer.id, item_name="UI Cable", packed_qty=10)
        db.add(product)
        db.flush()
        db.add(models.JobOrderCartonSlot(
            job_order="1257157", product_id=product.id, carton_number=1,
            carton_sn="CN261000001", status="PENDING",
        ))
        db.add(models.Carton(
            product_id=product.id, job_order="1257157", carton_sn="CN261000001", status="SUCCESS",
        ))
        db.commit()

        app = create_app()

        def override_get_db():
            session = testing_session()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as client:
            login = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
            assert login.status_code == 200
            headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

            check = client.get(
                "/api/v1/admin/production-runs/job-orders/1257157/cancellation-check",
                headers=headers,
            )
            response = client.delete(
                "/api/v1/admin/production-runs/job-orders/1257157/slots",
                headers=headers,
            )

        assert check.status_code == 200
        assert check.json()["can_cancel"] is False
        assert check.json()["scanned_slots"] == 1
        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()
        db.close()
