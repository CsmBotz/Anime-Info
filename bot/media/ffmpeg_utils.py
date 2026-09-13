import asyncio
import os
import re
import uuid
from typing import Tuple, Optional
from bot.utils.logging import get_logger

logger = get_logger(__name__)

MEDIA_TMP_DIR = os.path.join(os.path.dirname(__file__), "tmp")
os.makedirs(MEDIA_TMP_DIR, exist_ok=True)

# Concurrency semaphore (max 2 jobs)
MEDIA_SEMAPHORE = asyncio.Semaphore(2)

def sanitize_filename(ext: str) -> str:
    ext = ext.lstrip(".").lower()
    return f"{uuid.uuid4().hex}.{ext}"

def get_tmp_path(ext: str) -> str:
    return os.path.join(MEDIA_TMP_DIR, sanitize_filename(ext))

def cleanup_file(path: Optional[str]):
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except Exception as e:
            logger.warning(f"Failed to remove temporary file {path}: {e}")

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

async def get_media_duration(file_path: str) -> Optional[float]:
    valid, info = await run_ffprobe(file_path)
    if not valid:
        return None
    match = re.search(r"duration=([\d\.]+)", info)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None

async def merge_video_intro(main_path: str, intro_path: str, output_path: str, timeout: int = 120) -> Tuple[bool, str]:
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

async def trim_media(
    input_path: str,
    output_path: str,
    start_seconds: float = 0.0,
    duration_seconds: Optional[float] = None,
    timeout: int = 120
) -> Tuple[bool, str]:
    """Trim a media file by skipping start_seconds or capping duration."""
    cmd = ["ffmpeg", "-y", "-ss", str(start_seconds), "-i", input_path]
    if duration_seconds is not None and duration_seconds > 0:
        cmd.extend(["-t", str(duration_seconds)])
    cmd.extend(["-c", "copy", output_path])

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
            # If stream copy fails due to codec keyframes, fallback to re-encoding
            reencode_cmd = ["ffmpeg", "-y", "-ss", str(start_seconds), "-i", input_path]
            if duration_seconds is not None and duration_seconds > 0:
                reencode_cmd.extend(["-t", str(duration_seconds)])
            reencode_cmd.append(output_path)
            proc2 = await asyncio.create_subprocess_exec(*reencode_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            s2, e2 = await asyncio.wait_for(proc2.communicate(), timeout=timeout)
            if proc2.returncode == 0 and os.path.exists(output_path):
                return True, output_path
            return False, e2.decode().strip()
        except asyncio.TimeoutError:
            proc.kill()
            return False, "FFmpeg process timed out."
    except Exception as e:
        return False, str(e)
