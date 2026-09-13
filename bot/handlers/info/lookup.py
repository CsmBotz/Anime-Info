import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot.fetchers.anilist import AniListFetcher
from bot.fetchers.filler_list import FillerFetcher
from bot.utils.formatting import format_anime_card, escape_html, clean_synopsis

def _title(item: dict) -> str:
    return item.get("title", {}).get("english") or item.get("title", {}).get("romaji") or "Unknown"

def _cover(item: dict) -> str:
    return item.get("coverImage", {}).get("large") or ""

def _build_anime_buttons(anime_id: int, query: str = "", page: int = 1, has_next: bool = False) -> list:
    buttons = [
        [
            InlineKeyboardButton("➕ Watchlist", callback_data=f"wl_add:{anime_id}"),
            InlineKeyboardButton("⭐ Favorite",  callback_data=f"fav_add:{anime_id}")
        ]
    ]
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("◀ Prev", callback_data=f"anime_page:{query}:{page-1}"))
    if has_next:
        nav.append(InlineKeyboardButton("▶ Next", callback_data=f"anime_page:{query}:{page+1}"))
    if nav:
        buttons.append(nav)
    return buttons

def register_info_handlers(app: Client):

    # ── /anime ──────────────────────────────────────
    @app.on_message(filters.command("anime"))
    async def anime_cmd(client: Client, message: Message):
        if len(message.command) < 2:
            await message.reply_text("Usage: <code>/anime Naruto</code>")
            return
        query = " ".join(message.command[1:])
        msg = await message.reply_text("🔍 Searching...")
        data = await AniListFetcher.search_anime(query, page=1, per_page=5)
        media_list = data.get("media", [])
        if not media_list:
            await msg.edit_text("❌ No anime found for that query. Try a different spelling.")
            return

        item = media_list[0]
        text = format_anime_card(_title(item), item.get("status"), item.get("averageScore"), item.get("description"), item.get("siteUrl"))
        has_next = len(media_list) > 1
        markup = InlineKeyboardMarkup(_build_anime_buttons(item["id"], query, 1, has_next))
        cover = _cover(item)
        await msg.delete()
        if cover:
            await message.reply_photo(photo=cover, caption=text, reply_markup=markup)
        else:
            await message.reply_text(text, reply_markup=markup)

    # Pagination callback for /anime
    @app.on_callback_query(filters.regex(r"^anime_page:(.+):(\d+)$"))
    async def anime_page_cb(client: Client, cb: CallbackQuery):
        match = cb.data.split(":", 2)
        query = match[1]
        page = int(match[2])
        data = await AniListFetcher.search_anime(query, page=page, per_page=5)
        media_list = data.get("media", [])
        page_info = data.get("pageInfo", {})
        if not media_list:
            await cb.answer("No more results.", show_alert=True)
            return
        item = media_list[0]
        text = format_anime_card(_title(item), item.get("status"), item.get("averageScore"), item.get("description"), item.get("siteUrl"))
        has_next = page_info.get("hasNextPage", False) or len(media_list) > 1
        markup = InlineKeyboardMarkup(_build_anime_buttons(item["id"], query, page, has_next))
        cover = _cover(item)
        try:
            if cover:
                await cb.message.edit_media(
                    media={"_": "InputMediaPhoto", "media": cover, "caption": text, "parse_mode": "html"},
                    reply_markup=markup
                )
            else:
                await cb.message.edit_text(text, reply_markup=markup)
        except Exception:
            await cb.answer("Result updated.", show_alert=False)

    # ── /manga ──────────────────────────────────────
    @app.on_message(filters.command("manga"))
    async def manga_cmd(client: Client, message: Message):
        if len(message.command) < 2:
            await message.reply_text("Usage: <code>/manga Berserk</code>")
            return
        query = " ".join(message.command[1:])
        msg = await message.reply_text("🔍 Searching...")
        data = await AniListFetcher.search_manga(query, page=1, per_page=5)
        media_list = data.get("media", [])
        if not media_list:
            await msg.edit_text("❌ No manga found. Try a different title.")
            return
        item = media_list[0]
        text = format_anime_card(_title(item), item.get("status"), item.get("averageScore"), item.get("description"), item.get("siteUrl"))
        cover = _cover(item)
        await msg.delete()
        if cover:
            await message.reply_photo(photo=cover, caption=text)
        else:
            await message.reply_text(text)

    # ── /character ──────────────────────────────────
    @app.on_message(filters.command("character"))
    async def character_cmd(client: Client, message: Message):
        if len(message.command) < 2:
            await message.reply_text("Usage: <code>/character Gojo Satoru</code>")
            return
        query = " ".join(message.command[1:])
        msg = await message.reply_text("🔍 Searching...")
        data = await AniListFetcher.search_character(query, page=1, per_page=1)
        # AniList returns key "mediaCharacters" in our query
        chars = data.get("mediaCharacters") or data.get("characters") or []
        if not chars:
            await msg.edit_text("❌ Character not found.")
            return
        c = chars[0]
        name = c.get("name", {}).get("full") or "Unknown"
        desc = clean_synopsis(c.get("description") or "No description available.", limit=400)
        text = f"<b>👤 {escape_html(name)}</b>\n\n<i>{desc}</i>"
        image = c.get("image", {}).get("large")
        await msg.delete()
        if image:
            await message.reply_photo(photo=image, caption=text)
        else:
            await message.reply_text(text)

    # ── /studio ──────────────────────────────────────
    @app.on_message(filters.command("studio"))
    async def studio_cmd(client: Client, message: Message):
        if len(message.command) < 2:
            await message.reply_text("Usage: <code>/studio Mappa</code>")
            return
        query = " ".join(message.command[1:])
        msg = await message.reply_text("🔍 Searching...")
        data = await AniListFetcher.search_studio(query, page=1, per_page=5)
        studios = data.get("studios", [])
        if not studios:
            await msg.edit_text("❌ Studio not found.")
            return
        s = studios[0]
        kind = "Animation Studio" if s.get("isAnimationStudio") else "Studio"
        text = f"🎬 <b>{kind}: {escape_html(s.get('name', 'Unknown'))}</b>"
        if s.get("siteUrl"):
            text += f'\n<a href="{escape_html(s["siteUrl"])}">🔗 Official Page</a>'
        await msg.delete()
        await message.reply_text(text)

    # ── /schedule ────────────────────────────────────
    @app.on_message(filters.command("schedule"))
    async def schedule_cmd(client: Client, message: Message):
        msg = await message.reply_text("📅 Fetching airing schedule...")
        schedules = await AniListFetcher.get_airing_schedule(page=1, per_page=10)
        if not schedules:
            await msg.edit_text("No upcoming airing schedule found.")
            return
        text = "<b>📅 Upcoming Airing Episodes:</b>\n\n"
        for item in schedules:
            media = item.get("media", {})
            title = media.get("title", {}).get("english") or media.get("title", {}).get("romaji") or "Unknown"
            ep = item.get("episode", "?")
            airing_at = item.get("airingAt")
            time_str = ""
            if airing_at:
                dt = datetime.datetime.utcfromtimestamp(airing_at)
                time_str = f" — {dt.strftime('%b %d, %H:%M UTC')}"
            text += f"• <b>{escape_html(title)}</b> Ep {ep}{time_str}\n"
        await msg.edit_text(text)

    # ── /filler ──────────────────────────────────────
    @app.on_message(filters.command("filler"))
    async def filler_cmd(client: Client, message: Message):
        if len(message.command) < 2:
            await message.reply_text(
                "Usage: <code>/filler Naruto</code>\n"
                "Fetches real filler data from animefillerlist.com"
            )
            return
        query = " ".join(message.command[1:])
        msg = await message.reply_text(f"⏳ Fetching filler data for <b>{escape_html(query)}</b>...")
        info = await FillerFetcher.get_filler_info(query)
        if not info:
            await msg.edit_text(
                f"❌ No filler data found for <b>{escape_html(query)}</b>.\n\n"
                "Try using the exact English title (e.g. <code>/filler Naruto Shippuden</code>)."
            )
            return

        filler_ranges = FillerFetcher.format_episode_ranges(info.get("filler_episodes", []))
        mixed_ranges  = FillerFetcher.format_episode_ranges(info.get("mixed_episodes", []))

        text = (
            f"<b>📺 {escape_html(info['title'])} — Filler Guide</b>\n\n"
            f"<b>Total Episodes:</b> {info['total_episodes']}\n"
            f"<b>Filler Episodes:</b> {info['filler_count']} ({info['filler_percentage']})\n\n"
            f"<b>🔴 Pure Filler:</b> <code>{filler_ranges}</code>\n"
        )
        if info.get("mixed_episodes"):
            text += f"<b>🟡 Mixed (partial filler):</b> <code>{mixed_ranges}</code>\n"
        text += f'\n<a href="{escape_html(info["source_url"])}">📖 Full List on AnimeFillerList</a>'

        await msg.edit_text(text)
