import httpx
from typing import Dict, Any, List, Optional
from bot.db.cache_repo import CacheRepo
from bot.utils.logging import get_logger

logger = get_logger(__name__)

ANILIST_URL = "https://graphql.anilist.co"

ANIME_QUERY = """
query ($search: String, $page: Int, $perPage: Int, $isAdult: Boolean) {
  Page(page: $page, perPage: $perPage) {
    pageInfo {
      total
      currentPage
      lastPage
      hasNextPage
    }
    media(search: $search, type: ANIME, isAdult: $isAdult) {
      id
      title {
        romaji
        english
        native
      }
      status
      averageScore
      episodes
      description
      coverImage {
        large
        extraLarge
      }
      bannerImage
      siteUrl
      genres
      nextAiringEpisode {
        airingAt
        timeUntilAiring
        episode
      }
    }
  }
}
"""

MANGA_QUERY = """
query ($search: String, $page: Int, $perPage: Int, $isAdult: Boolean) {
  Page(page: $page, perPage: $perPage) {
    pageInfo {
      total
      currentPage
      lastPage
      hasNextPage
    }
    media(search: $search, type: MANGA, isAdult: $isAdult) {
      id
      title {
        romaji
        english
      }
      status
      averageScore
      chapters
      volumes
      description
      coverImage {
        large
      }
      siteUrl
    }
  }
}
"""

CHARACTER_QUERY = """
query ($search: String, $page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    mediaCharacters: characters(search: $search) {
      id
      name {
        full
        native
      }
      description
      image {
        large
      }
      siteUrl
    }
  }
}
"""

STUDIO_QUERY = """
query ($search: String, $page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    studios(search: $search) {
      id
      name
      siteUrl
      isAnimationStudio
    }
  }
}
"""

TRENDING_QUERY = """
query ($page: Int, $perPage: Int, $isAdult: Boolean) {
  Page(page: $page, perPage: $perPage) {
    media(type: ANIME, sort: TRENDING_DESC, isAdult: $isAdult) {
      id
      title {
        romaji
        english
      }
      status
      averageScore
      episodes
      description
      coverImage {
        large
      }
      siteUrl
    }
  }
}
"""

SCHEDULE_QUERY = """
query ($page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    airingSchedules(notYetAiring: true, sort: TIME) {
      id
      airingAt
      episode
      media {
        id
        title {
          romaji
          english
        }
        siteUrl
      }
    }
  }
}
"""

class AniListFetcher:
    @staticmethod
    async def post_query(query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        cache_key = f"anilist:{hash(query)}:{str(variables)}"
        cached = await CacheRepo.get(cache_key)
        if cached:
            return cached

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(ANILIST_URL, json={"query": query, "variables": variables})
            resp.raise_for_status()
            data = resp.json()
            await CacheRepo.set(cache_key, data)
            return data

    @classmethod
    async def search_anime(cls, search: str, page: int = 1, per_page: int = 5, is_adult: bool = False) -> Dict[str, Any]:
        res = await cls.post_query(ANIME_QUERY, {"search": search, "page": page, "perPage": per_page, "isAdult": is_adult})
        return res.get("data", {}).get("Page", {})

    @classmethod
    async def search_manga(cls, search: str, page: int = 1, per_page: int = 5, is_adult: bool = False) -> Dict[str, Any]:
        res = await cls.post_query(MANGA_QUERY, {"search": search, "page": page, "perPage": per_page, "isAdult": is_adult})
        return res.get("data", {}).get("Page", {})

    @classmethod
    async def search_character(cls, search: str, page: int = 1, per_page: int = 5) -> Dict[str, Any]:
        res = await cls.post_query(CHARACTER_QUERY, {"search": search, "page": page, "perPage": per_page})
        return res.get("data", {}).get("Page", {})

    @classmethod
    async def search_studio(cls, search: str, page: int = 1, per_page: int = 5) -> Dict[str, Any]:
        res = await cls.post_query(STUDIO_QUERY, {"search": search, "page": page, "perPage": per_page})
        return res.get("data", {}).get("Page", {})

    @classmethod
    async def get_trending(cls, page: int = 1, per_page: int = 10, is_adult: bool = False) -> List[Dict[str, Any]]:
        res = await cls.post_query(TRENDING_QUERY, {"page": page, "perPage": per_page, "isAdult": is_adult})
        return res.get("data", {}).get("Page", {}).get("media", [])

    @classmethod
    async def get_airing_schedule(cls, page: int = 1, per_page: int = 10) -> List[Dict[str, Any]]:
        res = await cls.post_query(SCHEDULE_QUERY, {"page": page, "perPage": per_page})
        return res.get("data", {}).get("Page", {}).get("airingSchedules", [])

