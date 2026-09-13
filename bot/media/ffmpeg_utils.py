import asyncio
import os
import shutil
import uuid
from typing import Tuple
from bot.utils.logging import get_logger

logger = get_logger(__name__)

MEDIA_TMP_DIR = os.path.join(os.path.dirname(__file__), "tmp")
os.makedirs(MEDIA_TMP_DIR, exist_ok=True)

# Max 2 concurrent jobs
MEDIA_SEMAPHORE = asyncio.Semaphore(2)

def sanitize_filename(ext: str) -> str:
    # Always generate safe random filename
    ext = ext.lstrip(".").lower()
    return f"{uuid.uuid4().hex}.{ext}"

def get_tmp_path(ext: str) -> str:
    return os.path.join(MEDIA_TMP_DIR, sanitize_filename(ext))

def cleanup_file(path: str):
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except Exception as e:
            logger.warning(f"Failed to remove tmp file {path}: {e}")

async def run_ffprobe(file_path: str) -> Tuple[bool, str]:
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration,format_name",
        "-of", "default=noprint_wrappers=1",
        file_path
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            return True, stdout.decode().strip()
        return False, stderr.decode().strip()
    except Exception as e:
        return False, str(e)

async def merge_video_intro(main_path: str, intro_path: str, output_path: str, timeout: int = 120) -> Tuple[bool, str]:
    # Use concat filter or concat demuxer via ffmpeg subprocess
    cmd = [
        "ffmpeg",
        "-y",
        "-i", intro_path,
        "-i", main_path,
        "-filter_complex", "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]",
        "-map", "[v]",
        "-map", "[a]",
        output_path
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            if proc.returncode == 0 and os.path.exists(output_path):
                return True, output_path
            return False, stderr.decode().strip()
        except asyncio.TimeoutError:
            proc.kill()
            return False, "FFmpeg process timed out."
    except Exception as e:
        return False, str(e)

