import shutil
import sys
from pathlib import Path

from pydantic_settings import BaseSettings


def _find_ffmpeg_binary(name: str) -> str:
    """Locate an FFmpeg binary (ffmpeg or ffprobe) on the current system.

    Checks PATH first, then common Windows install locations.
    Returns the full path if found, otherwise returns the bare name
    so the error message from subprocess is clear.
    """
    # 1. Check if it's already on PATH
    found = shutil.which(name)
    if found:
        return found

    # 2. On Windows, check common install directories
    if sys.platform == "win32":
        candidates = [
            Path(r"C:\ffmpeg\bin") / f"{name}.exe",
            Path(r"C:\Program Files\ffmpeg\bin") / f"{name}.exe",
            Path(r"C:\Program Files (x86)\ffmpeg\bin") / f"{name}.exe",
            Path.home() / "ffmpeg" / "bin" / f"{name}.exe",
            Path.home() / "Downloads" / "ffmpeg" / "bin" / f"{name}.exe",
            Path.home() / "scoop" / "shims" / f"{name}.exe",
        ]
        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)

    # 3. Fallback: return the bare name (will fail with a clear FileNotFoundError)
    return name


class Settings(BaseSettings):
    app_name: str = "VideoCompressor Pro"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000

    upload_dir: str = "./uploads"
    output_dir: str = "./outputs"

    ffmpeg_path: str = _find_ffmpeg_binary("ffmpeg")
    ffprobe_path: str = _find_ffmpeg_binary("ffprobe")

    ai_enabled: bool = True
    ai_base_url: str = "http://localhost:11434/v1"
    ai_model: str = "qwen2.5-coder:7b"
    ai_timeout: int = 30

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    def ensure_dirs(self) -> None:
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)


settings = Settings()
