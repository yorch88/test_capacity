from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user
from ..db import get_families_collection, get_users_collection
from ..models import FamilyCreate, FamilyUpdate, FamilyPublic, UserPublic

router = APIRouter(prefix="/families", tags=["families"])


@router.post("", response_model=FamilyPublic)
async def create_family(payload: FamilyCreate, current_user: UserPublic = Depends(get_current_user)):
    families_col = get_families_collection()
    now = datetime.utcnow()
    doc = {
        "name": payload.name,
        "test_cycle_time_hours": payload.test_cycle_time_hours,
        "created_by_user_id": current_user.id,
        "created_at": now,
    }
    result = await families_col.insert_one(doc)

    return FamilyPublic(
        id=str(result.inserted_id),
        name=payload.name,
        test_cycle_time_hours=payload.test_cycle_time_hours,
        created_by_user_id=current_user.id,
        created_at=now,
        created_by_email=current_user.email,   # 👈 aquí
    )

@router.get("", response_model=list[FamilyPublic])
async def list_families(current_user: UserPublic = Depends(get_current_user)):
    families_col = get_families_collection()
    users_col = get_users_collection()
    families: list[FamilyPublic] = []

    async for doc in families_col.find({}):
        created_by_user_id = doc.get("created_by_user_id", "")
        created_by_email = None

        if created_by_user_id:
            try:
                user_doc = await users_col.find_one({"_id": ObjectId(created_by_user_id)})
                if user_doc:
                    created_by_email = user_doc.get("email")
            except Exception:
                # Si el id no es válido o algo falla, simplemente dejamos el email como None
                pass

        families.append(
            FamilyPublic(
                id=str(doc["_id"]),
                name=doc["name"],
                test_cycle_time_hours=doc["test_cycle_time_hours"],
                created_by_user_id=created_by_user_id,
                created_at=doc.get("created_at"),
                created_by_email=created_by_email,  # 👈 aquí
            )
        )
    return families



@router.put("/{family_id}", response_model=FamilyPublic)
async def update_family(
    family_id: str,
    payload: FamilyUpdate,
    current_user: UserPublic = Depends(get_current_user),
):
    families_col = get_families_collection()
    try:
        _id = ObjectId(family_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid family id.")

    update_data = {k: v for k, v in payload.dict(exclude_unset=True).items()}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update.")

    updated = await families_col.find_one_and_update(
        {"_id": _id},
        {"$set": update_data},
        return_document=True,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Family not found.")

    return FamilyPublic(
        id=str(updated["_id"]),
        name=updated["name"],
        test_cycle_time_hours=updated["test_cycle_time_hours"],
        created_by_user_id=updated.get("created_by_user_id", ""),
        created_at=updated.get("created_at"),
    )