import os
from fastapi import FastAPI, Header, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from bot.db.clients import db_clients
from bot.db.users_repo import UsersRepo
from bot.fetchers.anilist import AniListFetcher
from webapp.backend.auth import validate_telegram_init_data

app = FastAPI(title="Anime Info Bot Mini App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_current_user(x_init_data: Optional[str] = Header(None)) -> Dict[str, Any]:
    if not x_init_data:
        return {"id": 12345678, "first_name": "Demo", "username": "demouser"}
    user = validate_telegram_init_data(x_init_data)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired Telegram initData")
    return user

@app.on_event("startup")
async def startup_event():
    await db_clients.init_clients()

@app.get("/api/discover")
async def discover_page(current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user.get("id")
    trending = await AniListFetcher.get_trending(page=1, per_page=10)
    watchlist = await UsersRepo.get_watchlist(user_id, limit=10) if user_id else []
    return {"carousel": trending, "watchlist": watchlist, "user": current_user}

@app.get("/api/search")
async def search_anime(q: str = "", current_user: Dict[str, Any] = Depends(get_current_user)):
    if not q.strip():
        items = await AniListFetcher.get_trending(page=1, per_page=20)
        return {"results": items}
    data = await AniListFetcher.search_anime(q.strip(), page=1, per_page=20)
    return {"results": data.get("media", [])}

@app.get("/api/catalog")
async def catalog_page(
    filter: Optional[str] = "trending",
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    if filter == "trending":
        items = await AniListFetcher.get_trending(page=1, per_page=30)
    elif filter == "new":
        items = await AniListFetcher.get_new_releases(page=1, per_page=30)
    else:
        items = await AniListFetcher.get_popular(page=1, per_page=30)

    # Sort alphabetically
    items_sorted = sorted(
        items,
        key=lambda x: (x.get("title", {}).get("english") or x.get("title", {}).get("romaji") or "").lower()
    )

    # Group by first letter
    grouped = {}
    for item in items_sorted:
        title = item.get("title", {}).get("english") or item.get("title", {}).get("romaji") or "Unknown"
        letter = title[0].upper() if title else "#"
        if letter not in grouped:
            grouped[letter] = []
        grouped[letter].append(item)

    return {"catalog": grouped}

@app.get("/api/anime/{anime_id}")
async def get_anime_detail(anime_id: int, current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user.get("id")

    data = await AniListFetcher.get_by_id(anime_id)
    if not data:
        raise HTTPException(status_code=404, detail="Anime not found")

    # Enrich with user-specific data
    watchlist_items = await UsersRepo.get_watchlist(user_id, limit=100) if user_id else []
    in_watchlist = any(w.get("anime_id") == anime_id for w in watchlist_items)
    wl_item = next((w for w in watchlist_items if w.get("anime_id") == anime_id), None)
    is_favorite = await UsersRepo.is_favorite(user_id, anime_id) if user_id else False

    data["in_watchlist"] = in_watchlist
    data["is_favorite"] = is_favorite
    data["progress"] = wl_item.get("progress", 0) if wl_item else 0

    return data

@app.get("/api/watchlist")
async def get_watchlist_api(current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user.get("id")
    items = await UsersRepo.get_watchlist(user_id, limit=50)
    # Convert ObjectId to string for JSON
    for item in items:
        if "_id" in item:
            item["_id"] = str(item["_id"])
    return items

class WatchlistAddReq(BaseModel):
    anime_id: int
    title: str
    poster_image: Optional[str] = ""
    total_episodes: Optional[int] = 0

@app.post("/api/watchlist")
async def add_watchlist(req: WatchlistAddReq, current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user.get("id")
    success = await UsersRepo.add_to_watchlist(user_id, req.anime_id, req.title, req.poster_image, req.total_episodes)
    return {"success": success, "added": success}

@app.delete("/api/watchlist/{anime_id}")
async def remove_watchlist(anime_id: int, current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user.get("id")
    success = await UsersRepo.remove_from_watchlist(user_id, anime_id)
    return {"success": success}

@app.patch("/api/watchlist/{anime_id}/progress")
async def update_progress(anime_id: int, current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user.get("id")
    new_prog = await UsersRepo.update_tracker_progress(user_id, anime_id, delta=1)
    return {"progress": new_prog}

class FavoriteReq(BaseModel):
    anime_id: int
    title: str
    poster_image: Optional[str] = ""

@app.post("/api/favorites/toggle")
async def toggle_favorite(req: FavoriteReq, current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user.get("id")
    is_now_fav = await UsersRepo.toggle_favorite(user_id, req.anime_id, req.title, req.poster_image)
    return {"is_favorite": is_now_fav}

# Serve frontend static files — must be LAST
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
