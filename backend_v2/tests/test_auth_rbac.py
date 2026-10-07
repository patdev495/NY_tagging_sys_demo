
def test_password_hash_and_verify():
    from src.features.auth.security import hash_password, verify_password

    raw_password = "SecretPassword123!"
    hashed = hash_password(raw_password)

    # Must be hashed, not plaintext
    assert hashed != raw_password
    assert ":" in hashed  # contains salt:hash format

    # Correct password verifies to True
    assert verify_password(raw_password, hashed) is True

    # Wrong password verifies to False
    assert verify_password("WrongPassword", hashed) is False

def test_create_and_decode_token():

    from src.features.auth.security import create_access_token, decode_access_token

    payload = {"sub": "admin", "user_id": 1, "role": "admin"}
    token = create_access_token(payload, expires_delta_seconds=3600)

    assert isinstance(token, str)
    assert len(token) > 20

    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "admin"
    assert decoded["role"] == "admin"
    assert decoded["user_id"] == 1

    # Tampered token fails
    tampered_token = token[:-4] + "abcd"
    assert decode_access_token(tampered_token) is None

    # Expired token fails
    expired_token = create_access_token(payload, expires_delta_seconds=-10)
    assert decode_access_token(expired_token) is None

def test_user_seeding_and_authentication():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from src.core import models
    from src.core.database import Base
    from src.features.auth.service import authenticate_user, seed_default_users

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    try:
        # Initial seed
        seed_default_users(db)

        # Check users in DB
        admin = db.query(models.User).filter(models.User.username == "admin").first()
        assert admin is not None
        assert admin.role == "admin"

        qa = db.query(models.User).filter(models.User.username == "qa").first()
        assert qa is not None
        assert qa.role == "qa"

        # Idempotent seed
        seed_default_users(db)
        assert db.query(models.User).count() == 2

        # Authenticate valid credentials
        authed_admin = authenticate_user(db, "admin", "admin123")
        assert authed_admin is not None
        assert authed_admin.username == "admin"
        assert authed_admin.role == "admin"

        authed_qa = authenticate_user(db, "qa", "qa123")
        assert authed_qa is not None
        assert authed_qa.username == "qa"
        assert authed_qa.role == "qa"

        # Invalid password
        assert authenticate_user(db, "admin", "wrongpassword") is None
        # Non-existent user
        assert authenticate_user(db, "nobody", "pass") is None
    finally:
        db.close()

def test_auth_api_login_and_me():
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from main import app
    from src.core.database import Base, get_db
    from src.features.auth.service import seed_default_users

    # Create shared memory test DB with StaticPool
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    test_db = TestingSession()
    seed_default_users(test_db)


    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        # 1. Login with admin
        resp = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "admin"
        assert data["user"]["role"] == "admin"
        admin_token = data["access_token"]

        # 2. Login with qa
        resp_qa = client.post("/auth/login", json={"username": "qa", "password": "qa123"})
        assert resp_qa.status_code == 200
        data_qa = resp_qa.json()
        assert data_qa["user"]["username"] == "qa"
        assert data_qa["user"]["role"] == "qa"
        qa_token = data_qa["access_token"]

        # 3. Login with wrong credentials
        resp_bad = client.post("/auth/login", json={"username": "admin", "password": "bad"})
        assert resp_bad.status_code == 401

        # 4. GET /auth/me with admin token
        me_admin = client.get("/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
        assert me_admin.status_code == 200
        assert me_admin.json()["username"] == "admin"
        assert me_admin.json()["role"] == "admin"

        # 5. GET /auth/me with qa token
        me_qa = client.get("/auth/me", headers={"Authorization": f"Bearer {qa_token}"})
        assert me_qa.status_code == 200
        assert me_qa.json()["username"] == "qa"
        assert me_qa.json()["role"] == "qa"

        # 6. GET /auth/me with no or invalid token
        assert client.get("/auth/me").status_code == 401
        assert client.get("/auth/me", headers={"Authorization": "Bearer invalid_token"}).status_code == 401

    finally:
        app.dependency_overrides.clear()
        test_db.close()

def test_rbac_enforcement_blocks_qa():
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from main import app
    from src.core.database import Base, get_db
    from src.features.auth.service import seed_default_users

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    test_db = TestingSession()
    seed_default_users(test_db)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        # Get tokens
        admin_token = client.post("/auth/login", json={"username": "admin", "password": "admin123"}).json()["access_token"]
        qa_token = client.post("/auth/login", json={"username": "qa", "password": "qa123"}).json()["access_token"]

        # 1. Unauthenticated request to protected POST /api/v1/customers -> 401
        resp_unauth = client.post("/api/v1/customers", json={"code": "TEST1", "name": "Test 1"})
        assert resp_unauth.status_code == 401

        # 2. QA request to protected POST /api/v1/customers -> 403 Forbidden
        resp_qa = client.post(
            "/api/v1/customers",
            json={"code": "TEST_QA", "name": "Test QA"},
            headers={"Authorization": f"Bearer {qa_token}"}
        )
        assert resp_qa.status_code == 403

        # 3. Admin request to protected POST /api/v1/customers -> 200 OK (Allowed)
        resp_admin = client.post(
            "/api/v1/customers",
            json={"code": "TEST_ADM", "name": "Test Admin"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert resp_admin.status_code == 200

        # 4. QA request to DELETE /api/v1/cartons/999 -> 403 Forbidden
        resp_del_qa = client.delete(
            "/api/v1/cartons/999",
            headers={"Authorization": f"Bearer {qa_token}"}
        )
        assert resp_del_qa.status_code == 403

    finally:
        app.dependency_overrides.clear()
        test_db.close()




