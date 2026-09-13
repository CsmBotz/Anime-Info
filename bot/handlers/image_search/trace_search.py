from pyrogram import Client, filters
from pyrogram.types import Message
from bot.fetchers.tracemoe import TraceMoeFetcher
from bot.utils.decorators import cooldown
from bot.utils.formatting import escape_html

def register_image_search_handlers(app: Client):
    @app.on_message(filters.photo | (filters.reply & filters.command(["find", "whatanime"])))
    @cooldown(seconds=10)
    async def image_search_cmd(client: Client, message: Message):
        photo = message.photo
        if not photo and message.reply_to_message and message.reply_to_message.photo:
            photo = message.reply_to_message.photo

        if not photo:
            return

        status_msg = await message.reply_text("› Searching trace.moe database...")
        try:
            file_bytes = await client.download_media(photo.file_id, in_memory=True)
            res = await TraceMoeFetcher.search_by_image_bytes(file_bytes.getvalue())
            results = res.get("result", [])
            if not results:
                await status_msg.edit_text("[-] No matching anime scene identified.")
                return

            top = results[0]
            anilist = top.get("anilist", {})
            title = anilist.get("title", {}).get("english") or anilist.get("title", {}).get("romaji") or "Unknown Anime"
            episode = top.get("episode", "?")
            similarity = round(top.get("similarity", 0) * 100, 1)
            from_sec = int(top.get("from", 0))
            minutes = from_sec // 60
            seconds = from_sec % 60

            text = (
                f"<b>Match Identified: {escape_html(title)}</b>\n"
                f"• Episode: <b>{episode}</b>\n"
                f"• Timestamp: <b>{minutes:02d}:{seconds:02d}</b>\n"
                f"• Similarity: <b>{similarity}%</b>"
            )
            await status_msg.edit_text(text)
        except Exception as e:
            await status_msg.edit_text(f"[!] Failed to search image: {escape_html(str(e))}")
