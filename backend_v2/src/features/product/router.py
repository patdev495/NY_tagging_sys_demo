from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.features.auth.dependencies import require_admin
from src.features.history.schemas import CartonDetail

from . import schemas, service

router = APIRouter(tags=["Products"])

@router.get("/customers/{customer_id}/products", response_model=list[schemas.Product])
def get_products_by_customer(customer_id: int, db: Session = Depends(get_db)):
    """Lấy danh sách sản phẩm theo khách hàng"""
    return service.get_products_by_customer(customer_id, db)

@router.get("/products", response_model=list[schemas.Product])
def get_all_products(
    customer_code: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db)
):
    """Lấy tất cả sản phẩm (cho trang Admin hoặc lọc theo customer_code / search)"""
    return service.get_all_products(db, customer_code=customer_code, search=search)

@router.get("/products/resolve-internal-factory-part-number", response_model=schemas.Product)
def resolve_internal_factory_part_number(value: str, db: Session = Depends(get_db)):
    """Resolve an Erro Product from the Factory P/N entered at a packing station."""
    product = service.resolve_erro_product_by_internal_factory_part_number(value, db)
    if not product:
        raise HTTPException(status_code=404, detail="Factory P/N chưa được cấu hình cho khách hàng Erro.")
    return product

@router.get("/products/{product_id}", response_model=schemas.Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Lấy thông tin chi tiết một sản phẩm"""
    db_product = service.get_product_by_id(product_id, db)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@router.post("/products", response_model=schemas.Product, dependencies=[Depends(require_admin)])
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    """Tạo sản phẩm mới (Chỉ dành cho Admin)"""
    return service.create_product(db, product)

@router.put("/products/{product_id}", response_model=schemas.Product, dependencies=[Depends(require_admin)])
def update_product(product_id: int, product: schemas.ProductUpdate, db: Session = Depends(get_db)):
    """Cập nhật thông tin sản phẩm (Chỉ dành cho Admin)"""
    db_product = service.update_product(db, product_id, product)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@router.delete("/products/{product_id}", dependencies=[Depends(require_admin)])
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Xóa sản phẩm (Chỉ dành cho Admin)"""
    success = service.delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}

@router.get("/products/{product_id}/next-sn")
def get_next_sn(product_id: int, yymm: str | None = None, db: Session = Depends(get_db)):
    """Lấy S/N tiếp theo cho sản phẩm"""
    return service.get_next_sn(product_id, db, yymm)

@router.get("/products/{product_id}/last-carton", response_model=Optional[CartonDetail])
def get_last_carton(product_id: int, job_order: str | None = None, db: Session = Depends(get_db)):
    """Lấy Carton cuối của Product, có thể giới hạn trong một Công Lệnh."""
    return service.get_last_carton(product_id, db, job_order=job_order)


@router.get(
    "/products/{product_id}/internal-factory-part-numbers",
    response_model=list[schemas.InternalFactoryPartNumberOut],
)
def get_product_internal_factory_part_numbers(product_id: int, db: Session = Depends(get_db)):
    """Lấy danh sách Factory P/N (1-N mapping) đã cấu hình cho sản phẩm."""
    return service.get_product_factory_part_numbers(product_id, db)


@router.post(
    "/products/{product_id}/internal-factory-part-numbers",
    response_model=schemas.InternalFactoryPartNumberOut,
    dependencies=[Depends(require_admin)],
)
def add_product_internal_factory_part_number(
    product_id: int,
    mapping_data: schemas.InternalFactoryPartNumberCreate,
    db: Session = Depends(get_db),
):
    """Thêm một Factory P/N cho sản phẩm (Chỉ dành cho Admin)."""
    return service.add_product_factory_part_number(product_id, mapping_data, db)


@router.post(
    "/products/{product_id}/internal-factory-part-numbers/batch",
    response_model=list[schemas.InternalFactoryPartNumberOut],
    dependencies=[Depends(require_admin)],
)
def batch_add_product_internal_factory_part_numbers(
    product_id: int,
    batch_data: schemas.InternalFactoryPartNumberBatchCreate,
    db: Session = Depends(get_db),
):
    """Thêm hàng loạt Factory P/N cho sản phẩm (Chỉ dành cho Admin)."""
    return service.batch_add_product_factory_part_numbers(product_id, batch_data.items, db)


@router.delete(
    "/products/{product_id}/internal-factory-part-numbers/{mapping_id}",
    dependencies=[Depends(require_admin)],
)
def delete_product_internal_factory_part_number(
    product_id: int,
    mapping_id: int,
    db: Session = Depends(get_db),
):
    """Xóa một Factory P/N khỏi sản phẩm (Chỉ dành cho Admin)."""
    service.delete_product_factory_part_number(product_id, mapping_id, db)
    return {"message": "Factory P/N mapping deleted successfully"}
