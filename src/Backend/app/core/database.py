"""
Async MongoDB connection via motor
"""
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

_client: AsyncIOMotorClient | None = None
_db = None


async def connect_db():
    global _client, _db
    _client = AsyncIOMotorClient(settings.MONGO_URI)
    _db = _client[settings.MONGO_DB]
    # Create indexes
    await _db.users.create_index("email", unique=True)
    await _db.sessions.create_index("pan")
    await _db.sessions.create_index("id", unique=True)
    await _db.compliance_records.create_index("pan")
    await _db.compliance_records.create_index("session_id", unique=True)
    await _db.fraud_records.create_index("session_id", unique=True)
    await _db.fraud_records.create_index("pan")
    print("✅ MongoDB connected")


async def close_db():
    global _client
    if _client:
        _client.close()


def get_db():
    return _db
