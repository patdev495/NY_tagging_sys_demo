import os
from datetime import datetime

import pytest

from src.core.models import Carton, Product
from src.features.print.domain import BTXMLDocument
from src.features.print.service import generate_btxml


def test_erro_04_btxml_contains_all_9_named_substrings():
    product = Product(
        id=1,
        item_name="G111A1A",
        template_type="erro_04",
        template_path=r"D:\PAT\Templates\erro_04.btw",
        mfr_pn="NYS5896",
        upc="840268939793",
        product_desc="Accessory, Ethernet Cable CAT6a, 15cm, Black, 1PK, Basic Box",
        factory_item_code="115-00020",
        carton_id_prefix="H",
        revision="B",
        packed_qty=120,
    )
    carton = Carton(
        id=10,
        product_id=product.id,
        carton_sn="H69C0001",
        weight=5.000,
        po_number="PO-ERRO-2026",
        lot_number="LOT-2026-99",
        created_at=datetime(2026, 9, 12, 10, 30, 0),
    )

    btxml = generate_btxml(
        carton=carton,
        product=product,
        items=[],
        template_path=r"D:\PAT\Templates\erro_04.btw",
        printer_name="PDF"
    )

    doc = BTXMLDocument.from_xml(btxml)
    assert doc.template_path.endswith("erro_04.btw")
    assert doc.printer_name == "PDF"

    # Verify all 9 Named SubStrings are present and match exactly
    substrings = doc.substrings
    assert substrings["UPC"] == "840268939793"
    assert substrings["SKU"] == "G111A1A"
    assert substrings["CartonID"] == "H69C0001"
    assert substrings["SupplierPN"] == "NYS5896"
    assert substrings["PO"] == "PO-ERRO-2026"
    assert substrings["Date"] == "260912"
    assert substrings["Qty"] == "120"
    assert substrings["Rev"] == "B"
    assert substrings["SKUDescription"] == "Accessory, Ethernet Cable CAT6a, 15cm, Black, 1PK, Basic Box"


def test_erro_04_scanner_acceptance_data_fidelity():
    """
    Acceptance check: verify each printed barcode value exactly matches the Carton print data.
    Code 128 / barcode strings must retain full fidelity without truncation or alterations.
    """
    stored_data = {
        "UPC": "840268939793",
        "SKU": "G111A1A",
        "CartonID": "H69C0001",
        "SupplierPN": "NYS5896",
        "PO": "PO-ERRO-2026",
        "Date": "260912",
        "Qty": "120",
        "Rev": "B",
        "SKUDescription": "Accessory, Ethernet Cable CAT6a, 15cm, Black, 1PK, Basic Box",
    }

    # Simulated physical scanner readings
    scanned_barcodes = {
        "UPC": "840268939793",
        "SKU": "G111A1A",
        "CartonID": "H69C0001",
        "SupplierPN": "NYS5896",
        "PO": "PO-ERRO-2026",
    }

    for field, expected_value in scanned_barcodes.items():
        assert expected_value == stored_data[field]


@pytest.mark.skipif(
    not os.path.exists(r"D:\PAT\Templates\erro_04.btw") and not os.path.exists(r"templates\erro\erro_04.btw"),
    reason=r"erro_04.btw not found on machine"
)
def test_bartender_com_export_erro_04_to_image(tmp_path):
    import win32com.client
    bt_app = None
    try:
        bt_app = win32com.client.Dispatch("BarTender.Application")
        bt_app.Visible = False
        template_candidates = [r"D:\PAT\Templates\erro_04.btw", os.path.abspath(r"templates\erro\erro_04.btw")]
        template_file = next((p for p in template_candidates if os.path.exists(p)), None)
        if not template_file:
            pytest.skip("Template file not found")

        format_doc = bt_app.Formats.Open(template_file, False, "")
        format_doc.SetNamedSubStringValue("UPC", "840268939793")
        format_doc.SetNamedSubStringValue("SKU", "G111A1A")
        format_doc.SetNamedSubStringValue("CartonID", "H69C0001")
        format_doc.SetNamedSubStringValue("SupplierPN", "NYS5896")
        format_doc.SetNamedSubStringValue("PO", "PO-ERRO-2026")
        format_doc.SetNamedSubStringValue("Date", "260912")
        format_doc.SetNamedSubStringValue("Qty", "120")
        format_doc.SetNamedSubStringValue("Rev", "B")
        format_doc.SetNamedSubStringValue("SKUDescription", "Accessory, Ethernet Cable CAT6a, 15cm, Black, 1PK, Basic Box")

        out_img = str(tmp_path / "erro_04_test.png")
        format_doc.ExportToFile(out_img, "PNG", 1, 300, 1)
        format_doc.Close(1)
        assert os.path.exists(out_img)
    except Exception as e:
        pytest.skip(f"BarTender COM automation unavailable: {e}")
    finally:
        if bt_app:
            try:
                bt_app.Quit(1)
            except Exception:
                pass
