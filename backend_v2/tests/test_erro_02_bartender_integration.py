import os

import pytest

from src.core.models import Carton, Product
from src.features.print.domain import BTXMLDocument
from src.features.print.service import generate_btxml


def test_erro_02_btxml_contains_all_7_named_substrings():
    product = Product(
        id=1,
        item_name="G012C1B",
        template_type="erro_02",
        template_path=r"D:\PAT\Templates\a11_02.btw",
        mfr_pn="NYS5998",
        upc="852582006785",
        asin="B08G9M4HXS",
        pkg_prefix="37033907",
        product_desc="ASSY,BAND WRAPPED,CAT5E ETHERNET CABLE 4.0mm OD:91CM,WHITE,RUBBER BAND",
        packed_qty=190,
    )
    carton = Carton(
        id=10,
        product_id=product.id,
        carton_sn="03703390700000013",
        weight=6.050,
        po_number=None,
        lot_number=None,
    )

    btxml = generate_btxml(
        carton=carton,
        product=product,
        items=[],
        template_path=r"D:\PAT\Templates\a11_02.btw",
        printer_name="PDF"
    )

    # Parse back to domain document
    doc = BTXMLDocument.from_xml(btxml)
    assert doc.template_path.endswith("a11_02.btw")
    assert doc.printer_name == "PDF"

    # Verify all 7 Named SubStrings are present and correct
    substrings = doc.substrings
    assert substrings["ProductName"] == "Product name:ASSY,BAND WRAPPED,CAT5E ETHERNET CABLE 4.0mm OD:91CM,WHITE,RUBBER BAND"
    assert substrings["QTY"] == "190"
    assert substrings["SSCC_Text"] == "(00) 0 37033907 0000001"
    assert substrings["SSCC_CD"] == "3"
    assert substrings["PN"] == "NYS5998"
    assert substrings["ASIN"] == "B08G9M4HXS"
    assert substrings["UnitUPC"] == "852582006785"


@pytest.mark.skipif(
    not os.path.exists(r"D:\PAT\Templates\a11_02.btw"),
    reason=r"D:\PAT\Templates\a11_02.btw not found on machine"
)
def test_bartender_com_export_both_tem2_products_to_image(tmp_path):
    import win32com.client

    app = win32com.client.Dispatch("BarTender.Application")
    app.Visible = False

    try:
        fmt = app.Formats.Open(r"D:\PAT\Templates\a11_02.btw", False, "")

        # 1. Product G012C1B
        fmt.SetNamedSubStringValue("PN", "NYS5998")
        fmt.SetNamedSubStringValue("SSCC_CD", "3")
        fmt.SetNamedSubStringValue("ASIN", "B08G9M4HXS")
        fmt.SetNamedSubStringValue("SSCC_Text", "(00) 0 37033907 0000001")
        fmt.SetNamedSubStringValue("UnitUPC", "852582006785")
        fmt.SetNamedSubStringValue("QTY", "190")
        fmt.SetNamedSubStringValue("ProductName", "Product name:ASSY,BAND WRAPPED,CAT5E ETHERNET CABLE 4.0mm OD:91CM,WHITE,RUBBER BAND")

        out_g012 = str(tmp_path / "G012C1B.png")
        fmt.ExportToFile(out_g012, "PNG", 1, 300, 0)
        assert os.path.exists(out_g012)
        assert os.path.getsize(out_g012) > 1000

        # 2. Product G112C1B
        fmt.SetNamedSubStringValue("PN", "NYS5996")
        fmt.SetNamedSubStringValue("SSCC_CD", "1")
        fmt.SetNamedSubStringValue("ASIN", "B0C32N712K")
        fmt.SetNamedSubStringValue("SSCC_Text", "(00) 0 37033907 1000286")
        fmt.SetNamedSubStringValue("UnitUPC", "840268969493")
        fmt.SetNamedSubStringValue("QTY", "190")
        fmt.SetNamedSubStringValue("ProductName", "Product name:ASSY, BAND WRAPPED, CAT6A ETHERNET CABLE 4.7MM OD, 91CM , WHITE,RUBBER BAND")

        out_g112 = str(tmp_path / "G112C1B.png")
        fmt.ExportToFile(out_g112, "PNG", 1, 300, 0)
        assert os.path.exists(out_g112)
        assert os.path.getsize(out_g112) > 1000

        fmt.Close(2)  # btDoNotSaveChanges
    finally:
        app.Quit(1)  # btDoNotSaveChanges
