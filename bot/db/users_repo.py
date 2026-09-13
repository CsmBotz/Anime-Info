from typing import List, Dict, Any, Optional
from bot.db.clients import db_clients

class UsersRepo:
    @staticmethod
    async def ensure_user(user_id: int, username: Optional[str] = None):
        db = db_clients.users_db
        if db is None: return
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id, "username": username}},
            upsert=True
        )

    @staticmethod
    async def add_to_watchlist(user_id: int, anime_id: int, title: str, poster_image: str = "", total_episodes: int = 0) -> bool:
        db = db_clients.users_db
        if db is None: return False
        await UsersRepo.ensure_user(user_id)
        doc = {
            "user_id": user_id,
            "anime_id": anime_id,
            "title": title,
            "poster_image": poster_image,
            "progress": 0,
            "total_episodes": total_episodes,
            "status": "watching"
        }
        res = await db.watchlist.update_one(
            {"user_id": user_id, "anime_id": anime_id},
            {"$setOnInsert": doc},
            upsert=True
        )
        return res.upserted_id is not None

    @staticmethod
    async def remove_from_watchlist(user_id: int, anime_id: int) -> bool:
        db = db_clients.users_db
        if db is None: return False
        res = await db.watchlist.delete_one({"user_id": user_id, "anime_id": anime_id})
        return res.deleted_count > 0

    @staticmethod
    async def get_watchlist(user_id: int, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        db = db_clients.users_db
        if db is None: return []
        cursor = db.watchlist.find({"user_id": user_id}).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    @staticmethod
    async def update_tracker_progress(user_id: int, anime_id: int, delta: int = 1) -> Optional[int]:
        db = db_clients.users_db
        if db is None: return None
        item = await db.watchlist.find_one({"user_id": user_id, "anime_id": anime_id})
        if not item:
            return None
        new_progress = item.get("progress", 0) + delta
        await db.watchlist.update_one(
            {"user_id": user_id, "anime_id": anime_id},
            {"$set": {"progress": new_progress}}
        )
        return new_progress

    @staticmethod
    async def toggle_favorite(user_id: int, anime_id: int, title: str, poster_image: str = "") -> bool:
        db = db_clients.users_db
        if db is None: return False
        await UsersRepo.ensure_user(user_id)
        existing = await db.favorites.find_one({"user_id": user_id, "anime_id": anime_id})
        if existing:
            await db.favorites.delete_one({"user_id": user_id, "anime_id": anime_id})
            return False  # removed
        else:
            await db.favorites.insert_one({
                "user_id": user_id,
                "anime_id": anime_id,
                "title": title,
                "poster_image": poster_image
            })
            return True  # added

    @staticmethod
    async def get_favorites(user_id: int, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        db = db_clients.users_db
        if db is None: return []
        cursor = db.favorites.find({"user_id": user_id}).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    @staticmethod
    async def is_favorite(user_id: int, anime_id: int) -> bool:
        db = db_clients.users_db
        if db is None: return False
        item = await db.favorites.find_one({"user_id": user_id, "anime_id": anime_id})
        return item is not None

    @staticmethod
    async def delete_user_data(user_id: int) -> bool:
        db = db_clients.users_db
        if db is None: return False
        await db.users.delete_one({"user_id": user_id})
        await db.watchlist.delete_many({"user_id": user_id})
        await db.favorites.delete_many({"user_id": user_id})
        return True

