import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


def test_erro_03_print_agent_uses_named_substrings_without_legacy_object_import():
    agent_dir = Path(__file__).resolve().parents[2] / "print_agent_v2"
    sys.path.insert(0, str(agent_dir))
    try:
        import bartender_com

        class FakeObjects:
            def __init__(self):
                self.import_calls = 0

            def ImportDataSourceValuesFromXML(self, _xml):
                self.import_calls += 1

        class FakeFormat:
            def __init__(self):
                self.Objects = FakeObjects()
                self.PrintSetup = SimpleNamespace(Printer=None)
                self.values = {}

            def SetNamedSubStringValue(self, key, value):
                self.values[key] = value

            def PrintOut(self, *_args):
                return None

            def Close(self, *_args):
                return None

        fmt = FakeFormat()
        app = bartender_com.BarTenderCOMApp()
        app.is_initialized = True
        app.bt_app = SimpleNamespace(Formats=SimpleNamespace(Open=lambda *_args: fmt))

        with patch.object(bartender_com, "HAS_WINDOWS_DEPS", True), patch.object(
            bartender_com, "pythoncom", SimpleNamespace(CoInitialize=lambda: None, CoUninitialize=lambda: None)
        ), patch.object(app, "_ensure_connected"):
            result = app.print_label(
                str(agent_dir / "erro_03.btw"),
                "Zebra",
                {"CartonSN": "10126652609180003", "SupplierName": "NIENYI VIETNAM"},
            )

        assert result["success"] is True
        assert fmt.Objects.import_calls == 0
        assert fmt.values["CartonSN"] == "10126652609180003"
    finally:
        sys.path.remove(str(agent_dir))
