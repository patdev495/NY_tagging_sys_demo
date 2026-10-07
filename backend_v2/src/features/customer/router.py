
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.features.auth.dependencies import require_admin

from . import schemas, service

router = APIRouter(prefix="/customers", tags=["Customers"])

@router.get("", response_model=list[schemas.Customer])
def get_customers(db: Session = Depends(get_db)):
    """Lấy danh sách tất cả khách hàng"""
    return service.get_all_customers(db)

@router.post("", response_model=schemas.Customer, dependencies=[Depends(require_admin)])
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    """Tạo khách hàng mới (Chỉ dành cho Admin)"""
    db_customer = service.get_customer_by_code(db, customer.code)
    if db_customer:
        raise HTTPException(status_code=400, detail="Customer code already exists")
    return service.create_customer(db, customer)

@router.put("/{customer_id}", response_model=schemas.Customer, dependencies=[Depends(require_admin)])
def update_customer(customer_id: int, customer: schemas.CustomerUpdate, db: Session = Depends(get_db)):
    """Cập nhật thông tin khách hàng (Chỉ dành cho Admin)"""
    db_customer = service.update_customer(db, customer_id, customer)
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return db_customer

@router.delete("/{customer_id}", dependencies=[Depends(require_admin)])
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    """Xóa khách hàng (Chỉ dành cho Admin)"""
    success = service.delete_customer(db, customer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Customer deleted successfully"}
