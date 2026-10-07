from datetime import datetime

from pydantic import BaseModel, field_validator, model_validator


class InternalFactoryPartNumberBase(BaseModel):
    internal_factory_part_number: str
    source_drawing_code: str

    @field_validator("internal_factory_part_number")
    @classmethod
    def validate_and_normalize_part_number(cls, v: str) -> str:
        val = (v or "").strip().upper()
        if not val:
            raise ValueError("Factory P/N cannot be empty")
        return val

    @field_validator("source_drawing_code")
    @classmethod
    def validate_and_normalize_drawing_code(cls, v: str) -> str:
        val = (v or "").strip().upper()
        if not val:
            raise ValueError("source_drawing_code cannot be empty")
        return val


class InternalFactoryPartNumberCreate(InternalFactoryPartNumberBase):
    pass


class InternalFactoryPartNumberBatchCreate(BaseModel):
    items: list[InternalFactoryPartNumberCreate]


class InternalFactoryPartNumberOut(InternalFactoryPartNumberBase):
    id: int
    product_id: int
    customer_id: int
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    item_name: str
    upc: str | None = None
    packed_qty: int
    start_part: str | None = "VN"
    middle_part: str | None = ""
    template_type: str | None = "standard"
    template_path: str | None = None
    allow_partial: int | None = 0
    customer_id: int
    packing_mode: str | None = "item_scan"
    target_weight: float | None = None
    min_weight: float | None = None
    max_weight: float | None = None
    weight_unit: str | None = "kg"
    mfr_pn: str | None = None
    pkg_prefix: str | None = None
    revision: str | None = None
    asin: str | None = None
    product_desc: str | None = None
    customer_project: str | None = None
    production_stage: str | None = None
    luxshare_part_number: str | None = None
    internal_factory_part_number: str | None = None
    factory_item_code: str | None = None
    carton_id_prefix: str | None = None

    @model_validator(mode="after")
    def validate_label_metadata(self):
        if self.template_type == "erro_03":
            required = {
                "customer_project": self.customer_project,
                "production_stage": self.production_stage,
                "luxshare_part_number": self.luxshare_part_number,
            }
            missing = [name for name, value in required.items() if not (value or "").strip()]
            if missing:
                raise ValueError(f"Erro 03 Product requires: {', '.join(missing)}")
            return self

        if self.template_type != "erro_04":
            return self

        required = {
            "upc": self.upc,
            "mfr_pn": self.mfr_pn,
            "product_desc": self.product_desc,
            "factory_item_code": self.factory_item_code,
            "revision": self.revision,
        }
        missing = [name for name, value in required.items() if not (value or "").strip()]
        if missing:
            raise ValueError(f"Erro 04 Product requires: {', '.join(missing)}")

        prefix = (self.carton_id_prefix or "").strip().upper()
        if prefix not in {"H", "K"}:
            raise ValueError("Erro 04 Product requires carton_id_prefix H or K")
        if self.packing_mode != "weight_scale":
            raise ValueError("Erro 04 Product requires weight_scale packing_mode")
        return self


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    item_name: str | None = None
    upc: str | None = None
    packed_qty: int | None = None
    start_part: str | None = None
    middle_part: str | None = None
    template_type: str | None = None
    template_path: str | None = None
    allow_partial: int | None = None
    customer_id: int | None = None
    packing_mode: str | None = None
    target_weight: float | None = None
    min_weight: float | None = None
    max_weight: float | None = None
    weight_unit: str | None = None
    mfr_pn: str | None = None
    pkg_prefix: str | None = None
    revision: str | None = None
    asin: str | None = None
    product_desc: str | None = None
    customer_project: str | None = None
    production_stage: str | None = None
    luxshare_part_number: str | None = None
    internal_factory_part_number: str | None = None
    factory_item_code: str | None = None
    carton_id_prefix: str | None = None


class Product(ProductBase):
    id: int
    internal_factory_part_numbers: list[InternalFactoryPartNumberOut] = []

    class Config:
        from_attributes = True
