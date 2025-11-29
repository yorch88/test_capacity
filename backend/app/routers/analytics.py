from datetime import datetime, timedelta, timezone
import math
from typing import Optional
from fastapi import Query
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from ..auth import get_current_user
from ..db import get_analytics_collection, get_families_collection, get_users_collection
from ..helpers import _ensure_utc
from ..models import AnalyticsCreate, AnalyticsPublic, UserPublic, AnalyticsHistoryPage

router = APIRouter(prefix="/analytics", tags=["analytics"])


async def _build_analytics_doc(
    payload: AnalyticsCreate,
    current_user: UserPublic,
):
    families_col = get_families_collection()

    # 1) Obtener familia y CT
    family = await families_col.find_one({"_id": ObjectId(payload.family_id)})
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    test_cycle_time_hours = float(family["test_cycle_time_hours"])

    if payload.input_cycle_time_minutes <= 0:
        raise HTTPException(
            status_code=400,
            detail="input_cycle_time_minutes must be > 0",
        )

    # 2) Capacidades (unidades por día)
    equipment_capacity_units_per_day = (
        24.0 / test_cycle_time_hours
    ) * payload.capacity_slots

    manpower_capacity_units_per_day = (
        payload.manpower_qty * payload.units_per_manpower_per_day
    )

    # capacidad real de input desde producción (min/ud → ud/día)
    input_capacity_units_per_day = (24.0 * 60.0) / payload.input_cycle_time_minutes

    # 3) Throughput = mínimo de las tres capacidades
    capacity_map = {
        "equipment": equipment_capacity_units_per_day,
        "manpower": manpower_capacity_units_per_day,
        "input": input_capacity_units_per_day,
    }
    bottleneck_type = min(capacity_map, key=capacity_map.get)
    throughput_units_per_day = capacity_map[bottleneck_type]
    if throughput_units_per_day <= 0:
        raise HTTPException(
            status_code=400,
            detail="Computed throughput is not valid (<= 0). Check inputs.",
        )
    throughput_units_per_hour = throughput_units_per_day / 24.0

    # CT efectivo del sistema (no el de producción)
    input_cycle_time_hours = 24.0 / throughput_units_per_day
    input_cycle_time_minutes = 60.0 / throughput_units_per_hour

    # 4) Duración total para procesar todas las unidades
    total_duration_days = payload.quantity / throughput_units_per_day
    total_duration_hours = total_duration_days * 24.0

    fecha_release = payload.fecha_release
    required_first_unit_datetime = fecha_release - timedelta(
        hours=total_duration_hours
    )

    estimated = payload.estimated_first_unit_datetime

    # 5) Lógica de Estimated Input Date + commit_on_risk (parte 1)
    if estimated is None:
        first_unit_datetime = required_first_unit_datetime
        is_feasible = True
        commit_on_risk = False
    else:
        finish_from_estimated = estimated + timedelta(hours=total_duration_hours)
        is_feasible = finish_from_estimated <= fecha_release
        commit_on_risk = not is_feasible
        first_unit_datetime = required_first_unit_datetime

    # 6) Check adicional: ¿la primera unidad requerida está en el pasado?
    now_utc = datetime.now(timezone.utc)
    if first_unit_datetime.tzinfo is None:
        first_dt_utc = first_unit_datetime.replace(tzinfo=timezone.utc)
    else:
        first_dt_utc = first_unit_datetime.astimezone(timezone.utc)

    if first_dt_utc < now_utc:
        is_feasible = False
        commit_on_risk = True

    now = now_utc

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
        "input_cycle_time_hours": input_cycle_time_hours,
        "input_cycle_time_minutes": input_cycle_time_minutes,
        "input_cycle_time_minutes_input": payload.input_cycle_time_minutes,
        "total_duration_hours": total_duration_hours,
        "first_unit_datetime": first_unit_datetime,
        "estimated_first_unit_datetime": estimated,
        "is_feasible": is_feasible,
        "commit_on_risk": commit_on_risk,
        "created_by_user_id": current_user.id,
        "created_at": now,
    }

    return doc, family

@router.post("/compute", response_model=AnalyticsPublic)
async def compute_analytics(
    payload: AnalyticsCreate,
    current_user: UserPublic = Depends(get_current_user),
):
    doc, family = await _build_analytics_doc(payload, current_user)

    # id "fake" para cumplir AnalyticsPublic; este resultado NO se guarda
    return AnalyticsPublic(
        id="preview",
        **doc,
        created_by_email=current_user.email,
        family_name=family.get("name"),
    )

@router.get("", response_model=AnalyticsHistoryPage)
async def list_analytics_history(
    sku: str | None = Query(default=None),
    family_id: str | None = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserPublic = Depends(get_current_user),
):
    analytics_col = get_analytics_collection()
    families_col = get_families_collection()
    users_col = get_users_collection()

    query: dict = {}
    if sku:
        query["sku"] = {"$regex": sku, "$options": "i"}
    if family_id:
        query["family_id"] = family_id

    total = await analytics_col.count_documents(query)
    skip = (page - 1) * page_size

    cursor = (
        analytics_col.find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(page_size)
    )

    items: list[AnalyticsPublic] = []

    async for doc in cursor:
        # resolver family_name y created_by_email como ya lo hacías
        family_name = None
        fid = doc.get("family_id")
        if fid:
            try:
                fam = await families_col.find_one({"_id": ObjectId(fid)})
                if fam:
                    family_name = fam.get("name")
            except Exception:
                pass

        created_by_email = None
        created_by_user_id = doc.get("created_by_user_id")
        if created_by_user_id:
            try:
                user_doc = await users_col.find_one({"_id": ObjectId(created_by_user_id)})
                if user_doc:
                    created_by_email = user_doc.get("email")
            except Exception:
                pass

        # 👇 Normalizar fechas a UTC-aware para que el front las vea igual que el POST
        fecha_release = _ensure_utc(doc["fecha_release"])
        first_unit_datetime = _ensure_utc(doc["first_unit_datetime"])
        estimated_first_unit = _ensure_utc(doc.get("estimated_first_unit_datetime"))
        created_at = _ensure_utc(doc["created_at"])

        items.append(
            AnalyticsPublic(
                id=str(doc["_id"]),
                family_id=doc["family_id"],
                sku=doc.get("sku"),
                quantity=doc["quantity"],
                capacity_slots=doc["capacity_slots"],
                manpower_qty=doc["manpower_qty"],
                units_per_manpower_per_day=doc["units_per_manpower_per_day"],
                fecha_release=fecha_release,
                test_cycle_time_hours=doc["test_cycle_time_hours"],
                bottleneck_type=doc["bottleneck_type"],
                equipment_capacity_units_per_day=doc["equipment_capacity_units_per_day"],
                manpower_capacity_units_per_day=doc["manpower_capacity_units_per_day"],
                input_capacity_units_per_day=doc.get("input_capacity_units_per_day"),
                throughput_units_per_hour=doc["throughput_units_per_hour"],
                input_cycle_time_hours=doc["input_cycle_time_hours"],
                input_cycle_time_minutes=doc["input_cycle_time_minutes"],
                total_duration_hours=doc["total_duration_hours"],
                first_unit_datetime=first_unit_datetime,
                estimated_first_unit_datetime=estimated_first_unit,
                is_feasible=doc.get("is_feasible", True),
                commit_on_risk=doc.get("commit_on_risk", False),
                created_by_user_id=created_by_user_id or "",
                created_at=created_at,
                created_by_email=created_by_email,
                family_name=family_name,
                input_cycle_time_minutes_input=doc.get("input_cycle_time_minutes_input"),
            )
        )

    total_pages = math.ceil(total / page_size) if page_size else 1

    return AnalyticsHistoryPage(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )



@router.post("", response_model=AnalyticsPublic)
async def create_analytics(
    payload: AnalyticsCreate,
    current_user: UserPublic = Depends(get_current_user),
):
    analytics_col = get_analytics_collection()

    doc, family = await _build_analytics_doc(payload, current_user)

    result = await analytics_col.insert_one(doc)

    return AnalyticsPublic(
        id=str(result.inserted_id),
        **doc,
        created_by_email=current_user.email,
        family_name=family.get("name"),
    )