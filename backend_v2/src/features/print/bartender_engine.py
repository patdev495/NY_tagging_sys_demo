"""
BarTender Engine — Tích hợp trực tiếp vào Backend.
Quản lý COM connection tới BarTender, in tem, xuất PDF.
Delegates heavy lifting to the unified BarTenderCOMApp module.
"""
import logging

from src.features.print.bartender_com import bt_com_app

logger = logging.getLogger("BarTenderEngine")

class BarTenderEngine:
    """Wrapper class over the unified BarTenderCOMApp to maintain 100% backward compatibility."""

    def __init__(self):
        # Delegate to the shared COM app singleton
        self.com_app = bt_com_app

    @property
    def is_initialized(self) -> bool:
        return self.com_app.is_initialized

    def start(self) -> bool:
        """Khởi tạo kết nối COM tới BarTender."""
        return self.com_app.start()

    def print_xml(self, xml_content: str, printer_name_override: str | None = None, fallback_path: str | None = None) -> dict:
        """In tem từ BTXML (BTXML string)."""
        return self.com_app.print_xml(
            xml_content=xml_content, 
            printer_name_override=printer_name_override, 
            fallback_path=fallback_path
        )

    def get_printers(self) -> list:
        """Lấy danh sách máy in Windows (lọc bỏ máy in ảo)."""
        return self.com_app.get_printers()


# Singleton instance
bt_engine = BarTenderEngine()
