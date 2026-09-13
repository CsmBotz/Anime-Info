import time
from functools import wraps
from pyrogram.types import Message
from bot.utils.logging import get_logger

logger = get_logger(__name__)

def cooldown(seconds: int = 5):
    user_cooldowns = {}

    def decorator(func):
        @wraps(func)
        async def wrapper(client, message: Message, *args, **kwargs):
            user_id = message.from_user.id if message.from_user else None
            if user_id:
                now = time.time()
                last_time = user_cooldowns.get(user_id, 0)
                elapsed = now - last_time
                if elapsed < seconds:
                    wait_time = int(seconds - elapsed)
                    await message.reply_text(f"⏳ Please wait {wait_time}s before using this command again.")
                    return
                user_cooldowns[user_id] = now
            return await func(client, message, *args, **kwargs)
        return wrapper
    return decorator

