from pyrogram import Client, filters
from pyrogram.types import Message
from bot.db.users_repo import UsersRepo

def register_deleteme_handler(app: Client):
    @app.on_message(filters.command("deleteme"))
    async def deleteme_cmd(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else None
        if not user_id:
            return
        success = await UsersRepo.delete_user_data(user_id)
        if success:
            await message.reply_text("🗑️ All your data (watchlist, favorites, settings) has been completely deleted from our database.")
        else:
            await message.reply_text("❌ Failed to delete data or no data found.")

