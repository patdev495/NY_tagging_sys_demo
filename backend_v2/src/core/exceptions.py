from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


_STATUS_CODES = {
    400: "VALIDATION_ERROR",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
}


def _error_code(status_code: int, detail: object) -> str:
    if isinstance(detail, dict) and isinstance(detail.get("code"), str):
        return detail["code"]
    return _STATUS_CODES.get(status_code, "INTERNAL_ERROR")


async def custom_http_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, (HTTPException, StarletteHTTPException)):
        status_code = exc.status_code
        detail = exc.detail
    else:
        status_code = 500
        detail = str(exc)
        
    return JSONResponse(
        status_code=status_code,
        content={"error": detail, "code": _error_code(status_code, detail)},
    )
