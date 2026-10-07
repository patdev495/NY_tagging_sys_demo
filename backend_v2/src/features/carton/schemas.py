
from pydantic import BaseModel


class CartonCreate(BaseModel):
    product_id: int
    items: list[str] # List of scanned Item S/Ns
    template_path: str | None = None
    printer_name: str | None = None
    print_folder: str | None = None
    job_order: str | None = None
    slot_id: int | None = None
    custom_sn: int | None = None
    carton_origin: str = "VN"
    station_id: str | None = None
    custom_yymm: str | None = None

class CartonRescan(BaseModel):
    carton_sn: str
    items: list[str]
    template_path: str | None = None
    printer_name: str | None = None
    station_id: str | None = None

class CartonWeighPackCreate(BaseModel):
    product_id: int
    weight: float
    job_order: str | None = None
    po_number: str | None = None
    lot_number: str | None = None
    printer_name: str | None = None
    template_path: str | None = None
    station_id: str | None = None
    carton_origin: str = "VN"
    custom_yymm: str | None = None
    custom_sn: int | None = None


class AdminCartonCreate(BaseModel):
    product_id: int
    sequence: int
    reason: str
    weight: float
    job_order: str
    po_number: str | None = None
    lot_number: str | None = None
    printer_name: str | None = None
    template_path: str | None = None
    carton_origin: str = "VN"
