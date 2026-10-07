import os
import sys

# Add current directory to path so we can import src
sys.path.append(os.getcwd())

from src.core.database import SessionLocal
from src.core.models import Product

def migrate():
    db = SessionLocal()
    try:
        # Update products where template_type is NULL or empty
        updated = db.query(Product).filter(
            (Product.template_type == None) | (Product.template_type == '')
        ).update({Product.template_type: 'standard'}, synchronize_session=False)
        
        db.commit()
        print(f"Successfully updated {updated} products to 'standard' template type.")
    except Exception as e:
        db.rollback()
        print(f"Error during migration: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
