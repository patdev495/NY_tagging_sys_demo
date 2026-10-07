import sys
import os
from sqlalchemy import text

# Add current directory to path
sys.path.append(os.getcwd())

from src.core.database import engine

def migrate():
    with engine.connect() as conn:
        print("Checking for station_id column in cartons table...")
        # For SQL Server
        check_sql = text("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('cartons') AND name = 'station_id')
            BEGIN
                ALTER TABLE cartons ADD station_id NVARCHAR(50) NULL;
                SELECT 'Column added' as result;
            END
            ELSE
            BEGIN
                SELECT 'Column already exists' as result;
            END
        """)
        result = conn.execute(check_sql)
        print(result.scalar())
        conn.commit()

if __name__ == "__main__":
    migrate()
