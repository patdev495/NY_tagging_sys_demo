from typing import cast as typing_cast

from sqlalchemy.orm import Session

from src.core import models


def carton_group_filters(carton: models.Carton):
    filters = [
        models.Carton.product_id == carton.product_id,
        models.Carton.carton_sn == carton.carton_sn,
    ]
    if carton.job_order:
        filters.append(models.Carton.job_order == carton.job_order)
    else:
        filters.append(models.Carton.job_order.is_(None))
    return filters


def get_carton_attempts(db: Session, carton: models.Carton) -> list[models.Carton]:
    return db.query(models.Carton).filter(*carton_group_filters(carton)).all()


def get_carton_attempt_ids(db: Session, carton: models.Carton) -> list[int]:
    return [typing_cast(int, attempt.id) for attempt in get_carton_attempts(db, carton)]


def get_original_carton(db: Session, carton: models.Carton) -> models.Carton | None:
    if typing_cast(int, carton.is_reprint) != 1:
        return carton
    return db.query(models.Carton).filter(
        *carton_group_filters(carton),
        models.Carton.is_reprint == 0,
    ).first()


def get_original_carton_id(db: Session, carton: models.Carton) -> int | None:
    original = get_original_carton(db, carton)
    if original is None:
        return None
    return typing_cast(int, original.id)


def get_original_carton_id_for_group(db: Session, carton: models.Carton) -> int | None:
    return db.query(models.Carton.id).filter(
        *carton_group_filters(carton),
        models.Carton.is_reprint == 0,
    ).scalar()


def item_sns_for_attempt(db: Session, carton: models.Carton) -> list[str]:
    original = get_original_carton(db, carton)
    if original is None:
        return []
    return [item.item_sn for item in original.items if item.item_sn is not None]


def item_count_for_group(db: Session, carton: models.Carton) -> int:
    original_id = get_original_carton_id_for_group(db, carton)
    carton_id = original_id or typing_cast(int, carton.id)
    return db.query(models.CartonItem).filter(models.CartonItem.carton_id == carton_id).count()


def print_history_for_carton(db: Session, carton: models.Carton) -> list[models.Carton]:
    return db.query(models.Carton).filter(
        *carton_group_filters(carton),
        models.Carton.id != carton.id,
    ).order_by(models.Carton.id.asc()).all()


def successful_print_status(db: Session, carton: models.Carton) -> str:
    if typing_cast(int, carton.is_reprint) != 1:
        return "PRINTED"
    original = get_original_carton(db, carton)
    if original and original.status == "SUCCESS":
        return "SUCCESS"
    return "PRINTED"
