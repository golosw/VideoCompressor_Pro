"""Download and install FFmpeg binaries automatically.

Downloads pre-built FFmpeg from GitHub (BtbN/FFmpeg-Builds) and extracts
the binaries to a local directory next to the application.
"""

import io
import logging
import platform
import stat
import sys
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

# BtbN provides reliable, up-to-date FFmpeg builds for Windows and Linux.
_FFMPEG_BUILDS: dict[str, str] = {
    "win64": (
        "https://github.com/BtbN/FFmpeg-Builds/releases/download/"
        "latest/ffmpeg-master-latest-win64-gpl.zip"
    ),
    "linux64": (
        "https://github.com/BtbN/FFmpeg-Builds/releases/download/"
        "latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
    ),
}


def get_ffmpeg_dir() -> Path:
    """Return the local directory where FFmpeg binaries are stored.

    When running as a PyInstaller .exe, this is next to the executable.
    Otherwise it's at the project root level.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "ffmpeg"
    # backend/ is the cwd set by _setup_backend_path
    return Path.cwd().parent / "ffmpeg"


def is_ffmpeg_installed() -> bool:
    """Check whether ffmpeg and ffprobe are available.

    Uses the same search logic as ``_find_ffmpeg_binary`` in config
    (PATH, local dir, common Windows locations) so the result is
    consistent with what the app will actually use at runtime.
    """
    from app.core.config import _find_ffmpeg_binary

    ffmpeg = _find_ffmpeg_binary("ffmpeg")
    ffprobe = _find_ffmpeg_binary("ffprobe")
    # _find_ffmpeg_binary returns the bare name as fallback when nothing is found
    return ffmpeg != "ffmpeg" and ffprobe != "ffprobe"


def _get_platform_key() -> str:
    """Return the platform key for the download URL."""
    if sys.platform == "win32":
        return "win64"
    if sys.platform.startswith("linux") and platform.machine() in ("x86_64", "AMD64"):
        return "linux64"
    raise RuntimeError(
        f"No pre-built FFmpeg available for {sys.platform}/{platform.machine()}.\n"
        "Please install FFmpeg manually: https://ffmpeg.org/download.html"
    )


def download_ffmpeg(
    progress_callback: "callable[[float, str], None] | None" = None,
) -> Path:
    """Download and extract FFmpeg to the local ffmpeg/ directory.

    Args:
        progress_callback: Optional ``(percent, status_text)`` callback
            invoked during download and extraction.  ``percent`` is 0-100.

    Returns:
        Path to the directory containing the ffmpeg/ffprobe binaries.

    Raises:
        RuntimeError: If the platform is not supported or the download fails.
    """
    plat = _get_platform_key()
    url = _FFMPEG_BUILDS[plat]
    dest = get_ffmpeg_dir()
    dest.mkdir(parents=True, exist_ok=True)

    if progress_callback:
        progress_callback(0, "Connecting...")

    logger.info("Downloading FFmpeg from %s", url)

    req = Request(url, headers={"User-Agent": "VideoCompressorPro/1.0"})
    resp = urlopen(req, timeout=120)  # noqa: S310

    total = int(resp.headers.get("Content-Length", 0))
    downloaded = 0
    buf = io.BytesIO()
    chunk_size = 256 * 1024  # 256 KB

    while True:
        chunk = resp.read(chunk_size)
        if not chunk:
            break
        buf.write(chunk)
        downloaded += len(chunk)
        if progress_callback and total > 0:
            pct = min(downloaded / total * 90, 90)  # Reserve 10% for extraction
            mb_done = downloaded / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            progress_callback(pct, f"Downloading... {mb_done:.0f}/{mb_total:.0f} MB")

    buf.seek(0)

    if progress_callback:
        progress_callback(90, "Extracting...")

    logger.info("Extracting FFmpeg to %s", dest)

    if plat == "win64":
        _extract_zip(buf, dest)
    else:
        _extract_tar_xz(buf, dest)

    if progress_callback:
        progress_callback(100, "Done!")

    logger.info("FFmpeg installed at %s", dest)
    return dest


def _extract_zip(buf: io.BytesIO, dest: Path) -> None:
    """Extract ffmpeg.exe and ffprobe.exe from a zip archive."""
    with zipfile.ZipFile(buf) as zf:
        for name in zf.namelist():
            basename = Path(name).name
            if basename in ("ffmpeg.exe", "ffprobe.exe"):
                data = zf.read(name)
                target = dest / basename
                target.write_bytes(data)
                logger.info("Extracted %s", target)


def _extract_tar_xz(buf: io.BytesIO, dest: Path) -> None:
    """Extract ffmpeg and ffprobe from a tar.xz archive."""
    import lzma
    import tarfile

    decompressed = io.BytesIO(lzma.decompress(buf.read()))
    with tarfile.open(fileobj=decompressed, mode="r:") as tf:
        for member in tf.getmembers():
            basename = Path(member.name).name
            if basename in ("ffmpeg", "ffprobe") and member.isfile():
                f = tf.extractfile(member)
                if f is None:
                    continue
                data = f.read()
                target = dest / basename
                target.write_bytes(data)
                # Make executable on Linux/macOS
                target.chmod(target.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
                logger.info("Extracted %s", target)


def get_local_binary_path(name: str) -> str | None:
    """Return path to a locally downloaded FFmpeg binary, or None."""
    d = get_ffmpeg_dir()
    if sys.platform == "win32":
        p = d / f"{name}.exe"
    else:
        p = d / name
    return str(p) if p.is_file() else None
