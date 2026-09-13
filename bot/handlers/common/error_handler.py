import uuid
from pyrogram import Client
from pyrogram.types import Message
from bot.utils.logging import get_logger

logger = get_logger(__name__)

async def global_error_handler(client: Client, message: Message, exception: Exception):
    correlation_id = str(uuid.uuid4())[:8]
    logger.error(f"Error handling message {message.id}: {exception}", extra={"correlation_id": correlation_id}, exc_info=True)
    user_text = f"❌ An unexpected error occurred. (Ref ID: <code>{correlation_id}</code>)"
    try:
        await message.reply_text(user_text)
    except Exception as e:
        logger.error(f"Failed to send error message to user: {e}")

