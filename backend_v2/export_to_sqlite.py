"""
export_to_sqlite.py — DEMO VERSION
===================================
Export dữ liệu từ MSSQL production sang SQLite cho môi trường demo.

Chạy từ thư mục backend_v2/:
    uv run python export_to_sqlite.py

Yêu cầu:
- Máy nội bộ có thể kết nối DB_SERVER (192.168.209.18)
- File .env đã cấu hình DB_SERVER / DB_NAME / DB_USER / DB_PASS
- uv đã cài sẵn các dependency (pyodbc, sqlalchemy, passlib...)
"""
import os
import sys

# Force UTF-8 encoding for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Must set DATABASE_URL BEFORE importing any src module
os.environ["DATABASE_URL"] = "sqlite:///database.db"

import pyodbc
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.config import settings
from src.core.database import Base, engine as sqlite_engine
from src.core.models import (
    Carton, CartonItem, Customer, Product,
    ProductInternalFactoryPartNumber, JobOrderCartonSlot, User,
)
from src.features.auth.security import hash_password

CARTON_LIMIT_PER_PRODUCT = 20  # TOP N cartons per product


# ── helpers ──────────────────────────────────────────────────────────────────

def _str(v) -> str | None:
    return str(v).strip() if v is not None else None

def _int(v) -> int | None:
    try:
        return int(v) if v is not None else None
    except Exception:
        return None

def _float(v) -> float | None:
    try:
        return float(v) if v is not None else None
    except Exception:
        return None


# ── main migration ────────────────────────────────────────────────────────────

def migrate():
    # 1. Connect MSSQL
    if settings.DB_USER:
        auth_str = f"UID={settings.DB_USER};PWD={settings.DB_PASS};"
    else:
        auth_str = "Trusted_Connection=yes;"

    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={settings.DB_SERVER};"
        f"DATABASE={settings.DB_NAME};"
        f"{auth_str}"
        "Encrypt=no;TrustServerCertificate=yes;"
    )

    print(f"Connecting to MSSQL: {settings.DB_SERVER} / {settings.DB_NAME} ...")
    try:
        mssql = pyodbc.connect(conn_str)
        cur = mssql.cursor()
        print("  ✓ Connected")
    except Exception as e:
        print(f"  ✗ MSSQL connection failed: {e}")
        return

    # 2. Init SQLite schema
    print("Initializing SQLite database ...")
    Base.metadata.create_all(bind=sqlite_engine)
    Session = sessionmaker(bind=sqlite_engine)
    db = Session()
    print("  ✓ Schema ready")

    # 3. Customers
    print("Migrating Customers ...")
    cur.execute("SELECT id, code, name FROM customers")
    n = 0
    for row in cur.fetchall():
        if not db.query(Customer).filter_by(id=row.id).first():
            db.add(Customer(id=row.id, code=_str(row.code), name=_str(row.name)))
            n += 1
    db.commit()
    print(f"  ✓ {n} customers inserted")

    # 4. Products — full schema
    print("Migrating Products ...")
    cur.execute("""
        SELECT
            id, customer_id, item_name, upc, packed_qty, start_part, middle_part,
            template_type, template_path, allow_partial,
            packing_mode, target_weight, min_weight, max_weight, weight_unit,
            mfr_pn, pkg_prefix, revision, asin, product_desc,
            customer_project, production_stage, luxshare_part_number,
            internal_factory_part_number, factory_item_code, carton_id_prefix
        FROM products
    """)
    n = 0
    for row in cur.fetchall():
        if not db.query(Product).filter_by(id=row.id).first():
            db.add(Product(
                id=row.id,
                customer_id=_int(row.customer_id),
                item_name=_str(row.item_name),
                upc=_str(row.upc),
                packed_qty=_int(row.packed_qty),
                start_part=_str(row.start_part),
                middle_part=_str(row.middle_part),
                template_type=_str(row.template_type),
                template_path=_str(row.template_path),
                allow_partial=_int(row.allow_partial),
                packing_mode=_str(row.packing_mode),
                target_weight=_float(row.target_weight),
                min_weight=_float(row.min_weight),
                max_weight=_float(row.max_weight),
                weight_unit=_str(row.weight_unit),
                mfr_pn=_str(row.mfr_pn),
                pkg_prefix=_str(row.pkg_prefix),
                revision=_str(row.revision),
                asin=_str(row.asin),
                product_desc=_str(row.product_desc),
                customer_project=_str(row.customer_project),
                production_stage=_str(row.production_stage),
                luxshare_part_number=_str(row.luxshare_part_number),
                internal_factory_part_number=_str(row.internal_factory_part_number),
                factory_item_code=_str(row.factory_item_code),
                carton_id_prefix=_str(row.carton_id_prefix),
            ))
            n += 1
    db.commit()
    print(f"  ✓ {n} products inserted")

    # 5. ProductInternalFactoryPartNumbers
    print("Migrating ProductInternalFactoryPartNumbers ...")
    try:
        cur.execute("""
            SELECT id, product_id, customer_id, internal_factory_part_number,
                   source_drawing_code, created_at, updated_at
            FROM product_internal_factory_part_numbers
        """)
        n = 0
        for row in cur.fetchall():
            if not db.query(ProductInternalFactoryPartNumber).filter_by(id=row.id).first():
                db.add(ProductInternalFactoryPartNumber(
                    id=row.id,
                    product_id=row.product_id,
                    customer_id=row.customer_id,
                    internal_factory_part_number=_str(row.internal_factory_part_number),
                    source_drawing_code=_str(row.source_drawing_code) or "",
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                ))
                n += 1
        db.commit()
        print(f"  ✓ {n} factory part number mappings inserted")
    except Exception as e:
        db.rollback()
        print(f"  ⚠ Skipped (table may not exist): {e}")

    # 6. Cartons — TOP N per product
    print(f"Migrating Cartons (TOP {CARTON_LIMIT_PER_PRODUCT} per product, SUCCESS only) ...")
    product_ids = [p.id for p in db.query(Product.id).all()]
    migrated_carton_ids: list[int] = []
    n = 0
    for product_id in product_ids:
        cur.execute(f"""
            SELECT TOP {CARTON_LIMIT_PER_PRODUCT}
                id, product_id, carton_sn, created_at, packed_by, job_order,
                status, btxml, is_reprint, carton_origin, station_id,
                weight, po_number, lot_number, date_code, admin_creation_reason
            FROM cartons
            WHERE product_id = ? AND status = 'SUCCESS'
            ORDER BY created_at DESC
        """, (product_id,))
        for row in cur.fetchall():
            migrated_carton_ids.append(row.id)
            if not db.query(Carton).filter_by(id=row.id).first():
                db.add(Carton(
                    id=row.id,
                    product_id=row.product_id,
                    carton_sn=_str(row.carton_sn),
                    created_at=row.created_at,
                    packed_by=_str(row.packed_by),
                    job_order=_str(row.job_order),
                    status=_str(row.status),
                    btxml=None,  # strip BTXML — not needed for demo, saves space
                    is_reprint=_int(row.is_reprint),
                    carton_origin=_str(row.carton_origin),
                    station_id=_str(row.station_id),
                    weight=_float(row.weight),
                    po_number=_str(row.po_number),
                    lot_number=_str(row.lot_number),
                    date_code=_str(row.date_code),
                    admin_creation_reason=_str(row.admin_creation_reason),
                ))
                n += 1
    db.commit()
    print(f"  ✓ {n} cartons inserted ({len(migrated_carton_ids)} total tracked)")

    # 7. CartonItems (batch)
    print(f"Migrating CartonItems for {len(migrated_carton_ids)} cartons ...")
    n = 0
    batch_size = 500
    for i in range(0, len(migrated_carton_ids), batch_size):
        batch = migrated_carton_ids[i:i + batch_size]
        ph = ",".join(["?"] * len(batch))
        cur.execute(f"SELECT id, carton_id, item_sn FROM carton_items WHERE carton_id IN ({ph})", batch)
        for row in cur.fetchall():
            if not db.query(CartonItem).filter_by(id=row.id).first():
                db.add(CartonItem(id=row.id, carton_id=row.carton_id, item_sn=_str(row.item_sn)))
                n += 1
        db.commit()
    print(f"  ✓ {n} carton items inserted")

    # 8. Seed demo admin account
    print("Seeding demo accounts ...")
    _seed_user(db, username="admin", password="demo123", role="admin", full_name="Demo Admin")
    _seed_user(db, username="qa",    password="demo123", role="qa",    full_name="Demo QA")
    db.commit()
    print("  ✓ admin / demo123  (role: admin)")
    print("  ✓ qa    / demo123  (role: qa)")

    mssql.close()
    db.close()

    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")
    size_mb = os.path.getsize(db_path) / 1024 / 1024
    print(f"\n✅ Export complete! database.db — {size_mb:.1f} MB")
    print("   Next: copy database.db to the demo server under backend_v2/")


def _seed_user(db, username: str, password: str, role: str, full_name: str):
    existing = db.query(User).filter_by(username=username).first()
    if existing:
        existing.password_hash = hash_password(password)
        existing.role = role
        existing.full_name = full_name
        existing.is_active = 1
    else:
        db.add(User(
            username=username,
            password_hash=hash_password(password),
            role=role,
            full_name=full_name,
            is_active=1,
        ))


if __name__ == "__main__":
    migrate()
