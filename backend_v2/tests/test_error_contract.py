import pytest
from fastapi import HTTPException
from starlette.requests import Request

from src.core.exceptions import custom_http_exception_handler


@pytest.mark.asyncio
async def test_http_error_response_includes_stable_code_without_removing_legacy_error():
    request = Request({"type": "http", "method": "GET", "path": "/test", "headers": []})

    response = await custom_http_exception_handler(
        request,
        HTTPException(status_code=401, detail="legacy private text"),
    )

    assert response.status_code == 401
    assert b'"code":"UNAUTHORIZED"' in response.body
    assert b'"error":"legacy private text"' in response.body
