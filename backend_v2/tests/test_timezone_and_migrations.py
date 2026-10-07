import datetime

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.core import models
from src.core.database import Base, init_db


def test_carton_created_at_defaults_to_local_time():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    
    with Session() as db:
        product = models.Product(item_name="Test Prod", packed_qty=10)
        db.add(product)
        db.flush()

        before = datetime.datetime.now()
        carton = models.Carton(product_id=product.id, carton_sn="VN26081100001")
        db.add(carton)
        db.commit()
        db.refresh(carton)
        after = datetime.datetime.now()

        assert carton.created_at is not None
        assert before - datetime.timedelta(seconds=2) <= carton.created_at <= after + datetime.timedelta(seconds=2)


def test_migration_timezone_utc_to_local(monkeypatch):
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)

    # Insert a carton with a known simulated UTC timestamp
    with test_engine.connect() as conn:
        conn.execute(text("INSERT INTO cartons (carton_sn, created_at, status) VALUES ('TEST_UTC', '2026-08-27 01:00:00', 'SUCCESS')"))
        conn.commit()

    monkeypatch.setattr("src.core.database.engine", test_engine)
    monkeypatch.setattr("src.core.database.SessionLocal", sessionmaker(bind=test_engine))

    init_db()

    with test_engine.connect() as conn:
        res = conn.execute(text("SELECT created_at FROM cartons WHERE carton_sn = 'TEST_UTC'")).scalar()
        # In SQLite, datetime('2026-08-27 01:00:00', '+7 hours') is '2026-08-27 08:00:00'
        assert str(res) == "2026-08-27 08:00:00"

        # Verify migration record was recorded
        migrated = conn.execute(text("SELECT version FROM schema_migrations WHERE version = 'cartons_timezone_utc_to_local_v1'")).scalar()
        assert migrated == "cartons_timezone_utc_to_local_v1"

    # Running init_db() a second time must be idempotent (not shift another 7 hours)
    init_db()
    with test_engine.connect() as conn:
        res_second = conn.execute(text("SELECT created_at FROM cartons WHERE carton_sn = 'TEST_UTC'")).scalar()
        assert str(res_second) == "2026-08-27 08:00:00"
