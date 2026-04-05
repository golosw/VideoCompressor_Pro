from enum import Enum

from pydantic import BaseModel, Field


class VideoCodec(str, Enum):
    H264 = "h264"
    H265 = "h265"
    VP9 = "vp9"
    AV1 = "av1"


class AudioCodec(str, Enum):
    AAC = "aac"
    OPUS = "opus"
    MP3 = "mp3"
    COPY = "copy"


class CompressionPreset(str, Enum):
    ULTRAFAST = "ultrafast"
    SUPERFAST = "superfast"
    VERYFAST = "veryfast"
    FASTER = "faster"
    FAST = "fast"
    MEDIUM = "medium"
    SLOW = "slow"
    SLOWER = "slower"
    VERYSLOW = "veryslow"


class VideoMetadata(BaseModel):
    filename: str
    format: str
    duration: float = Field(description="Duration in seconds")
    width: int
    height: int
    bitrate: int = Field(description="Bitrate in kbps")
    fps: float
    codec: str
    audio_codec: str | None = None
    audio_bitrate: int | None = None
    file_size_bytes: int
    file_size_mb: float


class CompressionSettings(BaseModel):
    video_codec: VideoCodec = VideoCodec.H264
    audio_codec: AudioCodec = AudioCodec.AAC
    preset: CompressionPreset = CompressionPreset.MEDIUM
    crf: int = Field(
        default=23, ge=0, le=51,
        description="Constant Rate Factor (0=lossless, 51=worst)",
    )
    resolution: str | None = Field(default=None, description="Target resolution e.g. 1920x1080")
    max_bitrate: int | None = Field(default=None, description="Max bitrate in kbps")
    audio_bitrate: int = Field(default=128, description="Audio bitrate in kbps")
    fps: float | None = Field(default=None, description="Target frame rate")
    strip_audio: bool = False


class CompressionJob(BaseModel):
    job_id: str
    status: str
    input_file: str
    output_file: str | None = None
    settings: CompressionSettings
    input_metadata: VideoMetadata | None = None
    output_metadata: VideoMetadata | None = None
    compression_ratio: float | None = None
    progress: float = 0.0
    error: str | None = None


class AIAnalysisRequest(BaseModel):
    metadata: VideoMetadata
    target_use: str = Field(
        default="general",
        description="Target use case: web, mobile, archive, streaming, social",
    )
    target_quality: str = Field(
        default="balanced",
        description="Quality preference: highest, high, balanced, low, lowest",
    )
    max_file_size_mb: float | None = Field(
        default=None,
        description="Optional target max file size in MB",
    )


class AIAnalysisResponse(BaseModel):
    recommended_settings: CompressionSettings
    explanation: str
    estimated_output_size_mb: float | None = None
    estimated_compression_ratio: float | None = None


class AIChatRequest(BaseModel):
    message: str
    context: VideoMetadata | None = None


class AIChatResponse(BaseModel):
    response: str
