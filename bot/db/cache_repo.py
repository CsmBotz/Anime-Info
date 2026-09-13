import datetime
from typing import Optional, Any
from bot.db.clients import db_clients

class CacheRepo:
    @staticmethod
    async def get(key: str) -> Optional[Any]:
        db = db_clients.cache_db
        if db is None: return None
        doc = await db.api_cache.find_one({"key": key})
        return doc.get("data") if doc else None

    @staticmethod
    async def set(key: str, data: Any):
        db = db_clients.cache_db
        if db is None: return
        await db.api_cache.update_one(
            {"key": key},
            {"$set": {
                "key": key,
                "data": data,
                "created_at": datetime.datetime.utcnow()
            }},
            upsert=True
        )

