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
        
        # 1. Query the Linked Server directly
        query_linked = text("""
            SELECT wadoco, walitm, wadl01, wauorg
            FROM [192.168.206.18].ShopFloorDW.DBO.F4801 
            WHERE wadoco = '1232225'
        """)
        row = conn.execute(query_linked).fetchone()
        print("Direct Linked Server row:", row)
        if row:
            # Let's check with wauorg/10000
            query_div = text("""
                SELECT wauorg/10000
                FROM [192.168.206.18].ShopFloorDW.DBO.F4801 
                WHERE wadoco = '1232225'
            """)
            div_val = conn.execute(query_div).scalar()
            print("wauorg/10000 in SQL:", div_val)
            
        # 2. Query what the database says for products
        query_prod = text("""
            SELECT id, item_name, packed_qty
            FROM products
            WHERE item_name LIKE '%Outdoor-2M-BK%' OR item_name LIKE '%1CAD2420D2BK01NX9%'
        """)
        prod_rows = conn.execute(query_prod).fetchall()
        print("Matching products in DB:", prod_rows)

        # 3. Query existing slots for job order '1232225'
        query_slots = text("""
            SELECT id, job_order, box_number, carton_sn, status, product_id
            FROM job_order_carton_slots
            WHERE job_order = '1232225'
        """)
        slots = conn.execute(query_slots).fetchall()
        print("Slots count in DB:", len(slots))
        for slot in slots[:5]:
            print("  Slot:", slot)
except Exception as e:
    print("Error:", e)
