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

def test_dashboard_kpis_calculation(db_session):
    from src.features.dashboard.service import get_dashboard_stats
    
    # 1. Setup Customer & Product
    customer = models.Customer(code="CUST01", name="Apple Inc")
    db_session.add(customer)
    db_session.commit()
    
    product = models.Product(
        customer_id=customer.id,
        item_name="iPhone 15 Case",
        upc="194253123456",
        packed_qty=10
    )
    db_session.add(product)
    db_session.commit()
    
    # 2. Setup Cartons for Today
    now = datetime.datetime.now()
    today_morning = now.replace(hour=8, minute=30, second=0, microsecond=0)
    today_noon = now.replace(hour=11, minute=15, second=0, microsecond=0)
    yesterday = now - datetime.timedelta(days=1)
    
    # Carton 1: SUCCESS, 2 items
    c1 = models.Carton(
        product_id=product.id,
        carton_sn="CN01-1001",
        created_at=today_morning,
        status="SUCCESS",
        is_reprint=0,
        weight=2.5
    )
    db_session.add(c1)
    db_session.flush()
    db_session.add(models.CartonItem(carton_id=c1.id, item_sn="ITEM-101"))
    db_session.add(models.CartonItem(carton_id=c1.id, item_sn="ITEM-102"))
    
    # Carton 2: FAILED, 0 items
    c2 = models.Carton(
        product_id=product.id,
        carton_sn="CN01-1002",
        created_at=today_morning.replace(minute=45),
        status="FAILED",
        is_reprint=0,
        weight=0.0
    )
    db_session.add(c2)
    
    # Carton 3: SUCCESS, REPRINT, 1 item
    c3 = models.Carton(
        product_id=product.id,
        carton_sn="CN01-1001",
        created_at=today_noon,
        status="SUCCESS",
        is_reprint=1,
        weight=2.5
    )
    db_session.add(c3)
    db_session.flush()
    db_session.add(models.CartonItem(carton_id=c3.id, item_sn="ITEM-101"))
    
    # Carton 4: Yesterday carton (should NOT be counted in 'today' filter)
    c4 = models.Carton(
        product_id=product.id,
        carton_sn="CN01-0999",
        created_at=yesterday,
        status="SUCCESS",
        is_reprint=0,
        weight=2.5
    )
    db_session.add(c4)
    db_session.flush()
    db_session.add(models.CartonItem(carton_id=c4.id, item_sn="ITEM-099"))
    
    db_session.commit()
    
    # 3. Test 'today' time_range
    stats_today = get_dashboard_stats(db_session, time_range="today")
    kpi = stats_today.kpis
    
    assert kpi.total_cartons == 3
    assert kpi.success_cartons == 2
    assert kpi.failed_cartons == 1
    assert kpi.reprint_cartons == 1
    assert kpi.total_items == 3  # 2 from c1 + 1 from c3
    assert round(kpi.success_rate, 1) == 66.7
    assert round(kpi.error_rate, 1) == 33.3
    assert round(kpi.reprint_rate, 1) == 33.3
    
    # 4. Test '7d' time_range (includes yesterday)
    stats_7d = get_dashboard_stats(db_session, time_range="7d")
    kpi_7d = stats_7d.kpis
    assert kpi_7d.total_cartons == 4
    assert kpi_7d.success_cartons == 3
    assert kpi_7d.failed_cartons == 1
    assert kpi_7d.total_items == 4

def test_dashboard_hourly_and_product_distribution(db_session):
    from src.features.dashboard.service import get_dashboard_stats

    # Create customers & products
    c1 = models.Customer(code="CUST_A", name="Company A")
    c2 = models.Customer(code="CUST_B", name="Company B")
    db_session.add_all([c1, c2])
    db_session.commit()

    p1 = models.Product(customer_id=c1.id, item_name="Widget Alpha", upc="1111", packed_qty=10)
    p2 = models.Product(customer_id=c2.id, item_name="Gadget Beta", upc="2222", packed_qty=5)
    db_session.add_all([p1, p2])
    db_session.commit()

    now = datetime.datetime.now()
    # Cartons in different hours
    t_08_15 = now.replace(hour=8, minute=15, second=0, microsecond=0)
    t_08_45 = now.replace(hour=8, minute=45, second=0, microsecond=0)
    t_14_20 = now.replace(hour=14, minute=20, second=0, microsecond=0)

    # 2 cartons for p1 at 08:00 (1 success, 1 failed)
    db_session.add(models.Carton(product_id=p1.id, carton_sn="SN01", created_at=t_08_15, status="SUCCESS"))
    db_session.add(models.Carton(product_id=p1.id, carton_sn="SN02", created_at=t_08_45, status="FAILED"))
    # 1 carton for p2 at 14:00 (success)
    db_session.add(models.Carton(product_id=p2.id, carton_sn="SN03", created_at=t_14_20, status="SUCCESS"))
    db_session.commit()

    stats = get_dashboard_stats(db_session, time_range="today")

    # Verify hourly throughput
    hourly = {item.hour: item for item in stats.hourly_throughput}
    assert "08:00" in hourly
    assert hourly["08:00"].total == 2
    assert hourly["08:00"].success == 1
    assert hourly["08:00"].failed == 1

    assert "14:00" in hourly
    assert hourly["14:00"].total == 1
    assert hourly["14:00"].success == 1
    assert hourly["14:00"].failed == 0

    # Hours with 0 production should still be represented (e.g. 09:00)
    assert "09:00" in hourly
    assert hourly["09:00"].total == 0

    # Verify top products breakdown
    top_products = stats.top_products
    assert len(top_products) == 2
    # p1 has 2 cartons out of 3 (66.7%)
    assert top_products[0].item_name == "Widget Alpha"
    assert top_products[0].customer_code == "CUST_A"
    assert top_products[0].count == 2
    assert round(top_products[0].percentage, 1) == 66.7

    # p2 has 1 carton out of 3 (33.3%)
    assert top_products[1].item_name == "Gadget Beta"
    assert top_products[1].customer_code == "CUST_B"
    assert top_products[1].count == 1
    assert round(top_products[1].percentage, 1) == 33.3

def test_dashboard_live_feed_and_system_health(db_session):
    from src.features.dashboard.service import get_dashboard_stats

    customer = models.Customer(code="CUST_X", name="X Corp")
    db_session.add(customer)
    db_session.commit()

    product = models.Product(customer_id=customer.id, item_name="Super Device", upc="9999", packed_qty=2)
    db_session.add(product)
    db_session.commit()

    # Create 20 cartons to verify that live feed is capped at 15 and ordered descending by id
    now = datetime.datetime.now()
    for i in range(1, 21):
        c = models.Carton(
            product_id=product.id,
            carton_sn=f"SN-{i:03d}",
            created_at=now + datetime.timedelta(minutes=i),
            status="SUCCESS" if i % 2 == 0 else "FAILED",
            is_reprint=1 if i == 20 else 0,
            station_id="STATION_01",
            weight=1.25 + i * 0.1
        )
        db_session.add(c)
        db_session.flush()
        # Add items to the 20th carton
        if i == 20:
            db_session.add(models.CartonItem(carton_id=c.id, item_sn="ITEM_A"))
            db_session.add(models.CartonItem(carton_id=c.id, item_sn="ITEM_B"))
    db_session.commit()

    stats = get_dashboard_stats(db_session, time_range="today")

    # Verify live feed
    live_feed = stats.live_feed
    assert len(live_feed) == 15
    # The most recent carton should be first (SN-020)
    top_carton = live_feed[0]
    assert top_carton.carton_sn == "SN-020"
    assert top_carton.item_name == "Super Device"
    assert top_carton.customer_code == "CUST_X"
    assert top_carton.is_reprint == 1
    assert top_carton.station_id == "STATION_01"
    assert top_carton.items_count == 2
    assert top_carton.status == "SUCCESS"

    # Verify system health exists
    assert stats.system is not None
    assert stats.system.bartender_status in ["ready", "offline"]
    assert isinstance(stats.system.active_printers_count, int)

def test_dashboard_api_endpoint_access():
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
        # 1. Without auth -> 401 Unauthorized
        unauth_resp = client.get("/api/v1/admin/dashboard/stats")
        assert unauth_resp.status_code == 401

        # 2. Login QA
        login_qa = client.post("/auth/login", json={"username": "qa", "password": "qa123"})
        assert login_qa.status_code == 200
        qa_token = login_qa.json()["access_token"]

        # 3. QA has READ access -> 200 OK
        qa_resp = client.get(
            "/api/v1/admin/dashboard/stats?time_range=today",
            headers={"Authorization": f"Bearer {qa_token}"}
        )
        assert qa_resp.status_code == 200
        data = qa_resp.json()
        assert "kpis" in data
        assert "hourly_throughput" in data
        assert "top_products" in data
        assert "live_feed" in data
        assert "system" in data

        # 4. Login Admin
        login_admin = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
        assert login_admin.status_code == 200
        admin_token = login_admin.json()["access_token"]

        # 5. Admin also has access -> 200 OK
        admin_resp = client.get(
            "/api/v1/admin/dashboard/stats?time_range=7d",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert admin_resp.status_code == 200
        assert admin_resp.json()["time_range"] == "7d"

        # 6. Test yesterday range
        yesterday_resp = client.get(
            "/api/v1/admin/dashboard/stats?time_range=yesterday",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert yesterday_resp.status_code == 200
        assert yesterday_resp.json()["time_range"] == "yesterday"

        # 7. Test custom date range
        custom_resp = client.get(
            "/api/v1/admin/dashboard/stats?time_range=custom&start_date=2026-09-01&end_date=2026-09-04",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert custom_resp.status_code == 200
        assert custom_resp.json()["time_range"] == "custom"
    finally:
        app.dependency_overrides.clear()



