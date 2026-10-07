
from pydantic import BaseModel


class CartonStatusUpdate(BaseModel):
    status: str # SUCCESS or FAILED

class TemplateInfo(BaseModel):
    name: str
    path: str
    size_bytes: int
    updated_at: str

class TemplateListResponse(BaseModel):
    templates: list[TemplateInfo]

class TemplateValidateRequest(BaseModel):
    template_name: str
    folder: str | None = None

class TemplateValidateResponse(BaseModel):
    valid: bool
    message: str
    resolved_path: str | None = None

class CanonicalTemplateItem(BaseModel):
    filename: str
    customer: str
    type: str
    name: str
    exists: bool = False
    resolved_path: str | None = None

class CanonicalTemplatesResponse(BaseModel):
    templates: list[CanonicalTemplateItem]
    templates_dir: str

class EngineRestartResponse(BaseModel):
    success: bool
    message: str
    bartender_ready: bool
