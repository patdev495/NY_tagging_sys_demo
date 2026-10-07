from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobOrderSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_order: str
    product_id: int
    product_name: str
    customer_code: str
    total_slots: int
    scanned_slots: int
    pending_slots: int
    shipped_slots: int
    completion_rate: float
    latest_scan_at: datetime | None = None

class JobOrderSlotDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    carton_number: int
    carton_sn: str
    status: str
    scanned_at: datetime | None = None
    carton_id: int | None = None
    shipped: int = 0


class JobOrderSlotCancellationCheck(BaseModel):
    job_order: str
    total_slots: int
    scanned_slots: int
    can_cancel: bool


class JobOrderSlotCancellationResult(BaseModel):
    job_order: str
    deleted_slots: int


class POLotRunSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    po_number: str
    lot_number: str
    product_name: str
    customer_code: str
    date_code: str | None = None
    total_cartons: int
    total_weight: float
    latest_packed_at: datetime | None = None
