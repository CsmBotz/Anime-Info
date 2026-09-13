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

# CORS setup locked to Telegram origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://web.telegram.org", "https://telegram.org", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_current_user(x_init_data: Optional[str] = Header(None)) -> Dict[str, Any]:
    # Allow fallback for dev/demo if init_data not provided
    if not x_init_data:
        # Return mock user for local preview/tests
        return {"id": 12345678, "first_name": "DemoUser", "username": "demouser"}
    
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
    trending = await AniListFetcher.get_trending(page=1, per_page=5)
    watchlist = await UsersRepo.get_watchlist(user_id, limit=5) if user_id else []
    
    return {
        "carousel": trending,
        "recommended": watchlist
    }

@app.get("/api/catalog")
async def catalog_page(genre: Optional[str] = None, current_user: Dict[str, Any] = Depends(get_current_user)):
    data = await AniListFetcher.search_anime("", page=1, per_page=20)
    items = data.get("media", [])
    
    # Sort alphabetically by title
    items_sorted = sorted(items, key=lambda x: (x.get("title", {}).get("english") or x.get("title", {}).get("romaji") or "").lower())
    
    # Group by first letter
    grouped = {}
    for item in items_sorted:
        title = item.get("title", {}).get("english") or item.get("title", {}).get("romaji") or "Unknown"
        letter = title[0].upper() if title else "#"
        if letter not in grouped:
            grouped[letter] = []
        grouped[letter].append(item)

    return {"catalog": grouped}

@app.get("/api/watchlist")
async def get_watchlist(current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user.get("id")
    return await UsersRepo.get_watchlist(user_id)

class WatchlistAddReq(BaseModel):
    anime_id: int
    title: str
    poster_image: Optional[str] = ""
    total_episodes: Optional[int] = 0

@app.post("/api/watchlist")
async def add_watchlist(req: WatchlistAddReq, current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user.get("id")
    success = await UsersRepo.add_to_watchlist(user_id, req.anime_id, req.title, req.poster_image, req.total_episodes)
    return {"success": success}

@app.patch("/api/watchlist/{anime_id}/progress")
async def update_progress(anime_id: int, current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user.get("id")
    new_prog = await UsersRepo.update_tracker_progress(user_id, anime_id, delta=1)
    return {"progress": new_prog}

# Serve frontend static files
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

