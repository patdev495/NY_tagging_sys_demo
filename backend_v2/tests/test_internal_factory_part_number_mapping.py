from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from src.core.database import get_db
from src.core.models import Base, Customer, Product, ProductInternalFactoryPartNumber
from src.features.auth.service import seed_default_users


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

    p1 = Product(
        customer_id=customer.id,
        item_name="G111D1A",
        packed_qty=66,
        template_type="erro_04",
        template_path="erro_04.btw",
        packing_mode="weight_scale",
        mfr_pn="NYS5945",
        upc="840268972110",
        factory_item_code="115-00023",
        carton_id_prefix="H",
        revision="A",
        product_desc="Accessory, Ethernet Cable CAT6a, 152cm, Black, 1PK, Basic Box",
    )
    p2 = Product(
        customer_id=customer.id,
        item_name="G012C1B",
        packed_qty=190,
        template_type="erro_02",
        template_path="erro_02.btw",
        packing_mode="weight_scale",
    )
    db.add_all([p1, p2])
    db.flush()

    m1 = ProductInternalFactoryPartNumber(
        product_id=p1.id,
        customer_id=customer.id,
        internal_factory_part_number="1LAX0005F2U001MAA",
        source_drawing_code="PD027032",
    )
    m2 = ProductInternalFactoryPartNumber(
        product_id=p1.id,
        customer_id=customer.id,
        internal_factory_part_number="1LAX0005F2U001MAAR",
        source_drawing_code="PD027032",
    )
    db.add_all([m1, m2])
    db.commit()

    seed_default_users(db)
    db.commit()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    return client, db, customer, p1, p2


def test_multiple_factory_part_numbers_resolve_to_same_product():
    client, db, customer, p1, p2 = _setup_test_env()
    try:
        # First mapping
        r1 = client.get(
            "/api/v1/products/resolve-internal-factory-part-number",
            params={"value": "  1lax0005f2u001maa  "},
        )
        assert r1.status_code == 200
        data1 = r1.json()
        assert data1["id"] == p1.id
        assert data1["item_name"] == "G111D1A"
        assert data1["template_type"] == "erro_04"

        # Second mapping for the same product
        r2 = client.get(
            "/api/v1/products/resolve-internal-factory-part-number",
            params={"value": "1LAX0005F2U001MAAR"},
        )
        assert r2.status_code == 200
        data2 = r2.json()
        assert data2["id"] == p1.id
        assert data2["item_name"] == "G111D1A"
        assert data2["template_type"] == "erro_04"
    finally:
        client.close()
        app.dependency_overrides.clear()
        db.close()


def test_resolve_unconfigured_factory_part_number_returns_404():
    client, db, customer, p1, p2 = _setup_test_env()
    try:
        res = client.get(
            "/api/v1/products/resolve-internal-factory-part-number",
            params={"value": "1LAXNONEXISTENT"},
        )
        assert res.status_code == 404
        assert res.json()["error"] == "Factory P/N chưa được cấu hình cho khách hàng Erro."
    finally:
        client.close()
        app.dependency_overrides.clear()
        db.close()


def test_admin_crud_internal_factory_part_numbers():
    client, db, customer, p1, p2 = _setup_test_env()
    try:
        login = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # 1. Get mappings for p1
        res = client.get(f"/api/v1/products/{p1.id}/internal-factory-part-numbers", headers=headers)
        assert res.status_code == 200
        mappings = res.json()
        assert len(mappings) == 2
        part_numbers = {m["internal_factory_part_number"] for m in mappings}
        assert part_numbers == {"1LAX0005F2U001MAA", "1LAX0005F2U001MAAR"}

        # 2. Add new mapping to p2
        res_add = client.post(
            f"/api/v1/products/{p2.id}/internal-factory-part-numbers",
            json={"internal_factory_part_number": "1LAE0009D2U004MAAR", "source_drawing_code": "PD027504"},
            headers=headers,
        )
        assert res_add.status_code == 200
        new_mapping = res_add.json()
        assert new_mapping["internal_factory_part_number"] == "1LAE0009D2U004MAAR"
        assert new_mapping["source_drawing_code"] == "PD027504"

        # 3. Add duplicate mapping should fail with 409
        res_dup = client.post(
            f"/api/v1/products/{p1.id}/internal-factory-part-numbers",
            json={"internal_factory_part_number": "1LAE0009D2U004MAAR", "source_drawing_code": "PD027504"},
            headers=headers,
        )
        assert res_dup.status_code == 409

        # 4. Batch add mappings
        res_batch = client.post(
            f"/api/v1/products/{p2.id}/internal-factory-part-numbers/batch",
            json={
                "items": [
                    {"internal_factory_part_number": "1LAE0003F2U001MAA", "source_drawing_code": "PD027504"},
                    {"internal_factory_part_number": "1LAE0009D2U001MAA", "source_drawing_code": "PD027504"},
                ]
            },
            headers=headers,
        )
        assert res_batch.status_code == 200
        assert len(res_batch.json()) == 2

        # 5. Delete mapping
        res_del = client.delete(
            f"/api/v1/products/{p2.id}/internal-factory-part-numbers/{new_mapping['id']}",
            headers=headers,
        )
        assert res_del.status_code == 200

        # Verify deleted
        res_check = client.get(
            "/api/v1/products/resolve-internal-factory-part-number",
            params={"value": "1LAE0009D2U004MAAR"},
        )
        assert res_check.status_code == 404
    finally:
        client.close()
        app.dependency_overrides.clear()
        db.close()


def test_legacy_migration_copies_products_internal_factory_part_number_idempotently():
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
        item_name="G012C1B",
        packed_qty=190,
        template_type="erro_02",
        template_path="erro_02.btw",
        packing_mode="weight_scale",
        internal_factory_part_number="1LAE0009D2U004MAAR",
    )
    db.add(p)
    db.commit()

    # Run the migration logic
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO product_internal_factory_part_numbers (product_id, customer_id, internal_factory_part_number, source_drawing_code, created_at, updated_at)
            SELECT p.id, p.customer_id, UPPER(TRIM(p.internal_factory_part_number)), 'LEGACY', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            FROM products p
            WHERE p.internal_factory_part_number IS NOT NULL 
              AND TRIM(p.internal_factory_part_number) != ''
              AND NOT EXISTS (
                  SELECT 1 FROM product_internal_factory_part_numbers m 
                  WHERE m.customer_id = p.customer_id 
                    AND UPPER(m.internal_factory_part_number) = UPPER(TRIM(p.internal_factory_part_number))
              )
        """))
        conn.commit()

    mappings = db.query(ProductInternalFactoryPartNumber).filter(ProductInternalFactoryPartNumber.product_id == p.id).all()
    assert len(mappings) == 1
    assert mappings[0].internal_factory_part_number == "1LAE0009D2U004MAAR"
    assert mappings[0].source_drawing_code == "LEGACY"

    # Run migration again to verify idempotency
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO product_internal_factory_part_numbers (product_id, customer_id, internal_factory_part_number, source_drawing_code, created_at, updated_at)
            SELECT p.id, p.customer_id, UPPER(TRIM(p.internal_factory_part_number)), 'LEGACY', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            FROM products p
            WHERE p.internal_factory_part_number IS NOT NULL 
              AND TRIM(p.internal_factory_part_number) != ''
              AND NOT EXISTS (
                  SELECT 1 FROM product_internal_factory_part_numbers m 
                  WHERE m.customer_id = p.customer_id 
                    AND UPPER(m.internal_factory_part_number) = UPPER(TRIM(p.internal_factory_part_number))
              )
        """))
        conn.commit()

    mappings_second_run = db.query(ProductInternalFactoryPartNumber).filter(ProductInternalFactoryPartNumber.product_id == p.id).all()
    assert len(mappings_second_run) == 1

    db.close()


def test_import_erro_factory_part_numbers_logic(tmp_path):
    import csv
    from unittest.mock import patch

    from scripts.import_erro_factory_part_numbers import run_import

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
        item_name="G111D1A",
        packed_qty=66,
        template_type="erro_04",
        template_path="erro_04.btw",
        packing_mode="weight_scale",
    )
    db.add(p)
    db.commit()
    target_product_id = p.id
    db.close()

    csv_file = tmp_path / "test_staging.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source_drawing_code", "internal_factory_part_number", "source_product_identifier", "resolved_product_id", "template_type", "status", "confidence", "notes"])
        writer.writerow(["PD027032", "1LAX0005F2U001MAA", "G111D1A", "", "erro_04", "READY", "HIGH", ""])
        writer.writerow(["PD027032", "1LAX0005F2U001MAAR", "G111D1A", "", "erro_04", "READY", "HIGH", ""])
        writer.writerow(["PD027032", "1LA92815C2U001MAA", "NYS6248", "", "erro_04", "MISSING_PRODUCT", "LOW", ""])

    # Test DRY RUN
    with patch("scripts.import_erro_factory_part_numbers.SessionLocal", side_effect=session_factory):
        with patch("scripts.import_erro_factory_part_numbers.init_db"):
            run_import(str(csv_file), apply=False)

    check_db = session_factory()
    mappings_after_dry_run = check_db.query(ProductInternalFactoryPartNumber).all()
    assert len(mappings_after_dry_run) == 0
    check_db.close()

    # Test APPLY
    with patch("scripts.import_erro_factory_part_numbers.SessionLocal", side_effect=session_factory):
        with patch("scripts.import_erro_factory_part_numbers.init_db"):
            run_import(str(csv_file), apply=True)

    check_db = session_factory()
    mappings_after_apply = check_db.query(ProductInternalFactoryPartNumber).filter(ProductInternalFactoryPartNumber.product_id == target_product_id).all()
    assert len(mappings_after_apply) == 2
    part_numbers = {m.internal_factory_part_number for m in mappings_after_apply}
    assert part_numbers == {"1LAX0005F2U001MAA", "1LAX0005F2U001MAAR"}
    check_db.close()

    # Test RE-APPLY (Idempotent)
    with patch("scripts.import_erro_factory_part_numbers.SessionLocal", side_effect=session_factory):
        with patch("scripts.import_erro_factory_part_numbers.init_db"):
            run_import(str(csv_file), apply=True)

    check_db = session_factory()
    mappings_after_reapply = check_db.query(ProductInternalFactoryPartNumber).filter(ProductInternalFactoryPartNumber.product_id == target_product_id).all()
    assert len(mappings_after_reapply) == 2
    check_db.close()


