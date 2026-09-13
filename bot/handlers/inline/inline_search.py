from pyrogram import Client
from pyrogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from bot.fetchers.anilist import AniListFetcher
from bot.utils.formatting import format_anime_card, clean_synopsis

def register_inline_handlers(app: Client):
    @app.on_inline_query()
    async def inline_search(client: Client, inline_query: InlineQuery):
        query = inline_query.query.strip()
        
        if not query:
            # Show trending titles on empty query
            media_list = await AniListFetcher.get_trending(page=1, per_page=10)
        else:
            data = await AniListFetcher.search_anime(query, page=1, per_page=10)
            media_list = data.get("media", [])

        results = []
        for item in media_list:
            title = item.get("title", {}).get("english") or item.get("title", {}).get("romaji") or "Unknown"
            synopsis = clean_synopsis(item.get("description"), limit=150)
            cover = item.get("coverImage", {}).get("large")
            anime_id = item.get("id")

            card_text = format_anime_card(
                title=title,
                status=item.get("status"),
                score=item.get("averageScore"),
                synopsis=item.get("description"),
                site_url=item.get("siteUrl")
            )

            markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("➕ Watchlist", callback_data=f"wl_add:{anime_id}"),
                    InlineKeyboardButton("⭐ Favorite", callback_data=f"fav_add:{anime_id}")
                ]
            ])

            results.append(
                InlineQueryResultArticle(
                    id=str(anime_id),
                    title=title,
                    description=f"Status: {item.get('status')} | Score: {item.get('averageScore')}\n{synopsis}",
                    thumb_url=cover,
                    input_message_content=InputTextMessageContent(card_text, parse_mode="html"),
                    reply_markup=markup
                )
            )

        await inline_query.answer(results, cache_time=300)

