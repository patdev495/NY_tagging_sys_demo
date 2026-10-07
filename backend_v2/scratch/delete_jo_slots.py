import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.database import SessionLocal
from src.core import models

def main():
    db = SessionLocal()
    try:
        job_order = "1244054"
        print(f"=== Deleting slots for Job Order {job_order} ===")
        
        # 1. Double check no cartons exist
        carton_count = db.query(models.Carton).filter(
            models.Carton.job_order == job_order
        ).count()
        
        if carton_count > 0:
            print(f"ERROR: Cannot delete slots. There are {carton_count} cartons already created for this job order.")
            return
            
        # 2. Check slots
        slots = db.query(models.JobOrderCartonSlot).filter(
            models.JobOrderCartonSlot.job_order == job_order
        ).all()
        
        if not slots:
            print("No slots found for this job order.")
            return
            
        print(f"Found {len(slots)} slots. Deleting them...")
        for slot in slots:
            print(f"  Deleting Slot #{slot.carton_number}: SN={slot.carton_sn}, Status={slot.status}")
            db.delete(slot)
            
        db.commit()
        print("Successfully deleted all slots!")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
