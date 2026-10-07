from datetime import datetime

from pydantic import BaseModel


class CartonItem(BaseModel):
    id: int
    item_sn: str
    
    class Config:
        from_attributes = True

class CustomerInfo(BaseModel):
    id: int
    code: str
    name: str

    class Config:
        from_attributes = True

class ProductInfo(BaseModel):
    id: int
    customer_id: int | None = None
    item_name: str
    upc: str | None = None
    packed_qty: int | None = 1
    allow_partial: int | None = 0
    start_part: str | None = ""
    middle_part: str | None = ""
    template_type: str | None = "standard"
    template_path: str | None = None
    customer: CustomerInfo | None = None
    
    class Config:
        from_attributes = True

class CartonBase(BaseModel):
    carton_sn: str
    job_order: str | None = None
    packed_by: str | None = None
    status: str
    created_at: datetime
    carton_origin: str | None = "VN"
    station_id: str | None = None
    items_count: int | None = 0
    is_reprint: int | None = 0
    reprint_count: int | None = 0
    weight: float | None = None
    po_number: str | None = None
    lot_number: str | None = None
    date_code: str | None = None
    admin_creation_reason: str | None = None

class CartonListItem(CartonBase):
    id: int
    product_id: int
    product: ProductInfo | None = None
    
    class Config:
        from_attributes = True

class Carton(CartonListItem):
    btxml: str | None = None

class CartonDetail(Carton):
    items: list[CartonItem] = []
    print_history: list[CartonBase] = []


class ItemSNConflictCarton(BaseModel):
    id: int
    carton_sn: str
    product_name: str | None = None
    job_order: str | None = None
    status: str | None = None
    station_id: str | None = None
    created_at: datetime | None = None
    items_count: int


class ItemSNConflictResponse(BaseModel):
    item_sn: str
    conflicts: list[ItemSNConflictCarton]


class CartonListResponse(BaseModel):
    total: int
    items: list[CartonListItem]

class DailyStat(BaseModel):
    date: str
    total: int
    success: int
    reprint: int

class ProductStat(BaseModel):
    item_name: str
    total: int
    reprint: int

class PackagingStatisticsResponse(BaseModel):
    total_cartons: int
    success_cartons: int
    failed_cartons: int
    reprint_cartons: int
    total_items: int
    daily_breakdown: list[DailyStat]
    product_breakdown: list[ProductStat]


class JobOrderProductStat(BaseModel):
    product_id: int
    item_name: str
    total_cartons: int
    success_cartons: int
    failed_cartons: int


class JobOrderStatisticsResponse(BaseModel):
    job_order: str
    total_cartons: int
    success_cartons: int
    failed_cartons: int
    total_attempts: int
    reprint_attempts: int
    total_items: int
    product_breakdown: list[JobOrderProductStat]
    cartons: list[Carton]


