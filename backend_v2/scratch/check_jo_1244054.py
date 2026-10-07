import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from sqlalchemy import text, func
from src.core.database import SessionLocal
from src.core import models

def main():
    db = SessionLocal()
    try:
        job_order = "1244054"
        print(f"=== Checking Job Order {job_order} ===")
        
        # 1. Check in job_order_carton_slots
        slots = db.query(models.JobOrderCartonSlot).filter(
            models.JobOrderCartonSlot.job_order == job_order
        ).order_by(models.JobOrderCartonSlot.carton_number).all()
        
        print(f"\nSlots in database: {len(slots)}")
        if slots:
            prod_id = slots[0].product_id
            product = db.query(models.Product).filter(models.Product.id == prod_id).first()
            if product:
                print(f"Product Info:")
                print(f"  ID: {product.id}")
                print(f"  Item Name: {product.item_name}")
                print(f"  UPC: {product.upc}")
                print(f"  Packed Qty: {product.packed_qty}")
                print(f"  Template: {product.template_type} ({product.template_path})")
                print(f"  Allow Partial: {product.allow_partial}")
        
        for slot in slots:
            print(f"  Slot #{slot.carton_number}: SN={slot.carton_sn}, Status={slot.status}, Scanned At={slot.scanned_at}, Carton ID={slot.carton_id}, Shipped={slot.shipped}")
            
        # 2. Check in cartons table
        cartons = db.query(models.Carton).filter(
            models.Carton.job_order == job_order
        ).all()
        print(f"\nCartons in database: {len(cartons)}")
        for carton in cartons:
            print(f"  Carton SN={carton.carton_sn}, Created At={carton.created_at}, Packed By={carton.packed_by}, Status={carton.status}, Origin={carton.carton_origin}, Station ID={carton.station_id}")
            
        # 3. Query from ERP via Linked Server (if not sqlite)
        is_sqlite = db.get_bind().dialect.name == "sqlite"
        if not is_sqlite:
            print("\nQuerying ERP via Linked Server...")
            query = text("""
                SELECT wadoco AS [工單], walitm AS [年益料號], wadl01 AS [客戶料號], wauorg/10000 AS [數量] 
                FROM [192.168.206.18].ShopFloorDW.DBO.F4801 
                WHERE wadoco = :job_order
            """)
            try:
                row = db.execute(query, {"job_order": job_order}).fetchone()
                if row:
                    print(f"  ERP Job Order: {str(row[0]).strip()}")
                    print(f"  ERP Product Code: {str(row[1]).strip()}")
                    print(f"  ERP Customer Ref: {str(row[2]).strip()}")
                    print(f"  ERP Qty: {row[3]}")
                else:
                    print("  Job Order not found in ERP ShopFloorDW.")
            except Exception as e:
                print(f"  Error querying ERP: {e}")
        else:
            print("\nDatabase is SQLite, skipping ERP query.")

        # 4. Check max sequence for 2606 and 2607 prefixes for this product
        if slots:
            prod_id = slots[0].product_id
            product = db.query(models.Product).filter(models.Product.id == prod_id).first()
            if product:
                prefix_2606 = f"{product.start_part}2606{product.middle_part}"
                prefix_2607 = f"{product.start_part}2607{product.middle_part}"
                
                max_carton_2606 = db.query(func.max(models.Carton.carton_sn)).filter(
                    models.Carton.carton_sn.like(f"{prefix_2606}%"),
                    models.Carton.is_reprint == 0
                ).scalar()
                max_slot_2606 = db.query(func.max(models.JobOrderCartonSlot.carton_sn)).filter(
                    models.JobOrderCartonSlot.carton_sn.like(f"{prefix_2606}%")
                ).scalar()
                
                max_carton_2607 = db.query(func.max(models.Carton.carton_sn)).filter(
                    models.Carton.carton_sn.like(f"{prefix_2607}%"),
                    models.Carton.is_reprint == 0
                ).scalar()
                max_slot_2607 = db.query(func.max(models.JobOrderCartonSlot.carton_sn)).filter(
                    models.JobOrderCartonSlot.carton_sn.like(f"{prefix_2607}%")
                ).scalar()
                
                print(f"\nMax sequence checks for product {product.item_name} (prefix {product.start_part}YYMM{product.middle_part}):")
                print(f"  Month 2606:")
                print(f"    Max Carton SN in DB: {max_carton_2606}")
                print(f"    Max Slot SN in DB: {max_slot_2606}")
                print(f"  Month 2607:")
                print(f"    Max Carton SN in DB: {max_carton_2607}")
                print(f"    Max Slot SN in DB: {max_slot_2607}")
            
    finally:
        db.close()

if __name__ == "__main__":
    main()
