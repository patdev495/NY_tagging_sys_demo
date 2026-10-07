import os

import pytest

from src.core.models import Carton, Product
from src.features.print.domain import BTXMLDocument
from src.features.print.service import generate_btxml


def test_erro_03_btxml_contains_all_12_named_substrings():
    product = Product(
        id=30,
        item_name="2M21-00508-0004H",
        luxshare_part_number="LLERJ014-NC-R",
        template_type="erro_03",
        template_path=r"D:\PAT\Templates\a11_03.btw",
        pkg_prefix="1012665",
        product_desc="CAT5E ETHERNET CABLE",
        packed_qty=190,
        revision="/",
        customer_project="Andy Town/ Firefly",
        production_stage="MP",
    )
    carton = Carton(
        id=60,
        product_id=product.id,
        carton_sn="10126652609110001",
        weight=6.050,
        po_number=None,
        lot_number="92607933",
    )

    btxml = generate_btxml(
        carton=carton,
        product=product,
        items=[],
        template_path=r"D:\PAT\Templates\a11_03.btw",
        printer_name="PDF"
    )

    # Parse back to domain document
    doc = BTXMLDocument.from_xml(btxml)
    assert doc.template_path.endswith("a11_03.btw")
    assert doc.printer_name == "PDF"

    # Verify all 12 Named SubStrings are present and correct
    substrings = doc.substrings
    assert substrings["CartonSN"] == "10126652609110001"
    assert substrings["SupplierCode"] == "1012665"
    assert substrings["SupplierName"] == "NIENYI VIETNAM INDUSTRIAL COMPANY LIMITED"
    assert substrings["LuxsharePartNo"] == "LLERJ014-NC-R"
    assert substrings["APNRev"] == "/"
    assert substrings["QTY"] == "190"
    assert substrings["LotNo"] == "92607933"
    assert substrings["PartDesc"] == "CAT5E ETHERNET CABLE"
    assert substrings["Origin"] == "VIETNAM"
    assert len(substrings["Date"]) == 8
    assert substrings["ProjectStage"] == "项目: Andy Town/ Firefly         生产阶段：MP"
    assert "10126652609110001$1012665$" in substrings["QRCode_Content"]


@pytest.mark.skipif(
    not os.path.exists(r"D:\PAT\Templates\a11_03.btw"),
    reason=r"D:\PAT\Templates\a11_03.btw not found on machine"
)
def test_bartender_com_export_tem3_product_to_image(tmp_path):
    from src.features.print.bartender_com import bt_com_app

    substrings = {
        "CartonSN": "10126652609110001",
        "SupplierCode": "1012665",
        "SupplierName": "NIENYI VIETNAM INDUSTRIAL COMPANY LIMITED",
        "LuxsharePartNo": "LLERJ014-NC-R",
        "APNRev": "/",
        "QTY": "190",
        "Date": "20260911",
        "LotNo": "92607933",
        "PartDesc": "CAT5E ETHERNET CABLE",
        "Origin": "VIETNAM",
        "ProjectStage": "项目: Andy Town/ Firefly         生产阶段：QB/CR",
        "QRCode_Content": "10126652609110001$1012665$NIENYI VIETNAM INDUSTRIAL COMPANY LIMITED$2M21-00508-0004H$$92607933$20260911$190$$$$$$",
    }

    res = bt_com_app.print_label(
        template_path=r"D:\PAT\Templates\a11_03.btw",
        printer_name="PDF",
        substrings=substrings,
    )
    assert res["success"] is True
    assert res.get("data") is not None
