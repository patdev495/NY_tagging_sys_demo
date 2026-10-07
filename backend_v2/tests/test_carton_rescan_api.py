from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from src.core.database import Base, get_db
from src.core.models import Carton, CartonItem, Product


def test_rescan_updates_the_original_carton_when_reprints_exist():
    """A rescan must replace the original Carton Items, never a Reprint attempt."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(bind=engine)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        setup_db = testing_session()
        product = Product(
            item_name="UI-ITEM",
            packed_qty=40,
            allow_partial=0,
            template_type="detailed",
            template_path="carton.ui.btw",
        )
        original = Carton(
            product=product,
            carton_sn="CN26096800141",
            is_reprint=0,
            status="SUCCESS",
        )
        reprint = Carton(
            product=product,
            carton_sn="CN26096800141",
            is_reprint=1,
            status="SUCCESS",
        )
        setup_db.add_all([original, reprint])
        setup_db.flush()
        setup_db.add_all(
            [CartonItem(carton_id=original.id, item_sn=f"OLD-{index:02}") for index in range(12)]
        )
        setup_db.commit()
        original_id = original.id
        reprint_id = reprint.id
        setup_db.close()

        with TestClient(app) as client:
            response = client.put(
                "/api/v1/cartons/rescan",
                json={
                    "carton_sn": "CN26096800141",
                    "items": [f"NEW-{index:02}" for index in range(40)],
                },
            )

        assert response.status_code == 200, response.text
        assert response.json()["id"] == original_id
        assert "40 PCS" in response.json()["btxml"]

        verify_db = testing_session()
        try:
            assert verify_db.query(CartonItem).filter_by(carton_id=original_id).count() == 40
            assert verify_db.query(CartonItem).filter_by(carton_id=reprint_id).count() == 0
        finally:
            verify_db.close()
    finally:
        app.dependency_overrides.clear()
