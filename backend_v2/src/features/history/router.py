import datetime

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.features.auth.dependencies import require_admin

from . import schemas, service

router = APIRouter(prefix="/cartons", tags=["History"])

@router.get("", response_model=schemas.CartonListResponse)
def list_cartons(
    skip: int = 0, 
    limit: int = 50, 
    search: str | None = None,
    product_id: int | None = Query(None),
    status: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    customer_id: int | None = Query(None),
    job_order: str | None = Query(None),
    po_number: str | None = Query(None),
    db: Session = Depends(get_db)
):
    """Lấy danh sách lịch sử thùng hàng (có phân trang và lọc đa chiều)"""
    return service.get_cartons(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        product_id=product_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        customer_id=customer_id,
        job_order=job_order,
        po_number=po_number,
    )

@router.get("/export")
def export_cartons(
    mode: str = Query("summary", pattern="^(summary|detailed)$"),
    search: str | None = None,
    product_id: int | None = Query(None),
    status: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    customer_id: int | None = Query(None),
    job_order: str | None = Query(None),
    po_number: str | None = Query(None),
    db: Session = Depends(get_db)
):
    """Xuất báo cáo danh sách thùng ra file Excel (chế độ summary hoặc detailed)"""
    excel_bytes = service.export_cartons_to_excel(
        db=db,
        mode=mode,
        search=search,
        product_id=product_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        customer_id=customer_id,
        job_order=job_order,
        po_number=po_number,
    )
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"carton_export_{mode}_{timestamp}.xlsx"
    
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/search", response_model=schemas.CartonDetail)
def search_carton(carton_sn: str, db: Session = Depends(get_db)):
    """Tìm kiếm thùng theo Carton Serial Number"""
    return service.search_carton_by_sn(carton_sn, db)

@router.get("/search/item", response_model=schemas.CartonDetail)
def search_by_item(item_sn: str, db: Session = Depends(get_db)):
    """Tìm kiếm thùng theo Serial Number của sản phẩm bên trong"""
    return service.search_by_item_sn(item_sn, db)


@router.get("/item-sn-conflicts", response_model=schemas.ItemSNConflictResponse)
def get_item_sn_conflicts(
    item_sn: str,
    exclude_carton_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    """Look up existing UI Carton ownership for one scanned Item SN."""
    return service.get_ui_item_sn_conflicts(item_sn, db, exclude_carton_id)

@router.get("/statistics", response_model=schemas.PackagingStatisticsResponse)
def get_statistics(
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db)
):
    """Lấy thống kê sản lượng đóng gói và chi tiết theo ngày/sản phẩm"""
    return service.get_packaging_statistics(db, start_date, end_date)

@router.get("/job-order/{job_order}/statistics", response_model=schemas.JobOrderStatisticsResponse)
def get_job_order_statistics(job_order: str, db: Session = Depends(get_db)):
    """Lấy thống kê chi tiết của một lệnh sản xuất (Job Order)"""
    return service.get_job_order_statistics(db, job_order)

@router.get("/{carton_id}", response_model=schemas.CartonDetail)
def get_carton_detail(carton_id: int, db: Session = Depends(get_db)):
    """Lấy chi tiết một thùng hàng bao gồm danh sách S/N sản phẩm"""
    return service.get_carton_detail(db, carton_id)

@router.delete("/{carton_id}", dependencies=[Depends(require_admin)])
def delete_carton(carton_id: int, db: Session = Depends(get_db)):
    """Xóa một thùng hàng và toàn bộ S/N bên trong nó (Chỉ dành cho Admin)"""
    return service.delete_carton(db, carton_id)
