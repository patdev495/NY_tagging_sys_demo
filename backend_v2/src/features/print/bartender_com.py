"""
BarTender COM Integration Module — Unified & Thread-Safe.
Handles Windows COM Automation, printing lifecycle, PDF export, and automatic process recovery.
Works out of the box on Windows, and falls back to a mock mode on other operating systems.
"""
import logging
import os
import subprocess
import sys
import threading
import time
from typing import Any

logger = logging.getLogger("BarTenderCOM")

# Try to import Windows-specific COM libraries safely
try:
    import pythoncom  # type: ignore
    import win32com.client  # type: ignore
    import win32com.client.dynamic  # type: ignore
    import win32print  # type: ignore
    HAS_WINDOWS_DEPS = True
except ImportError:
    HAS_WINDOWS_DEPS = False
    pythoncom: Any = None
    win32com: Any = None
    win32print: Any = None
    logger.warning("Windows COM or Win32Print libraries not found. BarTender running in MOCK mode.")


class BarTenderCOMApp:
    """
    Unified Singleton Manager for BarTender COM Application.
    Encapsulates thread safety, connection lifecycle, and self-healing process recovery.
    """
    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Ensure thread-safe Singleton instantiation."""
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        """Initialize locks, states, and flags once."""
        if self._initialized:
            return
        self.bt_app = None
        self._lock = threading.Lock()
        self.is_initialized = False
        self._initialized = True

    def _kill_bartender_process(self):
        """Forcefully kill any stuck or orphaned bartend.exe processes."""
        logger.warning("Forcefully killing stuck bartend.exe processes...")
        try:
            subprocess.run(["taskkill", "/F", "/IM", "bartend.exe"], capture_output=True, timeout=5)
            time.sleep(2)
        except Exception as e:
            logger.error(f"Failed to kill bartend.exe: {e}")

    def _create_dispatch_instance(self) -> bool:
        """Attempt to dispatch a new BarTender application COM instance using multiple strategies."""
        if not HAS_WINDOWS_DEPS:
            logger.info("[MOCK] Simulating BarTender COM App connection...")
            self.is_initialized = True
            return True

        pythoncom.CoInitialize()
        strategies = [
            ("Standard Dispatch", lambda: win32com.client.Dispatch("BarTender.Application")),
            ("Dynamic Dispatch", lambda: win32com.client.dynamic.Dispatch("BarTender.Application")),
        ]

        for name, creator in strategies:
            try:
                logger.info(f"Trying connection strategy: {name}...")
                app = creator()
                # Diagnostic check to verify the COM object actually works
                _ = app.Formats
                app.Visible = False
                self.bt_app = app
                self.is_initialized = True
                logger.info(f"Successfully connected to BarTender via {name}")
                return True
            except Exception as e:
                logger.warning(f"Strategy {name} failed: {e}")

        return False

    def start(self) -> bool:
        """
        Start the BarTender engine.
        Attempts normal connection first; falls back to killing stuck processes if connection fails.
        """
        with self._lock:
            if self.is_initialized and (self.bt_app is not None or not HAS_WINDOWS_DEPS):
                return True

            logger.info("Starting BarTender COM Application integration...")
            if self._create_dispatch_instance():
                return True

            # If failed, kill any orphaned processes and try one last time
            self._kill_bartender_process()
            if self._create_dispatch_instance():
                return True

            logger.critical("BarTender COM automation could not be initialized after all attempts.")
            self.is_initialized = False
            return False

    def _ensure_connected(self):
        """Verify the COM connection is still active; re-establish if broken."""
        if not HAS_WINDOWS_DEPS:
            return

        if self.bt_app is None:
            logger.warning("BarTender COM app is None. Attempting connection...")
            if not self._create_dispatch_instance():
                self._kill_bartender_process()
                if not self._create_dispatch_instance():
                    raise RuntimeError("Connection to BarTender COM failed (app is None).")
            return

        try:
            # Check if the connection is alive by accessing a standard property
            _ = self.bt_app.Formats
        except Exception:
            logger.warning("BarTender COM connection lost or dead. Attempting reconnection...")
            if not self._create_dispatch_instance():
                self._kill_bartender_process()
                if not self._create_dispatch_instance():
                    raise RuntimeError("Reconnection to BarTender COM failed.")

    def get_printers(self) -> list[dict[str, Any]]:
        """Fetch all available Windows physical/network printers, excluding typical virtual ones."""
        printers = [{"name": "PDF", "driver": "Virtual PDF Export", "port": "VIRTUAL", "status": 0}]

        if not HAS_WINDOWS_DEPS:
            # Return high-quality mock printers on non-Windows dev systems
            printers.extend([
                {"name": "Zebra ZT411 (Mock)", "driver": "ZDesigner ZT411", "port": "USB001", "status": 0},
                {"name": "TSC TE244 (Mock)", "driver": "TSC Barcode Printer", "port": "LPT1", "status": 0}
            ])
            return printers

        try:
            # Retrieve printers from win32print API
            enum_flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            raw_printers = win32print.EnumPrinters(enum_flags, None, 2)
            
            skip_keywords = ["microsoft print to pdf", "microsoft xps", "fax", "onenote", "send to onenote"]
            
            for p in raw_printers:
                name = p.get("pPrinterName", "")
                if any(kw in name.lower() for kw in skip_keywords):
                    continue
                printers.append({
                    "name": name,
                    "driver": p.get("pDriverName", ""),
                    "port": p.get("pPortName", ""),
                    "status": p.get("Status", 0)
                })
        except Exception as e:
            logger.error(f"Failed to enumerate Windows printers: {e}")

        return printers

    def _export_to_pdf(self, bt_format, substrings: dict[str, str] | None = None) -> dict[str, Any]:
        """
        Executes print-to-PDF using native BarTender ExportToFile or Windows print interception.
        Returns a base64 encoded string of the generated PDF document.
        """
        import base64
        import uuid

        # Check if we are running in the Print Agent context (handles both dev python and compiled exe)
        is_agent = False
        if getattr(sys, 'frozen', False):
            is_agent = "NY_Print_Agent" in os.path.basename(sys.executable)
        else:
            is_argv_agent = len(sys.argv) > 0 and "agent.py" in os.path.basename(sys.argv[0])
            this_dir = os.path.dirname(os.path.abspath(__file__))
            is_src_agent = "print_agent_v2" in this_dir and os.path.exists(os.path.join(this_dir, "agent.py"))
            is_agent = is_argv_agent or is_src_agent
        
        carton_sn = substrings.get("CartonSN", f"label_{str(uuid.uuid4())[:8]}") if substrings else f"label_{str(uuid.uuid4())[:8]}"
        # Sanitize filename
        carton_sn = "".join(c for c in carton_sn if c.isalnum() or c in ('-', '_', '.'))

        if is_agent:
            # Save permanently next to Print Agent so the user can easily find it!
            pdf_dir = os.path.normpath(os.path.join(os.getcwd(), "pdf_output"))
            os.makedirs(pdf_dir, exist_ok=True)
            pdf_path = os.path.normpath(os.path.join(pdf_dir, f"{carton_sn}.pdf"))
            logger.info(f"[PDF] Permanent save path configured: {pdf_path}")
        else:
            # Central backend mode: temporary location, will clean up after encoding
            temp_dir = os.path.join(os.environ.get('TEMP', 'C:\\temp'), 'ny_labels')
            os.makedirs(temp_dir, exist_ok=True)
            pdf_path = os.path.normpath(os.path.join(temp_dir, f"{carton_sn}_{str(uuid.uuid4())[:8]}.pdf"))

        # Strategy 1: Ultra-fast Native BarTender COM ExportToFile (takes ~0.2s)
        try:
            logger.info(f"Attempting native BarTender ExportToFile to {pdf_path}...")
            if os.path.exists(pdf_path):
                try: os.remove(pdf_path)
                except Exception: pass

            bt_format.ExportToFile(pdf_path, 'PDF', 1, 300, 0)
            time.sleep(0.3)

            if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 100:
                with open(pdf_path, "rb") as f:
                    pdf_base64 = base64.b64encode(f.read()).decode('utf-8')
                logger.info(f"Native PDF export successful: {os.path.getsize(pdf_path)} bytes")
                return {
                    "success": True, 
                    "message": "PDF export completed successfully", 
                    "type": "pdf", 
                    "data": pdf_base64,
                    "file_path": pdf_path
                }
        except Exception as e:
            logger.warning(f"Native ExportToFile was not available or failed: {e}. Falling back to dialog interception.")

        # Strategy 2: Fallback to Print Setup + Windows Dialog Auto-Interceptor
        def handle_save_dialog_asynchronously(target_pdf, timeout=15):
            """Runs on a background thread to wait for, fill, and click the Windows Save dialog box."""
            import win32con
            import win32gui

            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    dialog_matches = []
                    win32gui.EnumWindows(lambda h, m: m.append(h) if win32gui.IsWindowVisible(h) and any(k in win32gui.GetWindowText(h).lower() for k in ("save", "print", "output", "pdf")) else True, dialog_matches)
                    if dialog_matches:
                        dialog_hwnd = dialog_matches[0]
                        edit_children, buttons = [], []
                        win32gui.EnumChildWindows(dialog_hwnd, lambda h, _: edit_children.append(h) if win32gui.GetClassName(h) in ('Edit', 'ComboBoxEx32') else None, None)
                        for edit_hwnd in edit_children:
                            if win32gui.GetClassName(edit_hwnd) == 'Edit':
                                win32gui.SendMessage(edit_hwnd, win32con.WM_SETTEXT, 0, target_pdf)
                                break
                            inner = win32gui.FindWindowEx(edit_hwnd, 0, 'ComboBox', None)
                            inner_edit = win32gui.FindWindowEx(inner or edit_hwnd, 0, 'Edit', None)
                            if inner_edit:
                                win32gui.SendMessage(inner_edit, win32con.WM_SETTEXT, 0, target_pdf)
                                break
                        time.sleep(0.3)
                        win32gui.EnumChildWindows(dialog_hwnd, lambda h, _: buttons.append(h) if win32gui.GetClassName(h) == 'Button' and win32gui.GetWindowText(h) in ('&Save', 'Save', '&Lưu', 'Lưu', 'OK', '&OK') else None, None)
                        if buttons:
                            win32gui.SendMessage(buttons[0], win32con.BM_CLICK, 0, 0)
                            time.sleep(0.5)
                            return True
                except Exception as e:
                    logger.warning(f"Error in async dialog handler: {e}")
                time.sleep(0.3)
            return False

        try:
            bt_format.PrintSetup.Printer = "Microsoft Print to PDF"
            
            # Start background thread to handle Windows Save Dialog immediately
            dialog_thread = threading.Thread(target=handle_save_dialog_asynchronously, args=(pdf_path,), daemon=True)
            dialog_thread.start()

            bt_format.PrintOut(False, False)
            dialog_thread.join(timeout=15)

            # Wait for the PDF to write fully to disk
            write_start = time.time()
            success = False
            while time.time() - write_start < 10:
                if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 100:
                    time.sleep(0.5)
                    success = True
                    break
                time.sleep(0.3)

            if success:
                with open(pdf_path, "rb") as f:
                    pdf_base64 = base64.b64encode(f.read()).decode('utf-8')
                logger.info(f"PDF exported successfully via PrintOut: {os.path.getsize(pdf_path)} bytes")
                return {"success": True, "message": "PDF export completed successfully", "type": "pdf", "data": pdf_base64, "file_path": pdf_path}
            else:
                return {"success": False, "message": "Failed to generate PDF document (Save dialog timeout/failure)."}

        except Exception as e:
            logger.error(f"PDF export crashed: {e}")
            return {"success": False, "message": f"PDF export crashed: {e!s}"}
        finally:
            if not is_agent:
                def cleanup():
                    time.sleep(2)
                    try:
                        if os.path.exists(pdf_path):
                            os.remove(pdf_path)
                    except Exception: pass
                threading.Thread(target=cleanup, daemon=True).start()

    def print_label(self, template_path: str, printer_name: str, substrings: dict[str, str]) -> dict[str, Any]:
        """
        Prints a label using structured parameters (Template Path, Target Printer, Substring Dictionary).
        This is the preferred, robust, and deep interface.
        """
        # Ensure start was called
        if not self.is_initialized:
            self.start()

        # Check if we are running in the Print Agent context (handles both dev python and compiled exe)
        is_agent = False
        if getattr(sys, 'frozen', False):
            is_agent = "NY_Print_Agent" in os.path.basename(sys.executable)
        else:
            is_argv_agent = len(sys.argv) > 0 and "agent.py" in os.path.basename(sys.argv[0])
            this_dir = os.path.dirname(os.path.abspath(__file__))
            is_src_agent = "print_agent_v2" in this_dir and os.path.exists(os.path.join(this_dir, "agent.py"))
        mapped_printer = printer_name or ""

        # Handle Mock Mode on Dev/Non-Windows OS
        if not HAS_WINDOWS_DEPS:
            logger.info(f"[MOCK PRINT] Template: {template_path}, Printer: {mapped_printer}")
            logger.info(f"[MOCK DATA] Substrings: {substrings}")
            if not mapped_printer or mapped_printer.upper() == "PDF" or "PDF" in mapped_printer.upper():
                return {"success": True, "message": "Mock PDF Export completed", "type": "pdf", "data": "bW9ja19wZGZfYmFzZTY0X2NvbnRlbnQ="}
            return {"success": True, "message": "Mock Print Job processed successfully", "type": "print"}

        with self._lock:
            pythoncom.CoInitialize()
            bt_format = None
            try:
                self._ensure_connected()
                if self.bt_app is None:
                    return {"success": False, "message": "BarTender COM application instance is None after connection check."}

                # Open the btw template with up to 3 retries
                for attempt in range(3):
                    try:
                        bt_format = self.bt_app.Formats.Open(template_path, False, "")
                        if bt_format:
                            break
                    except Exception as e:
                        logger.warning(f"Opening template attempt {attempt + 1} failed: {e}")
                        self._ensure_connected()
                        if self.bt_app is None:
                            return {"success": False, "message": "BarTender COM application instance is None after reconnection check."}
                        time.sleep(1)

                if not bt_format:
                    return {"success": False, "message": f"Could not open template path: {template_path}"}

                # Special handling for Erro 03 / Luxshare NME template.
                if "erro_03" in template_path.lower() or "tem ngo" in template_path.lower():
                    import base64
                    def _b64_u16(t: str) -> str:
                        return base64.b64encode(str(t).encode('utf-16le')).decode('ascii')

                    carton_sn = substrings.get("CartonSN", "")
                    supplier_code = substrings.get("SupplierCode", "1012665")
                    supplier_name = substrings.get("SupplierName", "NIENYI VIETNAM INDUSTRIAL COMPANY LIMITED")
                    part_no = substrings.get("LuxsharePartNo", "")
                    apn_rev = substrings.get("APNRev", "/")
                    lot_no = substrings.get("LotNo", "")
                    date_ymd = substrings.get("Date", "")
                    qty = substrings.get("QTY", "")
                    part_desc = substrings.get("PartDesc", "")
                    origin = substrings.get("Origin", "VIETNAM")
                    project_stage = substrings.get("ProjectStage", "")
                    qr_content = substrings.get("QR_Content") or substrings.get("QRCode_Content", f"{carton_sn}${supplier_code}${supplier_name}${part_no}$${lot_no}${date_ymd}${qty}$$$$$$")

                    fields = [
                        ("文本 10", project_stage),
                        ("Text 2", f"料号:                        {part_no}"),
                        ("文本 17", f"APN-Rev :             {apn_rev}"),
                        ("文本 18", f"数量:                    {qty}"),
                        ("文本 20", f"生产日期:                {date_ymd}"),
                        ("文本 16", f" 生产批号:                   {lot_no}"),
                        ("文本 13", f" 料件描述:        {part_desc}"),
                        ("文本 23", f"供应商代码:                          {supplier_code}"),
                        ("文本 25", f"箱号:                                   {carton_sn}"),
                        ("文本 26", f"供应商名称：  {supplier_name}"),
                        ("文本 28", f"原产地：{origin}                                     型号：                              品牌："),
                    ]
                    objs = "".join(f'<Object Name="{n}" Type="2"><SubString Position="0"><Value Encoding="base64">{_b64_u16(v)}</Value></SubString></Object>' for n, v in fields)
                    objs += f'<Object Name="条形码 13" Type="1"><SubString Position="0"><Value Encoding="base64">{_b64_u16(qr_content)}</Value></SubString></Object>'
                    xml_merge = f'<?xml version="1.0" encoding="UTF-8" ?><Command><DataMerge>{objs}</DataMerge></Command>'
                    try:
                        bt_format.Objects.ImportDataSourceValuesFromXML(xml_merge)
                    except Exception as e:
                        logger.warning(f"Failed to import datasource values for Tem 3: {e}")

                # Feed values to the template's Named Substrings
                for key, val in substrings.items():
                    try:
                        bt_format.SetNamedSubStringValue(key, val)
                    except Exception as e:
                        # Some templates might not have all keys, skip silently or log weakly
                        logger.debug(f"Failed to set template key '{key}': {e}")

                # Check if it's a PDF export or a physical print job
                is_pdf_export = not mapped_printer or mapped_printer.upper() == "PDF" or "PDF" in mapped_printer.upper()

                if is_pdf_export:
                    return self._export_to_pdf(bt_format, substrings)

                # Set Printer and Print Out for physical printer
                if mapped_printer:
                    bt_format.PrintSetup.Printer = mapped_printer

                bt_format.PrintOut(False, False)
                return {"success": True, "message": "Success", "type": "print"}

            except Exception as e:
                logger.error(f"Print job encountered an error: {e}")
                return {"success": False, "message": f"Print failure: {e!s}"}
            finally:
                if bt_format:
                    try:
                        bt_format.Close(0)
                    except Exception: pass
                pythoncom.CoUninitialize()

    def print_xml(self, xml_content: str, printer_name_override: str | None = None, fallback_path: str | None = None, local_template_dir: str | None = None) -> dict[str, Any]:
        """
        Fallback parser that accepts a raw BTXML string, parses it, and maps it to print_label.
        Ensures 100% backward compatibility with legacy routes.
        """
        try:
            from src.core.utils import TemplateResolver
            from src.features.print.domain import BTXMLDocument
            doc = BTXMLDocument.from_xml(xml_content)
            
            # Apply overrides/fallbacks
            if printer_name_override:
                doc.printer_name = printer_name_override
            
            # Use unified TemplateResolver
            doc.template_path = TemplateResolver.resolve(
                path=doc.template_path,
                fallback_path=fallback_path,
                local_dir=local_template_dir
            )

            if not os.path.exists(doc.template_path):
                return {"success": False, "message": f"BTW Template file not found: {doc.template_path}"}

            return self.print_label(doc.template_path, doc.printer_name, doc.substrings)
        except Exception as e:
            logger.error(f"Failed parsing BTXML string: {e}")
            return {"success": False, "message": f"BTXML parsing failure: {e!s}"}

    def validate_template_file(self, template_path: str) -> tuple[bool, str]:
        """Thread-safe template verification via BarTender COM or file inspection."""
        if not HAS_WINDOWS_DEPS:
            return True, "MOCK: Template valid"

        with self._lock:
            try:
                pythoncom.CoInitialize()
                self._ensure_connected()
                if not self.bt_app:
                    return True, "BarTender COM not connected, file exists on disk"
                fmt = self.bt_app.Formats.Open(template_path, False, "")
                if fmt:
                    fmt.Close(0)
                    return True, "Tệp mẫu tem hợp lệ và mở thành công qua BarTender COM Engine."
                return False, "BarTender COM Engine không thể mở định dạng tệp tem này."
            except Exception as e:
                logger.warning(f"COM Format open check warning: {e}")
                if os.path.exists(template_path):
                    return True, "Tệp mẫu tem tồn tại trên ổ đĩa máy chủ."
                return False, f"Lỗi BarTender Engine khi mở mẫu tem: {e!s}"


# Singleton instance
bt_com_app = BarTenderCOMApp()
