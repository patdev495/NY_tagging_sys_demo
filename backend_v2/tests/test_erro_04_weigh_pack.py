from datetime import datetime
from typing import cast

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.models import Base, Carton, Customer, Product
from src.features.carton import schemas as carton_schemas
from src.features.carton import service as carton_service


def _pd027032_date_code(value: datetime) -> str:
    year_codes = {
        2023: "3", 2024: "4", 2025: "5", 2026: "6", 2027: "7", 2028: "8",
        2029: "9", 2030: "A", 2031: "B", 2032: "C", 2033: "D", 2034: "E",
    }
    alphabet = "123456789ABCDEFGHJKMNPQRSTVWXYZ"
    return f"{year_codes[value.year]}{alphabet[value.month - 1]}{alphabet[value.day - 1]}"


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def erro_04_product(db_session):
    customer = Customer(code="ERRO", name="Erro")
    db_session.add(customer)
    db_session.flush()

    product = Product(
        customer_id=customer.id,
        item_name="G111A1A",
        upc="840268939793",
        packed_qty=120,
        template_type="erro_04",
        template_path=r"D:\PAT\Templates\erro_04.btw",
        packing_mode="weight_scale",
        mfr_pn="NYS5896",
        product_desc="Accessory, Ethernet Cable CAT6a, 15cm, Black, 1PK, Basic Box",
        factory_item_code="115-00020",
        carton_id_prefix="H",
        revision="B",
        min_weight=0.0,
        max_weight=10.0,
        target_weight=5.0,
    )
    db_session.add(product)
    db_session.commit()
    return product


def test_weigh_pack_erro_04_creates_pd027032_carton_and_bartender_payload(db_session, erro_04_product):
    carton, btxml = carton_service.weigh_pack_carton(
        carton_schemas.CartonWeighPackCreate(
            product_id=cast(int, erro_04_product.id),
            weight=5.0,
            po_number="PO-ERRO-04",
            lot_number="LOT-ERRO-04",
        ),
        db_session,
    )

    expected_sn = f"H{_pd027032_date_code(datetime.now())}0001"
    assert carton.carton_sn == expected_sn
    assert carton.po_number == "PO-ERRO-04"
    assert carton.lot_number == datetime.now().strftime("%Y%m%d")
    assert db_session.query(Carton).filter_by(id=carton.id).one().btxml == btxml

    expected_substrings = {
        "UPC": "840268939793",
        "SKU": "G111A1A",
        "CartonID": expected_sn,
        "SupplierPN": "NYS5896",
        "PO": "PO-ERRO-04",
        "Date": datetime.now().strftime("%y%m%d"),
        "Qty": "120",
        "Rev": "B",
        "SKUDescription": "Accessory, Ethernet Cable CAT6a, 15cm, Black, 1PK, Basic Box",
    }
    for name, value in expected_substrings.items():
        assert f'<NamedSubString Name="{name}"><Value>{value}</Value></NamedSubString>' in btxml, btxml


def test_weigh_pack_erro_04_shares_base_32_sequence_between_h_and_k_products(db_session, erro_04_product):
    customer = db_session.query(Customer).filter_by(code="ERRO").one()
    cat5e_product = Product(
        customer_id=customer.id,
        item_name="G011C1B",
        upc="840268995669",
        packed_qty=90,
        template_type="erro_04",
        template_path=r"D:\PAT\Templates\erro_04.btw",
        packing_mode="weight_scale",
        mfr_pn="NYS5989",
        product_desc="Accessory, Ethernet Cable CAT5e, 91cm, White, 1PK, Basic Box",
        factory_item_code="115-00035",
        carton_id_prefix="K",
        revision="B",
        min_weight=0.0,
        max_weight=10.0,
        target_weight=5.0,
    )
    db_session.add(cat5e_product)
    db_session.flush()

    date_code = _pd027032_date_code(datetime.now())
    for suffix in ("0001", "0002", "0003", "0004", "0005", "0006", "0007", "0008", "0009"):
        db_session.add(Carton(product_id=erro_04_product.id, carton_sn=f"H{date_code}{suffix}", is_reprint=0))
    db_session.commit()

    carton, _ = carton_service.weigh_pack_carton(
        carton_schemas.CartonWeighPackCreate(
            product_id=cast(int, cat5e_product.id),
            weight=5.0,
            po_number="PO-CAT5E",
            lot_number="LOT-CAT5E",
        ),
        db_session,
    )

    assert carton.carton_sn == f"K{date_code}000A"


def test_weigh_pack_erro_04_rejects_weight_outside_product_tolerance(db_session, erro_04_product):
    with pytest.raises(HTTPException, match="above maximum tolerance"):
        carton_service.weigh_pack_carton(
            carton_schemas.CartonWeighPackCreate(
                product_id=cast(int, erro_04_product.id),
                weight=10.001,
                po_number="PO-1",
                lot_number="LOT-1",
            ),
            db_session,
        )

    assert db_session.query(Carton).count() == 0

    with pytest.raises(HTTPException, match="below minimum tolerance"):
        carton_service.weigh_pack_carton(
            carton_schemas.CartonWeighPackCreate(
                product_id=cast(int, erro_04_product.id),
                weight=-0.001,
                po_number="PO-1",
                lot_number="LOT-1",
            ),
            db_session,
        )

    assert db_session.query(Carton).count() == 0


def test_weigh_pack_erro_04_blocks_until_po_supplied(db_session, erro_04_product):
    # Missing PO Number
    with pytest.raises(HTTPException) as exc_po:
        carton_service.weigh_pack_carton(
            carton_schemas.CartonWeighPackCreate(
                product_id=cast(int, erro_04_product.id),
                weight=5.0,
                po_number="",
                lot_number="LOT-12345",
            ),
            db_session,
        )
    assert exc_po.value.status_code == 400
    assert "PO Number" in exc_po.value.detail

    carton, _ = carton_service.weigh_pack_carton(
        carton_schemas.CartonWeighPackCreate(
            product_id=cast(int, erro_04_product.id),
            weight=5.0,
            po_number="PO-12345",
            lot_number=None,
        ),
        db_session,
    )
    assert carton.lot_number == datetime.now().strftime("%Y%m%d")


def test_weigh_pack_erro_04_po_mutation_preserves_carton_snapshot_and_payload(db_session, erro_04_product):
    # Print Carton 1 with PO-SESSION-1. LOT is generated by the backend.
    c1, btxml1 = carton_service.weigh_pack_carton(
        carton_schemas.CartonWeighPackCreate(
            product_id=cast(int, erro_04_product.id),
            weight=5.0,
            po_number="PO-SESSION-1",
            lot_number="LOT-SESSION-1",
        ),
        db_session,
    )
    assert c1.po_number == "PO-SESSION-1"
    assert c1.lot_number == datetime.now().strftime("%Y%m%d")
    assert '<NamedSubString Name="PO"><Value>PO-SESSION-1</Value></NamedSubString>' in btxml1

    # Operator changes PO in the same active station.
    c2, btxml2 = carton_service.weigh_pack_carton(
        carton_schemas.CartonWeighPackCreate(
            product_id=cast(int, erro_04_product.id),
            weight=5.0,
            po_number="PO-SESSION-2",
            lot_number="LOT-SESSION-2",
        ),
        db_session,
    )
    assert c2.po_number == "PO-SESSION-2"
    assert c2.lot_number == datetime.now().strftime("%Y%m%d")
    assert '<NamedSubString Name="PO"><Value>PO-SESSION-2</Value></NamedSubString>' in btxml2

    # Verify historical Carton 1 snapshot and payload remain unchanged in DB
    refreshed_c1 = db_session.query(Carton).filter_by(id=c1.id).one()
    assert refreshed_c1.po_number == "PO-SESSION-1"
    assert refreshed_c1.lot_number == datetime.now().strftime("%Y%m%d")
    assert refreshed_c1.btxml == btxml1


def test_weigh_pack_erro_04_reprint_keeps_sequence_and_next_print_advances(db_session, erro_04_product):
    from src.features.print.service import reprint_carton

    c1, _ = carton_service.weigh_pack_carton(
        carton_schemas.CartonWeighPackCreate(
            product_id=cast(int, erro_04_product.id),
            weight=5.0,
            po_number="PO-TEST",
            lot_number="LOT-TEST",
        ),
        db_session,
    )

    reprint = reprint_carton(carton_id=cast(int, c1.id), db=db_session)
    assert reprint.id != c1.id
    assert reprint.carton_sn == c1.carton_sn
    assert reprint.is_reprint == 1

    # A subsequent original print consumes the next shared sequence.
    c2, _ = carton_service.weigh_pack_carton(
        carton_schemas.CartonWeighPackCreate(
            product_id=cast(int, erro_04_product.id),
            weight=5.0,
            po_number="PO-TEST",
            lot_number="LOT-TEST",
        ),
        db_session,
    )
    assert c2.id != c1.id
    assert c2.carton_sn.endswith("0002")


def test_erro_04_base32_sequence_invariants_and_omitted_letters():
    from src.features.carton.erro_04_sn_allocator import (
        ERRO_04_ALPHABET,
        format_erro_04_sequence,
        parse_erro_04_sequence,
    )

    # 32 characters: 0-9 and uppercase letters excluding I, L, O, U
    assert len(ERRO_04_ALPHABET) == 32
    for forbidden in ("I", "L", "O", "U"):
        assert forbidden not in ERRO_04_ALPHABET

    # Sequence 1 -> 0001
    assert format_erro_04_sequence(1) == "0001"
    assert parse_erro_04_sequence("H69C0001") == 1

    # Sequence 9 -> 0009, advances to 10 -> 000A
    assert format_erro_04_sequence(9) == "0009"
    assert format_erro_04_sequence(10) == "000A"

    # Sequence 31 -> 000Z, advances to 32 -> 0010 (rollover)
    assert format_erro_04_sequence(31) == "000Z"
    assert format_erro_04_sequence(32) == "0010"
    assert parse_erro_04_sequence("K69C0010") == 32


def test_erro_04_sequence_resets_yearly_on_new_year(db_session, erro_04_product):
    from src.features.carton.erro_04_sn_allocator import plan_next_erro_04_carton_sn

    # Year 2026 (year code '6'): create carton sequence 5
    db_session.add(Carton(
        product_id=erro_04_product.id,
        carton_sn="H69E0005",
        status="SUCCESS",
        is_reprint=0,
    ))
    db_session.commit()

    # Next carton in 2026 should be sequence 6 -> 0006
    plan_2026 = plan_next_erro_04_carton_sn(
        db_session,
        erro_04_product,
        printed_at=datetime(2026, 9, 15),
    )
    assert plan_2026.sequence == 6
    assert plan_2026.carton_sn == "H69F0006"

    # New Year 2027 (year code '7'): sequence MUST RESET back to 1 -> 0001
    plan_2027 = plan_next_erro_04_carton_sn(
        db_session,
        erro_04_product,
        printed_at=datetime(2027, 1, 1),
    )
    assert plan_2027.sequence == 1
    assert plan_2027.carton_sn == "H7110001"
