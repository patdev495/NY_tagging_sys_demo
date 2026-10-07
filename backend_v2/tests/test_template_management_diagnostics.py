import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from src.core.database import Base, get_db
from src.features.auth.service import seed_default_users


@pytest.fixture
def test_setup():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    seed_default_users(db)

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    yield db, client

    app.dependency_overrides.clear()
    db.close()


def test_get_available_templates(test_setup):
    """Test GET /api/v1/print/templates returns available .btw templates."""
    _, client = test_setup

    response = client.get("/api/v1/print/templates")
    assert response.status_code == 200
    data = response.json()
    assert "templates" in data
    templates = data["templates"]
    assert isinstance(templates, list)
    assert len(templates) > 0

    names = [t["name"] for t in templates]
    # Known existing files in repo or resources/label_templates
    assert any("btw" in n.lower() for n in names)
    first = templates[0]
    assert "name" in first
    assert "path" in first
    assert "size_bytes" in first
    assert "updated_at" in first


def test_validate_template_endpoint(test_setup):
    """Test POST /api/v1/print/validate-template returns valid status for existing vs missing."""
    _, client = test_setup

    # Existing template (e.g. carton_base.btw or a11.btw)
    resp_valid = client.post("/api/v1/print/validate-template", json={"template_name": "carton_base.btw"})
    assert resp_valid.status_code == 200
    data_valid = resp_valid.json()
    assert data_valid["valid"] is True
    assert data_valid["resolved_path"] is not None

    # Missing template
    resp_invalid = client.post("/api/v1/print/validate-template", json={"template_name": "totally_missing_file_9999.btw"})
    assert resp_invalid.status_code == 200
    data_invalid = resp_invalid.json()
    assert data_invalid["valid"] is False


def test_restart_engine_rbac_and_recovery(test_setup):
    """Test POST /api/v1/print/restart-engine enforces Admin RBAC."""
    _, client = test_setup

    # QA login
    resp_qa = client.post("/auth/login", json={"username": "qa", "password": "qa123"})
    qa_headers = {"Authorization": f"Bearer {resp_qa.json()['access_token']}"}

    # Admin login
    resp_admin = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    admin_headers = {"Authorization": f"Bearer {resp_admin.json()['access_token']}"}

    # QA call should be blocked (403)
    resp_blocked = client.post("/api/v1/print/restart-engine", headers=qa_headers)
    assert resp_blocked.status_code == 403

    # Admin call should succeed (200)
    resp_ok = client.post("/api/v1/print/restart-engine", headers=admin_headers)
    assert resp_ok.status_code == 200
    data = resp_ok.json()
    assert data["success"] is True
    assert "bartender_ready" in data


def test_get_canonical_templates(test_setup):
    """Test GET /api/v1/print/canonical-templates returns all canonical templates."""
    _, client = test_setup
    resp = client.get("/api/v1/print/canonical-templates")
    assert resp.status_code == 200
    data = resp.json()
    assert "templates" in data
    assert len(data["templates"]) == 10
    filenames = [t["filename"] for t in data["templates"]]
    assert "erro_05.btw" in filenames
    assert "erro_04.btw" in filenames
    assert "erro_03.btw" in filenames
    assert "erro_02.btw" in filenames
    assert "erro_01.btw" in filenames
    assert "carton_base.btw" in filenames
    assert "Carton_45.btw" in filenames
    assert "carton_detail_1M_W.btw" in filenames
    assert "carton_detail_2_3M_W.btw" in filenames
    assert "carton_detail_UISP_Connector_SHD.btw" in filenames
