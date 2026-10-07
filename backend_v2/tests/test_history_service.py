"""
Tests for History Service — carton search and lookup logic.
"""
from unittest.mock import MagicMock

import pytest

# pyrefly: ignore [missing-import]
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# pyrefly: ignore [missing-import]
from src.core import models
from src.core.database import Base

# pyrefly: ignore [missing-import]
from src.features.history import service


class TestGetCartonDetail:
    """Test carton detail retrieval."""

    def test_returns_carton_with_items_count(self):
        """Should set items_count on the returned carton."""
        mock_item1 = models.CartonItem(id=1, item_sn="SN001")
        mock_item2 = models.CartonItem(id=2, item_sn="SN002")
        mock_carton = models.Carton(id=1, carton_sn="VN26051100001")
        mock_carton.items = [mock_item1, mock_item2]
        mock_carton.product = models.Product(id=1, item_name="Test")

        db = MagicMock()
        db.query.return_value.options.return_value.filter.return_value.first.return_value = mock_carton

        result = service.get_carton_detail(db, 1)
        assert result.items_count == 2

    def test_raises_404_when_not_found(self):
        """Should raise 404 when carton doesn't exist."""
        db = MagicMock()
        db.query.return_value.options.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc:
            service.get_carton_detail(db, 999)
        assert exc.value.status_code == 404


class TestSearchCartonBySN:
    """Test search by carton S/N."""

    def test_raises_404_when_sn_not_found(self):
        """Should raise 404 for non-existing carton S/N."""
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc:
            service.search_carton_by_sn("NONEXISTENT", db)
        assert exc.value.status_code == 404


class TestSearchByItemSN:
    """Test search by item S/N (find which carton contains an item)."""

    def test_raises_404_when_item_sn_not_found(self):
        """Should raise 404 when item S/N doesn't exist in any carton."""
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc:
            service.search_by_item_sn("UNKNOWN_ITEM", db)
        assert exc.value.status_code == 404


class TestDeleteCarton:
    """Test carton deletion."""

    def test_deletes_carton_and_items(self):
        """Should delete all attempts and items belonging to the selected Carton."""
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = TestingSessionLocal()

        try:
            customer = models.Customer(code="CUST", name="Customer")
            db.add(customer)
            db.flush()
            product = models.Product(
                customer_id=customer.id,
                item_name="Product",
                packed_qty=1,
                start_part="CN",
                middle_part="52",
                allow_partial=0,
            )
            db.add(product)
            db.flush()

            original = models.Carton(
                product_id=product.id,
                carton_sn="CN26065200001",
                job_order="JO-DELETE",
                status="SUCCESS",
                is_reprint=0,
            )
            reprint = models.Carton(
                product_id=product.id,
                carton_sn="CN26065200001",
                job_order="JO-DELETE",
                status="PRINTED",
                is_reprint=1,
            )
            failed = models.Carton(
                product_id=product.id,
                carton_sn="CN26065200001",
                job_order="JO-DELETE",
                status="FAILED",
                is_reprint=1,
            )
            other_carton = models.Carton(
                product_id=product.id,
                carton_sn="CN26065299999",
                job_order="JO-DELETE",
                status="SUCCESS",
                is_reprint=0,
            )
            db.add_all([original, reprint, failed, other_carton])
            db.flush()
            db.add_all([
                models.CartonItem(carton_id=original.id, item_sn="ITEM-ORIGINAL"),
                models.CartonItem(carton_id=reprint.id, item_sn="ITEM-REPRINT"),
                models.CartonItem(carton_id=failed.id, item_sn="ITEM-FAILED"),
                models.CartonItem(carton_id=other_carton.id, item_sn="ITEM-OTHER"),
            ])
            db.commit()

            result = service.delete_carton(db, reprint.id)

            assert result["message"] == "Carton deleted successfully"
            assert result["deleted_count"] == 3
            assert db.query(models.Carton).filter(models.Carton.carton_sn == "CN26065200001").count() == 0
            assert db.query(models.CartonItem).filter(models.CartonItem.item_sn.like("ITEM-%")).count() == 1
            assert db.query(models.Carton).filter(models.Carton.id == other_carton.id).first() is not None
        finally:
            db.close()
            Base.metadata.drop_all(bind=engine)

    def test_raises_404_when_deleting_nonexistent(self):
        """Should raise 404 when trying to delete a carton that doesn't exist."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc:
            service.delete_carton(db, 999)
        assert exc.value.status_code == 404

    def test_resets_job_order_slot_when_deleting_carton_group(self):
        """Deleting a Carton group should release its Job Order Carton Slot."""
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = TestingSessionLocal()

        try:
            customer = models.Customer(code="CUST", name="Customer")
            db.add(customer)
            db.flush()
            product = models.Product(
                customer_id=customer.id,
                item_name="Product",
                packed_qty=1,
                start_part="CN",
                middle_part="52",
                allow_partial=0,
            )
            db.add(product)
            db.flush()

            original = models.Carton(
                product_id=product.id,
                carton_sn="CN26065200001",
                job_order="JO-DELETE",
                status="SUCCESS",
                is_reprint=0,
            )
            db.add(original)
            db.flush()
            latest_attempt = models.Carton(
                product_id=product.id,
                carton_sn=original.carton_sn,
                job_order=original.job_order,
                status="PRINTED",
                is_reprint=1,
            )
            db.add(latest_attempt)
            slot = models.JobOrderCartonSlot(
                job_order=original.job_order,
                product_id=product.id,
                carton_number=1,
                carton_sn=original.carton_sn,
                status="SCANNED",
                carton_id=original.id,
            )
            db.add(slot)
            db.commit()

            result = service.delete_carton(db, latest_attempt.id)

            db.refresh(slot)
            assert result["deleted_count"] == 2
            assert slot.status == "PENDING"
            assert slot.carton_id is None
            assert slot.scanned_at is None
            assert db.query(models.Carton).filter(models.Carton.carton_sn == original.carton_sn).count() == 0
        finally:
            db.close()
            Base.metadata.drop_all(bind=engine)

    def test_rejects_deleting_a_shipped_carton_group(self):
        """A shipped Job Order Carton Slot must protect its Carton from deletion."""
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = TestingSessionLocal()

        try:
            customer = models.Customer(code="CUST", name="Customer")
            db.add(customer)
            db.flush()
            product = models.Product(
                customer_id=customer.id,
                item_name="Product",
                packed_qty=1,
                start_part="CN",
                middle_part="52",
                allow_partial=0,
            )
            db.add(product)
            db.flush()

            carton = models.Carton(
                product_id=product.id,
                carton_sn="CN26065200002",
                job_order="JO-SHIPPED",
                status="SUCCESS",
                is_reprint=0,
            )
            db.add(carton)
            db.flush()
            slot = models.JobOrderCartonSlot(
                job_order=carton.job_order,
                product_id=product.id,
                carton_number=1,
                carton_sn=carton.carton_sn,
                status="SCANNED",
                carton_id=carton.id,
                shipped=1,
            )
            db.add(slot)
            db.commit()

            with pytest.raises(HTTPException) as exc:
                service.delete_carton(db, carton.id)

            assert exc.value.status_code == 409
            assert db.query(models.Carton).filter(models.Carton.id == carton.id).first() is not None
            db.refresh(slot)
            assert slot.status == "SCANNED"
            assert slot.carton_id == carton.id
        finally:
            db.close()
            Base.metadata.drop_all(bind=engine)

    def test_new_slot_defaults_to_not_shipped(self):
        """New slots should be persisted with shipped=0 without caller changes."""
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = TestingSessionLocal()

        try:
            customer = models.Customer(code="CUST", name="Customer")
            db.add(customer)
            db.flush()
            product = models.Product(
                customer_id=customer.id,
                item_name="Product",
                packed_qty=1,
                start_part="CN",
                middle_part="52",
                allow_partial=0,
            )
            db.add(product)
            db.flush()
            slot = models.JobOrderCartonSlot(
                job_order="JO-DEFAULT",
                product_id=product.id,
                carton_number=1,
                carton_sn="CN26065200003",
                status="PENDING",
            )
            db.add(slot)
            db.commit()
            db.refresh(slot)

            assert slot.shipped == 0
        finally:
            db.close()
            Base.metadata.drop_all(bind=engine)


class TestGetCartons:
    """Test carton listing with filters."""

    def test_returns_the_original_and_each_reprint_as_separate_history_rows(self):
        """Admin history must retain the complete print-attempt audit trail."""
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = testing_session()

        try:
            product = models.Product(id=1, item_name="Product", packed_qty=40)
            original = models.Carton(
                product=product,
                carton_sn="CN26096800141",
                status="SUCCESS",
                is_reprint=0,
            )
            reprint = models.Carton(
                product=product,
                carton_sn="CN26096800141",
                status="SUCCESS",
                is_reprint=1,
            )
            db.add_all([original, reprint])
            db.commit()

            result = service.get_cartons(db, search="CN26096800141")

            assert result["total"] == 2
            assert {carton.id for carton in result["items"]} == {original.id, reprint.id}
            assert [carton.is_reprint for carton in result["items"]] == [1, 0]
        finally:
            db.close()
            Base.metadata.drop_all(bind=engine)

    def test_returns_total_and_items(self):
        """Should return dict with total count and items list."""
        mock_carton = models.Carton(id=1, carton_sn="VN26051100001")
        mock_carton.product = models.Product(id=1, item_name="Test")

        db = MagicMock()
        query = MagicMock()
        query.join.return_value = query
        query.outerjoin.return_value = query
        query.options.return_value = query
        query.order_by.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        
        query.count.return_value = 1
        query.all.return_value = [(mock_carton, 1)]

        db.query.return_value = query

        result = service.get_cartons(db)
        assert result["total"] == 1
        assert len(result["items"]) == 1

    def test_applies_search_filter(self):
        """Should apply LIKE filter when search is provided."""
        db = MagicMock()
        query = MagicMock()
        query.join.return_value = query
        query.outerjoin.return_value = query
        query.options.return_value = query
        query.filter.return_value = query
        query.order_by.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        
        query.count.return_value = 0
        query.all.return_value = []

        db.query.return_value = query

        result = service.get_cartons(db, search="VN2605")
        # Verify filter was called (search applied)
        query.filter.assert_called()

    def test_applies_status_filter(self):
        """Should filter by status when provided."""
        db = MagicMock()
        query = MagicMock()
        query.join.return_value = query
        query.outerjoin.return_value = query
        query.options.return_value = query
        query.filter.return_value = query
        query.order_by.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        
        query.count.return_value = 0
        query.all.return_value = []

        db.query.return_value = query

        result = service.get_cartons(db, status="SUCCESS")
        query.filter.assert_called()


class TestGetJobOrderStatistics:
    """Test job order statistics retrieval."""

    def test_returns_job_order_metrics(self):
        """Should return correct metrics for a job order."""
        mock_product = models.Product(id=1, item_name="Test Product")
        mock_carton = models.Carton(id=1, carton_sn="VN26051100001", status="SUCCESS")
        mock_carton.product = mock_product

        db = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.join.return_value = query
        query.outerjoin.return_value = query
        query.options.return_value = query
        
        # count() is called for: total_attempts, reprint_attempts, and in-loop item_count
        query.count.side_effect = [3, 1, 5]
        query.all.return_value = [(mock_carton, 2)]

        db.query.return_value = query

        result = service.get_job_order_statistics(db, "JO-123")
        
        assert result["job_order"] == "JO-123"
        assert result["total_cartons"] == 1
        assert result["success_cartons"] == 1
        assert result["failed_cartons"] == 0
        assert result["total_attempts"] == 3
        assert result["reprint_attempts"] == 1
        assert result["total_items"] == 5
        assert len(result["product_breakdown"]) == 1
        assert result["product_breakdown"][0]["product_id"] == 1
        assert result["product_breakdown"][0]["total_cartons"] == 1
