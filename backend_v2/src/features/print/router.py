from typing import cast as typing_cast

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.features.auth.dependencies import get_current_user, require_admin
from src.features.carton import print_attempts
from src.features.history.schemas import Carton

from . import schemas, service
from .bartender_engine import bt_engine

router = APIRouter(prefix="/print", tags=["Print"])

# ===== Cấu hình & Máy in =====

@router.get("/config")
def get_print_config():
    """Trả về trạng thái BarTender Engine."""
    return {
        "bartender_ready": bt_engine.is_initialized,
    }

@router.get("/whoami")
def get_client_ip(request: Request):
    """Trả về IP của Client gửi yêu cầu."""
    client_ip = request.headers.get("X-Forwarded-For") or (request.client.host if request.client else "127.0.0.1")
    return {"ip": client_ip}

@router.get("/printers")
def get_available_printers():
    """Lấy danh sách máy in trực tiếp từ Windows."""
    printers = bt_engine.get_printers()
    return {"printers": printers}

@router.get("/templates", response_model=schemas.TemplateListResponse)
def get_templates():
    """Lấy danh sách các file mẫu tem .btw có sẵn trên server kèm metadata."""
    templates = service.get_available_templates()
    return {"templates": templates}

@router.post("/validate-template", response_model=schemas.TemplateValidateResponse)
def validate_template(request: schemas.TemplateValidateRequest):
    """Kiểm tra sự tồn tại và tính hợp lệ của tệp mẫu tem."""
    return service.validate_template(request.template_name, folder=request.folder)

@router.get("/canonical-templates", response_model=schemas.CanonicalTemplatesResponse)
def get_canonical_templates(folder: str | None = None):
    """Lấy danh sách 7 mẫu tem chuẩn và trạng thái tồn tại trên máy chủ."""
    return service.get_canonical_templates(folder=folder)

@router.post("/restart-engine", response_model=schemas.EngineRestartResponse, dependencies=[Depends(require_admin)])
def restart_engine():
    """Khởi động lại BarTender COM Engine (Chỉ dành cho Admin)."""
    return service.restart_engine()

# ===== In ấn =====

@router.patch("/carton/{carton_id}/status", response_model=Carton)
def update_carton_status(carton_id: int, status_update: schemas.CartonStatusUpdate, db: Session = Depends(get_db)):
    """Cập nhật trạng thái in của thùng (SUCCESS / FAILED)"""
    return service.update_status(carton_id, status_update, db)

@router.get("/carton/{carton_id}/btxml")
def download_carton_btxml(carton_id: int, template_path: str | None = None, db: Session = Depends(get_db)):
    """Tải file .xml của thùng để in thủ công"""
    carton_sn, btxml_content = service.download_carton_btxml(carton_id, template_path, db)
    return Response(
        content=btxml_content,
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename=print_job_{carton_sn}.xml"}
    )

@router.post("/carton/{carton_id}/reprint", response_model=Carton)
def reprint_carton(carton_id: int, request: Request, template_path: str | None = None, printer_name: str | None = None, authorization: str | None = Header(None), db: Session = Depends(get_db)):
    """UI may reprint at a station; ERRO and other customers require Admin."""
    if service.reprint_requires_admin(carton_id, db):
        require_admin(get_current_user(authorization, db))
    client_ip = request.headers.get("X-Forwarded-For") or (request.client.host if request.client else "127.0.0.1")
    return service.reprint_carton(carton_id, printer_name, template_path, client_ip, db)

@router.post("/carton/{carton_id}/server-print")
def server_print_carton(carton_id: int, request: Request, printer_name: str | None = None, fallback_template_path: str | None = None, authorization: str | None = Header(None), db: Session = Depends(get_db)):
    """UI may print at a station; ERRO and other customers require Admin."""
    if service.reprint_requires_admin(carton_id, db):
        require_admin(get_current_user(authorization, db))

    client_ip = request.headers.get("X-Forwarded-For") or (request.client.host if request.client else "127.0.0.1")

    carton = db.query(service.models.Carton).filter(service.models.Carton.id == carton_id).first()
    if not carton:
        return {"success": False, "message": "Carton not found"}
    
    # Cập nhật trạm thực hiện in nếu chưa có hoặc in từ máy khác
    carton.station_id = client_ip  # type: ignore

    carton_btxml = carton.btxml
    if not carton_btxml:  # type: ignore
        _, regenerated_btxml = service.download_carton_btxml(carton_id=typing_cast(int, carton.id), template_path=fallback_template_path, db=db)
        if not regenerated_btxml:
            return {"success": False, "message": "No BTXML data available for this carton"}
        carton_btxml = regenerated_btxml

    # Gọi BarTender trực tiếp — không qua HTTP nữa
    result = bt_engine.print_xml(
        xml_content=carton_btxml,  # type: ignore
        printer_name_override=printer_name,
        fallback_path=fallback_template_path,
    )

    # Cập nhật trạng thái
    if result["success"]:
        carton.status = print_attempts.successful_print_status(db, carton)  # type: ignore
    else:
        carton.status = "FAILED"  # type: ignore
    db.commit()

    return result
