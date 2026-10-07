import datetime
import logging
from typing import cast as typing_cast

from sqlalchemy import case, desc, func
from sqlalchemy.orm import Session, joinedload, selectinload

from src.core import models

from .schemas import (
    DashboardStatsResponse,
    HourlyStat,
    KPIStats,
    LiveCartonFeed,
    ProductStat,
    SystemHealth,
)

logger = logging.getLogger("DashboardService")

def get_time_boundary(
    time_range: str,
    start_date: str | None = None,
    end_date: str | None = None
) -> tuple[datetime.datetime, datetime.datetime]:
    now = datetime.datetime.now()
    today_start = datetime.datetime.combine(now.date(), datetime.time.min)
    today_end = datetime.datetime.combine(now.date(), datetime.time.max)

    if time_range == "yesterday":
        yesterday_date = now.date() - datetime.timedelta(days=1)
        start_dt = datetime.datetime.combine(yesterday_date, datetime.time.min)
        end_dt = datetime.datetime.combine(yesterday_date, datetime.time.max)
    elif time_range == "7d":
        start_dt = today_start - datetime.timedelta(days=6)
        end_dt = today_end
    elif time_range == "30d":
        start_dt = today_start - datetime.timedelta(days=29)
        end_dt = today_end
    elif time_range == "custom" and start_date and end_date:
        try:
            parsed_start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            parsed_end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            start_dt = datetime.datetime.combine(parsed_start.date(), datetime.time.min)
            end_dt = datetime.datetime.combine(parsed_end.date(), datetime.time.max)
            if start_dt > end_dt:
                start_dt, end_dt = end_dt, start_dt
        except ValueError:
            start_dt = today_start
            end_dt = today_end
    else:  # default "today"
        start_dt = today_start
        end_dt = today_end

    return start_dt, end_dt

def get_system_health() -> SystemHealth:
    try:
        from src.features.print.bartender_engine import bt_engine
        is_ready = bt_engine.is_initialized
        printers = bt_engine.get_printers()
        return SystemHealth(
            bartender_status="ready" if is_ready else "offline",
            active_printers_count=len(printers)
        )
    except Exception as e:
        logger.warning(f"Error checking system health: {e}")
        return SystemHealth(bartender_status="offline", active_printers_count=0)

def calculate_hourly_throughput(
    db: Session,
    start_dt: datetime.datetime,
    end_dt: datetime.datetime,
    time_range: str
) -> list[HourlyStat]:
    span_days = (end_dt.date() - start_dt.date()).days
    is_hourly = time_range in ("today", "yesterday") or (time_range == "custom" and span_days <= 1)

    # Fast query 1: Fetch cartons headers without 132k items Cartesian join
    cartons = db.query(
        models.Carton.id,
        models.Carton.created_at,
        models.Carton.status,
        models.Product.packed_qty
    ).outerjoin(
        models.Product, models.Carton.product_id == models.Product.id
    ).filter(
        models.Carton.created_at >= start_dt,
        models.Carton.created_at <= end_dt
    ).all()

    # Fast query 2: Batch item counts per carton using indexed foreign key
    item_counts: dict[int, int] = {
        carton_id: count
        for carton_id, count in db.query(
            models.CartonItem.carton_id,
            func.count(models.CartonItem.id)
        ).join(
            models.Carton, models.CartonItem.carton_id == models.Carton.id
        ).filter(
            models.Carton.created_at >= start_dt,
            models.Carton.created_at <= end_dt
        ).group_by(models.CartonItem.carton_id).all()
    }

    if is_hourly:
        # Standard hourly view (06:00 to 22:00 baseline)
        hour_keys = [f"{h:02d}:00" for h in range(6, 23)]
        extra_keys = set()
        for _, created_at, _, _ in cartons:
            if created_at:
                h_key = created_at.strftime("%H:00")
                if h_key not in hour_keys:
                    extra_keys.add(h_key)
        all_keys = sorted(list(set(hour_keys).union(extra_keys)))

        stats_map: dict[str, dict[str, int]] = {
            k: {"total": 0, "success": 0, "failed": 0, "total_items": 0} for k in all_keys
        }
        for c_id, created_at, status, packed_qty in cartons:
            if created_at:
                key = created_at.strftime("%H:00")
                if key in stats_map:
                    stats_map[key]["total"] += 1
                    scanned = item_counts.get(c_id, 0)
                    items_count = scanned if scanned > 0 else (packed_qty or 0 if status == "SUCCESS" else 0)
                    stats_map[key]["total_items"] += items_count
                    if status == "SUCCESS":
                        stats_map[key]["success"] += 1
                    elif status == "FAILED":
                        stats_map[key]["failed"] += 1

        return [
            HourlyStat(
                hour=k,
                total=stats_map[k]["total"],
                success=stats_map[k]["success"],
                failed=stats_map[k]["failed"],
                total_items=stats_map[k]["total_items"]
            )
            for k in all_keys
        ]
    else:
        # Multi-day view (grouped by DD/MM)
        date_keys = []
        cur = start_dt.date()
        end_date = end_dt.date()
        while cur <= end_date:
            date_keys.append(cur.strftime("%d/%m"))
            cur += datetime.timedelta(days=1)

        stats_map = {k: {"total": 0, "success": 0, "failed": 0, "total_items": 0} for k in date_keys}
        for c_id, created_at, status, packed_qty in cartons:
            if created_at:
                key = created_at.strftime("%d/%m")
                if key in stats_map:
                    stats_map[key]["total"] += 1
                    scanned = item_counts.get(c_id, 0)
                    items_count = scanned if scanned > 0 else (packed_qty or 0 if status == "SUCCESS" else 0)
                    stats_map[key]["total_items"] += items_count
                    if status == "SUCCESS":
                        stats_map[key]["success"] += 1
                    elif status == "FAILED":
                        stats_map[key]["failed"] += 1

        return [
            HourlyStat(
                hour=k,
                total=stats_map[k]["total"],
                success=stats_map[k]["success"],
                failed=stats_map[k]["failed"],
                total_items=stats_map[k]["total_items"]
            )
            for k in date_keys
        ]

def calculate_top_products(
    db: Session,
    start_dt: datetime.datetime,
    end_dt: datetime.datetime,
    total_cartons: int
) -> list[ProductStat]:
    results = db.query(
        models.Product.id.label("product_id"),
        models.Product.item_name,
        models.Product.upc,
        models.Product.packed_qty,
        models.Customer.code.label("customer_code"),
        models.Customer.name.label("customer_name"),
        func.count(models.Carton.id).label("cnt")
    ).join(
        models.Carton, models.Carton.product_id == models.Product.id
    ).outerjoin(
        models.Customer, models.Product.customer_id == models.Customer.id
    ).filter(
        models.Carton.created_at >= start_dt,
        models.Carton.created_at <= end_dt
    ).group_by(
        models.Product.id,
        models.Product.item_name,
        models.Product.upc,
        models.Product.packed_qty,
        models.Customer.code,
        models.Customer.name
    ).order_by(
        desc("cnt")
    ).limit(8).all()

    if not results:
        return []

    # Batch query item counts for all top products to eliminate N+1 queries
    prod_ids = [r.product_id for r in results]
    prod_items_map: dict[int, int] = {
        product_id: count
        for product_id, count in db.query(
            models.Carton.product_id,
            func.count(models.CartonItem.id)
        ).join(
            models.CartonItem, models.CartonItem.carton_id == models.Carton.id
        ).filter(
            models.Carton.product_id.in_(prod_ids),
            models.Carton.created_at >= start_dt,
            models.Carton.created_at <= end_dt
        ).group_by(models.Carton.product_id).all()
    }

    top_products = []
    for r in results:
        pct = round((r.cnt / total_cartons * 100), 1) if total_cartons > 0 else 0.0
        prod_items = prod_items_map.get(r.product_id, 0)
        if prod_items == 0 and r.packed_qty:
            prod_items = r.cnt * r.packed_qty

        top_products.append(
            ProductStat(
                item_name=r.item_name or "Unknown",
                customer_code=r.customer_code or "N/A",
                customer_name=r.customer_name,
                upc=r.upc,
                packed_qty=r.packed_qty,
                count=r.cnt,
                total_items=prod_items,
                percentage=pct
            )
        )
    return top_products

def get_dashboard_stats(
    db: Session,
    time_range: str = "today",
    start_date: str | None = None,
    end_date: str | None = None
) -> DashboardStatsResponse:
    start_dt, end_dt = get_time_boundary(time_range, start_date=start_date, end_date=end_date)

    # 1. Combined KPI counts in 1 single query using CASE WHEN + SUM
    kpi_query = db.query(
        func.count(models.Carton.id).label("total"),
        func.sum(case((models.Carton.status == "SUCCESS", 1), else_=0)).label("success"),
        func.sum(case((models.Carton.status == "FAILED", 1), else_=0)).label("failed"),
        func.sum(case((models.Carton.is_reprint == 1, 1), else_=0)).label("reprint"),
    ).filter(
        models.Carton.created_at >= start_dt,
        models.Carton.created_at <= end_dt
    ).first()

    total_cartons = (kpi_query.total if kpi_query else 0) or 0
    success_cartons = (kpi_query.success if kpi_query else 0) or 0
    failed_cartons = (kpi_query.failed if kpi_query else 0) or 0
    reprint_cartons = (kpi_query.reprint if kpi_query else 0) or 0

    total_items = db.query(func.count(models.CartonItem.id)).join(
        models.Carton, models.CartonItem.carton_id == models.Carton.id
    ).filter(
        models.Carton.created_at >= start_dt,
        models.Carton.created_at <= end_dt
    ).scalar() or 0

    success_rate = round((success_cartons / total_cartons * 100), 1) if total_cartons > 0 else 0.0
    error_rate = round((failed_cartons / total_cartons * 100), 1) if total_cartons > 0 else 0.0
    reprint_rate = round((reprint_cartons / total_cartons * 100), 1) if total_cartons > 0 else 0.0

    kpis = KPIStats(
        total_cartons=total_cartons,
        success_cartons=success_cartons,
        failed_cartons=failed_cartons,
        reprint_cartons=reprint_cartons,
        total_items=total_items,
        success_rate=success_rate,
        error_rate=error_rate,
        reprint_rate=reprint_rate
    )

    # 2. Hourly/Daily throughput (optimized)
    hourly_throughput = calculate_hourly_throughput(db, start_dt, end_dt, time_range)

    # 3. Top products (optimized, no N+1)
    top_products = calculate_top_products(db, start_dt, end_dt, total_cartons)

    # 4. Live feed (Cycle 3)
    recent_cartons = db.query(models.Carton).options(
        joinedload(models.Carton.product).joinedload(models.Product.customer),
        selectinload(models.Carton.items)
    ).order_by(models.Carton.id.desc()).limit(15).all()

    live_feed: list[LiveCartonFeed] = []
    for c in recent_cartons:
        p_name = c.product.item_name if c.product else "N/A"
        c_code = c.product.customer.code if (c.product and c.product.customer) else "N/A"
        items_cnt = len(typing_cast(list, c.items)) if c.items else 0
        live_feed.append(
            LiveCartonFeed.model_validate({
                "id": c.id,
                "carton_sn": c.carton_sn or "N/A",
                "item_name": p_name,
                "customer_code": c_code,
                "created_at": c.created_at or datetime.datetime.now(),
                "status": c.status or "UNKNOWN",
                "is_reprint": c.is_reprint or 0,
                "weight": c.weight,
                "station_id": c.station_id,
                "items_count": items_cnt
            })
        )

    system = get_system_health()

    return DashboardStatsResponse(
        time_range=time_range,
        kpis=kpis,
        hourly_throughput=hourly_throughput,
        top_products=top_products,
        live_feed=live_feed,
        system=system
    )

