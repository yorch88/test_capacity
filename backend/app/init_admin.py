# backend/app/init_admin.py
import os
import asyncio
import time

from motor.motor_asyncio import AsyncIOMotorClient

from .auth import hash_password
from .db import MONGO_URL, MONGO_DB_NAME


MAX_RETRIES = 10
RETRY_DELAY_SECONDS = 3


async def create_default_admin():
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "changeme")

    if not admin_username or not admin_email or not admin_password:
        print("[init_admin] ADMIN_* env vars not fully set, skipping default admin creation.")
        return

    client = AsyncIOMotorClient(MONGO_URL)
    db = client[MONGO_DB_NAME]
    users_col = db["users"]

    existing_count = await users_col.count_documents({})
    if existing_count > 0:
        print("[init_admin] Users already exist, skipping default admin creation.")
        return

    doc = {
        "username": admin_username,
        "email": admin_email,
        "password_hash": hash_password(admin_password),
        "is_admin": True,
        "is_active": True,
    }

    await users_col.insert_one(doc)
    print(f"[init_admin] Created default admin user '{admin_username}' ({admin_email})")


def main():
    # Esperar a que Mongo esté listo con unos reintentos sencillos
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"[init_admin] Attempt {attempt}/{MAX_RETRIES} to connect to Mongo...")
            client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=2000)
            # Llamada de prueba
            client.admin.command("ping")
            print("[init_admin] Mongo is available.")
            break
        except Exception as exc:
            print(f"[init_admin] Mongo not ready yet: {exc}")
            if attempt == MAX_RETRIES:
                print("[init_admin] Giving up on creating default admin (Mongo unavailable).")
                return
            time.sleep(RETRY_DELAY_SECONDS)

    # Si llegamos aquí, Mongo responde, podemos crear admin
    asyncio.run(create_default_admin())


if __name__ == "__main__":
    main()
