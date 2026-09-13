from pyrogram import Client, filters
from pyrogram.types import Message
from bot.media.ffmpeg_utils import (
    MEDIA_SEMAPHORE, get_tmp_path, cleanup_file, run_ffprobe, merge_video_intro
)
from bot.utils.decorators import cooldown
from bot.utils.logging import get_logger

logger = get_logger(__name__)

def register_media_tools_handlers(app: Client):
    @app.on_message(filters.command("merge_video"))
    @cooldown(seconds=15)
    async def merge_video_cmd(client: Client, message: Message):
        if not message.reply_to_message or not (message.reply_to_message.video or message.reply_to_message.document):
            await message.reply_text("Please reply to a video message with <code>/merge_video</code> and attach/link an intro video.")
            return

        status_msg = await message.reply_text("⏳ Request queued... checking server load.")
        
        main_path = None
        intro_path = None
        output_path = None

        async with MEDIA_SEMAPHORE:
            await status_msg.edit_text("📥 Downloading video files...")
            try:
                main_path = get_tmp_path("mp4")
                intro_path = get_tmp_path("mp4")
                output_path = get_tmp_path("mp4")

                await client.download_media(message.reply_to_message, file_name=main_path)
                
                # Check video format with ffprobe
                valid, probe_info = await run_ffprobe(main_path)
                if not valid:
                    await status_msg.edit_text(f"❌ Invalid or unsupported video format: {probe_info}")
                    cleanup_file(main_path)
                    cleanup_file(intro_path)
                    cleanup_file(output_path)
                    return

                await status_msg.edit_text("⚙️ Merging video with intro via ffmpeg...")
                # For demo purposes, duplicate main_path as intro if no separate intro provided
                intro_path = main_path
                
                success, res_path = await merge_video_intro(main_path, intro_path, output_path)
                if success:
                    await status_msg.edit_text("📤 Uploading merged video...")
                    await message.reply_video(video=output_path, caption="✅ Merged video successfully!")
                    await status_msg.delete()
                else:
                    await status_msg.edit_text(f"❌ Video merge failed: {res_path}")

            except Exception as e:
                logger.error(f"Error during video merge: {e}")
                await status_msg.edit_text("❌ An error occurred while processing the video.")
            finally:
                cleanup_file(main_path)
                cleanup_file(intro_path)
                cleanup_file(output_path)

