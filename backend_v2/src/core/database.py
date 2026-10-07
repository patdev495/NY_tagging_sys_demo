import logging
import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from src.core.config import settings

logger = logging.getLogger("Database")

# Connection string for pyodbc
DATABASE_URL = os.environ.get("DATABASE_URL", "")
print(f"DEBUG: DATABASE_URL is '{DATABASE_URL}'")

if not DATABASE_URL:
    # Build MSSQL connection string only as a fallback
    if settings.DB_USER:
        auth_str = f"UID={settings.DB_USER};PWD={settings.DB_PASS};"
    else:
        auth_str = "Trusted_Connection=yes;"

    default_connection_string = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={settings.DB_SERVER};"
        f"DATABASE={settings.DB_NAME};"
        f"{auth_str}"
        "Encrypt=no;"
        "TrustServerCertificate=yes;"
    )
    DATABASE_URL = f"mssql+pyodbc:///?odbc_connect={default_connection_string}"

# Create engine
if "sqlite" in DATABASE_URL.lower():
    print("DEBUG: Using SQLite engine")
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    print(f"DEBUG: Using non-SQLite engine (URL starts with {DATABASE_URL[:10]}...)")
    try:
        import pyodbc
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=1800,
            pool_size=10,
            max_overflow=20,
            fast_executemany=True,
        )
    except ImportError:
        print("ERROR: pyodbc not found but DATABASE_URL is not SQLite. Falling back to dummy engine to prevent crash.")
        engine = create_engine("sqlite:///:memory:") 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from src.core.database_migrations import (
    migrate_legacy_erro_data,
    seed_erro_data,
    seed_erro_factory_part_number_mappings,
)


def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully (if not existed).")
        
        # Lightweight migrations for existing installations.
        inspector = inspect(engine)
        is_sqlite = "sqlite" in str(engine.url).lower()

        with engine.connect() as conn:
            # Exact Item SN lookup is on the packing-station hot path.  Existing
            # deployments need this index because create_all only creates it for
            # fresh databases.
            if inspector.has_table("carton_items"):
                if is_sqlite:
                    conn.execute(text(
                        "CREATE INDEX IF NOT EXISTS ix_carton_items_item_sn_carton_id "
                        "ON carton_items (item_sn, carton_id)"
                    ))
                else:
                    conn.execute(text(
                        "IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = "
                        "'ix_carton_items_item_sn_carton_id' AND object_id = OBJECT_ID('carton_items')) "
                        "CREATE INDEX ix_carton_items_item_sn_carton_id ON carton_items (item_sn, carton_id)"
                    ))
                conn.commit()

            # 1. Migrate job_order_carton_slots
            if inspector.has_table('job_order_carton_slots'):
                slot_cols = [c['name'] for c in inspector.get_columns('job_order_carton_slots')]
                if 'box_number' in slot_cols and 'carton_number' not in slot_cols:
                    logger.info("Migrating: renaming job_order_carton_slots.box_number to carton_number")
                    if is_sqlite:
                        conn.execute(text("ALTER TABLE job_order_carton_slots RENAME COLUMN box_number TO carton_number"))
                    else:
                        conn.execute(text("EXEC sp_rename 'job_order_carton_slots.box_number', 'carton_number', 'COLUMN'"))
                    conn.commit()

                if 'shipped' not in slot_cols:
                    logger.info("Migrating: adding job_order_carton_slots.shipped")
                    if is_sqlite:
                        conn.execute(text("ALTER TABLE job_order_carton_slots ADD COLUMN shipped INTEGER NOT NULL DEFAULT 0"))
                    else:
                        conn.execute(text("ALTER TABLE job_order_carton_slots ADD shipped INT NOT NULL CONSTRAINT DF_job_order_carton_slots_shipped DEFAULT 0 WITH VALUES"))
                    conn.commit()

            # 2. Migrate products table for weight_scale columns
            if inspector.has_table('products'):
                prod_cols = [c['name'] for c in inspector.get_columns('products')]
                new_prod_cols = [
                    ('packing_mode', 'VARCHAR(50) DEFAULT \'item_scan\'', 'VARCHAR(50) DEFAULT \'item_scan\''),
                    ('target_weight', 'FLOAT NULL', 'FLOAT NULL'),
                    ('min_weight', 'FLOAT NULL', 'FLOAT NULL'),
                    ('max_weight', 'FLOAT NULL', 'FLOAT NULL'),
                    ('weight_unit', 'VARCHAR(10) DEFAULT \'kg\'', 'VARCHAR(10) DEFAULT \'kg\''),
                    ('mfr_pn', 'VARCHAR(50) NULL', 'VARCHAR(50) NULL'),
                    ('pkg_prefix', 'VARCHAR(20) NULL', 'VARCHAR(20) NULL'),
                    ('revision', 'VARCHAR(10) DEFAULT \'B\'', 'VARCHAR(10) DEFAULT \'B\''),
                    ('asin', 'VARCHAR(50) NULL', 'VARCHAR(50) NULL'),
                    ('product_desc', 'VARCHAR(255) NULL', 'VARCHAR(255) NULL'),
                    ('customer_project', 'VARCHAR(255) NULL', 'VARCHAR(255) NULL'),
                    ('production_stage', 'VARCHAR(20) NULL', 'VARCHAR(20) NULL'),
                    ('luxshare_part_number', 'VARCHAR(100) NULL', 'VARCHAR(100) NULL'),
                    ('internal_factory_part_number', 'VARCHAR(100) NULL', 'VARCHAR(100) NULL'),
                    ('factory_item_code', 'VARCHAR(50) NULL', 'VARCHAR(50) NULL'),
                    ('carton_id_prefix', 'VARCHAR(1) NULL', 'VARCHAR(1) NULL'),
                ]
                for col_name, sqlite_type, mssql_type in new_prod_cols:
                    if col_name not in prod_cols:
                        logger.info(f"Migrating products table: adding column {col_name}")
                        col_type = sqlite_type if is_sqlite else mssql_type
                        conn.execute(text(f"ALTER TABLE products ADD COLUMN {col_name} {col_type}" if is_sqlite else f"ALTER TABLE products ADD {col_name} {col_type}"))
                        conn.commit()

                # Drop obsolete unique index on products(customer_id, internal_factory_part_number) to release 1-1 constraint
                if is_sqlite:
                    conn.execute(text("DROP INDEX IF EXISTS ux_products_customer_internal_factory_part_number"))
                else:
                    conn.execute(text(
                        "IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'ux_products_customer_internal_factory_part_number' "
                        "AND object_id = OBJECT_ID('products')) "
                        "DROP INDEX ux_products_customer_internal_factory_part_number ON products"
                    ))
                conn.commit()

                # 5. Migrate product_internal_factory_part_numbers table and copy legacy 1-1 values
                if is_sqlite:
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS product_internal_factory_part_numbers (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                            customer_id INTEGER NOT NULL REFERENCES customers(id),
                            internal_factory_part_number VARCHAR(100) NOT NULL,
                            source_drawing_code VARCHAR(20) NOT NULL,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    conn.execute(text(
                        "CREATE UNIQUE INDEX IF NOT EXISTS ux_pifpn_customer_part_no "
                        "ON product_internal_factory_part_numbers (customer_id, internal_factory_part_number)"
                    ))
                    conn.commit()
                else:
                    conn.execute(text("""
                        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='product_internal_factory_part_numbers' AND xtype='U')
                        CREATE TABLE product_internal_factory_part_numbers (
                            id INT IDENTITY(1,1) PRIMARY KEY,
                            product_id INT NOT NULL CONSTRAINT FK_pifpn_product FOREIGN KEY REFERENCES products(id) ON DELETE CASCADE,
                            customer_id INT NOT NULL CONSTRAINT FK_pifpn_customer FOREIGN KEY REFERENCES customers(id),
                            internal_factory_part_number VARCHAR(100) NOT NULL,
                            source_drawing_code VARCHAR(20) NOT NULL,
                            created_at DATETIME DEFAULT GETDATE(),
                            updated_at DATETIME DEFAULT GETDATE()
                        )
                    """))
                    conn.execute(text("""
                        IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'ux_pifpn_customer_part_no' 
                        AND object_id = OBJECT_ID('product_internal_factory_part_numbers'))
                        CREATE UNIQUE INDEX ux_pifpn_customer_part_no 
                        ON product_internal_factory_part_numbers (customer_id, internal_factory_part_number)
                    """))
                    conn.commit()

                # Copy any existing non-empty values from products.internal_factory_part_number into mapping table (idempotently)
                if inspector.has_table('products') and 'internal_factory_part_number' in [c['name'] for c in inspector.get_columns('products')]:
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
                    """ if is_sqlite else """
                        INSERT INTO product_internal_factory_part_numbers (product_id, customer_id, internal_factory_part_number, source_drawing_code, created_at, updated_at)
                        SELECT p.id, p.customer_id, UPPER(LTRIM(RTRIM(p.internal_factory_part_number))), 'LEGACY', GETDATE(), GETDATE()
                        FROM products p
                        WHERE p.internal_factory_part_number IS NOT NULL 
                          AND LTRIM(RTRIM(p.internal_factory_part_number)) != ''
                          AND NOT EXISTS (
                              SELECT 1 FROM product_internal_factory_part_numbers m 
                              WHERE m.customer_id = p.customer_id 
                                AND UPPER(m.internal_factory_part_number) = UPPER(LTRIM(RTRIM(p.internal_factory_part_number)))
                          )
                    """))
                    conn.commit()

                # Factory P/N was never used by the Erro label formats. Remove
                # the obsolete storage column and its optional index.
                if 'factory_pn' in prod_cols:
                    logger.info("Migrating products table: removing obsolete factory_pn")
                    if is_sqlite:
                        conn.execute(text("DROP INDEX IF EXISTS ix_products_factory_pn"))
                        conn.execute(text("ALTER TABLE products DROP COLUMN factory_pn"))
                    else:
                        conn.execute(text(
                            "IF EXISTS (SELECT 1 FROM sys.indexes "
                            "WHERE name = 'ix_products_factory_pn' "
                            "AND object_id = OBJECT_ID('products')) "
                            "DROP INDEX ix_products_factory_pn ON products"
                        ))
                        conn.execute(text("ALTER TABLE products DROP COLUMN factory_pn"))
                    conn.commit()

            # 3. Migrate cartons table for weight & PO/LOT/date_code columns
            if inspector.has_table('cartons'):
                carton_cols = [c['name'] for c in inspector.get_columns('cartons')]
                new_carton_cols = [
                    ('weight', 'FLOAT NULL', 'FLOAT NULL'),
                    ('po_number', 'VARCHAR(100) NULL', 'VARCHAR(100) NULL'),
                    ('lot_number', 'VARCHAR(100) NULL', 'VARCHAR(100) NULL'),
                    ('date_code', 'VARCHAR(20) NULL', 'VARCHAR(20) NULL'),
                    ('admin_creation_reason', 'VARCHAR(500) NULL', 'VARCHAR(500) NULL'),
                ]
                for col_name, sqlite_type, mssql_type in new_carton_cols:
                    if col_name not in carton_cols:
                        logger.info(f"Migrating cartons table: adding column {col_name}")
                        col_type = sqlite_type if is_sqlite else mssql_type
                        conn.execute(text(f"ALTER TABLE cartons ADD COLUMN {col_name} {col_type}" if is_sqlite else f"ALTER TABLE cartons ADD {col_name} {col_type}"))
                        conn.commit()

            # 4. Migrate historical UTC timestamps in cartons to Local Time (+7 hours)
            if inspector.has_table('cartons'):
                conn.execute(text(
                    "CREATE TABLE IF NOT EXISTS schema_migrations (version VARCHAR(100) PRIMARY KEY, applied_at DATETIME)"
                    if is_sqlite else
                    "IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='schema_migrations' AND xtype='U') CREATE TABLE schema_migrations (version VARCHAR(100) PRIMARY KEY, applied_at DATETIME)"
                ))
                conn.commit()

                res = conn.execute(text("SELECT version FROM schema_migrations WHERE version = 'cartons_timezone_utc_to_local_v1'")).first()
                if not res:
                    logger.info("Migrating: adjusting historical cartons.created_at (+7 hours to local time)")
                    if is_sqlite:
                        conn.execute(text("UPDATE cartons SET created_at = datetime(created_at, '+7 hours') WHERE created_at IS NOT NULL"))
                        conn.execute(text("INSERT INTO schema_migrations (version, applied_at) VALUES ('cartons_timezone_utc_to_local_v1', datetime('now'))"))
                    else:
                        conn.execute(text("UPDATE cartons SET created_at = DATEADD(hour, 7, created_at) WHERE created_at IS NOT NULL"))
                        conn.execute(text("INSERT INTO schema_migrations (version, applied_at) VALUES ('cartons_timezone_utc_to_local_v1', GETDATE())"))
                    conn.commit()

        # Run seed data
        with SessionLocal() as db:
            migrate_legacy_erro_data(db)
            seed_erro_data(db)
            seed_erro_factory_part_number_mappings(db)
            try:
                from src.features.auth.service import seed_default_users
                seed_default_users(db)
            except Exception as e:
                logger.warning(f"Seed default users notice: {e}")

    except Exception as e:
        logger.error(f"Failed to initialize or migrate database tables: {e}")
