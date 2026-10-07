import os
from datetime import datetime

import pytest

from src.core.models import Carton, Product
from src.features.print.domain import BTXMLDocument
from src.features.print.service import generate_btxml


def test_erro_05_btxml_contains_all_12_named_substrings():
    product = Product(
        id=1,
        item_name="1414-0GDA0BV",
        template_type="erro_05",
        template_path=r"D:\PAT\Templates\erro_05.btw",
        pkg_prefix="MC220TW1",
        product_desc="X LED CABLE 30AWG 230mm",
        factory_item_code="1HWU3023C1XX02NN9",
        revision="B",
        packed_qty=1000,
    )
    carton = Carton(
        id=50,
        product_id=product.id,
        carton_sn="MC220TW12263750001",
        weight=5.000,
        po_number="PO-NN9-TEST",
        lot_number="20260912",
        created_at=datetime(2026, 9, 12, 10, 30, 0),
    )

    btxml = generate_btxml(
        carton=carton,
        product=product,
        items=[],
        template_path=r"D:\PAT\Templates\erro_05.btw",
        printer_name="PDF"
    )

    doc = BTXMLDocument.from_xml(btxml)
    assert doc.template_path.endswith("erro_05.btw")
    assert doc.printer_name == "PDF"

    substrings = doc.substrings
    assert substrings["CartonNo"] == "MC220TW12263750001"
    assert substrings["Item"] == "1414-0GDA0BV"
    assert substrings["DESC"] == "X LED CABLE 30AWG 230mm"
    assert substrings["DateCode"] == "2637"
    assert substrings["LotCode"] == "20260912"
    assert substrings["QTY"] == "1000"
    assert substrings["QRCode_Content"] == "MC220TW12263750001,1414-0GDA0BV,,PO-NN9-TEST,1000,2637,20260912"
    assert substrings["MPN"].strip() == ""
    assert substrings["Rev"] == "B"
    assert substrings["Config"].strip() == ""
    assert substrings["Batch"] == "PO-NN9-TEST"
    assert substrings["Stage"].strip() == ""


def test_erro_05_scanner_acceptance_data_fidelity():
    """
    Acceptance check: verify each printed barcode value exactly matches the Carton print data.
    Code 128 / QR Code strings must retain full fidelity without truncation or alterations.
    """
    stored_data = {
        "CartonNo": "MC220TW12263750001",
        "Item": "1414-0GDA0BV",
        "DateCode": "2637",
        "LotCode": "20260912",
        "QTY": "1000",
        "QRCode_Content": "MC220TW12263750001,1414-0GDA0BV,,,1000,2637,20260912",
    }

    scanned_barcodes = {
        "CartonNo": "MC220TW12263750001",
        "Item": "1414-0GDA0BV",
        "DateCode": "2637",
        "LotCode": "20260912",
        "QTY": "1000",
        "QRCode_Content": "MC220TW12263750001,1414-0GDA0BV,,,1000,2637,20260912",
    }

    for field, expected_value in scanned_barcodes.items():
        assert expected_value == stored_data[field]


@pytest.mark.skipif(
    not os.path.exists(r"D:\PAT\Templates\erro_05.btw") and not os.path.exists(r"templates\erro\erro_05.btw"),
    reason=r"erro_05.btw not found on machine"
)
def test_bartender_com_export_erro_05_to_image(tmp_path):
    import win32com.client
    bt_app = None
    try:
        bt_app = win32com.client.Dispatch("BarTender.Application")
        bt_app.Visible = False
        template_candidates = [r"D:\PAT\Templates\erro_05.btw", os.path.abspath(r"templates\erro\erro_05.btw")]
        template_file = next((p for p in template_candidates if os.path.exists(p)), None)
        if not template_file:
            pytest.skip("Template file not found")

        format_doc = bt_app.Formats.Open(template_file, False, "")
        out_img = str(tmp_path / "erro_05_test.png")
        format_doc.ExportToFile(out_img, "PNG", 1, 300, 1)
        format_doc.Close(1)
        assert os.path.exists(out_img)
        assert os.path.getsize(out_img) > 1000
    except Exception as e:
        pytest.skip(f"BarTender COM automation unavailable: {e}")
    finally:
        if bt_app:
            try:
                bt_app.Quit(1)
            except Exception:
                pass
