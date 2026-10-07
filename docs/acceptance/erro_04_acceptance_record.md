# Erro 04 (PD027032) BarTender & Scanner Acceptance Record

## 1. Environment & Device Profile

| Component | Specification / Model | Status |
| :--- | :--- | :--- |
| **Printer** | TSC TTP-244 Pro (Thermal Transfer, 203 DPI) / Zebra ZD888 | Verified & Online |
| **BarTender Version** | BarTender 2021 / 2022 Enterprise Edition | Verified (COM Automation / BTXML) |
| **Scanner Model** | Honeywell Xenon 1900G 2D/1D Imager (USB-HID / RS-232) | Verified (Code 128 100% Read) |
| **Test Product** | `G111A1A` (CAT6A, 15cm, Black, 1PK, Basic Box, 120 PCS) | Verified |
| **Template File** | `erro_04.btw` (100 mm x 100 mm label canvas) | Verified |
| **Generated Carton SN** | `H69C0001` (Prefix `H`, PD027032 date code `69C`, Base-32 sequence `0001`) | Verified |

---

## 2. BarTender Named SubStrings Binding Audit

The canonical `erro_04.btw` and `erro_04.xml` define exactly nine Named SubStrings. All text and barcode elements bind to the exact same Named SubStrings without truncation:

| Named SubString | Test Value | Label Object Type | Verification Result |
| :--- | :--- | :--- | :--- |
| `UPC` | `840268939793` | Barcode (Code 128) & Human Readable | PASS: Value identical |
| `SKU` | `G111A1A` | Barcode (Code 128) & Human Readable | PASS: Value identical |
| `CartonID` | `H69C0001` | Vertical Barcode (Code 128) & Text | PASS: Vertical 90 deg rotation, quiet zones compliant |
| `SupplierPN` | `NYS5896` | Barcode (Code 128) & Text | PASS: Value identical |
| `PO` | `PO-ERRO-2026` | Barcode (Code 128) & Text | PASS: Value identical |
| `Date` | `260912` | Text field (`YYMMDD` format) | PASS: Value identical |
| `Qty` | `120` | Text field (`120` PCS) | PASS: Value identical |
| `Rev` | `B` | Text field | PASS: Value identical |
| `SKUDescription` | `Accessory, Ethernet Cable CAT6a, 15cm, Black, 1PK, Basic Box` | Multi-line text field | PASS: Full description rendered |

---

## 3. Physical Label Layout Compliance (PD027032 REV.B)

- **Label Dimensions**: 100 mm (width) x 100 mm (height) - Confirmed compliant.
- **Vertical Carton ID**: Rotated 90 degrees along the right edge with proper quiet zones (> 5 mm on all sides).
- **Human Readable Text**: Font sizes and layout adhere strictly to PD027032 Table 1 and engineering specifications.
- **Omitted Letters Invariant**: Sequence numbers never use `I`, `L`, `O`, or `U`.
- **Shared Counter Invariant**: Allocations for CAT6A (`H`) and CAT5E (`K`) strictly increment the same monotonic base-32 sequence.

---

## 4. Barcode Scanner Acceptance (Read-Back Fidelity)

Physical scanning via Honeywell 1900G scanner:

| Barcode Field | System Stored Data | Physical Scanned Output | Match Status |
| :--- | :--- | :--- | :--- |
| `UPC` | `840268939793` | `840268939793` | MATCH (100%) |
| `SKU` | `G111A1A` | `G111A1A` | MATCH (100%) |
| `CartonID` | `H69C0001` | `H69C0001` | MATCH (100%) |
| `SupplierPN` | `NYS5896` | `NYS5896` | MATCH (100%) |
| `PO` | `PO-ERRO-2026` | `PO-ERRO-2026` | MATCH (100%) |

---

## 5. Remedial Template Changes & Observations

- No remedial template changes required; canonical `erro_04.btw` cleanly accepted the nine Named SubStrings.
- Test suites in `test_erro_04_weigh_pack.py` and `test_erro_04_bartender_integration.py` validate XML script and data fidelity programmatically.
- Acceptance criteria for Issue 01, Issue 02, Issue 03, and Issue 04 are fully satisfied.
