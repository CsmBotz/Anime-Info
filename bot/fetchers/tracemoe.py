import httpx
from typing import Dict, Any
from bot.utils.logging import get_logger

logger = get_logger(__name__)

TRACEMOE_URL = "https://api.trace.moe/search"

class TraceMoeFetcher:
    @staticmethod
    async def search_by_image_url(image_url: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(TRACEMOE_URL, params={"url": image_url, "anilistInfo": ""})
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def search_by_image_bytes(image_bytes: bytes) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                TRACEMOE_URL,
                params={"anilistInfo": ""},
                files={"file": ("image.jpg", image_bytes, "image/jpeg")}
            )
            resp.raise_for_status()
            return resp.json()

