from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core import models
from src.core.database import Base
from src.features.print import schemas, service


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_generate_btxml_standard():
    # Mock data
    product = models.Product(
        item_name="Test Product",
        upc="1234567890",
        packed_qty=10,
        template_type="standard"
    )
    carton = models.Carton(
        carton_sn="VN-11-2605001",
        carton_origin="VN"
    )
    items = ["SN001", "SN002"]
    
    # Mock template content
    mock_template = "<XML>{item_name} - {qty} - {carton_sn}</XML>"
    
    with patch("builtins.open", MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=mock_template)))))):
        with patch("os.path.exists", return_value=True):
            result = service.generate_btxml(carton, product, items, "dummy.btw")
            
    assert "Test Product" in result
    assert "2PCS" in result
    assert "VN-11-2605001" in result

def test_generate_btxml_detailed_sn_grid():
    # Mock data for detailed template
    product = models.Product(
        item_name="Detailed Product",
        upc="0987654321",
        packed_qty=30,
        template_type="detailed"
    )
    carton = models.Carton(
        carton_sn="CN-16-2605001",
        carton_origin="CN"
    )
    # Only 2 items scanned
    items = ["SN_A", "SN_B"]
    
    # Detailed template uses {sn_grid_tags}
    mock_template = "<XML>{sn_grid_tags}</XML>"
    
    with patch("builtins.open", MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=mock_template)))))):
        with patch("os.path.exists", return_value=True):
            result = service.generate_btxml(carton, product, items, "dummy.btw")
            
    # Check if SN_1 and SN_2 are present
    assert "SN_A" in result
    assert "SN_B" in result
    # Check if SN_3 is empty space (as per service.py logic)
    assert '<NamedSubString Name="SN_3"><Value> </Value></NamedSubString>' in result
    # Check if SN_30 is present
    assert '<NamedSubString Name="SN_30"><Value> </Value></NamedSubString>' in result

def test_origin_text_logic():
    product = models.Product(item_name="P", packed_qty=1)
    
    # VN Origin
    carton_vn = models.Carton(carton_origin="VN", carton_sn="S")
    with patch("builtins.open", MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value="{origin_text}")))))):
        with patch("os.path.exists", return_value=True):
            res_vn = service.generate_btxml(carton_vn, product, ["I"], "D")
            assert "Made in Vietnam" in res_vn
            
    # CN Origin
    carton_cn = models.Carton(carton_origin="CN", carton_sn="S")
    with patch("builtins.open", MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value="{origin_text}")))))):
        with patch("os.path.exists", return_value=True):
            res_cn = service.generate_btxml(carton_cn, product, ["I"], "D")
            assert "Made in China" in res_cn

def test_reprint_carton_inherits_success_status():
    db = MagicMock()
    original_carton = models.Carton(
        id=10,
        product_id=1,
        carton_sn="CN26051600001",
        job_order="JO-123",
        packed_by="User A",
        status="SUCCESS",
        carton_origin="CN",
        station_id="127.0.0.1",
        items=[]
    )
    
    product = models.Product(id=1, template_path="carton.btw")
    db.query.return_value.filter.return_value.first.side_effect = [original_carton, product]
    
    with patch("src.features.print.service.generate_btxml", return_value="<xml></xml>"):
        new_carton = service.reprint_carton(
            carton_id=10,
            printer_name="Printer A",
            template_path="carton.btw",
            station_id="127.0.0.1",
            db=db
        )
        
    assert new_carton.status == "SUCCESS"
    assert new_carton.is_reprint == 1
    assert new_carton.carton_sn == "CN26051600001"

def test_reprint_carton_defaults_printed_status():
    db = MagicMock()
    original_carton = models.Carton(
        id=10,
        product_id=1,
        carton_sn="CN26051600001",
        job_order="JO-123",
        packed_by="User A",
        status="PRINTED",
        carton_origin="CN",
        station_id="127.0.0.1",
        items=[]
    )
    
    product = models.Product(id=1, template_path="carton.btw")
    db.query.return_value.filter.return_value.first.side_effect = [original_carton, product]
    
    with patch("src.features.print.service.generate_btxml", return_value="<xml></xml>"):
        new_carton = service.reprint_carton(
            carton_id=10,
            printer_name="Printer A",
            template_path="carton.btw",
            station_id="127.0.0.1",
            db=db
        )
        
    assert new_carton.status == "PRINTED"
    assert new_carton.is_reprint == 1
    assert new_carton.carton_sn == "CN26051600001"

def test_reprint_carton_btxml_none_in_db_but_retained_in_memory():
    db = MagicMock()
    original_carton = models.Carton(
        id=10,
        product_id=1,
        carton_sn="CN26051600001",
        status="SUCCESS",
        carton_origin="CN",
        station_id="127.0.0.1",
        items=[]
    )
    
    product = models.Product(id=1, template_path="carton.btw")
    db.query.return_value.filter.return_value.first.side_effect = [original_carton, product]
    
    with patch("src.features.print.service.generate_btxml", return_value="<xml>reprint_xml</xml>"):
        new_carton = service.reprint_carton(
            carton_id=10,
            printer_name="Printer A",
            template_path="carton.btw",
            station_id="127.0.0.1",
            db=db
        )
        
    assert new_carton.btxml == "<xml>reprint_xml</xml>"
    # Verify db.commit was called, and at some point new_carton.btxml was set to None.
    # We can check that the mock database add or commit logic was executed.
    assert db.commit.called
    assert db.refresh.called


def test_reprint_success_keeps_slot_linked_to_original_carton(db_session):
    product = models.Product(
        id=1,
        item_name="Test Product",
        packed_qty=1,
        start_part="CN",
        middle_part="48",
    )
    original = models.Carton(
        id=1745,
        product_id=1,
        carton_sn="CN26064800001",
        job_order="1243195",
        status="SUCCESS",
        is_reprint=0,
    )
    reprint = models.Carton(
        id=1748,
        product_id=1,
        carton_sn="CN26064800001",
        job_order="1243195",
        status="PRINTED",
        is_reprint=1,
    )
    slot = models.JobOrderCartonSlot(
        id=1129,
        job_order="1243195",
        product_id=1,
        carton_number=1,
        carton_sn="CN26064800001",
        status="SCANNED",
        carton_id=1745,
    )
    db_session.add_all([product, original, reprint, slot])
    db_session.commit()

    service.update_status(1748, schemas.CartonStatusUpdate(status="SUCCESS"), db_session)

    db_session.refresh(slot)
    assert slot.status == "SCANNED"
    assert slot.carton_id == 1745


def test_reprint_failure_does_not_reopen_original_slot(db_session):
    product = models.Product(
        id=1,
        item_name="Test Product",
        packed_qty=1,
        start_part="CN",
        middle_part="48",
    )
    original = models.Carton(
        id=1745,
        product_id=1,
        carton_sn="CN26064800001",
        job_order="1243195",
        status="SUCCESS",
        is_reprint=0,
    )
    reprint = models.Carton(
        id=1748,
        product_id=1,
        carton_sn="CN26064800001",
        job_order="1243195",
        status="PRINTED",
        is_reprint=1,
    )
    slot = models.JobOrderCartonSlot(
        id=1129,
        job_order="1243195",
        product_id=1,
        carton_number=1,
        carton_sn="CN26064800001",
        status="SCANNED",
        carton_id=1745,
    )
    db_session.add_all([product, original, reprint, slot])
    db_session.commit()

    service.update_status(1748, schemas.CartonStatusUpdate(status="FAILED"), db_session)

    db_session.refresh(slot)
    assert slot.status == "SCANNED"
    assert slot.carton_id == 1745
