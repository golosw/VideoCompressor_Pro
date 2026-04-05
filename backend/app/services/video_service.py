import asyncio
import json
import os
import uuid
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import CompressionError, UnsupportedFormatError
from app.core.logging import logger
from app.models.schemas import (
    CompressionJob,
    CompressionSettings,
    VideoCodec,
    VideoMetadata,
)

SUPPORTED_FORMATS = {
    ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv",
    ".webm", ".m4v", ".mpeg", ".mpg", ".3gp",
}

_jobs: dict[str, CompressionJob] = {}


def get_job(job_id: str) -> CompressionJob | None:
    return _jobs.get(job_id)


def list_jobs() -> list[CompressionJob]:
    return list(_jobs.values())


async def probe_video(file_path: str) -> VideoMetadata:
    cmd = [
        settings.ffprobe_path,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        file_path,
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:
        raise CompressionError(
            f"FFprobe not found at '{settings.ffprobe_path}'.\n\n"
            "Please install FFmpeg and make sure ffprobe is in your PATH.\n"
            "Download from: https://ffmpeg.org/download.html\n\n"
            "On Windows you can also set FFPROBE_PATH in your .env file."
        ) from None

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise UnsupportedFormatError(Path(file_path).suffix)

    data = json.loads(stdout.decode())
    fmt = data.get("format", {})

    video_stream = None
    audio_stream = None
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video" and video_stream is None:
            video_stream = stream
        elif stream.get("codec_type") == "audio" and audio_stream is None:
            audio_stream = stream

    if not video_stream:
        raise UnsupportedFormatError("no video stream found")

    file_size = os.path.getsize(file_path)
    duration = float(fmt.get("duration", 0))
    bitrate = int(fmt.get("bit_rate", 0)) // 1000

    fps_parts = video_stream.get("r_frame_rate", "30/1").split("/")
    if len(fps_parts) == 2 and float(fps_parts[1]) != 0:
        fps = float(fps_parts[0]) / float(fps_parts[1])
    else:
        fps = 30.0

    return VideoMetadata(
        filename=Path(file_path).name,
        format=Path(file_path).suffix.lstrip("."),
        duration=round(duration, 2),
        width=int(video_stream.get("width", 0)),
        height=int(video_stream.get("height", 0)),
        bitrate=bitrate,
        fps=round(fps, 2),
        codec=video_stream.get("codec_name", "unknown"),
        audio_codec=audio_stream.get("codec_name") if audio_stream else None,
        audio_bitrate=(
            int(audio_stream.get("bit_rate", 0)) // 1000
            if audio_stream and audio_stream.get("bit_rate")
            else None
        ),
        file_size_bytes=file_size,
        file_size_mb=round(file_size / (1024 * 1024), 2),
    )


def _build_ffmpeg_args(
    input_path: str,
    output_path: str,
    s: CompressionSettings,
) -> list[str]:
    codec_map = {
        VideoCodec.H264: "libx264",
        VideoCodec.H265: "libx265",
        VideoCodec.VP9: "libvpx-vp9",
        VideoCodec.AV1: "libaom-av1",
    }

    args = [
        settings.ffmpeg_path,
        "-i", input_path,
        "-y",
    ]

    args.extend(["-c:v", codec_map[s.video_codec]])
    args.extend(["-crf", str(s.crf)])
    args.extend(["-preset", s.preset.value])

    if s.resolution:
        parts = s.resolution.split("x")
        if len(parts) == 2:
            args.extend(["-vf", f"scale={parts[0]}:{parts[1]}"])

    if s.max_bitrate:
        args.extend(["-maxrate", f"{s.max_bitrate}k", "-bufsize", f"{s.max_bitrate * 2}k"])

    if s.fps:
        args.extend(["-r", str(s.fps)])

    if s.strip_audio:
        args.append("-an")
    else:
        args.extend(["-c:a", s.audio_codec.value])
        args.extend(["-b:a", f"{s.audio_bitrate}k"])

    args.append(output_path)
    return args


async def compress_video(
    input_path: str,
    s: CompressionSettings,
) -> CompressionJob:
    job_id = str(uuid.uuid4())
    input_name = Path(input_path).stem
    ext = ".webm" if s.video_codec == VideoCodec.VP9 else ".mp4"
    output_filename = f"{input_name}_compressed_{job_id[:8]}{ext}"
    output_path = str(Path(settings.output_dir) / output_filename)

    settings.ensure_dirs()

    input_meta = await probe_video(input_path)

    job = CompressionJob(
        job_id=job_id,
        status="processing",
        input_file=Path(input_path).name,
        settings=s,
        input_metadata=input_meta,
    )
    _jobs[job_id] = job

    logger.info("Starting compression job %s: %s -> %s", job_id, input_path, output_path)

    try:
        args = _build_ffmpeg_args(input_path, output_path, s)
        logger.debug("FFmpeg command: %s", " ".join(args))

        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            raise CompressionError(
                f"FFmpeg not found at '{settings.ffmpeg_path}'.\n\n"
                "Please install FFmpeg and make sure it is in your PATH.\n"
                "Download from: https://ffmpeg.org/download.html\n\n"
                "On Windows you can also set FFMPEG_PATH in your .env file."
            ) from None

        _, stderr_data = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr_data.decode()[-500:]
            logger.error("FFmpeg failed for job %s: %s", job_id, error_msg)
            job.status = "failed"
            job.error = error_msg
            raise CompressionError(f"FFmpeg exited with code {process.returncode}")

        output_meta = await probe_video(output_path)
        ratio = (
            input_meta.file_size_bytes / output_meta.file_size_bytes
            if output_meta.file_size_bytes > 0
            else 0
        )

        job.status = "completed"
        job.output_file = output_filename
        job.output_metadata = output_meta
        job.compression_ratio = round(ratio, 2)
        job.progress = 100.0

        logger.info(
            "Job %s completed: %.1fMB -> %.1fMB (%.1fx compression)",
            job_id, input_meta.file_size_mb, output_meta.file_size_mb, ratio,
        )

    except CompressionError:
        raise
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        logger.exception("Unexpected error in job %s", job_id)
        raise CompressionError(str(e)) from e

    return job
