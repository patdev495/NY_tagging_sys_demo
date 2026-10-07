from collections import defaultdict
from typing import Iterable

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.core import models


def find_ui_item_sn_conflicts(
    db: Session,
    item_sns: Iterable[str],
    exclude_carton_id: int | None = None,
) -> dict[str, list[dict[str, object]]]:
    """Find existing UI Carton ownership with one indexed query for all Item SNs."""
    unique_item_sns = list(dict.fromkeys(item_sns))
    if not unique_item_sns:
        return {}

    item_count = (
        select(func.count(models.CartonItem.id))
        .where(models.CartonItem.carton_id == models.Carton.id)
        .correlate(models.Carton)
        .scalar_subquery()
    )
    query = (
        db.query(
            models.CartonItem.item_sn,
            models.Carton.id,
            models.Carton.carton_sn,
            models.Product.item_name.label("product_name"),
            models.Carton.job_order,
            models.Carton.status,
            models.Carton.station_id,
            models.Carton.created_at,
            item_count.label("items_count"),
        )
        .select_from(models.CartonItem)
        .join(models.Carton, models.CartonItem.carton_id == models.Carton.id)
        .join(models.Product, models.Carton.product_id == models.Product.id)
        .join(models.Customer, models.Product.customer_id == models.Customer.id)
        .filter(
            models.CartonItem.item_sn.in_(unique_item_sns),
            models.Customer.code == "UI",
            models.Carton.is_reprint == 0,
        )
    )
    if exclude_carton_id is not None:
        query = query.filter(models.Carton.id != exclude_carton_id)

    rows = query.distinct().order_by(models.Carton.id.desc()).all()

    conflicts: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        conflicts[str(row.item_sn)].append({
            "id": row.id,
            "carton_sn": row.carton_sn,
            "product_name": row.product_name,
            "job_order": row.job_order,
            "status": row.status,
            "station_id": row.station_id,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "items_count": row.items_count,
        })
    return dict(conflicts)


def reject_ui_item_sn_conflicts(
    db: Session,
    item_sns: Iterable[str],
    exclude_carton_id: int | None = None,
) -> None:
    conflicts = find_ui_item_sn_conflicts(db, item_sns, exclude_carton_id)
    if conflicts:
        raise HTTPException(
            status_code=409,
            detail={"code": "ITEM_SN_CONFLICT", "conflicts": conflicts},
        )


def replace_ui_item_sn_claims(db: Session, carton_id: int, item_sns: Iterable[str]) -> None:
    """Atomically reserve the current Item SN set for a UI Carton.

    The primary key on item_sn converts a simultaneous create at another station
    into a database conflict instead of a timing-dependent duplicate.
    """
    db.query(models.UIItemSNClaim).filter(models.UIItemSNClaim.carton_id == carton_id).delete()
    for item_sn in dict.fromkeys(item_sns):
        db.add(models.UIItemSNClaim(item_sn=item_sn, carton_id=carton_id))
    db.flush()
