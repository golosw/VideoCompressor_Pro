import os
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.exceptions import FileTooLargeError, UnsupportedFormatError
from app.core.logging import logger
from app.models.schemas import CompressionJob, CompressionSettings, VideoMetadata
from app.services.video_service import (
    SUPPORTED_FORMATS,
    compress_video,
    get_job,
    list_jobs,
    probe_video,
)

router = APIRouter(prefix="/video", tags=["Video"])


@router.post("/upload", response_model=VideoMetadata)
async def upload_video(file: UploadFile = File(...)):
    ext = Path(file.filename or "unknown").suffix.lower()
    if ext not in SUPPORTED_FORMATS:
        raise UnsupportedFormatError(ext)

    settings.ensure_dirs()

    unique_name = f"{uuid.uuid4()}{ext}"
    file_path = str(Path(settings.upload_dir) / unique_name)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size = os.path.getsize(file_path)
    if file_size > settings.max_file_size_mb * 1024 * 1024:
        os.remove(file_path)
        raise FileTooLargeError(settings.max_file_size_mb)

    logger.info("Uploaded %s (%s, %.1f MB)", file.filename, unique_name, file_size / 1024 / 1024)

    metadata = await probe_video(file_path)
    metadata.filename = file.filename or unique_name
    return metadata


@router.post("/compress", response_model=CompressionJob)
async def compress(
    filename: str,
    compression_settings: CompressionSettings | None = None,
):
    upload_dir = Path(settings.upload_dir)
    file_path = None

    for f in upload_dir.iterdir():
        if f.is_file() and f.name == filename:
            file_path = str(f)
            break

    if not file_path:
        for f in upload_dir.iterdir():
            if f.is_file():
                original_ext = Path(filename).suffix
                if f.suffix == original_ext:
                    file_path = str(f)
                    break

    if not file_path:
        from app.core.exceptions import FileNotFoundError as AppFileNotFoundError
        raise AppFileNotFoundError(f"File '{filename}' not found in uploads")

    s = compression_settings or CompressionSettings()
    logger.info("Starting compression: %s with settings %s", filename, s.model_dump())

    job = await compress_video(file_path, s)
    return job


@router.get("/jobs", response_model=list[CompressionJob])
async def get_jobs():
    return list_jobs()


@router.get("/jobs/{job_id}", response_model=CompressionJob)
async def get_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        from app.core.exceptions import FileNotFoundError as AppFileNotFoundError
        raise AppFileNotFoundError(f"Job '{job_id}' not found")
    return job


@router.get("/download/{filename}")
async def download_file(filename: str):
    file_path = Path(settings.output_dir) / filename
    if not file_path.exists():
        from app.core.exceptions import FileNotFoundError as AppFileNotFoundError
        raise AppFileNotFoundError(f"Output file '{filename}' not found")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream",
    )


@router.get("/formats")
async def supported_formats():
    return {
        "supported_input_formats": sorted(SUPPORTED_FORMATS),
        "supported_output_formats": [".mp4", ".webm"],
    }
