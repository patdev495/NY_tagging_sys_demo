import os

import pyodbc
from dotenv import load_dotenv

# Load env
load_dotenv()

DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={DB_SERVER};DATABASE={DB_NAME};UID={DB_USER};PWD={DB_PASS};TrustServerCertificate=yes'

def migrate_paths():
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # 1. Lấy danh sách sản phẩm
        cursor.execute("SELECT id, item_name, template_path FROM products")
        products = cursor.fetchall()
        
        print(f"Found {len(products)} products.")
        
        updates = 0
        for pid, name, path in products:
            if not path:
                continue
                
            # Nếu path là đường dẫn tuyệt đối kiểu cũ
            if "D:\\PAT\\Templates\\" in path:
                # Lấy tên file
                filename = os.path.basename(path)
                print(f"Updating {name}: {path} -> {filename}")
                
                cursor.execute("UPDATE products SET template_path = ? WHERE id = ?", (filename, pid))
                updates += 1
        
        conn.commit()
        print(f"Successfully updated {updates} products.")
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    migrate_paths()
