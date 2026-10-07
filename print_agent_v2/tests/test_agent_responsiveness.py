import asyncio
import os
import sys
import time

import pytest
from httpx import ASGITransport, AsyncClient


PRINT_AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PRINT_AGENT_DIR not in sys.path:
    sys.path.insert(0, PRINT_AGENT_DIR)

import agent  # noqa: E402


@pytest.mark.asyncio
async def test_status_responds_while_print_job_is_blocked(monkeypatch):
    def slow_print_xml(**_kwargs):
        time.sleep(0.4)
        return {"success": True, "message": "printed", "type": "print"}

    monkeypatch.setattr(agent.bt_com_app, "print_xml", slow_print_xml)

    async with AsyncClient(transport=ASGITransport(app=agent.app), base_url="http://test") as client:
        print_task = asyncio.create_task(
            client.post("/print", json={"xml_content": "<xml />"})
        )
        await asyncio.sleep(0.05)

        start = time.perf_counter()
        status_response = await client.get("/status")
        elapsed = time.perf_counter() - start
        print_response = await print_task

    assert status_response.status_code == 200
    assert status_response.json()["status"] == "online"
    assert elapsed < 0.2
    assert print_response.status_code == 200
