import os
import sys
import tempfile
import pytest
from httpx import ASGITransport, AsyncClient

PRINT_AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PRINT_AGENT_DIR not in sys.path:
    sys.path.insert(0, PRINT_AGENT_DIR)

import agent


@pytest.mark.asyncio
async def test_open_template_missing_file():
    async with AsyncClient(transport=ASGITransport(app=agent.app), base_url="http://test") as client:
        res = await client.post(
            "/open-template",
            json={"folder": "D:\\non_existent_folder_xyz", "filename": "missing_template.btw"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is False
        assert data["exists"] is False
        assert "không tồn tại" in data["message"]
        assert data["filename"] == "missing_template.btw"


@pytest.mark.asyncio
async def test_open_template_empty_filename():
    async with AsyncClient(transport=ASGITransport(app=agent.app), base_url="http://test") as client:
        res = await client.post(
            "/open-template",
            json={"folder": "D:\\PAT\\Templates", "filename": ""},
        )
        assert res.status_code == 400


@pytest.mark.asyncio
async def test_open_template_with_bartend_cli(monkeypatch):
    popen_args = []

    def mock_popen(cmd_list, *args, **kwargs):
        popen_args.append(cmd_list)

    monkeypatch.setattr(agent, "_find_bartend_executable", lambda: "C:\\Program Files\\Seagull\\BarTender Suite\\bartend.exe")
    monkeypatch.setattr(agent.os.path, "isfile", lambda p: True)
    monkeypatch.setattr(agent.subprocess, "Popen", mock_popen)

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "sample.btw")
        with open(test_file, "w") as f:
            f.write("mock btw content")

        async with AsyncClient(transport=ASGITransport(app=agent.app), base_url="http://test") as client:
            res = await client.post(
                "/open-template",
                json={"folder": tmpdir, "filename": "sample.btw"},
            )
            assert res.status_code == 200
            data = res.json()
            assert data["success"] is True
            assert data["exists"] is True
            assert "Đã mở tệp" in data["message"]
            assert len(popen_args) == 1
            cmd = popen_args[0]
            assert "bartend.exe" in cmd[0]
            assert f"/F={os.path.normpath(test_file)}" in cmd
            assert "/MAX" in cmd


@pytest.mark.asyncio
async def test_open_template_existing_file_fallback(monkeypatch):
    started_files = []

    def mock_startfile(filepath):
        started_files.append(filepath)

    monkeypatch.setattr(agent, "_find_bartend_executable", lambda: None)
    monkeypatch.setattr(agent.os, "startfile", mock_startfile, raising=False)

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "sample.btw")
        with open(test_file, "w") as f:
            f.write("mock btw content")

        async with AsyncClient(transport=ASGITransport(app=agent.app), base_url="http://test") as client:
            res = await client.post(
                "/open-template",
                json={"folder": tmpdir, "filename": "sample.btw"},
            )
            assert res.status_code == 200
            data = res.json()
            assert data["success"] is True
            assert data["exists"] is True
            assert "Đã mở tệp" in data["message"]
            assert data["filename"] == "sample.btw"
            assert test_file in started_files or os.path.normpath(test_file) in started_files


@pytest.mark.asyncio
async def test_open_dir(monkeypatch):
    started_dirs = []

    def mock_startfile(dirpath):
        started_dirs.append(dirpath)

    monkeypatch.setattr(agent.os, "startfile", mock_startfile, raising=False)

    with tempfile.TemporaryDirectory() as tmpdir:
        async with AsyncClient(transport=ASGITransport(app=agent.app), base_url="http://test") as client:
            res = await client.post(
                "/open-dir",
                json={"folder": tmpdir},
            )
            assert res.status_code == 200
            data = res.json()
            assert data["success"] is True
            assert "Đã mở thư mục" in data["message"]
            assert tmpdir in started_dirs or os.path.normpath(tmpdir) in started_dirs
