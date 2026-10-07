import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.core import models
from src.core.database import Base


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_get_job_orders_summary(db_session):
    from src.features.production_run.service import get_job_orders_summary

    # Setup customer & product
    customer = models.Customer(code="CUST_FOX", name="Foxconn")
    db_session.add(customer)
    db_session.commit()

    product = models.Product(
        customer_id=customer.id,
        item_name="Mainboard B650",
        upc="987654321",
        packed_qty=10
    )
    db_session.add(product)
    db_session.commit()

    now = datetime.datetime.now()

    # Job Order JO-1001: 4 slots: 2 SCANNED (1 shipped), 2 PENDING
    for i in range(1, 5):
        slot = models.JobOrderCartonSlot(
            job_order="JO-1001",
            product_id=product.id,
            carton_number=i,
            carton_sn=f"SN-JO1001-{i:03d}",
            status="SCANNED" if i <= 2 else "PENDING",
            scanned_at=now if i <= 2 else None,
            shipped=1 if i == 1 else 0
        )
        db_session.add(slot)

    # Job Order JO-1002: 2 slots: 2 SCANNED (100% completed)
    for i in range(1, 3):
        slot = models.JobOrderCartonSlot(
            job_order="JO-1002",
            product_id=product.id,
            carton_number=i,
            carton_sn=f"SN-JO1002-{i:03d}",
            status="SCANNED",
            scanned_at=now,
            shipped=0
        )
        db_session.add(slot)

    db_session.commit()

    summaries = get_job_orders_summary(db_session)
    assert len(summaries) == 2

    # Map by job_order
    summary_map = {s.job_order: s for s in summaries}

    jo1 = summary_map["JO-1001"]
    assert jo1.product_name == "Mainboard B650"
    assert jo1.customer_code == "CUST_FOX"
    assert jo1.total_slots == 4
    assert jo1.scanned_slots == 2
    assert jo1.pending_slots == 2
    assert jo1.shipped_slots == 1
    assert jo1.completion_rate == 50.0
    assert jo1.latest_scan_at is not None

    jo2 = summary_map["JO-1002"]
    assert jo2.total_slots == 2
    assert jo2.scanned_slots == 2
    assert jo2.pending_slots == 0
    assert jo2.shipped_slots == 0
    assert jo2.completion_rate == 100.0


def test_get_job_orders_summary_excludes_erro_slot_records(db_session):
    from src.features.production_run.service import get_job_orders_summary

    ui_customer = models.Customer(code="UI", name="UI")
    erro_customer = models.Customer(code="ERRO", name="Erro")
    db_session.add_all([ui_customer, erro_customer])
    db_session.flush()
    ui_product = models.Product(customer_id=ui_customer.id, item_name="UI Product", packed_qty=10)
    erro_product = models.Product(
        customer_id=erro_customer.id,
        item_name="840-00092",
        packed_qty=190,
        packing_mode="weight_scale",
        template_type="erro_01",
    )
    db_session.add_all([ui_product, erro_product])
    db_session.flush()
    db_session.add_all([
        models.JobOrderCartonSlot(
            job_order="UI-WO-001", product_id=ui_product.id, carton_number=1,
            carton_sn="UI-SLOT-001", status="PENDING",
        ),
        models.JobOrderCartonSlot(
            job_order="ERRO-WO-001", product_id=erro_product.id, carton_number=1,
            carton_sn="ERRO-SLOT-001", status="PENDING",
        ),
    ])
    db_session.commit()

    summaries = get_job_orders_summary(db_session)

    assert [summary.job_order for summary in summaries] == ["UI-WO-001"]

def test_get_job_order_slots_details(db_session):
    from src.features.production_run.service import get_job_order_slots

    customer = models.Customer(code="CUST_X", name="X Corp")
    erro_customer = models.Customer(code="ERRO", name="Erro")
    db_session.add_all([customer, erro_customer])
    db_session.flush()

    product = models.Product(customer_id=customer.id, item_name="Phone Case", upc="112233", packed_qty=10)
    erro_product = models.Product(
        customer_id=erro_customer.id,
        item_name="840-00092",
        upc="000000000001",
        packed_qty=190,
        packing_mode="weight_scale",
        template_type="erro_01",
    )
    db_session.add_all([product, erro_product])
    db_session.flush()

    now = datetime.datetime.now()
    # Add slots 1 to 3
    db_session.add(models.JobOrderCartonSlot(
        job_order="JO-2000", product_id=product.id, carton_number=1,
        carton_sn="SN-JO2000-001", status="SCANNED", scanned_at=now, shipped=1
    ))
    db_session.add(models.JobOrderCartonSlot(
        job_order="JO-2000", product_id=product.id, carton_number=2,
        carton_sn="SN-JO2000-002", status="SCANNED", scanned_at=now, shipped=0
    ))
    db_session.add(models.JobOrderCartonSlot(
        job_order="JO-2000", product_id=product.id, carton_number=3,
        carton_sn="SN-JO2000-003", status="PENDING", scanned_at=None, shipped=0
    ))
    db_session.add(models.JobOrderCartonSlot(
        job_order="JO-2000", product_id=erro_product.id, carton_number=4,
        carton_sn="ERRO-SLOT-001", status="PENDING", scanned_at=None, shipped=0
    ))
    db_session.commit()

    slots = get_job_order_slots(db_session, "JO-2000")
    assert len(slots) == 3
    assert slots[0].carton_number == 1
    assert slots[0].carton_sn == "SN-JO2000-001"
    assert slots[0].status == "SCANNED"
    assert slots[0].shipped == 1

    assert slots[2].carton_number == 3
    assert slots[2].status == "PENDING"
    assert slots[2].shipped == 0

def test_get_po_lot_runs_aggregation(db_session):
    from src.features.production_run.service import get_po_lot_runs

    customer = models.Customer(code="CUST_A11", name="A11 Client")
    db_session.add(customer)
    db_session.commit()

    product = models.Product(
        customer_id=customer.id,
        item_name="Precision Bearing",
        upc="554433",
        packed_qty=1,
        packing_mode="weight_scale"
    )
    db_session.add(product)
    db_session.commit()

    now = datetime.datetime.now()

    # Add 2 cartons with PO-999 / LOT-AAA (weight 5.0 and 5.5 = 10.5 kg)
    db_session.add(models.Carton(
        product_id=product.id,
        carton_sn="SN-PO999-01",
        po_number="PO-999",
        lot_number="LOT-AAA",
        date_code="260904",
        weight=5.0,
        status="SUCCESS",
        created_at=now
    ))
    db_session.add(models.Carton(
        product_id=product.id,
        carton_sn="SN-PO999-02",
        po_number="PO-999",
        lot_number="LOT-AAA",
        date_code="260904",
        weight=5.5,
        status="SUCCESS",
        created_at=now + datetime.timedelta(minutes=5)
    ))

    # Add 1 carton with PO-888 / LOT-BBB (weight 8.0 kg)
    db_session.add(models.Carton(
        product_id=product.id,
        carton_sn="SN-PO888-01",
        po_number="PO-888",
        lot_number="LOT-BBB",
        date_code="260903",
        weight=8.0,
        status="SUCCESS",
        created_at=now - datetime.timedelta(days=1)
    ))

    # Add 1 standard carton without PO (should not be included in po-runs)
    db_session.add(models.Carton(
        product_id=product.id,
        carton_sn="SN-NOPO-01",
        status="SUCCESS",
        created_at=now
    ))

    db_session.commit()

    runs = get_po_lot_runs(db_session)
    assert len(runs) == 2

    run_map = {(r.po_number, r.lot_number): r for r in runs}

    run_999 = run_map[("PO-999", "LOT-AAA")]
    assert run_999.product_name == "Precision Bearing"
    assert run_999.customer_code == "CUST_A11"
    assert run_999.date_code == "260904"
    assert run_999.total_cartons == 2
    assert run_999.total_weight == 10.5

    run_888 = run_map[("PO-888", "LOT-BBB")]
    assert run_888.total_cartons == 1
    assert run_888.total_weight == 8.0

def test_production_runs_api_endpoints():
    from fastapi.testclient import TestClient

    from main import create_app
    from src.core.database import Base, get_db
    from src.features.auth.service import seed_default_users

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()
    seed_default_users(db)

    # Seed customer, product, job order slot, and PO carton
    c = models.Customer(code="CUST_T", name="Test Customer")
    db.add(c)
    db.commit()

    p = models.Product(customer_id=c.id, item_name="Test Product", upc="0001", packed_qty=5)
    db.add(p)
    db.commit()

    db.add(models.JobOrderCartonSlot(
        job_order="JO-9999", product_id=p.id, carton_number=1, carton_sn="SN-JO-9999-1", status="PENDING"
    ))
    db.add(models.Carton(
        product_id=p.id, carton_sn="SN-PO-1", po_number="PO-123", lot_number="LOT-ABC", weight=4.2, status="SUCCESS"
    ))
    db.commit()

    app = create_app()

    def override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        # 1. Unauthenticated -> 401
        assert client.get("/api/v1/admin/production-runs/job-orders").status_code == 401
        assert client.get("/api/v1/admin/production-runs/job-orders/JO-9999/slots").status_code == 401
        assert client.get("/api/v1/admin/production-runs/po-runs").status_code == 401

        # 2. Login QA
        login_qa = client.post("/auth/login", json={"username": "qa", "password": "qa123"})
        assert login_qa.status_code == 200
        qa_token = login_qa.json()["access_token"]
        qa_headers = {"Authorization": f"Bearer {qa_token}"}

        # 3. QA access -> 200 OK on all 3 endpoints
        resp_jo = client.get("/api/v1/admin/production-runs/job-orders", headers=qa_headers)
        assert resp_jo.status_code == 200
        assert len(resp_jo.json()) == 1
        assert resp_jo.json()[0]["job_order"] == "JO-9999"

        resp_slots = client.get("/api/v1/admin/production-runs/job-orders/JO-9999/slots", headers=qa_headers)
        assert resp_slots.status_code == 200
        assert len(resp_slots.json()) == 1
        assert resp_slots.json()[0]["carton_number"] == 1

        resp_po = client.get("/api/v1/admin/production-runs/po-runs", headers=qa_headers)
        assert resp_po.status_code == 200
        assert len(resp_po.json()) == 1
        assert resp_po.json()[0]["po_number"] == "PO-123"

        # 4. Login Admin -> 200 OK
        login_admin = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
        assert login_admin.status_code == 200
        admin_token = login_admin.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        resp_admin = client.get("/api/v1/admin/production-runs/job-orders", headers=admin_headers)
        assert resp_admin.status_code == 200
    finally:
        app.dependency_overrides.clear()
