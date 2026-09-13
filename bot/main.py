import asyncio
import sys
from pyrogram import Client
from pyrogram.types import BotCommand
from bot.config import API_ID, API_HASH, BOT_TOKEN, validate_config
from bot.db.clients import db_clients
from bot.utils.logging import get_logger

from bot.handlers.common.start_help import register_start_help_handlers
from bot.handlers.common.deleteme import register_deleteme_handler
from bot.handlers.info.lookup import register_info_handlers
from bot.handlers.inline.inline_search import register_inline_handlers
from bot.handlers.watchlist.watchlist_cmd import register_watchlist_handlers
from bot.handlers.image_search.trace_search import register_image_search_handlers
from bot.handlers.media_tools.media_cmd import register_media_tools_handlers

logger = get_logger(__name__)

def create_app() -> Client:
    if not validate_config():
        sys.exit(1)
    
    app = Client(
        "anime_info_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN
    )

    # Register handlers
    register_start_help_handlers(app)
    register_deleteme_handler(app)
    register_info_handlers(app)
    register_inline_handlers(app)
    register_watchlist_handlers(app)
    register_image_search_handlers(app)
    register_media_tools_handlers(app)

    return app

async def set_bot_commands(app: Client):
    commands = [
        BotCommand("start", "Start the bot & open Mini App"),
        BotCommand("help", "Show available commands & help"),
        BotCommand("anime", "Search anime on AniList"),
        BotCommand("manga", "Search manga on AniList"),
        BotCommand("character", "Search anime characters"),
        BotCommand("studio", "Search animation studios"),
        BotCommand("schedule", "View upcoming anime airing schedule"),
        BotCommand("filler", "Check filler episode breakdown"),
        BotCommand("watchlist", "View & edit your anime watchlist"),
        BotCommand("favorites", "View your favorite anime list"),
        BotCommand("merge_video", "Merge intro with video file"),
        BotCommand("deleteme", "Delete all your user data")
    ]
    try:
        await app.set_bot_commands(commands)
        logger.info("BotFather command list updated successfully.")
    except Exception as e:
        logger.warning(f"Failed to set bot commands: {e}")

async def main():
    logger.info("Starting Anime Info Bot...")
    await db_clients.init_clients()
    app = create_app()
    
    async with app:
        await set_bot_commands(app)
        logger.info("Anime Info Bot is live and listening for messages!")
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

