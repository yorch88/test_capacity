from datetime import datetime, timedelta

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user
from ..db import get_analytics_collection, get_families_collection
from ..models import AnalyticsCreate, AnalyticsPublic, UserPublic

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("", response_model=AnalyticsPublic)
async def create_analytics_record(
    payload: AnalyticsCreate,
    current_user: UserPublic = Depends(get_current_user),
):
    families_col = get_families_collection()
    analytics_col = get_analytics_collection()

    # Get family and its test cycle time
    try:
        family_obj_id = ObjectId(payload.family_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid family id.")

    family = await families_col.find_one({"_id": family_obj_id})
    if not family:
        raise HTTPException(status_code=404, detail="Family not found.")

    CT = float(family["test_cycle_time_hours"])
    N = payload.quantity
    slots = payload.capacity_slots
    manpower_qty = payload.manpower_qty
    u_mp = payload.units_per_manpower_per_day
    deadline = payload.fecha_release

    # Capacity calculations
    equipment_capacity_units_per_day = slots * (24.0 / CT)
    manpower_capacity_units_per_day = manpower_qty * u_mp

    if manpower_capacity_units_per_day >= equipment_capacity_units_per_day:
        bottleneck_type = "equipment"
        throughput_units_per_day = equipment_capacity_units_per_day
    else:
        bottleneck_type = "manpower"
        throughput_units_per_day = manpower_capacity_units_per_day

    throughput_units_per_hour = throughput_units_per_day / 24.0

    if throughput_units_per_hour <= 0:
        raise HTTPException(status_code=400, detail="Throughput is zero or negative. Check your inputs.")

    input_cycle_time_hours = 1.0 / throughput_units_per_hour
    input_cycle_time_minutes = input_cycle_time_hours * 60.0

    total_duration_hours = CT + (N - 1) * input_cycle_time_hours

    # Compute first unit datetime
    first_unit_datetime = deadline - timedelta(hours=total_duration_hours)

    is_feasible = True  # You can add extra feasibility checks here if needed.

    now = datetime.utcnow()

    doc = {
        "family_id": payload.family_id,
        "sku": payload.sku,
        "quantity": N,
        "capacity_slots": slots,
        "manpower_qty": manpower_qty,
        "units_per_manpower_per_day": u_mp,
        "fecha_release": deadline,
        "test_cycle_time_hours": CT,
        "bottleneck_type": bottleneck_type,
        "equipment_capacity_units_per_day": equipment_capacity_units_per_day,
        "manpower_capacity_units_per_day": manpower_capacity_units_per_day,
        "throughput_units_per_hour": throughput_units_per_hour,
        "input_cycle_time_hours": input_cycle_time_hours,
        "input_cycle_time_minutes": input_cycle_time_minutes,
        "total_duration_hours": total_duration_hours,
        "first_unit_datetime": first_unit_datetime,
        "is_feasible": is_feasible,
        "created_by_user_id": current_user.id,
        "created_at": now,
    }

    result = await analytics_col.insert_one(doc)

    return AnalyticsPublic(
        id=str(result.inserted_id),
        family_id=payload.family_id,
        sku=payload.sku,
        quantity=N,
        capacity_slots=slots,
        manpower_qty=manpower_qty,
        units_per_manpower_per_day=u_mp,
        fecha_release=deadline,
        test_cycle_time_hours=CT,
        bottleneck_type=bottleneck_type,
        equipment_capacity_units_per_day=equipment_capacity_units_per_day,
        manpower_capacity_units_per_day=manpower_capacity_units_per_day,
        throughput_units_per_hour=throughput_units_per_hour,
        input_cycle_time_hours=input_cycle_time_hours,
        input_cycle_time_minutes=input_cycle_time_minutes,
        total_duration_hours=total_duration_hours,
        first_unit_datetime=first_unit_datetime,
        is_feasible=is_feasible,
        created_by_user_id=current_user.id,
        created_at=now,
    )