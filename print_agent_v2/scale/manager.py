"""Scale Manager Singleton coordinating serial engine and hotkeys."""

import json
import logging
import os
import sys
import time
from typing import Optional

from .serial_engine import SerialEngine, ConnectionStatus, list_com_ports
from .hotkey import GlobalHotkeyListener
from .parser import ScalePacketInfo

logger = logging.getLogger("ScaleManager")


class ScaleManager:
    """Coordinates serial connection, hotkey triggers, and scale state."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ScaleManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._port = "AUTO"
        self._baudrate = 9600
        self._hotkey = "NONE"
        self._auto_connect = True

        self._serial_engine: Optional[SerialEngine] = None
        self._hotkey_listener: Optional[GlobalHotkeyListener] = None
        self._latest_packet_info: Optional[ScalePacketInfo] = None
        self._is_connected = False
        self._trigger_count = 0
        self._initialized = True

    def _resolve_config_path(self, filename: str = "scale_config.json") -> str:
        if getattr(sys, 'frozen', False):
            return os.path.join(os.path.dirname(sys.executable), filename)
        return filename

    def load_config(self, config_path: Optional[str] = None) -> None:
        if not config_path:
            config_path = self._resolve_config_path("scale_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._port = data.get("port", self._port)
                    self._baudrate = int(data.get("baudrate", self._baudrate))
                    self._hotkey = data.get("hotkey", self._hotkey)
                    self._auto_connect = bool(data.get("auto_connect", self._auto_connect))
            except Exception as e:
                logger.warning(f"Error loading scale config: {e}")
        else:
            # Auto-generate default configuration JSON file on first run
            logger.info(f"scale_config.json not found at {config_path}. Auto-generating default configuration...")
            self.save_config(config_path)


    def save_config(self, config_path: Optional[str] = None) -> None:
        if not config_path:
            config_path = self._resolve_config_path("scale_config.json")
        try:
            data = {
                "port": self._port,
                "baudrate": self._baudrate,
                "hotkey": self._hotkey,
                "auto_connect": self._auto_connect,
            }
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving scale config: {e}")

    def auto_detect_port(self) -> Optional[str]:
        """Auto-detect connected USB serial scale port."""
        ports = list_com_ports()
        if not ports:
            return None
        
        # 1. Prefer USB Serial / CH340 / CP210x / FTDI / Prolific ports
        for p in ports:
            desc = (p.description or "").lower()
            hwid = (p.hwid or "").lower()
            if any(k in desc or k in hwid for k in ["usb", "ch340", "cp210", "ftdi", "prolific", "uart"]):
                logger.info(f"Auto-detected USB Scale COM Port: {p.device} ({p.description})")
                return p.device
        
        # 2. Fallback to first available port if only 1 exists
        if len(ports) == 1:
            logger.info(f"Auto-selected single available COM Port: {ports[0].device}")
            return ports[0].device

        return ports[0].device if ports else None

    def start(self) -> None:
        available_ports = [p.device for p in list_com_ports()]
        if not self._port or self._port == "AUTO" or (available_ports and self._port not in available_ports):
            detected = self.auto_detect_port()
            if detected:
                logger.info(f"Using auto-detected port: {detected} instead of {self._port}")
                self._port = detected

        logger.info(f"Starting Scale Manager (port={self._port}, baudrate={self._baudrate}, hotkey={self._hotkey})")
        self._serial_engine = SerialEngine(
            port=self._port,
            baudrate=self._baudrate,
            auto_reconnect=True,
        )
        self._serial_engine.on_scale_info_received = self._on_scale_info
        self._serial_engine.on_status_changed = self._on_status_changed

        if self._auto_connect:
            self._serial_engine.start()

        if self._hotkey and self._hotkey.upper() not in ("NONE", "OFF", ""):
            self._hotkey_listener = GlobalHotkeyListener(
                hotkey=self._hotkey,
                on_trigger=self._on_hotkey_triggered,
            )
            self._hotkey_listener.start()


    def stop(self) -> None:
        if self._serial_engine:
            self._serial_engine.stop()
        if self._hotkey_listener:
            self._hotkey_listener.stop()

    def reconnect(self, port: Optional[str] = None, baudrate: Optional[int] = None) -> None:
        """Reconnect serial engine with updated port or baudrate."""
        if port:
            self._port = port
        if baudrate:
            self._baudrate = baudrate
        logger.info(f"Reconnecting Scale Engine to {self._port} (baudrate={self._baudrate})...")
        if self._serial_engine:
            self._serial_engine.stop()
        self._serial_engine = SerialEngine(
            port=self._port,
            baudrate=self._baudrate,
            auto_reconnect=True,
        )
        self._serial_engine.on_scale_info_received = self._on_scale_info
        self._serial_engine.on_status_changed = self._on_status_changed
        if self._auto_connect:
            self._serial_engine.start()

    def _on_scale_info(self, info: ScalePacketInfo, raw: bytes) -> None:
        self._latest_packet_info = info

    def _on_status_changed(self, status: ConnectionStatus, msg: str) -> None:
        self._is_connected = (status == ConnectionStatus.CONNECTED)

    def _on_hotkey_triggered(self) -> None:
        self._trigger_count += 1
        logger.info(f"Hotkey triggered (total triggers={self._trigger_count})")

    def get_status(self) -> dict:
        ports = list_com_ports()
        engine_status = self._serial_engine.status.value if self._serial_engine else ("connected" if self._is_connected else "disconnected")
        engine_msg = self._serial_engine.status_message if self._serial_engine else ""
        is_streaming = self._serial_engine.is_streaming(threshold_seconds=2.0) if self._serial_engine else False
        is_connected = self._is_connected
        return {
            "connected": is_connected,
            "status": engine_status,
            "message": engine_msg,
            "port_opened": self._is_connected,
            "port": self._port,
            "baudrate": self._baudrate,
            "hotkey": self._hotkey,
            "is_streaming": is_streaming,
            "available_ports": [{"device": p.device, "description": p.description} for p in ports],
        }

    def get_current_reading(self) -> dict:
        is_streaming = self._serial_engine.is_streaming(threshold_seconds=2.0) if self._serial_engine else False
        is_connected = self._is_connected
        # In stable or manual push mode, retain latest packet info as long as port is open
        info = self._latest_packet_info if is_connected else None

        if info is None:
            return {
                "weight": 0.0,
                "weight_str": "0.000",
                "unit": "kg",
                "is_stable": False,
                "is_net": False,
                "is_tare": False,
                "is_zero": True,
                "is_hold": False,
                "connected": is_connected,
                "is_streaming": is_streaming,
                "timestamp": time.time(),
            }

        try:
            val_float = float(info.weight.replace(",", "."))
        except ValueError:
            val_float = 0.0

        return {
            "weight": val_float,
            "weight_str": info.weight,
            "unit": info.unit,
            "is_stable": info.is_stable,
            "is_net": info.is_net,
            "is_tare": info.is_tare,
            "is_zero": info.is_zero,
            "is_hold": info.is_hold,
            "connected": is_connected,
            "is_streaming": is_streaming,
            "timestamp": time.time(),
        }




    def tare(self) -> bool:
        return self._serial_engine.tare() if self._serial_engine else False

    def zero(self) -> bool:
        return self._serial_engine.zero() if self._serial_engine else False


scale_manager = ScaleManager()
