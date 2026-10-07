from unittest.mock import MagicMock

from src.core import models
from src.features.carton import sn_allocator


def make_product(**kwargs):
    defaults = dict(id=1, start_part="CN", middle_part="52", packed_qty=50)
    defaults.update(kwargs)
    return models.Product(**defaults)


def test_builds_carton_sn_from_product_parts_and_yymm():
    plan = sn_allocator.plan_next_carton_sn(
        MagicMock(),
        make_product(start_part="VN", middle_part="11"),
        custom_sn=42,
        custom_yymm="2605",
    )

    assert plan.prefix == "VN260511"
    assert plan.sequence == 42
    assert plan.carton_sn == "VN26051100042"


def test_next_sequence_uses_cartons_and_allocated_job_order_slots():
    db = MagicMock()
    carton_query = MagicMock()
    slot_query = MagicMock()
    carton_query.filter.return_value.scalar.return_value = "CN26055200010"
    slot_query.filter.return_value.scalar.return_value = "CN26055200025"
    db.query.side_effect = [carton_query, slot_query]

    plan = sn_allocator.plan_next_carton_sn(
        db,
        make_product(),
        custom_yymm="2605",
    )

    assert plan.sequence == 26
    assert plan.carton_sn == "CN26055200026"


def test_can_ignore_slots_when_a_caller_needs_carton_only_history():
    db = MagicMock()
    carton_query = MagicMock()
    carton_query.filter.return_value.scalar.return_value = "CN26055200010"
    db.query.return_value = carton_query

    plan = sn_allocator.plan_next_carton_sn(
        db,
        make_product(),
        custom_yymm="2605",
        include_slots=False,
    )

    assert plan.sequence == 11
    assert plan.carton_sn == "CN26055200011"
    assert db.query.call_count == 1


def test_job_order_slot_plans_are_contiguous_after_existing_usage():
    db = MagicMock()
    carton_query = MagicMock()
    slot_query = MagicMock()
    carton_query.filter.return_value.scalar.return_value = "CN26055200010"
    slot_query.filter.return_value.scalar.return_value = "CN26055200012"
    db.query.side_effect = [carton_query, slot_query]

    plans = sn_allocator.plan_job_order_slots(
        db,
        make_product(),
        total_cartons=3,
        yymm="2605",
    )

    assert [plan.sequence for plan in plans] == [13, 14, 15]
    assert [plan.carton_sn for plan in plans] == [
        "CN26055200013",
        "CN26055200014",
        "CN26055200015",
    ]


def test_parse_sequence_returns_zero_for_invalid_sn():
    assert sn_allocator.parse_sequence(None) == 0
    assert sn_allocator.parse_sequence("CN260552XXXXX") == 0
