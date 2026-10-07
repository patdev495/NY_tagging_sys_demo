"""
Tests for Carton Service — S/N generation logic.
This is the most critical business logic in the system.
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.core import models
from src.features.carton import schemas, service

# ============================================================
# get_next_carton_sn — Pure S/N generation
# ============================================================

class TestGetNextCartonSN:
    """Test the S/N generation algorithm."""

    def _make_product(self, **kwargs):
        defaults = dict(id=1, start_part="VN", middle_part="11", packed_qty=10)
        defaults.update(kwargs)
        return models.Product(**defaults)

    def test_first_sn_of_month(self):
        """First carton of the month should be seq 00001."""
        db = MagicMock()
        db.query.return_value.filter.return_value.with_for_update.return_value.scalar.return_value = None
        product = self._make_product()
        
        sn = service.get_next_carton_sn(db, product)
        
        assert sn.endswith("00001")
        assert str(product.start_part) in sn
        assert str(product.middle_part) in sn

    def test_increment_from_existing(self):
        """Should increment from the highest existing S/N."""
        db = MagicMock()
        db.query.return_value.filter.return_value.with_for_update.return_value.scalar.return_value = "VN26051100042"
        product = self._make_product()
        
        sn = service.get_next_carton_sn(db, product)
        
        assert sn.endswith("00043")

    def test_custom_sn_bypasses_sequence(self):
        """Custom S/N should use the provided number directly."""
        db = MagicMock()
        product = self._make_product()
        
        sn = service.get_next_carton_sn(db, product, custom_sn=99)
        
        assert sn.endswith("00099")
        # DB should NOT be queried when custom_sn is provided
        db.query.assert_not_called()

    def test_custom_yymm_overrides_date(self):
        """Custom YYMM should override the current date."""
        db = MagicMock()
        db.query.return_value.filter.return_value.with_for_update.return_value.scalar.return_value = None
        product = self._make_product()
        
        sn = service.get_next_carton_sn(db, product, custom_yymm="2601")
        
        assert "2601" in sn
        assert sn.endswith("00001")

    def test_different_products_have_different_prefixes(self):
        """Products with different start_part/middle_part should produce different prefixes."""
        db = MagicMock()
        db.query.return_value.filter.return_value.with_for_update.return_value.scalar.return_value = None
        
        product_vn = self._make_product(start_part="VN", middle_part="11")
        product_cn = self._make_product(start_part="CN", middle_part="16")
        
        sn_vn = service.get_next_carton_sn(db, product_vn, custom_yymm="2605")
        sn_cn = service.get_next_carton_sn(db, product_cn, custom_yymm="2605")
        
        assert sn_vn.startswith("VN260511")
        assert sn_cn.startswith("CN260516")

    def test_month_rollover_resets_sequence(self):
        """When switching months, sequence should start from 1 (no existing match)."""
        db = MagicMock()
        # Old month had cartons, new month has none
        db.query.return_value.filter.return_value.with_for_update.return_value.scalar.return_value = None
        product = self._make_product()
        
        sn = service.get_next_carton_sn(db, product, custom_yymm="2606")
        
        assert "2606" in sn
        assert sn.endswith("00001")

    def test_high_sequence_number(self):
        """Should handle high sequence numbers (e.g., 99999)."""
        db = MagicMock()
        db.query.return_value.filter.return_value.with_for_update.return_value.scalar.return_value = "VN26051199999"
        product = self._make_product()
        
        sn = service.get_next_carton_sn(db, product, custom_yymm="2605")
        
        assert sn.endswith("100000")  # 6 digits when exceeding 99999

    def test_corrupted_max_sn_fallback(self):
        """Should fallback to seq 1 if max_sn has corrupted suffix."""
        db = MagicMock()
        db.query.return_value.filter.return_value.with_for_update.return_value.scalar.return_value = "VN260511XXXXX"
        product = self._make_product()
        
        sn = service.get_next_carton_sn(db, product, custom_yymm="2605")
        
        assert sn.endswith("00001")


# ============================================================
# create_carton — Carton creation with validations
# ============================================================

class TestCreateCarton:
    """Test carton creation business rules."""

    def _make_carton_input(self, **kwargs):
        defaults = dict(
            product_id=1,
            items=["SN001", "SN002", "SN003"],
            template_path="dummy.btw",
            printer_name="Printer1",
            job_order=None,
            carton_origin="VN",
        )
        defaults.update(kwargs)
        return schemas.CartonCreate(**defaults)

    def test_rejects_duplicate_items_in_scan(self):
        """Should reject carton if scanned items contain duplicates."""
        db = MagicMock()
        product = models.Product(id=1, start_part="VN", middle_part="11", packed_qty=3)
        db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = product
        
        carton_in = self._make_carton_input(items=["SN001", "SN001", "SN002"])
        
        with pytest.raises(HTTPException) as exc:
            service.create_carton(carton_in, db)
        assert exc.value.status_code == 400
        assert "Duplicate" in exc.value.detail

    def test_rejects_nonexistent_product(self):
        """Should return 404 if product doesn't exist."""
        db = MagicMock()
        db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = None
        
        carton_in = self._make_carton_input(product_id=999)
        
        with pytest.raises(HTTPException) as exc:
            service.create_carton(carton_in, db)
        assert exc.value.status_code == 404

    def test_rejects_slot_sn_already_in_use(self):
        """Should reject if the allocated slot S/N already exists."""
        db = MagicMock()
        product = models.Product(id=1, start_part="VN", middle_part="11", packed_qty=3)
        slot = models.JobOrderCartonSlot(
            id=10,
            job_order="JO-001",
            product_id=1,
            carton_number=1,
            carton_sn="VN26051100042",
            status="PENDING",
        )
        existing_carton = models.Carton(id=5, carton_sn="VN26051100042", status="SUCCESS")
        
        product_query = MagicMock()
        product_query.filter.return_value.with_for_update.return_value.first.return_value = product
        slot_query = MagicMock()
        slot_query.filter.return_value.with_for_update.return_value.first.return_value = slot
        carton_query = MagicMock()
        carton_query.filter.return_value.first.return_value = existing_carton
        db.query.side_effect = [product_query, slot_query, carton_query]
        
        carton_in = self._make_carton_input(job_order="JO-001", slot_id=10)
        
        with pytest.raises(HTTPException) as exc:
            service.create_carton(carton_in, db)
        assert exc.value.status_code == 400
        assert "already in use" in exc.value.detail

    def test_allows_reusing_failed_carton_attempt(self):
        """Should reuse and update existing FAILED carton attempt when creating carton for the same slot."""
        db = MagicMock()
        product = models.Product(id=1, start_part="VN", middle_part="11", packed_qty=3)
        slot = models.JobOrderCartonSlot(
            id=10,
            job_order="JO-001",
            product_id=1,
            carton_number=1,
            carton_sn="VN26051100042",
            status="PENDING",
        )
        existing_carton = models.Carton(id=5, carton_sn="VN26051100042", job_order="JO-001", product_id=1, status="FAILED")
        
        product_query = MagicMock()
        product_query.filter.return_value.with_for_update.return_value.first.return_value = product
        slot_query = MagicMock()
        slot_query.filter.return_value.with_for_update.return_value.first.return_value = slot
        carton_query = MagicMock()
        carton_query.filter.return_value.first.return_value = existing_carton
        item_delete_query = MagicMock()
        
        db.query.side_effect = [product_query, slot_query, carton_query, item_delete_query]
        
        carton_in = self._make_carton_input(job_order="JO-001", slot_id=10, items=["SN1", "SN2", "SN3"])
        
        res_carton, btxml = service.create_carton(carton_in, db)
        assert res_carton.id == 5
        assert res_carton.carton_sn == "VN26051100042"
        
    def test_rejects_exceeded_capacity(self):
        """Should reject if scanned items exceed product packed_qty."""
        db = MagicMock()
        product = models.Product(id=1, start_part="VN", middle_part="11", packed_qty=2)
        db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = product
        
        carton_in = self._make_carton_input(items=["SN001", "SN002", "SN003"]) # 3 items, max is 2
        
        with pytest.raises(HTTPException) as exc:
            service.create_carton(carton_in, db)
        assert exc.value.status_code == 400
        assert "capacity exceeded" in exc.value.detail.lower()

    def test_rejects_partial_packing_if_disabled(self):
        """Should reject partial packing if allow_partial is disabled (default)."""
        db = MagicMock()
        product = models.Product(id=1, start_part="VN", middle_part="11", packed_qty=5, allow_partial=0)
        db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = product
        
        carton_in = self._make_carton_input(items=["SN001", "SN002"]) # 2 items, max is 5
        
        with pytest.raises(HTTPException) as exc:
            service.create_carton(carton_in, db)
        assert exc.value.status_code == 400
        assert "partial packing is not allowed" in exc.value.detail.lower()

    def test_rejects_carton_creation_without_job_order(self):
        db = MagicMock()
        product = models.Product(id=1, start_part="VN", middle_part="11", packed_qty=3)
        db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = product

        with pytest.raises(HTTPException) as exc:
            service.create_carton(self._make_carton_input(job_order=None, slot_id=None), db)

        assert exc.value.status_code == 400
        assert "job order" in exc.value.detail.lower()

    def test_job_order_requires_a_carton_slot(self):
        db = MagicMock()
        product = models.Product(id=1, start_part="VN", middle_part="11", packed_qty=3)
        db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = product

        with pytest.raises(HTTPException) as exc:
            service.create_carton(self._make_carton_input(job_order="JO-001", slot_id=None), db)

        assert exc.value.status_code == 400
        assert "slot" in exc.value.detail.lower()

    @patch("src.features.carton.service.generate_btxml", return_value="<xml />")
    @patch("src.features.carton.service.utils.resolve_template_path", return_value="dummy.btw")
    def test_job_order_uses_the_allocated_slot_sn(self, _resolve_path, _generate_xml):
        db = MagicMock()
        product = models.Product(id=1, start_part="VN", middle_part="11", packed_qty=3)
        slot = models.JobOrderCartonSlot(
            id=10,
            job_order="JO-001",
            product_id=1,
            carton_number=1,
            carton_sn="VN26051100042",
            status="PENDING",
        )
        product_query = MagicMock()
        product_query.filter.return_value.with_for_update.return_value.first.return_value = product
        slot_query = MagicMock()
        slot_query.filter.return_value.with_for_update.return_value.first.return_value = slot
        carton_query = MagicMock()
        carton_query.filter.return_value.first.return_value = None
        db.query.side_effect = [product_query, slot_query, carton_query]

        carton, _ = service.create_carton(self._make_carton_input(job_order="JO-001", slot_id=10), db)

        assert carton.carton_sn == slot.carton_sn
        assert carton.job_order == slot.job_order
