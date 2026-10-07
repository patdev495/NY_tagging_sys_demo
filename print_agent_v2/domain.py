"""
Domain Layer for BarTender Printing Feature.
Encapsulates Label Schema Invariants, XML Document Generation, and Parsing.
"""
import os
import sys
import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

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

    def __init__(self, template_path: str, printer_name: Optional[str] = None, substrings: Optional[Dict[str, str]] = None):
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
            raise ValueError(f"Error parsing BTXML: {str(e)}")

    @classmethod
    def from_carton_data(cls, carton, product, items: List[str], template_path: str, printer_name: Optional[str] = None) -> "BTXMLDocument":
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

        # Apply specific detailed template rules (such as ItemName repetition and MAC_ID)
        template_type = getattr(product, 'template_type', 'standard') or 'standard'
        if template_type == "detailed":
            substrings["ItemName2"] = product.item_name
            substrings["ItemName3"] = product.item_name
            substrings["MAC_ID"] = f"MAC ID ({actual_qty})"
            
            # Fill the detailed SN grid
            for i in range(MAX_SN_GRID):
                sn_value = items[i] if i < len(items) else " "
                substrings[f"SN_{i+1}"] = sn_value

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
            "qty": self.substrings.get("QTY", ""),
            "carton_sn": self.substrings.get("CartonSN", ""),
            "upc": self.substrings.get("UPC", ""),
            "qr_content": self.substrings.get("QR_Content", ""),
            "origin_text": self.substrings.get("Origin", ""),
            "mac_id": self.substrings.get("MAC_ID", "")
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
