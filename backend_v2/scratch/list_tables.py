import os
from sqlalchemy import create_engine, inspect
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
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("Tables in NY_Tagging_sys:")
    for t in tables:
        print(f"  - {t}")
        # print columns for each table
        columns = inspector.get_columns(t)
        col_names = [c['name'] for c in columns]
        print(f"    Columns: {col_names}")
except Exception as e:
    print("Error:", e)
