import logging
import os

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.core import models, utils
from src.features.carton import print_attempts, slot_lifecycle
from src.features.print import schemas
from src.features.print.domain import BTXMLDocument

logger = logging.getLogger("PrintService")

MAX_SN_GRID = 40  # Maximum SN slots on the detailed label


def reprint_requires_admin(carton_id: int, db: Session) -> bool:
    """Only UI labels may be reprinted directly from a packing station."""
    carton = db.query(models.Carton).filter(models.Carton.id == carton_id).first()
    if not carton:
        return False

    product = carton.product or (
        db.query(models.Product).filter(models.Product.id == carton.product_id).first()
        if carton.product_id else None
    )
    customer_code = (product.customer.code if product and product.customer else "").upper()
    return customer_code != "UI"

def generate_btxml(carton: models.Carton, product: models.Product, items: list[str], template_path: str, printer_name: str | None = None) -> str:
    # Use the unified domain object to build the document applying all validation and schema rules
    doc = BTXMLDocument.from_carton_data(
        carton=carton,
        product=product,
        items=items,
        template_path=template_path,
        printer_name=printer_name
    )
    
    template_type = getattr(product, 'template_type', 'standard') or 'standard'
    btxml_content = doc.to_xml(template_type=template_type)
    return btxml_content


def update_status(carton_id: int, status_update: schemas.CartonStatusUpdate, db: Session):
    if status_update.status not in {"SUCCESS", "FAILED", "PRINTED"}:
        raise HTTPException(status_code=400, detail="Invalid carton status")
    carton = db.query(models.Carton).filter(models.Carton.id == carton_id).first()
    if not carton:
        raise HTTPException(status_code=404, detail="Carton not found")
    carton.status = status_update.status  # type: ignore
    
    if status_update.status == "SUCCESS":
        slot_lifecycle.complete_slot_for_success(db, carton)
    elif status_update.status == "FAILED":
        slot_lifecycle.release_slot_for_failed_original(db, carton)
            
    db.commit()
    db.refresh(carton)
    return carton


def download_carton_btxml(carton_id: int, template_path: str | None = None, db: Session | None = None):
    carton = db.query(models.Carton).filter(models.Carton.id == carton_id).first() if db else None
    if not carton:
        raise HTTPException(status_code=404, detail="Carton not found")
    
    btxml_content = carton.btxml
    if not btxml_content and db:
        product = db.query(models.Product).filter(models.Product.id == carton.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        item_sns = print_attempts.item_sns_for_attempt(db, carton)
            
        # Priority logic inside resolve_template_path: DB -> Client -> Default
        db_path = getattr(product, 'template_path', None)
        path_to_use = utils.resolve_template_path(primary_path=db_path, fallback_path=template_path)
        btxml_content = generate_btxml(carton, product, item_sns, path_to_use)
        
    return carton.carton_sn, btxml_content

def reprint_carton(carton_id: int, printer_name: str | None = None, template_path: str | None = None, station_id: str | None = None, db: Session | None = None):
    logger.info(f"Reprinting carton {carton_id} (printer={printer_name}, template={template_path})")
    if not db:
        raise HTTPException(status_code=500, detail="Database session not provided")
    original = db.query(models.Carton).filter(models.Carton.id == carton_id).first()
    if not original:
        logger.warning(f"Reprint failed: Carton {carton_id} not found in database")
        raise HTTPException(status_code=404, detail="Original carton not found")
    
    product = original.product or (db.query(models.Product).filter(models.Product.id == original.product_id).first() if original.product_id else None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    initial_status = "SUCCESS" if original.status == "SUCCESS" else "PRINTED"
    new_carton = models.Carton(
        product_id=original.product_id,
        carton_sn=original.carton_sn,
        job_order=original.job_order,
        packed_by=printer_name or original.packed_by,
        status=initial_status,
        is_reprint=1,
        carton_origin=original.carton_origin,
        station_id=station_id or original.station_id,
        weight=original.weight,
        po_number=original.po_number,
        lot_number=original.lot_number,
        date_code=original.date_code,
    )
    db.add(new_carton)
    db.flush()
    
    item_sns = print_attempts.item_sns_for_attempt(db, original)
    # Priority logic inside resolve_template_path: DB -> Client -> Default
    db_path = getattr(product, 'template_path', None)
    path_to_use = utils.resolve_template_path(primary_path=db_path, fallback_path=template_path)
    btxml_content = generate_btxml(new_carton, product, item_sns, path_to_use, printer_name)
    new_carton.btxml = None  # type: ignore
    
    db.commit()
    db.refresh(new_carton)
    
    # In-memory assignment so FastAPI/Pydantic serialization returns it to the client (e.g. for MCP server)
    new_carton.btxml = btxml_content  # type: ignore
    
    return new_carton


def get_available_templates() -> list[dict]:
    """Quét các thư mục lưu mẫu .btw trên hệ thống và trả về danh sách kèm metadata."""
    import datetime

    from src.core.config import settings
    from src.core.utils import TemplateResolver

    root = TemplateResolver.get_execution_root()
    search_dirs = [
        os.path.normpath(os.path.join(root, getattr(settings, 'LABEL_TEMPLATES_DIR', 'resources/label_templates'))),
        os.path.normpath(os.path.join(root, 'resources', 'templates')),
        os.path.normpath(root),
        os.path.normpath("D:\\PAT\\Templates"),
    ]

    discovered = {}
    for d in search_dirs:
        if os.path.exists(d) and os.path.isdir(d):
            try:
                for entry in os.listdir(d):
                    if entry.lower().endswith(".btw"):
                        key = entry.lower()
                        full_p = os.path.normpath(os.path.join(d, entry))
                        if os.path.isfile(full_p) and key not in discovered:
                            stat = os.stat(full_p)
                            mod_time = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                            discovered[key] = {
                                "name": entry,
                                "path": full_p,
                                "size_bytes": stat.st_size,
                                "updated_at": mod_time
                            }
            except Exception as e:
                logger.warning(f"Error scanning template directory {d}: {e}")

    return sorted(list(discovered.values()), key=lambda x: x["name"].lower())


def validate_template(template_name: str, folder: str | None = None) -> dict:
    """Kiểm tra sự tồn tại và tính hợp lệ của tệp mẫu tem."""
    from src.core.utils import TemplateResolver
    from src.features.print.bartender_com import HAS_WINDOWS_DEPS, bt_com_app

    resolved_path = TemplateResolver.resolve(template_name, local_dir=folder)
    if not resolved_path or not os.path.exists(resolved_path):
        return {
            "valid": False,
            "message": f"Tệp mẫu tem không tồn tại trên máy chủ: {template_name}",
            "resolved_path": None
        }

    if HAS_WINDOWS_DEPS and bt_com_app.is_initialized and bt_com_app.bt_app is not None:
        valid, msg = bt_com_app.validate_template_file(resolved_path)
        return {
            "valid": valid,
            "message": msg,
            "resolved_path": resolved_path if valid else None
        }

    return {
        "valid": True,
        "message": "Tệp mẫu tem tồn tại và sẵn sàng sử dụng.",
        "resolved_path": resolved_path
    }


def get_canonical_templates(folder: str | None = None) -> dict:
    """Lấy danh sách 7 mẫu tem chuẩn và trạng thái tồn tại trên máy chủ."""
    from src.core.utils import TemplateResolver
    target_dir = folder or TemplateResolver.DEFAULT_TEMPLATES_DIR
    results = []
    for tpl in TemplateResolver.ALL_CANONICAL_TEMPLATES:
        filename = tpl["filename"]
        chk = TemplateResolver.check_template_exists(filename, custom_dir=folder)
        results.append({
            "filename": filename,
            "customer": tpl["customer"],
            "type": tpl["type"],
            "name": tpl["name"],
            "exists": chk["exists"],
            "resolved_path": chk["path"],
        })
    return {
        "templates": results,
        "templates_dir": target_dir,
    }


def restart_engine() -> dict:
    """Giải phóng tiến trình kẹt và tái lập kết nối BarTender Engine."""
    from src.features.print.bartender_com import bt_com_app
    logger.info("Restarting BarTender Engine requested...")
    
    bt_com_app._kill_bartender_process()
    bt_com_app.is_initialized = False
    bt_com_app.bt_app = None
    
    ready = bt_com_app.start()
    return {
        "success": ready,
        "message": "Đã khởi động lại BarTender COM Engine thành công." if ready else "Khởi động lại BarTender thất bại.",
        "bartender_ready": ready
    }
