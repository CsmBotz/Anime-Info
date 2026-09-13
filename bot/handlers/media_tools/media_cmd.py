from pyrogram import Client, filters
from pyrogram.types import Message
from bot.media.ffmpeg_utils import (
    MEDIA_SEMAPHORE, get_tmp_path, cleanup_file, run_ffprobe,
    get_media_duration, merge_video_intro, trim_media
)
from bot.utils.decorators import cooldown
from bot.utils.logging import get_logger

logger = get_logger(__name__)

def register_media_tools_handlers(app: Client):

    @app.on_message(filters.command("merge_video"))
    @cooldown(seconds=15)
    async def merge_video_cmd(client: Client, message: Message):
        if not message.reply_to_message or not (message.reply_to_message.video or message.reply_to_message.document):
            await message.reply_text(
                "<b>Merge Video</b>\n"
                "Reply to a video file with <code>/merge_video</code> to attach an intro clip."
            )
            return

        status_msg = await message.reply_text("› Queued request, checking server availability...")
        
        main_path = None
        intro_path = None
        output_path = None

        async with MEDIA_SEMAPHORE:
            await status_msg.edit_text("› Downloading media file...")
            try:
                main_path = get_tmp_path("mp4")
                intro_path = get_tmp_path("mp4")
                output_path = get_tmp_path("mp4")

                await client.download_media(message.reply_to_message, file_name=main_path)
                
                valid, probe_info = await run_ffprobe(main_path)
                if not valid:
                    await status_msg.edit_text(f"[!] Unsupported media format: {probe_info}")
                    return

                await status_msg.edit_text("› Merging video via ffmpeg...")
                intro_path = main_path
                
                success, res_path = await merge_video_intro(main_path, intro_path, output_path)
                if success:
                    await status_msg.edit_text("› Uploading processed video...")
                    await message.reply_video(video=output_path, caption="✓ Video merged successfully.")
                    await status_msg.delete()
                else:
                    await status_msg.edit_text(f"[!] Processing failed: {res_path}")

            except Exception as e:
                logger.error(f"Error during video merge: {e}")
                await status_msg.edit_text("[!] An unexpected error occurred while processing the video.")
            finally:
                cleanup_file(main_path)
                cleanup_file(intro_path)
                cleanup_file(output_path)

    @app.on_message(filters.command(["remove_intro", "skip_intro"]))
    @cooldown(seconds=15)
    async def remove_intro_cmd(client: Client, message: Message):
        if not message.reply_to_message or not (message.reply_to_message.video or message.reply_to_message.document):
            await message.reply_text(
                "<b>Remove Intro</b>\n"
                "Reply to an anime video with <code>/remove_intro [seconds]</code>\n"
                "• Default: 90 seconds (standard anime OP)\n"
                "• Example: <code>/remove_intro 85</code>"
            )
            return

        # Parse custom seconds if provided, default to 90s
        seconds = 90.0
        if len(message.command) > 1:
            try:
                seconds = float(message.command[1])
            except ValueError:
                seconds = 90.0

        status_msg = await message.reply_text(f"› Queued: Removing {int(seconds)}s intro...")
        input_path = None
        output_path = None

        async with MEDIA_SEMAPHORE:
            await status_msg.edit_text("› Downloading video...")
            try:
                input_path = get_tmp_path("mp4")
                output_path = get_tmp_path("mp4")

                await client.download_media(message.reply_to_message, file_name=input_path)
                total_duration = await get_media_duration(input_path)

                if total_duration and seconds >= total_duration:
                    await status_msg.edit_text(f"[!] Requested cut ({int(seconds)}s) is longer than video duration ({int(total_duration)}s).")
                    return

                await status_msg.edit_text(f"› Trimming first {int(seconds)}s...")
                success, res = await trim_media(input_path, output_path, start_seconds=seconds)
                if success:
                    await status_msg.edit_text("› Uploading trimmed video...")
                    await message.reply_video(video=output_path, caption=f"✓ Intro removed ({int(seconds)}s cut).")
                    await status_msg.delete()
                else:
                    await status_msg.edit_text(f"[!] Trim failed: {res}")
            except Exception as e:
                logger.error(f"Error removing intro: {e}")
                await status_msg.edit_text("[!] Failed to process video.")
            finally:
                cleanup_file(input_path)
                cleanup_file(output_path)

    @app.on_message(filters.command(["remove_outro", "skip_outro"]))
    @cooldown(seconds=15)
    async def remove_outro_cmd(client: Client, message: Message):
        if not message.reply_to_message or not (message.reply_to_message.video or message.reply_to_message.document):
            await message.reply_text(
                "<b>Remove Outro</b>\n"
                "Reply to an anime video with <code>/remove_outro [seconds]</code>\n"
                "• Default: 90 seconds (standard anime ED)\n"
                "• Example: <code>/remove_outro 90</code>"
            )
            return

        outro_seconds = 90.0
        if len(message.command) > 1:
            try:
                outro_seconds = float(message.command[1])
            except ValueError:
                outro_seconds = 90.0

        status_msg = await message.reply_text(f"› Queued: Removing last {int(outro_seconds)}s outro...")
        input_path = None
        output_path = None

        async with MEDIA_SEMAPHORE:
            await status_msg.edit_text("› Downloading video...")
            try:
                input_path = get_tmp_path("mp4")
                output_path = get_tmp_path("mp4")

                await client.download_media(message.reply_to_message, file_name=input_path)
                total_duration = await get_media_duration(input_path)

                if not total_duration or total_duration <= outro_seconds:
                    await status_msg.edit_text("[!] Could not determine valid video duration for outro cut.")
                    return

                target_duration = total_duration - outro_seconds
                await status_msg.edit_text(f"› Trimming video to {int(target_duration)}s...")
                success, res = await trim_media(input_path, output_path, start_seconds=0.0, duration_seconds=target_duration)
                if success:
                    await status_msg.edit_text("› Uploading trimmed video...")
                    await message.reply_video(video=output_path, caption=f"✓ Outro removed ({int(outro_seconds)}s cut from end).")
                    await status_msg.delete()
                else:
                    await status_msg.edit_text(f"[!] Trim failed: {res}")
            except Exception as e:
                logger.error(f"Error removing outro: {e}")
                await status_msg.edit_text("[!] Failed to process video.")
            finally:
                cleanup_file(input_path)
                cleanup_file(output_path)
