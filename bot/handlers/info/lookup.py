from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot.fetchers.anilist import AniListFetcher
from bot.fetchers.filler_list import FillerFetcher
from bot.utils.formatting import format_anime_card, escape_html, clean_synopsis

def register_info_handlers(app: Client):
    @app.on_message(filters.command("anime"))
    async def anime_cmd(client: Client, message: Message):
        if len(message.command) < 2:
            await message.reply_text("Please provide an anime title. Usage: <code>/anime Naruto</code>")
            return
        query = " ".join(message.command[1:])
        data = await AniListFetcher.search_anime(query, page=1, per_page=5)
        media_list = data.get("media", [])
        if not media_list:
            await message.reply_text("❌ No anime found for that query.")
            return

        item = media_list[0]
        title = item.get("title", {}).get("english") or item.get("title", {}).get("romaji") or "Unknown"
        text = format_anime_card(
            title=title,
            status=item.get("status"),
            score=item.get("averageScore"),
            synopsis=item.get("description"),
            site_url=item.get("siteUrl")
        )
        
        anime_id = item.get("id")
        buttons = [
            [
                InlineKeyboardButton("➕ Watchlist", callback_data=f"wl_add:{anime_id}"),
                InlineKeyboardButton("⭐ Favorite", callback_data=f"fav_add:{anime_id}")
            ]
        ]
        if len(media_list) > 1:
            buttons.append([InlineKeyboardButton("▶ Next Result", callback_data=f"anime_page:{query}:2")])

        markup = InlineKeyboardMarkup(buttons)
        cover = item.get("coverImage", {}).get("large")
        if cover:
            await message.reply_photo(photo=cover, caption=text, reply_markup=markup)
        else:
            await message.reply_text(text, reply_markup=markup)

    @app.on_message(filters.command("manga"))
    async def manga_cmd(client: Client, message: Message):
        if len(message.command) < 2:
            await message.reply_text("Please provide a manga title. Usage: <code>/manga Berserk</code>")
            return
        query = " ".join(message.command[1:])
        data = await AniListFetcher.search_manga(query, page=1, per_page=5)
        media_list = data.get("media", [])
        if not media_list:
            await message.reply_text("❌ No manga found for that query.")
            return

        item = media_list[0]
        title = item.get("title", {}).get("english") or item.get("title", {}).get("romaji") or "Unknown"
        text = format_anime_card(
            title=title,
            status=item.get("status"),
            score=item.get("averageScore"),
            synopsis=item.get("description"),
            site_url=item.get("siteUrl")
        )
        cover = item.get("coverImage", {}).get("large")
        if cover:
            await message.reply_photo(photo=cover, caption=text)
        else:
            await message.reply_text(text)

    @app.on_message(filters.command("character"))
    async def character_cmd(client: Client, message: Message):
        if len(message.command) < 2:
            await message.reply_text("Usage: <code>/character Gojo</code>")
            return
        query = " ".join(message.command[1:])
        data = await AniListFetcher.search_character(query, page=1, per_page=1)
        chars = data.get("mediaCharacters", [])
        if not chars:
            await message.reply_text("❌ Character not found.")
            return

        c = chars[0]
        name = c.get("name", {}).get("full")
        text = f"<b>{escape_html(name)}</b>\n\n<i>{clean_synopsis(c.get('description'))}</i>"
        image = c.get("image", {}).get("large")
        if image:
            await message.reply_photo(photo=image, caption=text)
        else:
            await message.reply_text(text)

    @app.on_message(filters.command("studio"))
    async def studio_cmd(client: Client, message: Message):
        if len(message.command) < 2:
            await message.reply_text("Usage: <code>/studio Mappa</code>")
            return
        query = " ".join(message.command[1:])
        data = await AniListFetcher.search_studio(query, page=1, per_page=5)
        studios = data.get("studios", [])
        if not studios:
            await message.reply_text("❌ Studio not found.")
            return

        s = studios[0]
        text = f"<b>Studio: {escape_html(s.get('name'))}</b>\n"
        if s.get("siteUrl"):
            text += f'<a href="{escape_html(s.get("siteUrl"))}">Official Page</a>'
        await message.reply_text(text)

    @app.on_message(filters.command("schedule"))
    async def schedule_cmd(client: Client, message: Message):
        schedules = await AniListFetcher.get_airing_schedule(page=1, per_page=5)
        if not schedules:
            await message.reply_text("No upcoming airing schedule found.")
            return

        text = "<b>📅 Upcoming Airing Episodes:</b>\n\n"
        for item in schedules:
            media = item.get("media", {})
            title = media.get("title", {}).get("english") or media.get("title", {}).get("romaji") or "Unknown"
            ep = item.get("episode")
            text += f"• <b>{escape_html(title)}</b> - Episode {ep}\n"
        await message.reply_text(text)

    @app.on_message(filters.command("filler"))
    async def filler_cmd(client: Client, message: Message):
        if len(message.command) < 2:
            await message.reply_text("Usage: <code>/filler Naruto</code>")
            return
        query = " ".join(message.command[1:])
        info = FillerFetcher.get_filler_info(query)
        if not info:
            await message.reply_text("❌ No filler data found for that show. (Available: Naruto, Bleach, One Piece)")
            return

        text = f"<b>{escape_html(info['title'])} Filler Breakdown:</b>\n"
        text += f"<b>Total Episodes:</b> {info['total_episodes']}\n"
        text += f"<b>Filler Percentage:</b> {info['filler_percentage']}\n\n"
        text += f"<b>Filler Episodes:</b> {info['filler_episodes'][:15]}..."
        await message.reply_text(text)

