"""
Import Erro Factory P/N Mappings from Staging CSV.

Usage:
    uv run python scripts/import_erro_factory_part_numbers.py [--csv PATH] [--apply]
"""
import argparse
import csv
import os
import sys
from collections import defaultdict
from datetime import datetime

# Add backend_v2 root to sys.path so src imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from src.core.database import SessionLocal, init_db
from src.core.models import Customer, Product, ProductInternalFactoryPartNumber


def run_import(csv_path: str, apply: bool = False):
    if not os.path.exists(csv_path):
        print(f"Error: Staging CSV not found at {csv_path}")
        sys.exit(1)

    print("=== ERRO FACTORY PART NUMBER IMPORT ===")
    print(f"File: {csv_path}")
    print(f"Mode: {'APPLY (Changes will be committed to DB)' if apply else 'DRY RUN (No DB changes)'}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("-" * 50)

    stats_by_drawing = defaultdict(lambda: {"READY": 0, "MISSING_PRODUCT": 0, "CONFLICT": 0, "NEEDS_REVIEW": 0, "OTHER": 0})
    ready_rows = []
    skipped_rows = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            drawing = (row.get("source_drawing_code") or "UNKNOWN").strip().upper()
            part_no = (row.get("internal_factory_part_number") or "").strip().upper()
            item_ident = (row.get("source_product_identifier") or "").strip()
            tmpl_type = (row.get("template_type") or "").strip()
            status = (row.get("status") or "").strip().upper()
            confidence = (row.get("confidence") or "").strip().upper()

            if status in stats_by_drawing[drawing]:
                stats_by_drawing[drawing][status] += 1
            else:
                stats_by_drawing[drawing]["OTHER"] += 1

            if status == "READY" and confidence == "HIGH":
                ready_rows.append((row_num, drawing, part_no, item_ident, tmpl_type))
            else:
                skipped_rows.append((row_num, drawing, part_no, item_ident, status, row.get("notes", "")))

    print("\n[1] Thong ke Staging Records theo Ban Ve:")
    print(f"{'Drawing':<12} | {'READY':<8} | {'MISSING':<8} | {'CONFLICT':<8} | {'REVIEW':<8}")
    print("-" * 52)
    total_ready = 0
    total_missing = 0
    for drawing, counts in sorted(stats_by_drawing.items()):
        print(f"{drawing:<12} | {counts['READY']:<8} | {counts['MISSING_PRODUCT']:<8} | {counts['CONFLICT']:<8} | {counts['NEEDS_REVIEW']:<8}")
        total_ready += counts["READY"]
        total_missing += counts["MISSING_PRODUCT"]
    print("-" * 52)
    print(f"{'TOTAL':<12} | {total_ready:<8} | {total_missing:<8}\n")

    if not apply:
        print("[DRY RUN] Hoan tat kiem tra cu phap va cau truc file staging.")
        print(f"Co {total_ready} ban ghi READY san sang nhap vao database.")
        print(f"Co {total_missing} ban ghi MISSING_PRODUCT bi tu choi (can bo sung catalog).")
        print("Chay lai voi tham so `--apply` de ghi vao co so du lieu.")
        return

    # Apply to DB
    print("[APPLY] Bat dau ket noi Database va nhap lieu...")
    init_db()
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.code == "ERRO").first()
        if not customer:
            print("Error: Customer ERRO does not exist in database.")
            sys.exit(1)

        created_count = 0
        skipped_existing_count = 0
        failed_count = 0

        for row_num, drawing, part_no, item_ident, tmpl_type in ready_rows:
            # Resolve product
            product = db.query(Product).filter(
                Product.customer_id == customer.id,
                Product.item_name == item_ident,
            ).first()

            if not product:
                print(f"Line {row_num}: Warning - Product '{item_ident}' not found in DB despite status READY. Skipping.")
                failed_count += 1
                continue

            # Verify template type
            if product.template_type != tmpl_type:
                print(f"Line {row_num}: Warning - Template mismatch for '{item_ident}': DB has '{product.template_type}', CSV has '{tmpl_type}'. Skipping.")
                failed_count += 1
                continue

            # Check if mapping exists
            existing = db.query(ProductInternalFactoryPartNumber).filter(
                ProductInternalFactoryPartNumber.customer_id == customer.id,
                ProductInternalFactoryPartNumber.internal_factory_part_number == part_no,
            ).first()

            if existing:
                if existing.product_id == product.id:
                    skipped_existing_count += 1
                else:
                    print(f"Line {row_num}: Conflict - Factory P/N '{part_no}' already mapped to product_id {existing.product_id}. Skipping.")
                    failed_count += 1
                continue

            mapping = ProductInternalFactoryPartNumber(
                product_id=product.id,
                customer_id=customer.id,
                internal_factory_part_number=part_no,
                source_drawing_code=drawing,
            )
            db.add(mapping)
            created_count += 1

        db.commit()
        print("\n[APPLY HOAN TAT]")
        print(f"- So ban ghi tao moi thanh cong: {created_count}")
        print(f"- So ban ghi da ton tai (idempotent skip): {skipped_existing_count}")
        print(f"- So ban ghi loi / bo qua: {failed_count}")

    except Exception as e:
        db.rollback()
        print(f"Fatal error during apply: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import Erro Factory Part Number mappings")
    parser.add_argument("--csv", default="../docs/data/erro_factory_part_number_mapping_review.csv", help="Path to staging CSV")
    parser.add_argument("--apply", action="store_true", help="Apply changes to DB")
    args = parser.parse_args()

    csv_path = args.csv
    if not os.path.isabs(csv_path):
        workspace_root = os.path.dirname(backend_dir)
        candidate1 = os.path.abspath(os.path.join(workspace_root, csv_path))
        candidate2 = os.path.abspath(os.path.join(backend_dir, csv_path))
        csv_path = candidate1 if os.path.exists(candidate1) else candidate2

    run_import(csv_path, apply=args.apply)
