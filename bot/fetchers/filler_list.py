import re
import httpx
import asyncio
from typing import Optional, Dict, Any, List
from bot.utils.logging import get_logger

logger = get_logger(__name__)

BASE_URL = "https://www.animefillerlist.com/shows"

# Slug map for common search aliases → animefillerlist.com slug
SLUG_MAP = {
    "naruto": "naruto",
    "naruto shippuden": "naruto-shippuden",
    "shippuden": "naruto-shippuden",
    "bleach": "bleach",
    "one piece": "one-piece",
    "fairy tail": "fairy-tail",
    "dragon ball z": "dragon-ball-z",
    "dbz": "dragon-ball-z",
    "dragon ball super": "dragon-ball-super",
    "boruto": "boruto-naruto-next-generations",
    "black clover": "black-clover",
    "detective conan": "detective-conan",
    "case closed": "detective-conan",
    "sword art online": "sword-art-online",
    "sao": "sword-art-online",
    "attack on titan": "attack-on-titan",
    "aot": "attack-on-titan",
    "fullmetal alchemist": "fullmetal-alchemist-brotherhood",
    "fmab": "fullmetal-alchemist-brotherhood",
    "hunter x hunter": "hunter-x-hunter-2011",
    "hxh": "hunter-x-hunter-2011",
    "inuyasha": "inuyasha",
    "yu yu hakusho": "yu-yu-hakusho",
    "yu-gi-oh": "yu-gi-oh-duel-monsters",
    "soul eater": "soul-eater",
    "ao no exorcist": "ao-no-exorcist",
    "blue exorcist": "ao-no-exorcist",
    "d gray man": "d-gray-man",
    "d.gray-man": "d-gray-man",
    "katekyo hitman reborn": "katekyo-hitman-reborn",
    "reborn": "katekyo-hitman-reborn",
    "toriko": "toriko",
    "pokemon": "pokemon",
    "digimon": "digimon-adventure",
    "claymore": "claymore",
    "rurouni kenshin": "rurouni-kenshin",
    "samurai x": "rurouni-kenshin",
    "gintama": "gintama",
}

def _query_to_slug(query: str) -> str:
    q = query.strip().lower()
    # Direct map first
    if q in SLUG_MAP:
        return SLUG_MAP[q]
    # Partial match
    for key, slug in SLUG_MAP.items():
        if key in q or q in key:
            return slug
    # Auto-slugify: lowercase, replace spaces/special chars with -
    slug = re.sub(r"[^a-z0-9]+", "-", q).strip("-")
    return slug

async def _fetch_filler_page(slug: str) -> Optional[str]:
    url = f"{BASE_URL}/{slug}"
    try:
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True, headers={
            "User-Agent": "Mozilla/5.0 (compatible; AnimeInfoBot/1.0)"
        }) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.text
            logger.warning(f"animefillerlist.com returned {resp.status_code} for slug '{slug}'")
            return None
    except Exception as e:
        logger.error(f"Failed to fetch filler page for slug '{slug}': {e}")
        return None

def _parse_filler_page(html: str, title_query: str) -> Optional[Dict[str, Any]]:
    """Parse animefillerlist.com episode table HTML."""
    # Extract show title
    title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
    title = title_match.group(1).strip() if title_match else title_query.title()

    # Extract episode rows: each row has episode number and type (Manga Canon, Filler, Mixed Canon/Filler, etc.)
    # Pattern: <td class="...">1</td> ... <td>Manga Canon</td>
    rows = re.findall(
        r'<tr[^>]*class="[^"]*(?:filler|canon|mixed)[^"]*"[^>]*>.*?</tr>',
        html, re.DOTALL | re.IGNORECASE
    )

    # Fallback: grab all <tr> rows from the episode table
    if not rows:
        table_match = re.search(r'<table[^>]*id="[^"]*EpisodeList[^"]*"[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
        if table_match:
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_match.group(1), re.DOTALL)

    filler_eps = []
    canon_eps = []
    mixed_eps = []
    total = 0

    for row in rows:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
        cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
        if len(cells) < 2:
            continue
        ep_str = cells[0]
        ep_type = cells[-1].lower() if len(cells) >= 2 else ""
        # Episode number might be a range like "1-6"
        ep_range = re.findall(r'\d+', ep_str)
        if not ep_range:
            continue
        ep_nums = list(range(int(ep_range[0]), int(ep_range[-1]) + 1))
        total += len(ep_nums)
        if "filler" in ep_type and "mixed" not in ep_type:
            filler_eps.extend(ep_nums)
        elif "mixed" in ep_type:
            mixed_eps.extend(ep_nums)
        else:
            canon_eps.extend(ep_nums)

    if total == 0:
        return None

    filler_pct = round(len(filler_eps) / total * 100) if total else 0

    return {
        "title": title,
        "total_episodes": total,
        "filler_episodes": sorted(filler_eps),
        "mixed_episodes": sorted(mixed_eps),
        "canon_episodes": sorted(canon_eps),
        "filler_count": len(filler_eps),
        "filler_percentage": f"{filler_pct}%",
        "source_url": f"{BASE_URL}/{_query_to_slug(title_query)}"
    }

class FillerFetcher:
    @staticmethod
    async def get_filler_info(query: str) -> Optional[Dict[str, Any]]:
        slug = _query_to_slug(query)
        html = await _fetch_filler_page(slug)
        if not html:
            return None
        result = _parse_filler_page(html, query)
        return result

    @staticmethod
    def format_episode_ranges(episodes: List[int]) -> str:
        """Convert flat list to compact range string: [1,2,3,7,8] → '1-3, 7-8'."""
        if not episodes:
            return "None"
        eps = sorted(set(episodes))
        ranges = []
        start = end = eps[0]
        for ep in eps[1:]:
            if ep == end + 1:
                end = ep
            else:
                ranges.append(f"{start}" if start == end else f"{start}-{end}")
                start = end = ep
        ranges.append(f"{start}" if start == end else f"{start}-{end}")
        return ", ".join(ranges)
