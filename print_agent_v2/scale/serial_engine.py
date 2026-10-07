"""Serial connection and packet receiver engine for OKS weighing scale."""

from dataclasses import dataclass
from enum import Enum
import logging
import threading
import time
from typing import Callable, Optional

try:
    import serial
    import serial.tools.list_ports
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False

from .parser import ScalePacketInfo, parse_scale_packet_with_reason

logger = logging.getLogger("ScaleSerialEngine")


class ConnectionStatus(Enum):
    """Enumeration of possible serial connection states."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


CMD_PRINT: bytes = b"P\r\n"
CMD_READ: bytes = b"R\r\n"
CMD_TARE: bytes = b"T\r\n"
CMD_ZERO: bytes = b"Z\r\n"
CMD_HOLD: bytes = b"H\r\n"
CMD_ACCUMULATE: bytes = b"A\r\n"


@dataclass(frozen=True)
class ComPortInfo:
    """Information regarding a detected COM port."""

    device: str
    description: str
    hwid: str


def list_com_ports() -> list[ComPortInfo]:
    """Scan and list all available serial COM ports on the system."""
    if not HAS_SERIAL:
        return []
    try:
        ports = serial.tools.list_ports.comports()
        return [
            ComPortInfo(
                device=str(p.device),
                description=str(p.description),
                hwid=str(p.hwid),
            )
            for p in ports
        ]
    except Exception as e:
        logger.warning(f"Failed listing COM ports: {e}")
        return []


class SerialEngine:
    """Background engine managing serial communications and data packet dispatch."""

    def __init__(
        self,
        port: str = "COM3",
        baudrate: int = 9600,
        auto_reconnect: bool = True,
        reconnect_interval: float = 2.0,
    ) -> None:
        self._port: str = port
        self._baudrate: int = baudrate
        self._auto_reconnect: bool = auto_reconnect
        self._reconnect_interval: float = reconnect_interval

        self._status: ConnectionStatus = ConnectionStatus.DISCONNECTED
        self._status_message: str = "Disconnected"

        self._ser = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event: threading.Event = threading.Event()
        self._lock: threading.Lock = threading.Lock()
        self._buffer: bytearray = bytearray()
        self._latest_packet_info: Optional[ScalePacketInfo] = None
        self._last_received_time: float = 0.0

        # Callbacks
        self.on_scale_info_received: Optional[Callable[[ScalePacketInfo, bytes], None]] = None
        self.on_status_changed: Optional[Callable[[ConnectionStatus, str], None]] = None

    @property
    def port(self) -> str:
        return self._port

    @property
    def baudrate(self) -> int:
        return self._baudrate

    @property
    def status(self) -> ConnectionStatus:
        return self._status

    @property
    def status_message(self) -> str:
        return self._status_message

    @property
    def latest_packet_info(self) -> Optional[ScalePacketInfo]:
        return self._latest_packet_info

    @property
    def last_received_time(self) -> float:
        return self._last_received_time

    def is_connected(self) -> bool:
        with self._lock:
            return self._ser is not None and getattr(self._ser, 'is_open', False)

    def is_streaming(self, threshold_seconds: float = 0.8) -> bool:
        return self.is_connected() and (time.time() - self._last_received_time < threshold_seconds)

    def send_command(self, cmd: bytes | str, cmd_name: str = "") -> bool:
        data: bytes = cmd.encode("ascii") if isinstance(cmd, str) else cmd
        with self._lock:
            if self._ser is None or not getattr(self._ser, 'is_open', False):
                return False
            try:
                self._ser.write(data)
                self._ser.flush()
                return True
            except Exception as e:
                logger.error(f"Failed sending command {cmd_name}: {e}")
                return False

    def trigger_read(self) -> bool:
        return self.send_command(CMD_PRINT, "PRINT")

    def tare(self) -> bool:
        return self.send_command(CMD_TARE, "TARE")

    def zero(self) -> bool:
        return self.send_command(CMD_ZERO, "ZERO")

    def hold(self) -> bool:
        return self.send_command(CMD_HOLD, "HOLD")

    def set_port(self, port: str) -> None:
        was_running = self._thread is not None and self._thread.is_alive()
        if was_running:
            self.stop()
        self._port = port
        if was_running:
            self.start()

    def set_baudrate(self, baudrate: int) -> None:
        was_running = self._thread is not None and self._thread.is_alive()
        if was_running:
            self.stop()
        self._baudrate = baudrate
        if was_running:
            self.start()

    def _set_status(self, status: ConnectionStatus, message: str) -> None:
        self._status = status
        self._status_message = message
        if self.on_status_changed is not None:
            try:
                self.on_status_changed(status, message)
            except Exception:
                pass

    def _process_incoming_chunk(self, chunk: bytes) -> None:
        if not chunk:
            return

        self._buffer.extend(chunk)

        while True:
            earliest_idx: int = -1
            matched_delim_len: int = 0

            for delim in (b"\r\n", b"\n", b"\r", b"\x03"):
                idx: int = self._buffer.find(delim)
                if idx != -1:
                    if earliest_idx == -1 or idx < earliest_idx:
                        earliest_idx = idx
                        matched_delim_len = len(delim)
                    elif idx == earliest_idx and len(delim) > matched_delim_len:
                        matched_delim_len = len(delim)

            if earliest_idx == -1:
                break

            packet_bytes: bytes = bytes(self._buffer[: earliest_idx + matched_delim_len])
            del self._buffer[: earliest_idx + matched_delim_len]

            info, _ = parse_scale_packet_with_reason(packet_bytes)
            if info is not None:
                self._latest_packet_info = info
                self._last_received_time = time.time()
                if self.on_scale_info_received is not None:
                    try:
                        self.on_scale_info_received(info, packet_bytes)
                    except Exception:
                        pass

    def _run_loop(self) -> None:
        if not HAS_SERIAL:
            self._set_status(ConnectionStatus.ERROR, "pyserial not installed")
            return

        while not self._stop_event.is_set():
            self._set_status(ConnectionStatus.CONNECTING, f"Connecting to {self._port}...")
            try:
                ser = serial.Serial(
                    port=self._port,
                    baudrate=self._baudrate,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=0.5,
                    xonxoff=False,
                    rtscts=False,
                    dsrdtr=False,
                )
                try:
                    ser.dtr = True
                    ser.rts = True
                except Exception:
                    pass

                with self._lock:
                    self._ser = ser
                self._set_status(ConnectionStatus.CONNECTED, f"Connected to {self._port}")

                while not self._stop_event.is_set() and ser.is_open:
                    try:
                        waiting: int = ser.in_waiting
                        if waiting > 0:
                            data: bytes = ser.read(waiting)
                            if data:
                                self._process_incoming_chunk(data)
                        else:
                            time.sleep(0.02)
                    except Exception:
                        break

            except Exception as err:
                self._set_status(ConnectionStatus.ERROR, f"Port error: {err}")

            with self._lock:
                if self._ser is not None:
                    try:
                        self._ser.close()
                    except Exception:
                        pass
                    self._ser = None

            if self._stop_event.is_set():
                break

            if not self._auto_reconnect:
                self._set_status(ConnectionStatus.DISCONNECTED, "Disconnected")
                break

            self._set_status(
                ConnectionStatus.RECONNECTING,
                f"Connection lost. Reconnecting in {self._reconnect_interval:.0f}s...",
            )
            self._stop_event.wait(self._reconnect_interval)

        self._set_status(ConnectionStatus.DISCONNECTED, "Disconnected")

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._buffer.clear()
        self._thread = threading.Thread(target=self._run_loop, name="ScaleSerialThread", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        with self._lock:
            if self._ser is not None and getattr(self._ser, 'is_open', False):
                try:
                    self._ser.close()
                except Exception:
                    pass
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None
        self._set_status(ConnectionStatus.DISCONNECTED, "Disconnected")
