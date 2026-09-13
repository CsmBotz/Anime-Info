from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from bot.config import WEBAPP_URL
from bot.db.users_repo import UsersRepo

HELP_TEXT = """
<b>Anime Info Bot Commands:</b>

<b>🔍 Information Lookup:</b>
• /anime <code>&lt;query&gt;</code> - Search anime on AniList
• /manga <code>&lt;query&gt;</code> - Search manga on AniList
• /character <code>&lt;query&gt;</code> - Search characters
• /studio <code>&lt;query&gt;</code> - Search studios
• /schedule - View upcoming airing schedule
• /filler <code>&lt;anime&gt;</code> - Check filler episode breakdown

<b>📌 Watchlist & Progress Tracker:</b>
• /watchlist - View your watchlist (paginated)
• /favorites - View your favorite titles
• /deleteme - Delete all your data from our database

<b>🎥 Media Tools:</b>
• Send a photo to search via trace.moe
• /merge_video - Merge video with intro/outro
"""

def register_start_help_handlers(app: Client):
    @app.on_message(filters.command("start"))
    async def start_cmd(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else None
        if user_id:
            await UsersRepo.ensure_user(user_id, message.from_user.username)
        
        reply_markup = None
        if WEBAPP_URL:
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Open Mini App", web_app=WebAppInfo(url=WEBAPP_URL))]
            ])
            
        welcome_text = (
            f"👋 Hello {message.from_user.first_name if message.from_user else 'there'}!\n\n"
            "Welcome to <b>Anime Info Bot</b>! Search anime, manga, track your watchlist, or open the Mini App."
        )
        await message.reply_text(welcome_text, reply_markup=reply_markup)

    @app.on_message(filters.command("help"))
    async def help_cmd(client: Client, message: Message):
        await message.reply_text(HELP_TEXT)

