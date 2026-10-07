import os
from unittest.mock import MagicMock, patch

import pytest

from src.core.utils import TemplateResolver
from src.features.print.bartender_com import BarTenderCOMApp
from src.features.print.domain import BTXMLDocument

# ==========================================
# 1. TESTS FOR TEMPLATERESOLVER
# ==========================================

class TestTemplateResolver:
    @patch("os.path.exists")
    def test_resolve_local_directory_priority(self, mock_exists):
        """Should prioritize local client template directory if file exists there."""
        # Setup: local path exists
        mock_exists.side_effect = lambda p: "local_dir" in p or "templates" in p
        
        resolved = TemplateResolver.resolve(
            "C:\\remote\\label.btw",
            local_dir="C:\\local_dir"
        )
        
        assert resolved == os.path.normpath("C:\\local_dir\\label.btw")

    @patch("os.path.exists")
    def test_resolve_absolute_path_fallback(self, mock_exists):
        """Should fallback to absolute path if no local directory is provided or if local file doesn't exist."""
        # Setup: only absolute path exists
        mock_exists.side_effect = lambda p: p == "C:\\absolute\\label.btw"
        
        resolved = TemplateResolver.resolve(
            "C:\\absolute\\label.btw",
            local_dir="C:\\local_dir"
        )
        
        assert resolved == os.path.normpath("C:\\absolute\\label.btw")

    @patch("os.path.exists")
    def test_resolve_settings_templates_dir(self, mock_exists):
        """Should fall back to search in central settings templates directory."""
        mock_exists.side_effect = lambda p: "src" in p and "templates" in p
        
        resolved = TemplateResolver.resolve(
            "label.btw"
        )
        
        assert "templates" in resolved
        assert resolved.endswith("label.btw")

    def test_template_resolver_canonical_mapping(self):
        """Should return canonical template filename for each template type."""
        assert TemplateResolver.get_canonical_template_filename("erro_02") == "erro_02.btw"
        assert TemplateResolver.get_canonical_template_filename("erro_01") == "erro_01.btw"
        assert TemplateResolver.get_canonical_template_filename("erro_04") == "erro_04.btw"
        assert TemplateResolver.get_canonical_template_filename("standard") == "carton_base.btw"
        assert TemplateResolver.get_canonical_template_filename("detailed") == "carton_detail.btw"
        assert TemplateResolver.get_canonical_template_filename("unknown") == "carton_base.btw"

    @patch("os.path.exists")
    def test_check_template_exists(self, mock_exists):
        """Should verify template existence in default or custom directory."""
        mock_exists.side_effect = lambda p: "D:\\PAT\\Templates\\a11_02.btw" in p
        
        res = TemplateResolver.check_template_exists("a11_02.btw")
        assert res["exists"] is True
        assert res["path"] == os.path.normpath("D:\\PAT\\Templates\\a11_02.btw")

        res_missing = TemplateResolver.check_template_exists("missing.btw")
        assert res_missing["exists"] is False


# ==========================================
# 2. TESTS FOR BTXMLDOCUMENT DOMAIN OBJECT
# ==========================================

class TestBTXMLDocument:
    def test_parse_from_xml(self):
        """Should successfully parse properties and substrings from raw BTXML content."""
        raw_xml = """<?xml version="1.0" encoding="utf-8"?>
        <XMLScript Version="2.0">
            <Command Name="Job1">
                <Print>
                    <Format>C:\\templates\\carton.btw</Format>
                    <Printer>Microsoft Print to PDF</Printer>
                    <NamedSubString Name="ItemName"><Value>Pro Product</Value></NamedSubString>
                    <NamedSubString Name="QTY"><Value>30PCS</Value></NamedSubString>
                    <NamedSubString Name="CartonSN"><Value>VN-18-2605001</Value></NamedSubString>
                </Print>
            </Command>
        </XMLScript>
        """
        
        doc = BTXMLDocument.from_xml(raw_xml)
        
        assert doc.template_path == "C:\\templates\\carton.btw"
        assert doc.printer_name == "Microsoft Print to PDF"
        assert doc.substrings["ItemName"] == "Pro Product"
        assert doc.substrings["QTY"] == "30PCS"
        assert doc.substrings["CartonSN"] == "VN-18-2605001"

    def test_parse_from_invalid_xml_raises_value_error(self):
        """Should raise ValueError when parsing malformed or invalid XML."""
        with pytest.raises(ValueError):
            BTXMLDocument.from_xml("<InvalidXML>NoPrintTag</InvalidXML>")

    def test_remap_template_path(self):
        """Should correctly remap template path to a local directory."""
        doc = BTXMLDocument(template_path="C:\\server\\labels\\carton.btw")
        doc.remap_template_path("D:\\client\\labels")
        
        assert doc.template_path == os.path.normpath("D:\\client\\labels\\carton.btw")


# ==========================================
# 3. TESTS FOR BARTENDERCOMAPP (INFRASTRUCTURE)
# ==========================================

class TestBarTenderCOMApp:
    def test_driver_mode_on_non_windows(self):
        """Should safely fallback to Mock Mode on non-Windows/dev environment without crashing."""
        app = BarTenderCOMApp()
        
        # Force non-Windows state for testing fallback
        with patch("src.features.print.bartender_com.HAS_WINDOWS_DEPS", False):
            success = app.start()
            assert success is True
            assert app.is_initialized is True
            
            # Print should mock successfully
            result = app.print_label("dummy.btw", "PDF", {"CartonSN": "MOCK"})
            assert result["success"] is True
            assert result["type"] == "pdf"
            assert result["data"] == "bW9ja19wZGZfYmFzZTY0X2NvbnRlbnQ="

    @patch("src.features.print.bartender_com.HAS_WINDOWS_DEPS", True)
    def test_connection_recovery_logic(self):
        """Should automatically trigger reconnection if the COM application goes down."""
        app = BarTenderCOMApp()
        app.bt_app = MagicMock()
        
        # Simulate active connection
        app.bt_app.Formats = MagicMock()
        app._ensure_connected()

        # Simulate connection loss by setting app to None
        app.bt_app = None
        
        with patch("src.features.print.bartender_com.BarTenderCOMApp._create_dispatch_instance", return_value=True) as mock_dispatch:
            app._ensure_connected()
            mock_dispatch.assert_called_once()
