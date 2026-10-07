import sys
import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure print_agent_v2 root is in sys.path
agent_root = str(Path(__file__).resolve().parent.parent)
if agent_root not in sys.path:
    sys.path.insert(0, agent_root)

def test_scale_packet_parser_stable():
    from scale.parser import parse_scale_packet
    raw = b"ST,GS,+   12.450kg\r\n"
    info = parse_scale_packet(raw)
    assert info is not None
    assert info.weight == "12.450"
    assert info.unit == "kg"
    assert info.is_stable is True
    assert info.is_net is False

def test_scale_packet_parser_unstable():
    from scale.parser import parse_scale_packet
    raw = b"US,GS,+   12.450kg\r\n"
    info = parse_scale_packet(raw)
    assert info is not None
    assert info.weight == "12.450"
    assert info.is_stable is False

def test_scale_packet_parser_net_tare():
    from scale.parser import parse_scale_packet
    raw = b"ST,NT,+    5.200kg\r\n"
    info = parse_scale_packet(raw)
    assert info is not None
    assert info.weight == "5.200"
    assert info.is_net is True
    assert info.is_tare is True

def test_scale_packet_parser_reject_header_noise():
    from scale.parser import parse_scale_packet
    assert parse_scale_packet(b"DATE: 2026-08-21 09:30:00\r\n") is None
    assert parse_scale_packet(b"=========================\r\n") is None
    assert parse_scale_packet(b"TICKET NO: 12345\r\n") is None

def test_scale_api_endpoints():
    from agent import app
    from scale.manager import scale_manager
    
    # Inject mock scale reading
    from scale.parser import ScalePacketInfo
    scale_manager._latest_packet_info = ScalePacketInfo(
        weight="12.480",
        unit="kg",
        is_stable=True
    )
    scale_manager._is_connected = True

    client = TestClient(app)

    # Test /scale/status
    res_status = client.get("/scale/status")
    assert res_status.status_code == 200
    data_status = res_status.json()
    assert "connected" in data_status
    assert "port" in data_status

    # Test /scale/current
    res_curr = client.get("/scale/current")
    assert res_curr.status_code == 200
    data_curr = res_curr.json()
    assert data_curr["weight"] == 12.480
    assert data_curr["unit"] == "kg"
    assert data_curr["is_stable"] is True
