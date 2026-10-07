from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.core import models
from src.features.carton import schemas, service
from src.features.print import service as print_service

# ============================================================
# Scenario 1: Concurrency (Tranh chấp dữ liệu)
# ============================================================

def test_concurrency_sequential_next_sn():
    """
    Simulate two concurrent calls to get_next_carton_sn.
    Since we mock the DB, we want to ensure that even if they happen rapidly,
    the sequence logic is sound. 
    In a real DB, with_for_update() would block. 
    Here we test that the logic increments correctly.
    """
    db = MagicMock()
    product = models.Product(id=1, start_part="VN", middle_part="11", packed_qty=10)
    
    # Simulate first call finding no existing cartons
    db.query.return_value.filter.return_value.with_for_update.return_value.scalar.return_value = None
    sn1 = service.get_next_carton_sn(db, product, custom_yymm="2605")
    
    # Simulate second call finding the first one already exists
    db.query.return_value.filter.return_value.with_for_update.return_value.scalar.return_value = sn1
    sn2 = service.get_next_carton_sn(db, product, custom_yymm="2605")
    
    assert sn1 == "VN26051100001"
    assert sn2 == "VN26051100002"
    assert sn1 != sn2

# ============================================================
# Scenario 2: Partial Packing (Hàng đóng dở)
# ============================================================

class TestPartialPacking:
    def _make_product(self, allow_partial=0, packed_qty=10):
        return models.Product(
            id=1, 
            start_part="VN", 
            middle_part="11", 
            packed_qty=packed_qty, 
            allow_partial=allow_partial,
            template_type="standard"
        )

    def test_reject_partial_when_not_allowed(self):
        """Sản phẩm A yêu cầu 10 cái, gửi 5 cái -> Bị từ chối (400)"""
        db = MagicMock()
        product = self._make_product(allow_partial=0, packed_qty=10)
        db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = product
        
        carton_in = schemas.CartonCreate(
            product_id=1,
            items=["SN1", "SN2", "SN3", "SN4", "SN5"], # Only 5 items
            job_order=None
        )
        
        with pytest.raises(HTTPException) as exc:
            service.create_carton(carton_in, db)
        
        assert exc.value.status_code == 400
        assert "Partial packing is not allowed" in exc.value.detail

    def test_allow_partial_when_enabled(self):
        """Sản phẩm B cho phép in dở, gửi 5 cái -> Thành công"""
        db = MagicMock()
        product = self._make_product(allow_partial=1, packed_qty=10)
        slot = models.JobOrderCartonSlot(
            id=10,
            job_order="JO-PARTIAL",
            product_id=1,
            carton_number=1,
            carton_sn="VN26051100001",
            status="PENDING",
        )
        product_query = MagicMock()
        product_query.filter.return_value.with_for_update.return_value.first.return_value = product
        slot_query = MagicMock()
        slot_query.filter.return_value.with_for_update.return_value.first.return_value = slot
        carton_query = MagicMock()
        carton_query.filter.return_value.first.return_value = None
        db.query.side_effect = [product_query, slot_query, carton_query]
        
        # Mock generate_btxml
        with patch("src.features.carton.service.generate_btxml", return_value="<XML>5PCS</XML>") as mock_gen:
            carton_in = schemas.CartonCreate(
                product_id=1,
                items=["SN1", "SN2", "SN3", "SN4", "SN5"],
                job_order="JO-PARTIAL",
                slot_id=10,
            )
            
            res_carton, res_xml = service.create_carton(carton_in, db)
            
            assert res_carton.carton_sn == "VN26051100001"
            # Ensure the generated XML reflects actual count (this is handled by generate_btxml)
            mock_gen.assert_called_once()
            # Check that items list passed to generate_btxml has length 5
            args, _ = mock_gen.call_args
            assert len(args[2]) == 5 

    def test_xml_content_for_partial(self):
        """Kiểm tra XML hiển thị đúng số lượng thực tế khi in dở"""
        product = self._make_product(allow_partial=1, packed_qty=10)
        carton = models.Carton(carton_sn="SN1", carton_origin="VN")
        items = ["I1", "I2", "I3"] # Only 3 items
        
        mock_template = "<QTY>{qty}</QTY>"
        
        with patch("builtins.open", MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=mock_template)))))):
            with patch("os.path.exists", return_value=True):
                # We call the actual print_service.generate_btxml
                xml = print_service.generate_btxml(carton, product, items, "dummy.btw")
                
                assert "<QTY>3 PCS</QTY>" in xml # Should show 3 PCS, not 10 PCS
