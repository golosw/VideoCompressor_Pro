import json

import httpx

from app.core.config import settings
from app.core.exceptions import AIServiceError
from app.core.logging import logger
from app.models.schemas import (
    AIAnalysisRequest,
    AIAnalysisResponse,
    AIChatRequest,
    AIChatResponse,
    AudioCodec,
    CompressionPreset,
    CompressionSettings,
    VideoCodec,
)


def _build_analysis_prompt(req: AIAnalysisRequest) -> str:
    m = req.metadata
    return (
        f"""You are a video compression expert. \
Analyze this video and recommend optimal FFmpeg compression settings.

VIDEO METADATA:
- Resolution: {m.width}x{m.height}
- Duration: {m.duration}s
- Current bitrate: {m.bitrate} kbps
- FPS: {m.fps}
- Codec: {m.codec}
- Audio codec: {m.audio_codec or 'none'}
- File size: {m.file_size_mb} MB

USER PREFERENCES:
- Target use case: {req.target_use}
- Quality preference: {req.target_quality}
- Max file size: {req.max_file_size_mb or 'no limit'} MB

Respond ONLY with valid JSON in this exact format:
{{
    "video_codec": "h264" | "h265" | "vp9",
    "audio_codec": "aac" | "opus" | "mp3" | "copy",
    "preset": "ultrafast" | "superfast" | "veryfast" | "faster" | "fast" \
| "medium" | "slow" | "slower" | "veryslow",
    "crf": <number 0-51>,
    "resolution": "<width>x<height>" or null,
    "max_bitrate": <number in kbps> or null,
    "audio_bitrate": <number in kbps>,
    "fps": <number> or null,
    "strip_audio": false,
    "explanation": "<brief explanation of why these settings are optimal>",
    "estimated_output_size_mb": <number>,
    "estimated_compression_ratio": <number>
}}"""
    )


def _build_chat_prompt(req: AIChatRequest) -> str:
    context_str = ""
    if req.context:
        m = req.context
        context_str = f"""
Current video context:
- File: {m.filename} ({m.format})
- Resolution: {m.width}x{m.height}, {m.fps} FPS
- Duration: {m.duration}s, Size: {m.file_size_mb} MB
- Codec: {m.codec}, Bitrate: {m.bitrate} kbps
"""

    return (
        f"""You are a helpful video compression assistant. \
Answer questions about video encoding, compression, codecs, and FFmpeg.
{context_str}
User question: {req.message}

Provide a clear, concise answer."""
    )


def _fallback_settings(req: AIAnalysisRequest) -> AIAnalysisResponse:
    """Rule-based fallback when AI service is unavailable."""
    m = req.metadata

    quality_crf = {
        "highest": 18,
        "high": 20,
        "balanced": 23,
        "low": 28,
        "lowest": 32,
    }
    crf = quality_crf.get(req.target_quality, 23)

    use_presets: dict[str, CompressionPreset] = {
        "web": CompressionPreset.FAST,
        "mobile": CompressionPreset.FAST,
        "streaming": CompressionPreset.VERYFAST,
        "social": CompressionPreset.FAST,
        "archive": CompressionPreset.SLOW,
        "general": CompressionPreset.MEDIUM,
    }
    preset = use_presets.get(req.target_use, CompressionPreset.MEDIUM)

    resolution = None
    if req.target_use == "mobile" and m.width > 1280:
        resolution = "1280x720"
    elif req.target_use == "social" and m.width > 1920:
        resolution = "1920x1080"

    codec = VideoCodec.H264
    if req.target_use == "web":
        codec = VideoCodec.H265
    elif req.target_use == "archive":
        codec = VideoCodec.H265

    estimated_ratio = 51.0 / max(crf, 1) * 0.8
    estimated_size = m.file_size_mb / max(estimated_ratio, 1)

    if req.max_file_size_mb and estimated_size > req.max_file_size_mb:
        crf = min(crf + 5, 45)
        estimated_size = m.file_size_mb / (51.0 / max(crf, 1) * 0.8)

    s = CompressionSettings(
        video_codec=codec,
        audio_codec=AudioCodec.AAC,
        preset=preset,
        crf=crf,
        resolution=resolution,
        audio_bitrate=128 if req.target_use != "mobile" else 96,
    )

    return AIAnalysisResponse(
        recommended_settings=s,
        explanation=(
            f"Rule-based recommendation for {req.target_use} use "
            f"with {req.target_quality} quality. "
            f"Using {codec.value} codec with CRF {crf} "
            f"and {preset.value} preset."
        ),
        estimated_output_size_mb=round(estimated_size, 1),
        estimated_compression_ratio=round(m.file_size_mb / max(estimated_size, 0.01), 1),
    )


async def analyze_video(req: AIAnalysisRequest) -> AIAnalysisResponse:
    if not settings.ai_enabled:
        logger.info("AI disabled, using fallback settings")
        return _fallback_settings(req)

    prompt = _build_analysis_prompt(req)

    try:
        async with httpx.AsyncClient(timeout=settings.ai_timeout) as client:
            response = await client.post(
                f"{settings.ai_base_url}/chat/completions",
                json={
                    "model": settings.ai_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 1000,
                },
            )
            response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

        parsed = json.loads(content)

        s = CompressionSettings(
            video_codec=VideoCodec(parsed.get("video_codec", "h264")),
            audio_codec=AudioCodec(parsed.get("audio_codec", "aac")),
            preset=CompressionPreset(parsed.get("preset", "medium")),
            crf=int(parsed.get("crf", 23)),
            resolution=parsed.get("resolution"),
            max_bitrate=parsed.get("max_bitrate"),
            audio_bitrate=int(parsed.get("audio_bitrate", 128)),
            fps=parsed.get("fps"),
            strip_audio=parsed.get("strip_audio", False),
        )

        return AIAnalysisResponse(
            recommended_settings=s,
            explanation=parsed.get("explanation", "AI-optimized compression settings."),
            estimated_output_size_mb=parsed.get("estimated_output_size_mb"),
            estimated_compression_ratio=parsed.get("estimated_compression_ratio"),
        )

    except httpx.ConnectError:
        logger.warning("AI service unreachable, using fallback")
        return _fallback_settings(req)
    except (httpx.HTTPStatusError, json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning("AI response parsing failed (%s), using fallback", e)
        return _fallback_settings(req)
    except Exception as e:
        logger.exception("Unexpected AI error")
        raise AIServiceError(str(e)) from e


async def chat(req: AIChatRequest) -> AIChatResponse:
    if not settings.ai_enabled:
        return AIChatResponse(
            response=(
                "AI service is currently disabled. "
                "Enable it in the configuration to use the chat feature."
            )
        )

    prompt = _build_chat_prompt(req)

    try:
        async with httpx.AsyncClient(timeout=settings.ai_timeout) as client:
            response = await client.post(
                f"{settings.ai_base_url}/chat/completions",
                json={
                    "model": settings.ai_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 1500,
                },
            )
            response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return AIChatResponse(response=content)

    except httpx.ConnectError:
        return AIChatResponse(
            response=(
                "AI service is currently unreachable. "
                "Please ensure the local LLM server is running."
            )
        )
    except Exception as e:
        logger.exception("AI chat error")
        raise AIServiceError(str(e)) from e


async def health_check() -> dict:
    if not settings.ai_enabled:
        return {"status": "disabled", "model": settings.ai_model}

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{settings.ai_base_url}/models")
            response.raise_for_status()
        return {
            "status": "connected",
            "model": settings.ai_model,
            "base_url": settings.ai_base_url,
        }
    except Exception:
        return {
            "status": "unreachable",
            "model": settings.ai_model,
            "base_url": settings.ai_base_url,
        }
