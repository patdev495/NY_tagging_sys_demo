"""
Domain Layer for BarTender Printing Feature.
Encapsulates Label Schema Invariants, XML Document Generation, and Parsing.
"""
import datetime
import logging
import os
import sys
import xml.etree.ElementTree as ET

logger = logging.getLogger("BarTenderDomain")

MAX_SN_GRID = 40  # Maximum SN slots on the detailed label

def _get_template_base_dir() -> str:
    """Get the correct base directory for XML templates, handling both dev and PyInstaller exe."""
    if getattr(sys, 'frozen', False):
        meipass = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        frozen_path = os.path.join(meipass, "src", "features", "print")
        if os.path.isdir(frozen_path):
            return frozen_path
    
    # Dev mode: relative to this file
    return os.path.dirname(os.path.abspath(__file__))


class BTXMLDocument:
    """
    Domain object representing a BarTender XMLScript print job.
    Encapsulates template-specific rules, path remapping, and XML serialization/deserialization.
    """

    def __init__(self, template_path: str, printer_name: str | None = None, substrings: dict[str, str] | None = None):
        self.template_path = template_path or ""
        self.printer_name = printer_name or ""
        self.substrings = substrings or {}

    @classmethod
    def from_xml(cls, xml_content: str) -> "BTXMLDocument":
        """
        Parses a raw BTXML string back into a structured BTXMLDocument.
        Encapsulates parsing logic, making callers completely independent of XML tags.
        """
        try:
            root = ET.fromstring(xml_content)
            print_element = root.find('.//Print')
            if print_element is None:
                raise ValueError("Invalid BTXML structure: No <Print> element found.")

            format_element = print_element.find('Format')
            template_path = (format_element.text or "") if format_element is not None else ""

            printer_name = ""
            printer_el = print_element.find('.//Printer')
            if printer_el is not None and printer_el.text:
                printer_name = printer_el.text or ""

            # Parse NamedSubStrings
            substrings = {}
            for ns in print_element.findall('NamedSubString'):
                name = ns.get('Name')
                value_el = ns.find('Value')
                if name and value_el is not None:
                    substrings[name] = value_el.text or " "

            return cls(template_path=template_path, printer_name=printer_name, substrings=substrings)
        except Exception as e:
            logger.error(f"Failed to parse BTXML document: {e}")
            raise ValueError(f"Error parsing BTXML: {e!s}")

    @classmethod
    def from_carton_data(cls, carton, product, items: list[str], template_path: str, printer_name: str | None = None) -> "BTXMLDocument":
        """
        Creates a BTXMLDocument from Carton domain data, automatically applying schema invariants
        and template-specific rules (like the detailed SN grid).
        """
        raw_origin = getattr(carton, 'carton_origin', 'VN') or 'VN'
        origin_text = "Made in China" if raw_origin == "CN" else "Made in Vietnam"
        qr_content = "&#xA;".join(items)

        actual_qty = len(items)
        qty_text = f"{actual_qty} PCS"

        substrings = {
            "ItemName": product.item_name,
            "QTY": qty_text,
            "CartonSN": carton.carton_sn,
            "UPC": product.upc,
            "QR_Content": qr_content,
            "Origin": origin_text
        }

        # Apply specific template rules
        template_type = getattr(product, 'template_type', 'standard') or 'standard'
        if template_type == "detailed":
            substrings["ItemName2"] = product.item_name
            substrings["ItemName3"] = product.item_name
            substrings["MAC_ID"] = f"MAC ID ({actual_qty})"
            
            # Fill the detailed SN grid
            for i in range(MAX_SN_GRID):
                sn_value = items[i] if i < len(items) else " "
                substrings[f"SN_{i+1}"] = sn_value
        elif template_type == "erro_01":
            cpn = product.item_name or ""
            qty = str(product.packed_qty or actual_qty or 190)
            mfr_pn = getattr(product, 'mfr_pn', '') or ""
            date_code = getattr(carton, 'date_code', '') or ""
            lot_no = getattr(carton, 'lot_number', '') or ""
            po_no = getattr(carton, 'po_number', '') or ""
            carton_sn = carton.carton_sn or ""
            rev = getattr(product, 'revision', '') or ''
            qr_content = f"P{cpn},Q{qty},M{mfr_pn},D{date_code},L{lot_no},K{po_no},S{carton_sn}"

            substrings["CPN"] = cpn
            substrings["QTY"] = qty
            substrings["MfrPN"] = mfr_pn
            substrings["DateCode"] = date_code
            substrings["LotNo"] = lot_no
            substrings["PONo"] = po_no
            substrings["CartonSN"] = carton_sn
            substrings["QR_Content"] = qr_content
            substrings["Rev"] = rev
            substrings["Origin"] = origin_text
        elif template_type == "erro_02":
            product_desc = getattr(product, 'product_desc', '') or ''
            product_name_text = f"Product name:{product_desc}" if product_desc else (product.item_name or "")
            qty = str(product.packed_qty or actual_qty or 190)
            carton_sn = carton.carton_sn or ""

            # Extract SSCC text and CD from carton_sn (e.g. 03703390710002861)
            # Format: '0' + prefix(8) + seq(7) + cd(1) = 17 chars
            if len(carton_sn) >= 17 and carton_sn.startswith("0"):
                company_prefix = carton_sn[1:9]
                seq_part = carton_sn[9:16]
                cd_part = carton_sn[16:17]
                sscc_text = f"(00) 0 {company_prefix} {seq_part}"
                sscc_cd = cd_part
            else:
                sscc_text = carton_sn
                sscc_cd = ""

            pn = getattr(product, 'mfr_pn', '') or ""
            asin = getattr(product, 'asin', '') or ""
            unit_upc = getattr(product, 'upc', '') or ""

            substrings["ProductName"] = product_name_text
            substrings["QTY"] = qty
            substrings["SSCC_Text"] = sscc_text
            substrings["SSCC_CD"] = sscc_cd
            substrings["PN"] = pn
            substrings["ASIN"] = asin
            substrings["UnitUPC"] = unit_upc
        elif template_type == "erro_03":
            carton_sn = carton.carton_sn or ""
            supplier_code = getattr(product, 'pkg_prefix', None) or "1012665"
            supplier_name = "NIENYI VIETNAM INDUSTRIAL COMPANY LIMITED"
            part_no = getattr(product, "luxshare_part_number", None) or ""
            apn_rev = getattr(product, 'revision', '') or "/"
            lot_no = getattr(carton, 'lot_number', '') or "92607933"
            qty = str(product.packed_qty or actual_qty or 190)
            part_desc = getattr(product, 'product_desc', '') or (product.item_name or "")
            origin_text = "VIETNAM"

            # Format Date: YYYYMMDD
            created_at = getattr(carton, 'created_at', None) or datetime.datetime.now()
            date_ymd = created_at.strftime("%Y%m%d")

            customer_project = (getattr(product, "customer_project", None) or "").strip()
            production_stage = (getattr(product, "production_stage", None) or "").strip()
            project_stage_text = f"项目: {customer_project}         生产阶段：{production_stage}"
            qr_apn_rev = "" if apn_rev == "/" else apn_rev
            qr_code_content = f"{carton_sn}${supplier_code}${supplier_name}${part_no}${qr_apn_rev}${lot_no}${date_ymd}${qty}$$$$$$"

            substrings["CartonSN"] = carton_sn
            substrings["SupplierCode"] = supplier_code
            substrings["SupplierName"] = supplier_name
            substrings["LuxsharePartNo"] = part_no
            substrings["APNRev"] = apn_rev
            substrings["LotNo"] = lot_no
            substrings["QTY"] = qty
            substrings["Date"] = date_ymd
            substrings["PartDesc"] = part_desc
            substrings["Origin"] = origin_text
            substrings["ProjectStage"] = project_stage_text
            substrings["QR_Content"] = qr_code_content
            substrings["QRCode_Content"] = qr_code_content
        elif template_type == "erro_04":
            carton_sn = carton.carton_sn or ""
            created_at = getattr(carton, "created_at", None) or datetime.datetime.now()
            substrings["UPC"] = getattr(product, "upc", "") or ""
            substrings["SKU"] = product.item_name or ""
            substrings["CartonID"] = carton_sn
            substrings["SupplierPN"] = getattr(product, "mfr_pn", "") or ""
            substrings["PO"] = getattr(carton, "po_number", "") or ""
            substrings["Date"] = created_at.strftime("%y%m%d")
            substrings["Qty"] = str(product.packed_qty or actual_qty or "")
            substrings["Rev"] = getattr(product, "revision", "") or ""
            substrings["SKUDescription"] = getattr(product, "product_desc", "") or ""
        elif template_type == "erro_05":
            carton_sn = carton.carton_sn or ""
            created_at = getattr(carton, "created_at", None) or datetime.datetime.now()
            yy = created_at.strftime("%y")
            ww = f"{created_at.isocalendar()[1]:02d}"
            date_code = f"{yy}{ww}"
            lot_code = (getattr(carton, "lot_number", None) or "").strip() or created_at.strftime("%Y%m%d")
            qty = str(product.packed_qty or actual_qty or "1000")
            item = product.item_name or ""
            desc = getattr(product, "product_desc", "") or ""
            mpn = ""
            rev = getattr(product, "revision", "") or ""
            config = ""
            batch = (getattr(carton, "po_number", None) or "").strip()
            stage = ""
            qr_code_content = f"{carton_sn},{item},{mpn},{batch},{qty},{date_code},{lot_code}"

            substrings["CartonNo"] = carton_sn
            substrings["Item"] = item
            substrings["DESC"] = desc
            substrings["DateCode"] = date_code
            substrings["LotCode"] = lot_code
            substrings["QTY"] = qty
            substrings["QRCode_Content"] = qr_code_content
            substrings["MPN"] = mpn
            substrings["Rev"] = rev
            substrings["Config"] = config
            substrings["Batch"] = batch
            substrings["Stage"] = stage

        return cls(template_path=template_path, printer_name=printer_name, substrings=substrings)

    def to_xml(self, template_type: str = "standard") -> str:
        """
        Serializes the document properties into a standardized, beautifully formatted BTXML script.
        Maintains 100% backward compatibility with existing templates.
        """
        # Map "standard" to "base" to prevent warning log
        if template_type == "standard":
            template_type = "base"

        base_dir = _get_template_base_dir()
        template_file = os.path.join(base_dir, "templates", f"{template_type}.xml")

        # Fallback to base.xml if specific template file does not exist
        if not os.path.exists(template_file):
            fallback_file = os.path.join(base_dir, "templates", "base.xml")
            logger.warning(f"Template '{template_file}' NOT FOUND! Falling back to '{fallback_file}'")
            template_file = fallback_file
            template_type = "standard"

        with open(template_file, "r", encoding="utf-8") as f:
            xml_template = f.read()

        printer_tag = f"<Printer>{self.printer_name}</Printer>" if self.printer_name else ""
        
        data_dict = {
            "template_path": self.template_path,
            "printer_tag": printer_tag,
            "item_name": self.substrings.get("ItemName", ""),
            "qty": self.substrings.get("Qty") or self.substrings.get("QTY", ""),
            "carton_sn": self.substrings.get("CartonSN", ""),
            "upc": self.substrings.get("UPC", ""),
            "qr_content": self.substrings.get("QR_Content", ""),
            "origin_text": self.substrings.get("Origin", ""),
            "mac_id": self.substrings.get("MAC_ID", ""),
            "cpn": self.substrings.get("CPN", ""),
            "mfr_pn": self.substrings.get("MfrPN", ""),
            "date_code": self.substrings.get("DateCode", ""),
            "lot_no": self.substrings.get("LotNo", ""),
            "po_no": self.substrings.get("PONo", ""),
            "rev": self.substrings.get("Rev", ""),
            "product_name": self.substrings.get("ProductName", ""),
            "sscc_text": self.substrings.get("SSCC_Text", ""),
            "sscc_cd": self.substrings.get("SSCC_CD", ""),
            "pn": self.substrings.get("PN", ""),
            "asin": self.substrings.get("ASIN", ""),
            "unit_upc": self.substrings.get("UnitUPC", ""),
            "project_stage": self.substrings.get("ProjectStage", ""),
            "part_no": self.substrings.get("LuxsharePartNo", ""),
            "apn_rev": self.substrings.get("APNRev", ""),
            "date": self.substrings.get("Date", ""),
            "part_desc": self.substrings.get("PartDesc", ""),
            "supplier_code": self.substrings.get("SupplierCode", ""),
            "supplier_name": self.substrings.get("SupplierName", ""),
            "origin": self.substrings.get("Origin", ""),
            "qr_code_content": self.substrings.get("QR_Content") or self.substrings.get("QRCode_Content", ""),
            "supplier_pn": self.substrings.get("SupplierPN", ""),
            "carton_id": self.substrings.get("CartonID", ""),
            "po": self.substrings.get("PO", ""),
            "sku": self.substrings.get("SKU", ""),
            "sku_description": self.substrings.get("SKUDescription", ""),
            "carton_no": self.substrings.get("CartonNo", ""),
            "item": self.substrings.get("Item", ""),
            "desc": self.substrings.get("DESC", ""),
            "lot_code": self.substrings.get("LotCode", ""),
            "mpn": self.substrings.get("MPN", ""),
            "config": self.substrings.get("Config", ""),
            "batch": self.substrings.get("Batch", ""),
            "stage": self.substrings.get("Stage", ""),
        }

        # Build dynamic detailed grid tags if needed
        if template_type == "detailed":
            sn_tags = []
            for i in range(MAX_SN_GRID):
                sn_value = self.substrings.get(f"SN_{i+1}", " ")
                sn_tags.append(f'            <NamedSubString Name="SN_{i+1}"><Value>{sn_value}</Value></NamedSubString>')
            data_dict["sn_grid_tags"] = "\n".join(sn_tags)

        # Format and strip
        return xml_template.format(**data_dict).strip()

    def remap_template_path(self, local_template_dir: str):
        """Helper to remap template path to a local directory for client-side printing."""
        if not local_template_dir or not self.template_path:
            return
        filename = os.path.basename(self.template_path)
        self.template_path = os.path.normpath(os.path.join(local_template_dir, filename))
