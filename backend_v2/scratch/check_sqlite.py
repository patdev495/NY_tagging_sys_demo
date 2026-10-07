import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Check products table
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", cursor.fetchall())

try:
    cursor.execute("SELECT id, item_name, packed_qty FROM products WHERE item_name LIKE '%Outdoor-2M-BK%'")
    print("SQLite Products matching 'Outdoor-2M-BK':", cursor.fetchall())
except Exception as e:
    print("Error querying products:", e)

try:
    cursor.execute("SELECT id, job_order, box_number, carton_sn, status FROM job_order_carton_slots WHERE job_order = '1232225'")
    print("SQLite Slots for '1232225':", cursor.fetchall())
except Exception as e:
    print("Error querying slots:", e)

conn.close()
