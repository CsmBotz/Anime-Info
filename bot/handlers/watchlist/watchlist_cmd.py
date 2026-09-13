from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot.db.users_repo import UsersRepo
from bot.utils.formatting import escape_html

def register_watchlist_handlers(app: Client):

    @app.on_message(filters.command("watchlist"))
    async def watchlist_cmd(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else None
        if not user_id:
            return
        items = await UsersRepo.get_watchlist(user_id, skip=0, limit=5)
        if not items:
            await message.reply_text("[-] Your watchlist is currently empty.\nUse /anime &lt;title&gt; to add entries.")
            return

        text = "<b>Your Watchlist</b>\n\n"
        buttons = []
        for idx, item in enumerate(items, start=1):
            title = escape_html(item.get("title", "Unknown"))
            progress = item.get("progress", 0)
            total = item.get("total_episodes", "?")
            anime_id = item.get("anime_id")
            text += f"{idx}. <b>{title}</b> — Ep {progress}/{total}\n"
            buttons.append([
                InlineKeyboardButton(f"+1 Ep ({title[:14]})", callback_data=f"track_inc:{anime_id}"),
                InlineKeyboardButton("[-] Remove", callback_data=f"wl_rem:{anime_id}")
            ])

        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    @app.on_message(filters.command("favorites"))
    async def favorites_cmd(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else None
        if not user_id:
            return
        items = await UsersRepo.get_favorites(user_id, skip=0, limit=10)
        if not items:
            await message.reply_text("[-] No favorites saved yet.\nTap ★ Favorite on any anime card to add it.")
            return

        text = "<b>Favorite Titles</b>\n\n"
        for idx, item in enumerate(items, start=1):
            title = escape_html(item.get("title", "Unknown"))
            text += f"• {idx}. <b>{title}</b>\n"

        await message.reply_text(text)

    @app.on_callback_query(filters.regex(r"^(wl_add|wl_rem|fav_add|track_inc):"))
    async def watchlist_callbacks(client: Client, callback: CallbackQuery):
        user_id = callback.from_user.id
        action, anime_id_str = callback.data.split(":")
        anime_id = int(anime_id_str)

        if action == "wl_add":
            added = await UsersRepo.add_to_watchlist(user_id, anime_id, title=f"Anime #{anime_id}")
            if added:
                await callback.answer("Added to your watchlist.", show_alert=False)
            else:
                await callback.answer("Already in your watchlist.", show_alert=False)

        elif action == "wl_rem":
            removed = await UsersRepo.remove_from_watchlist(user_id, anime_id)
            if removed:
                await callback.answer("Removed from watchlist.", show_alert=False)
                await callback.message.edit_text("✓ Watchlist updated.")
            else:
                await callback.answer("Entry not found.", show_alert=False)

        elif action == "fav_add":
            is_fav = await UsersRepo.toggle_favorite(user_id, anime_id, title=f"Anime #{anime_id}")
            if is_fav:
                await callback.answer("★ Added to favorites.", show_alert=False)
            else:
                await callback.answer("Removed from favorites.", show_alert=False)

        elif action == "track_inc":
            new_prog = await UsersRepo.update_tracker_progress(user_id, anime_id, delta=1)
            if new_prog is not None:
                await callback.answer(f"Progress updated: Episode {new_prog}", show_alert=False)
            else:
                await callback.answer("Title is not in your watchlist.", show_alert=False)
