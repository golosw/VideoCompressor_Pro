from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "VideoCompressor Pro"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000

    upload_dir: str = "./uploads"
    output_dir: str = "./outputs"
    max_file_size_mb: int = 500

    ffmpeg_path: str = "/usr/bin/ffmpeg"
    ffprobe_path: str = "/usr/bin/ffprobe"

    ai_enabled: bool = True
    ai_base_url: str = "http://localhost:11434/v1"
    ai_model: str = "qwen2.5-coder:7b"
    ai_timeout: int = 30

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def ensure_dirs(self) -> None:
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)


settings = Settings()
