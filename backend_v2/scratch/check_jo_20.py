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
        
        # 1. Product details
        query_prod = text("""
            SELECT id, item_name, start_part, middle_part, packed_qty
            FROM products
            WHERE item_name LIKE '%Outdoor-8M-BK%'
        """)
        prod = conn.execute(query_prod).fetchone()
        print("Product details:", prod)
        
        # 2. Existing cartons with prefix CN%55%
        # Let's search for cartons starting with CN260555 or just ending with 55%
        query_cartons = text("""
            SELECT id, carton_sn, job_order, status
            FROM cartons
            WHERE carton_sn LIKE 'CN%55%'
        """)
        cartons = conn.execute(query_cartons).fetchall()
        print("Cartons count with prefix 55 in DB:", len(cartons))
        for c in cartons[:5]:
            print("  Carton:", c)
            
        # 3. Existing slots with prefix CN%55%
        query_slots = text("""
            SELECT id, job_order, box_number, carton_sn, status
            FROM job_order_carton_slots
            WHERE carton_sn LIKE 'CN%55%'
        """)
        slots = conn.execute(query_slots).fetchall()
        print("Slots count with prefix 55 in DB:", len(slots))
        for s in slots[:10]:
            print("  Slot:", s)
            
        # 4. Check details of Job Order 1232227
        query_jo = text("""
            SELECT id, box_number, carton_sn, status
            FROM job_order_carton_slots
            WHERE job_order = '1232227'
            ORDER BY box_number
        """)
        jo_slots = conn.execute(query_jo).fetchall()
        print("Job Order 1232227 slots count:", len(jo_slots))
        for s in jo_slots[:5]:
            print("  Slot:", s)
            
except Exception as e:
    print("Error:", e)
