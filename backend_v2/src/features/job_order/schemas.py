import datetime

from pydantic import BaseModel


class JobOrderSlotResponse(BaseModel):
    id: int
    carton_number: int
    carton_sn: str
    status: str
    scanned_at: datetime.datetime | None = None
    carton_id: int | None = None

    class Config:
        from_attributes = True

class JobOrderProductResponse(BaseModel):
    id: int
    item_name: str
    upc: str
    packed_qty: int
    start_part: str | None = ""
    middle_part: str | None = ""
    template_type: str | None = "standard"
    template_path: str | None = None
    allow_partial: int | None = 0

    class Config:
        from_attributes = True

class JobOrderDetailsResponse(BaseModel):
    job_order: str
    total_qty: int
    total_cartons: int
    product: JobOrderProductResponse
    slots: list[JobOrderSlotResponse]

    class Config:
        from_attributes = True

from src.features.product.schemas import Product

class ErroJobOrderResolutionResponse(BaseModel):
    job_order: str
    factory_part_number: str
    customer_ref: str
    total_qty: int
    planned_cartons: int
    packed_cartons_count: int = 0
    name_mismatch: bool = False
    lot_number_default: str | None = None
    product: Product

    class Config:
        from_attributes = True
