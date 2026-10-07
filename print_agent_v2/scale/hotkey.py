"""Native Win32 Global Hotkey listener using RegisterHotKey."""

import ctypes
from ctypes import wintypes
import logging
import sys
import threading
import time
from typing import Callable, Optional

logger = logging.getLogger("ScaleHotkey")

_WM_HOTKEY: int = 0x0312
_WM_QUIT: int = 0x0012
_WM_USER: int = 0x0400
_WM_UPDATE_HOTKEY: int = _WM_USER + 101

_MOD_ALT: int = 0x0001
_MOD_CONTROL: int = 0x0002
_MOD_SHIFT: int = 0x0004
_MOD_WIN: int = 0x0008
_MOD_NOREPEAT: int = 0x4000

_VK_MAP: dict[str, int] = {
    "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73,
    "F5": 0x74, "F6": 0x75, "F7": 0x76, "F8": 0x77,
    "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
    "SPACE": 0x20, "RETURN": 0x0D, "TAB": 0x09,
}


def parse_hotkey_string(hotkey_str: str) -> tuple[int, int]:
    if not hotkey_str or not hotkey_str.strip():
        raise ValueError("Hotkey string cannot be empty.")

    parts: list[str] = [p.strip() for p in hotkey_str.split("+") if p.strip()]
    if not parts:
        raise ValueError("Invalid hotkey string.")

    modifiers: int = 0
    key_name: str = parts[-1].upper()

    for mod in parts[:-1]:
        mod_upper: str = mod.upper()
        if mod_upper in ("CTRL", "CONTROL"):
            modifiers |= _MOD_CONTROL
        elif mod_upper == "ALT":
            modifiers |= _MOD_ALT
        elif mod_upper == "SHIFT":
            modifiers |= _MOD_SHIFT
        elif mod_upper in ("WIN", "WINDOWS"):
            modifiers |= _MOD_WIN

    if key_name in _VK_MAP:
        vk_code: int = _VK_MAP[key_name]
    elif len(key_name) == 1 and key_name.isalnum():
        vk_code = ord(key_name)
    else:
        raise ValueError(f"Unknown key: {key_name}")

    return modifiers, vk_code


class GlobalHotkeyListener:
    """Background listener that captures global keyboard shortcuts via Win32 RegisterHotKey."""

    def __init__(
        self,
        hotkey: str = "F9",
        on_trigger: Optional[Callable[[], None]] = None,
        debounce_ms: float = 400.0,
    ) -> None:
        self._hotkey_str: str = hotkey
        self._on_trigger: Optional[Callable[[], None]] = on_trigger
        self._debounce_seconds: float = debounce_ms / 1000.0
        self._last_trigger_time: float = 0.0

        self._thread: Optional[threading.Thread] = None
        self._thread_id: Optional[int] = None
        self._stop_event: threading.Event = threading.Event()
        self._ready_event: threading.Event = threading.Event()
        self._lock: threading.Lock = threading.Lock()
        self._hotkey_id: int = 1

    @property
    def hotkey(self) -> str:
        return self._hotkey_str

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _handle_hotkey_pressed(self) -> None:
        now: float = time.monotonic()
        if now - self._last_trigger_time < self._debounce_seconds:
            return

        self._last_trigger_time = now
        logger.info(f"Hotkey {self._hotkey_str} triggered")
        if self._on_trigger is not None:
            try:
                self._on_trigger()
            except Exception as e:
                logger.error(f"Error in hotkey callback: {e}")

    def _run_message_loop(self) -> None:
        if sys.platform != "win32":
            self._ready_event.set()
            return

        self._thread_id = ctypes.windll.kernel32.GetCurrentThreadId()

        try:
            mod, vk = parse_hotkey_string(self._hotkey_str)
            ctypes.windll.user32.RegisterHotKey(None, self._hotkey_id, mod | _MOD_NOREPEAT, vk)
        except Exception as e:
            logger.warning(f"Hotkey registration error: {e}")

        self._ready_event.set()

        msg = wintypes.MSG()
        while not self._stop_event.is_set():
            res = ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if res == 0 or res == -1:
                break

            if msg.message == _WM_HOTKEY:
                if msg.wParam == self._hotkey_id:
                    self._handle_hotkey_pressed()
            elif msg.message == _WM_UPDATE_HOTKEY:
                ctypes.windll.user32.UnregisterHotKey(None, self._hotkey_id)
                try:
                    mod, vk = parse_hotkey_string(self._hotkey_str)
                    ctypes.windll.user32.RegisterHotKey(None, self._hotkey_id, mod | _MOD_NOREPEAT, vk)
                except Exception as err:
                    logger.warning(f"Re-register hotkey error: {err}")
            elif msg.message == _WM_QUIT:
                break

        ctypes.windll.user32.UnregisterHotKey(None, self._hotkey_id)

    def start(self) -> bool:
        with self._lock:
            if self.is_running():
                return True

            self._stop_event.clear()
            self._ready_event.clear()
            self._thread = threading.Thread(
                target=self._run_message_loop,
                name="ScaleHotkeyThread",
                daemon=True,
            )
            self._thread.start()

        self._ready_event.wait(timeout=2.0)
        return True

    def stop(self) -> None:
        with self._lock:
            if not self.is_running():
                return

            self._stop_event.set()
            if self._thread_id is not None and sys.platform == "win32":
                ctypes.windll.user32.PostThreadMessageW(self._thread_id, _WM_QUIT, 0, 0)

        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None
        self._thread_id = None
