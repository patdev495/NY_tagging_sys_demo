from src.core.models import Carton, Product
from src.features.print.domain import BTXMLDocument


def test_erro_02_btxml_document_from_carton_data():
    product = Product(
        id=10,
        item_name="G112C1B",
        packed_qty=190,
        mfr_pn="NYS5996",
        upc="840268969493",
        asin="B0C32N712K",
        product_desc="ASSY, BAND WRAPPED, CAT6A ETHERNET CABLE 4.7MM OD, 91CM , WHITE,RUBBER BAND",
        template_type="erro_02",
        template_path=r"D:\PAT\Templates\erro_02.btw",
    )
    carton = Carton(
        id=20,
        product_id=10,
        carton_sn="03703390710002861",
        packed_by="TSC_TTP_244_Pro",
    )

    doc = BTXMLDocument.from_carton_data(
        carton=carton,
        product=product,
        items=[],
        template_path=str(product.template_path or ""),
        printer_name="TSC_TTP_244_Pro",
    )

    assert doc.substrings["ProductName"] == "Product name:ASSY, BAND WRAPPED, CAT6A ETHERNET CABLE 4.7MM OD, 91CM , WHITE,RUBBER BAND"
    assert doc.substrings["QTY"] == "190"
    assert doc.substrings["SSCC_Text"] == "(00) 0 37033907 1000286"
    assert doc.substrings["SSCC_CD"] == "1"
    assert doc.substrings["PN"] == "NYS5996"
    assert doc.substrings["ASIN"] == "B0C32N712K"
    assert doc.substrings["UnitUPC"] == "840268969493"

    # XML serialization test
    xml = doc.to_xml(template_type="erro_02")
    assert "<Format>D:\\PAT\\Templates\\erro_02.btw</Format>" in xml
    assert "<Printer>TSC_TTP_244_Pro</Printer>" in xml
    assert '<NamedSubString Name="ProductName"><Value>Product name:ASSY, BAND WRAPPED, CAT6A ETHERNET CABLE 4.7MM OD, 91CM , WHITE,RUBBER BAND</Value></NamedSubString>' in xml
    assert '<NamedSubString Name="QTY"><Value>190</Value></NamedSubString>' in xml
    assert '<NamedSubString Name="SSCC_Text"><Value>(00) 0 37033907 1000286</Value></NamedSubString>' in xml
    assert '<NamedSubString Name="SSCC_CD"><Value>1</Value></NamedSubString>' in xml
    assert '<NamedSubString Name="PN"><Value>NYS5996</Value></NamedSubString>' in xml
    assert '<NamedSubString Name="ASIN"><Value>B0C32N712K</Value></NamedSubString>' in xml
    assert '<NamedSubString Name="UnitUPC"><Value>840268969493</Value></NamedSubString>' in xml

    # Parse back
    parsed = BTXMLDocument.from_xml(xml)
    assert parsed.substrings["PN"] == "NYS5996"
    assert parsed.substrings["SSCC_Text"] == "(00) 0 37033907 1000286"
    assert parsed.substrings["SSCC_CD"] == "1"
