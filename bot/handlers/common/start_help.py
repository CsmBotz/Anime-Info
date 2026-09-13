from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from bot.config import WEBAPP_URL
from bot.db.users_repo import UsersRepo

HELP_TEXT = """
<b>Anime Info Bot — Command Reference</b>

<b>Information & Lookup:</b>
• /anime <code>&lt;title&gt;</code> — Search anime details & episodes
• /manga <code>&lt;title&gt;</code> — Search manga information
• /character <code>&lt;name&gt;</code> — Search anime characters
• /studio <code>&lt;name&gt;</code> — Search animation studios
• /schedule — View upcoming broadcast schedule
• /filler <code>&lt;anime&gt;</code> — View filler vs canon episode guide

<b>Watchlist & Progress:</b>
• /watchlist — View and manage your watchlist
• /favorites — View your saved favorites
• /deleteme — Purge your stored data

<b>Media Utilities:</b>
• /remove_intro — Remove OP intro (reply to a video)
• /remove_outro — Remove ED outro (reply to a video)
• /merge_video — Merge video with custom intro clip
• Send or reply with an image to identify an anime scene via trace.moe
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
                [InlineKeyboardButton("› Launch Mini App", web_app=WebAppInfo(url=WEBAPP_URL))]
            ])
            
        welcome_text = (
            f"Hello {message.from_user.first_name if message.from_user else 'there'},\n\n"
            "Welcome to <b>Anime Info Bot</b>. You can look up anime, manage your watchlist, "
            "browse airing schedules, or open the Mini App below."
        )
        await message.reply_text(welcome_text, reply_markup=reply_markup)

    @app.on_message(filters.command("help"))
    async def help_cmd(client: Client, message: Message):
        await message.reply_text(HELP_TEXT)
