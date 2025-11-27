from datetime import datetime, timedelta

from typing import Optional
from fastapi import Query
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from ..auth import get_current_user
from ..db import get_analytics_collection, get_families_collection, get_users_collection
from ..models import AnalyticsCreate, AnalyticsPublic, UserPublic

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("", response_model=list[AnalyticsPublic])
async def list_analytics_history(
    sku: str | None = Query(default=None),
    family_id: str | None = Query(default=None),
    current_user: UserPublic = Depends(get_current_user),
):
    """
    List analytics records.
    Optional filters:
      - sku (partial match)
      - family_id (exact match)
    """
    analytics_col = get_analytics_collection()
    families_col = get_families_collection()
    users_col = get_users_collection()

    query: dict = {}
    if sku:
        # simple 'contains' filter usando regex
        query["sku"] = {"$regex": sku, "$options": "i"}
    if family_id:
        query["family_id"] = family_id

    cursor = analytics_col.find(query).sort("created_at", -1).limit(100)

    results: list[AnalyticsPublic] = []

    async for doc in cursor:
        # Resolver family_name
        family_name = None
        fid = doc.get("family_id")
        if fid:
            try:
                fam = await families_col.find_one({"_id": ObjectId(fid)})
                if fam:
                    family_name = fam.get("name")
            except Exception:
                pass

        # Resolver created_by_email
        created_by_email = None
        created_by_user_id = doc.get("created_by_user_id")
        if created_by_user_id:
            try:
                user_doc = await users_col.find_one({"_id": ObjectId(created_by_user_id)})
                if user_doc:
                    created_by_email = user_doc.get("email")
            except Exception:
                pass

        results.append(
            AnalyticsPublic(
                id=str(doc["_id"]),
                family_id=doc["family_id"],
                sku=doc.get("sku"),
                quantity=doc["quantity"],
                capacity_slots=doc["capacity_slots"],
                manpower_qty=doc["manpower_qty"],
                units_per_manpower_per_day=doc["units_per_manpower_per_day"],
                fecha_release=doc["fecha_release"],
                test_cycle_time_hours=doc["test_cycle_time_hours"],
                bottleneck_type=doc["bottleneck_type"],
                equipment_capacity_units_per_day=doc["equipment_capacity_units_per_day"],
                manpower_capacity_units_per_day=doc["manpower_capacity_units_per_day"],
                input_capacity_units_per_day=doc.get("input_capacity_units_per_day"),
                throughput_units_per_hour=doc["throughput_units_per_hour"],
                input_cycle_time_hours=doc["input_cycle_time_hours"],
                input_cycle_time_minutes=doc["input_cycle_time_minutes"],
                total_duration_hours=doc["total_duration_hours"],
                first_unit_datetime=doc["first_unit_datetime"],
                is_feasible=doc.get("is_feasible", True),
                created_by_user_id=doc.get("created_by_user_id", ""),
                created_at=doc["created_at"],
                created_by_email=created_by_email,
                family_name=family_name,
                input_cycle_time_minutes_input=doc.get("input_cycle_time_minutes_input"),
            )
        )

    return results

@router.post("", response_model=AnalyticsPublic)
async def create_analytics(payload: AnalyticsCreate, current_user: UserPublic = Depends(get_current_user)):
    analytics_col = get_analytics_collection()
    families_col = get_families_collection()

    # Obtener CT de la familia
    family = await families_col.find_one({"_id": ObjectId(payload.family_id)})
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    test_cycle_time_hours = float(family["test_cycle_time_hours"])

    if payload.input_cycle_time_minutes <= 0:
        raise HTTPException(status_code=400, detail="input_cycle_time_minutes must be > 0")

    # 1) Capacidades
    equipment_capacity_units_per_day = (24.0 / test_cycle_time_hours) * payload.capacity_slots
    manpower_capacity_units_per_day = payload.manpower_qty * payload.units_per_manpower_per_day
    input_capacity_units_per_day = (24.0 * 60.0) / payload.input_cycle_time_minutes

    # 2) Throughput = mínimo de las tres
    capacity_map = {
        "equipment": equipment_capacity_units_per_day,
        "manpower": manpower_capacity_units_per_day,
        "input": input_capacity_units_per_day,
    }
    bottleneck_type = min(capacity_map, key=capacity_map.get)
    throughput_units_per_day = capacity_map[bottleneck_type]
    throughput_units_per_hour = throughput_units_per_day / 24.0

    # 3) Tiempo total para procesar todas las unidades
    total_duration_days = payload.quantity / throughput_units_per_day
    total_duration_hours = total_duration_days * 24.0

    # 4) Primera unidad que debe llegar a pruebas
    fecha_release = payload.fecha_release
    first_unit_datetime = fecha_release - timedelta(hours=total_duration_hours)

    # (si quieres lógica de is_feasible más estricta, puedes checar first_unit_datetime < ahora, etc.)
    is_feasible = True

    doc = {
        "family_id": payload.family_id,
        "sku": payload.sku,
        "quantity": payload.quantity,
        "capacity_slots": payload.capacity_slots,
        "manpower_qty": payload.manpower_qty,
        "units_per_manpower_per_day": payload.units_per_manpower_per_day,
        "fecha_release": fecha_release,
        "test_cycle_time_hours": test_cycle_time_hours,
        "bottleneck_type": bottleneck_type,
        "equipment_capacity_units_per_day": equipment_capacity_units_per_day,
        "manpower_capacity_units_per_day": manpower_capacity_units_per_day,
        "input_capacity_units_per_day": input_capacity_units_per_day,
        "throughput_units_per_hour": throughput_units_per_hour,
        "input_cycle_time_hours": 24.0 / throughput_units_per_day,  # requerido global
        "input_cycle_time_minutes": 60.0 / throughput_units_per_hour,
        "input_cycle_time_minutes_input": payload.input_cycle_time_minutes,
        "total_duration_hours": total_duration_hours,
        "first_unit_datetime": first_unit_datetime,
        "is_feasible": is_feasible,
        "created_by_user_id": current_user.id,
        "created_at": datetime.utcnow(),
    }

    result = await analytics_col.insert_one(doc)

    return AnalyticsPublic(
        id=str(result.inserted_id),
        **doc,
        created_by_email=current_user.email,
        family_name=family.get("name"),
    )

# @router.post("", response_model=AnalyticsPublic)
# async def create_analytics_record(
#     payload: AnalyticsCreate,
#     current_user: UserPublic = Depends(get_current_user),
# ):
#     families_col = get_families_collection()
#     analytics_col = get_analytics_collection()

#     # Get family and its test cycle time
#     try:
#         family_obj_id = ObjectId(payload.family_id)
#     except Exception:
#         raise HTTPException(status_code=400, detail="Invalid family id.")

#     family = await families_col.find_one({"_id": family_obj_id})
#     if not family:
#         raise HTTPException(status_code=404, detail="Family not found.")

#     CT = float(family["test_cycle_time_hours"])
#     N = payload.quantity
#     slots = payload.capacity_slots
#     manpower_qty = payload.manpower_qty
#     u_mp = payload.units_per_manpower_per_day
#     deadline = payload.fecha_release

#     # Capacity calculations
#     equipment_capacity_units_per_day = slots * (24.0 / CT)
#     manpower_capacity_units_per_day = manpower_qty * u_mp

#     if manpower_capacity_units_per_day >= equipment_capacity_units_per_day:
#         bottleneck_type = "equipment"
#         throughput_units_per_day = equipment_capacity_units_per_day
#     else:
#         bottleneck_type = "manpower"
#         throughput_units_per_day = manpower_capacity_units_per_day

#     throughput_units_per_hour = throughput_units_per_day / 24.0

#     if throughput_units_per_hour <= 0:
#         raise HTTPException(status_code=400, detail="Throughput is zero or negative. Check your inputs.")

#     input_cycle_time_hours = 1.0 / throughput_units_per_hour
#     input_cycle_time_minutes = input_cycle_time_hours * 60.0

#     total_duration_hours = CT + (N - 1) * input_cycle_time_hours

#     # Compute first unit datetime
#     first_unit_datetime = deadline - timedelta(hours=total_duration_hours)

#     is_feasible = True  # You can add extra feasibility checks here if needed.

#     now = datetime.utcnow()

#     doc = {
#         "family_id": payload.family_id,
#         "sku": payload.sku,
#         "quantity": N,
#         "capacity_slots": slots,
#         "manpower_qty": manpower_qty,
#         "units_per_manpower_per_day": u_mp,
#         "fecha_release": deadline,
#         "test_cycle_time_hours": CT,
#         "bottleneck_type": bottleneck_type,
#         "equipment_capacity_units_per_day": equipment_capacity_units_per_day,
#         "manpower_capacity_units_per_day": manpower_capacity_units_per_day,
#         "throughput_units_per_hour": throughput_units_per_hour,
#         "input_cycle_time_hours": input_cycle_time_hours,
#         "input_cycle_time_minutes": input_cycle_time_minutes,
#         "total_duration_hours": total_duration_hours,
#         "first_unit_datetime": first_unit_datetime,
#         "is_feasible": is_feasible,
#         "created_by_user_id": current_user.id,
#         "created_at": now,
#     }

#     result = await analytics_col.insert_one(doc)

#     return AnalyticsPublic(
#         id=str(result.inserted_id),
#         family_id=payload.family_id,
#         sku=payload.sku,
#         quantity=N,
#         capacity_slots=slots,
#         manpower_qty=manpower_qty,
#         units_per_manpower_per_day=u_mp,
#         fecha_release=deadline,
#         test_cycle_time_hours=CT,
#         bottleneck_type=bottleneck_type,
#         equipment_capacity_units_per_day=equipment_capacity_units_per_day,
#         manpower_capacity_units_per_day=manpower_capacity_units_per_day,
#         throughput_units_per_hour=throughput_units_per_hour,
#         input_cycle_time_hours=input_cycle_time_hours,
#         input_cycle_time_minutes=input_cycle_time_minutes,
#         total_duration_hours=total_duration_hours,
#         first_unit_datetime=first_unit_datetime,
#         is_feasible=is_feasible,
#         created_by_user_id=current_user.id,
#         created_at=now,
#     )