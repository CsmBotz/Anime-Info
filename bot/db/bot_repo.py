from typing import Dict, Any, Optional
from bot.db.clients import db_clients

class BotRepo:
    @staticmethod
    async def get_config(key: str) -> Optional[Any]:
        db = db_clients.bot_db
        if db is None: return None
        doc = await db.config.find_one({"key": key})
        return doc.get("value") if doc else None

    @staticmethod
    async def set_config(key: str, value: Any):
        db = db_clients.bot_db
        if db is None: return
        await db.config.update_one(
            {"key": key},
            {"$set": {"key": key, "value": value}},
            upsert=True
        )

