import os
import sys

# MUST SET THIS BEFORE IMPORTING src.core.database
os.environ["DATABASE_URL"] = "sqlite:///database.db"

import pyodbc
from sqlalchemy.orm import sessionmaker

# Add current dir to path to import backend modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.config import settings
from src.core.database import Base
from src.core.database import engine as sqlite_engine
from src.core.models import Carton, CartonItem, Customer, Product


def migrate():
    # 1. Setup MSSQL Connection
    if settings.DB_USER:
        auth_str = f"UID={settings.DB_USER};PWD={settings.DB_PASS};"
    else:
        auth_str = "Trusted_Connection=yes;"

    mssql_conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={settings.DB_SERVER};"
        f"DATABASE={settings.DB_NAME};"
        f"{auth_str}"
        "Encrypt=no;"
        "TrustServerCertificate=yes;"
    )
    
    print(f"Connecting to MSSQL: {settings.DB_SERVER}...")
    try:
        mssql_conn = pyodbc.connect(mssql_conn_str)
        cursor = mssql_conn.cursor()
    except Exception as e:
        print(f"Failed to connect to MSSQL: {e}")
        return

    # 2. Setup SQLite
    print("Initializing SQLite database...")
    Base.metadata.create_all(bind=sqlite_engine)
    SessionLocal = sessionmaker(bind=sqlite_engine)
    session = SessionLocal()

    # 3. Migrate Customers
    print("Migrating Customers...")
    cursor.execute("SELECT id, code, name FROM customers")
    for row in cursor.fetchall():
        if not session.query(Customer).filter_by(id=row.id).first():
            session.add(Customer(id=row.id, code=row.code, name=row.name))
    session.commit()

    # 4. Migrate Products
    print("Migrating Products...")
    cursor.execute("SELECT id, customer_id, item_name, upc, packed_qty, start_part, middle_part, template_type, template_path, allow_partial FROM products")
    for row in cursor.fetchall():
        if not session.query(Product).filter_by(id=row.id).first():
            session.add(Product(
                id=row.id, customer_id=row.customer_id, item_name=row.item_name,
                upc=row.upc, packed_qty=row.packed_qty, start_part=row.start_part,
                middle_part=row.middle_part, template_type=row.template_type,
                template_path=row.template_path, allow_partial=row.allow_partial
            ))
    session.commit()

    # 5. Migrate Cartons (Limit to 5 per product for demo)
    print("Migrating Cartons (Limited to 5 latest per product for demo)...")
    
    # Get all product IDs from SQLite
    sqlite_product_ids = [p.id for p in session.query(Product.id).all()]
    
    migrated_carton_ids = []
    
    for product_id in sqlite_product_ids:
        # Get top 5 latest cartons for this product from MSSQL
        cursor.execute("""
            SELECT TOP 5 id, product_id, carton_sn, created_at, packed_by, job_order, status, btxml, is_reprint, carton_origin, station_id 
            FROM cartons 
            WHERE product_id = ? 
            ORDER BY created_at DESC
        """, (product_id,))
        
        rows = cursor.fetchall()
        for row in rows:
            migrated_carton_ids.append(row.id)
            if not session.query(Carton).filter_by(id=row.id).first():
                session.add(Carton(
                    id=row.id, product_id=row.product_id, carton_sn=row.carton_sn,
                    created_at=row.created_at, packed_by=row.packed_by, job_order=row.job_order,
                    status=row.status, btxml=row.btxml, is_reprint=row.is_reprint,
                    carton_origin=row.carton_origin, station_id=row.station_id
                ))
    session.commit()

    # 6. Migrate CartonItems (Only for the migrated cartons)
    print(f"Migrating CartonItems for {len(migrated_carton_ids)} cartons...")
    
    # Process in batches to avoid large IN clause
    batch_size = 500
    for i in range(0, len(migrated_carton_ids), batch_size):
        batch = migrated_carton_ids[i:i + batch_size]
        placeholders = ','.join(['?'] * len(batch))
        cursor.execute(f"SELECT id, carton_id, item_sn FROM carton_items WHERE carton_id IN ({placeholders})", batch)
        
        for row in cursor.fetchall():
            if not session.query(CartonItem).filter_by(id=row.id).first():
                session.add(CartonItem(id=row.id, carton_id=row.carton_id, item_sn=row.item_sn))
        session.commit()

    print("Migration completed successfully!")
    mssql_conn.close()
    session.close()

if __name__ == "__main__":
    migrate()
