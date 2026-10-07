import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    db_server = os.environ.get("DB_SERVER", "192.168.209.18")
    db_name = os.environ.get("DB_NAME", "NY_Tagging_sys")
    db_user = os.environ.get("DB_USER", "mis01")
    db_pass = os.environ.get("DB_PASS", "mis01")
    default_connection_string = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={db_server};"
        f"DATABASE={db_name};"
        f"UID={db_user};PWD={db_pass};"
        "Encrypt=no;"
        "TrustServerCertificate=yes;"
    )
    DATABASE_URL = f"mssql+pyodbc:///?odbc_connect={default_connection_string}"

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        row = conn.execute(text("SELECT * FROM products WHERE id = 59")).fetchone()
        print("Product 59 details:")
        if row:
            d = dict(row._mapping)
            for k, v in d.items():
                print(f"  {k}: {repr(v)}")
        else:
            print("Product 59 not found!")
except Exception as e:
    print("Error:", e)
