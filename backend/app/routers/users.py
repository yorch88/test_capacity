from datetime import timedelta
from ..models import UserCreate, UserPublic
from ..models import UserCreate, UserPublic, UserSelfRegister
from bson import ObjectId
from pymongo import ReturnDocument
# ... (y el resto de imports que ya tienes)

from ..auth import get_current_admin_user, hash_password
from ..db import get_users_collection
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_admin_user,
)
from ..db import get_users_collection
from ..models import UserCreate, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register-initial-admin", response_model=UserPublic)
async def register_initial_admin(user: UserCreate):
    users_col = get_users_collection()
    
    # Validate duplicates
    existing_user = await users_col.find_one({
        "$or": [
            {"username": user.username},
            {"email": user.email}
        ]
    })
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username or email already exists."
        )

    existing_count = await users_col.count_documents({})
    if existing_count > 0:
        raise HTTPException(
            status_code=400, 
            detail="Users already exist. Initial admin cannot be created."
        )

    doc = {
        "username": user.username,
        "email": user.email,
        "password_hash": hash_password(user.password),
        "is_admin": True,
        "is_active": True,
    }

    result = await users_col.insert_one(doc)
    return UserPublic(
        id=str(result.inserted_id),
        username=user.username,
        email=user.email,
        is_admin=True,
        is_active=True,
    )


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    users_col = get_users_collection()
    doc = await users_col.find_one({
            "$or": [
                {"username": form_data.username},
                {"email": form_data.username},
            ]
        })
    if not doc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password.")

    if not doc.get("is_active", True):
        raise HTTPException(status_code=403, detail="User is inactive.")

    if not verify_password(form_data.password, doc["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password.")

    access_token = create_access_token({"sub": doc["username"]}, expires_delta=timedelta(hours=8))
    return {"access_token": access_token, "token_type": "bearer"}


# ---- Admin user management ----

@router.get("/users", response_model=list[UserPublic])
async def list_users(admin=Depends(get_current_admin_user)):
    users_col = get_users_collection()
    users = []
    async for doc in users_col.find({}):
        users.append(
            UserPublic(
                id=str(doc["_id"]),
                username=doc["username"],
                email=doc["email"],
                is_admin=doc.get("is_admin", True),
                is_active=doc.get("is_active", True),
            )
        )
    return users


@router.post("/users/{user_id}/activate", response_model=UserPublic)
async def activate_user(user_id: str, admin=Depends(get_current_admin_user)):
    users_col = get_users_collection()

    # 1) Validar que el id tenga formato de ObjectId
    try:
        _id = ObjectId(user_id)
    except Exception:
        # Este es el 400 que estás viendo ahora
        raise HTTPException(
            status_code=400,
            detail=f"Invalid user id: {user_id}",
        )

    # 2) Actualizar y devolver el usuario ya actualizado
    result = await users_col.find_one_and_update(
        {"_id": _id},
        {"$set": {"is_active": True}},
        return_document=ReturnDocument.AFTER,
    )

    if result is None:
        raise HTTPException(status_code=404, detail="User not found.")

    return UserPublic(
        id=str(result["_id"]),
        username=result["username"],
        email=result["email"],
        is_admin=result.get("is_admin", False),
        is_active=result.get("is_active", False),
    )

    
@router.post("/users", response_model=UserPublic)
async def create_user(user: UserCreate, admin=Depends(get_current_admin_user)):
    """
    Create a new user (admin only).
    Username and email must be unique.
    """
    users_col = get_users_collection()

    # Validate duplicates username/email
    existing = await users_col.find_one({
        "$or": [
            {"username": user.username},
            {"email": user.email},
        ]
    })
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists.")

    doc = {
        "username": user.username,
        "email": user.email,
        "password_hash": hash_password(user.password),
        # For now all users are admins as you mentioned
        "is_admin": user.is_admin,
        "is_active": user.is_active,
    }

    result = await users_col.insert_one(doc)

    return UserPublic(
        id=str(result.inserted_id),
        username=user.username,
        email=user.email,
        is_admin=user.is_admin,
        is_active=user.is_active,
    )
    
@router.post("/register", response_model=UserPublic)
async def public_register(user: UserSelfRegister):
    """
    Public endpoint to create a user.
    - User is created as inactive and non-admin.
    - Captcha is required to avoid automated mass signups.
    """
    # Simple captcha validation: a + b == result
    if user.captcha_a + user.captcha_b != user.captcha_result:
        raise HTTPException(status_code=400, detail="Invalid captcha answer.")

    users_col = get_users_collection()

    # We'll use email as username for simplicity
    username = user.email

    # Check duplicates by username or email
    existing = await users_col.find_one({
        "$or": [
            {"username": username},
            {"email": user.email},
        ]
    })
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists.")

    doc = {
        "username": username,
        "email": user.email,
        "password_hash": hash_password(user.password),
        "is_admin": False,   # self-registered users are not admins
        "is_active": False,  # must be activated by an admin
    }

    result = await users_col.insert_one(doc)

    return UserPublic(
        id=str(result.inserted_id),
        username=username,
        email=user.email,
        is_admin=False,
        is_active=False,
    )
