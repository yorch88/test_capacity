import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "test_capacity_db")

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGO_URL)
    return _client


def get_database():
    client = get_client()
    return client[MONGO_DB_NAME]


def get_users_collection():
    db = get_database()
    return db["users"]


def get_families_collection():
    db = get_database()
    return db["families"]


def get_analytics_collection():
    db = get_database()
    return db["analytic_test_cycle_time"]