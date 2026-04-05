"""Entry point for VideoCompressor Pro — used by PyInstaller and direct execution."""

import multiprocessing
import os
import sys
from pathlib import Path


def get_base_dir() -> Path:
    """Return the base directory (handles both normal and PyInstaller frozen modes)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def main() -> None:
    base_dir = get_base_dir()
    os.chdir(base_dir)

    # Ensure .env is loaded from the correct location
    env_file = base_dir / ".env"
    if not env_file.exists():
        example = base_dir / ".env.example"
        if example.exists():
            import shutil
            shutil.copy(example, env_file)
            print(f"[INFO] Created .env from .env.example at {env_file}")

    # Set default FFmpeg paths for Windows if not configured
    if sys.platform == "win32":
        os.environ.setdefault("FFMPEG_PATH", "ffmpeg")
        os.environ.setdefault("FFPROBE_PATH", "ffprobe")

    import uvicorn

    from app.core.config import settings

    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Server: http://{settings.host}:{settings.port}")
    print(f"API docs: http://{settings.host}:{settings.port}/docs")
    print("Press Ctrl+C to stop.")

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
