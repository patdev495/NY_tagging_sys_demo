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
        print("Connected successfully!")
        
        # 1. Cartons with prefix CN260555%
        q_cartons = text("SELECT id, carton_sn, job_order, status FROM cartons WHERE carton_sn LIKE 'CN260555%'")
        cartons = conn.execute(q_cartons).fetchall()
        print("Cartons starting with CN260555 in DB:")
        for c in cartons:
            print("  Carton:", c)
            
        # 2. Slots with prefix CN260555%
        q_slots = text("SELECT id, job_order, box_number, carton_sn, status FROM job_order_carton_slots WHERE carton_sn LIKE 'CN260555%'")
        slots = conn.execute(q_slots).fetchall()
        print("Slots starting with CN260555 in DB:")
        for s in slots:
            print("  Slot:", s)
            
except Exception as e:
    print("Error:", e)
