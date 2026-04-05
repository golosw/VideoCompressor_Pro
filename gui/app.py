"""VideoCompressor Pro — Professional Desktop GUI."""

import asyncio
import os
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk


def _setup_backend_path() -> None:
    """Set up sys.path and working directory for backend imports.

    Handles both normal execution and PyInstaller frozen mode.
    """
    if getattr(sys, "frozen", False):
        # PyInstaller --onefile: executable lives next to the app/ package
        base = Path(sys.executable).parent
        sys.path.insert(0, str(base))
        os.chdir(base)
    else:
        # Normal Python execution: gui/ is a sibling of backend/
        root = Path(__file__).resolve().parent.parent
        sys.path.insert(0, str(root / "backend"))
        os.chdir(root / "backend")


_setup_backend_path()

from app.core.config import settings  # noqa: E402
from app.models.schemas import (  # noqa: E402
    AIAnalysisRequest,
    CompressionPreset,
    CompressionSettings,
    VideoCodec,
)
from app.services.ai_service import analyze_video  # noqa: E402
from app.services.ffmpeg_downloader import (  # noqa: E402
    download_ffmpeg,
    is_ffmpeg_installed,
)
from app.services.video_service import compress_video, probe_video  # noqa: E402

# ── Theme ────────────────────────────────────────────────────────────────
DARK_BG = "#0f1117"
PANEL_BG = "#1a1d27"
CARD_BG = "#242836"
ACCENT = "#6366f1"
ACCENT_HOVER = "#818cf8"
SUCCESS = "#22c55e"
SUCCESS_DARK = "#166534"
WARNING = "#f59e0b"
ERROR = "#ef4444"
TEXT = "#f1f5f9"
TEXT_DIM = "#94a3b8"
TEXT_MUTED = "#64748b"
BORDER = "#334155"


class VideoCompressorApp(ctk.CTk):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("VideoCompressor Pro")
        self.configure(fg_color=DARK_BG)

        # Fullscreen
        self.attributes("-fullscreen", True)
        self.bind("<Escape>", lambda _: self._toggle_fullscreen())
        self.bind("<F11>", lambda _: self._toggle_fullscreen())
        self._is_fullscreen = True

        # State
        self._input_path: str | None = None
        self._metadata = None
        self._ai_result = None
        self._compressing = False

        settings.ensure_dirs()

        self._build_ui()

        # Check FFmpeg availability after the window is visible
        if not is_ffmpeg_installed():
            self.after(300, self._show_ffmpeg_setup)

    # ── FFmpeg setup dialog ───────────────────────────────────────────
    def _show_ffmpeg_setup(self) -> None:
        """Show a dialog offering to download FFmpeg automatically."""
        self._clear_main()

        center = ctk.CTkFrame(self._main, fg_color="transparent")
        center.place(relx=0.5, rely=0.40, anchor="center")

        ctk.CTkLabel(
            center,
            text="\u26a0\ufe0f  FFmpeg Not Found",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color=WARNING,
        ).pack(pady=(0, 12))

        ctk.CTkLabel(
            center,
            text=(
                "FFmpeg is required for video compression.\n"
                "Click below to download and install it automatically (~90 MB)."
            ),
            font=ctk.CTkFont(size=15),
            text_color=TEXT_DIM,
            justify="center",
        ).pack(pady=(0, 30))

        self._ffmpeg_progress_label = ctk.CTkLabel(
            center, text="", font=ctk.CTkFont(size=13), text_color=TEXT_DIM,
        )

        self._ffmpeg_progress_bar = ctk.CTkProgressBar(
            center, width=400, mode="determinate",
            progress_color=ACCENT,
        )
        self._ffmpeg_progress_bar.set(0)

        # Buttons row
        btn_row = ctk.CTkFrame(center, fg_color="transparent")
        btn_row.pack(pady=(0, 20))

        self._ffmpeg_dl_btn = ctk.CTkButton(
            btn_row,
            text="\u2b07  Download FFmpeg",
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=48,
            width=260,
            command=self._download_ffmpeg,
        )
        self._ffmpeg_dl_btn.pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            btn_row,
            text="Skip",
            fg_color=CARD_BG,
            hover_color=BORDER,
            font=ctk.CTkFont(size=14),
            text_color=TEXT_DIM,
            height=48,
            width=100,
            command=self._show_upload_view,
        ).pack(side="left")

        ctk.CTkLabel(
            center,
            text="Or install manually: https://ffmpeg.org/download.html",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
        ).pack(pady=(10, 0))

    def _download_ffmpeg(self) -> None:
        """Start FFmpeg download in a background thread."""
        self._ffmpeg_dl_btn.configure(text="\u23f3  Downloading...", state="disabled")
        self._ffmpeg_progress_bar.pack(pady=(0, 8))
        self._ffmpeg_progress_label.pack()

        def on_progress(pct: float, status: str) -> None:
            self.after(0, lambda: self._update_ffmpeg_progress(pct, status))

        def run() -> None:
            try:
                download_ffmpeg(progress_callback=on_progress)
                self.after(0, self._on_ffmpeg_download_done)
            except Exception as exc:
                msg = str(exc)
                self.after(0, lambda: self._on_ffmpeg_download_error(msg))

        threading.Thread(target=run, daemon=True).start()

    def _update_ffmpeg_progress(self, pct: float, status: str) -> None:
        self._ffmpeg_progress_bar.set(pct / 100)
        self._ffmpeg_progress_label.configure(text=status)

    def _on_ffmpeg_download_done(self) -> None:
        # Refresh settings with newly available binaries
        from app.core.config import _find_ffmpeg_binary

        settings.ffmpeg_path = _find_ffmpeg_binary("ffmpeg")
        settings.ffprobe_path = _find_ffmpeg_binary("ffprobe")

        messagebox.showinfo(
            "FFmpeg Installed",
            "FFmpeg has been downloaded and installed successfully!\n\n"
            f"Location: {settings.ffmpeg_path}",
        )
        self._show_upload_view()

    def _on_ffmpeg_download_error(self, error: str) -> None:
        self._ffmpeg_dl_btn.configure(text="\u2b07  Download FFmpeg", state="normal")
        messagebox.showerror(
            "Download Failed",
            f"Failed to download FFmpeg:\n{error}\n\n"
            "Please install it manually from:\nhttps://ffmpeg.org/download.html",
        )

    # ── Fullscreen toggle ────────────────────────────────────────────────
    def _toggle_fullscreen(self) -> None:
        self._is_fullscreen = not self._is_fullscreen
        self.attributes("-fullscreen", self._is_fullscreen)

    # ── UI Construction ──────────────────────────────────────────────────
    def _build_ui(self) -> None:
        # Top bar
        self._build_topbar()

        # Main content area
        self._main = ctk.CTkFrame(self, fg_color=DARK_BG)
        self._main.pack(fill="both", expand=True, padx=40, pady=(10, 30))

        # Start with upload view
        self._show_upload_view()

    def _build_topbar(self) -> None:
        bar = ctk.CTkFrame(self, fg_color=PANEL_BG, height=60, corner_radius=0)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        # Logo / title
        title_frame = ctk.CTkFrame(bar, fg_color="transparent")
        title_frame.pack(side="left", padx=20)

        ctk.CTkLabel(
            title_frame,
            text="⚡ VideoCompressor Pro",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=TEXT,
        ).pack(side="left")

        ctk.CTkLabel(
            title_frame,
            text="  AI-powered video compression",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_MUTED,
        ).pack(side="left")

        # Right side buttons
        right_frame = ctk.CTkFrame(bar, fg_color="transparent")
        right_frame.pack(side="right", padx=20)

        self._new_btn = ctk.CTkButton(
            right_frame,
            text="New Video",
            width=100,
            height=32,
            fg_color=CARD_BG,
            hover_color=BORDER,
            text_color=TEXT_DIM,
            font=ctk.CTkFont(size=13),
            command=self._reset,
        )
        self._new_btn.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            right_frame,
            text="✕ Exit",
            width=70,
            height=32,
            fg_color=CARD_BG,
            hover_color="#7f1d1d",
            text_color=TEXT_DIM,
            font=ctk.CTkFont(size=13),
            command=self.destroy,
        ).pack(side="left")

    def _clear_main(self) -> None:
        for w in self._main.winfo_children():
            w.destroy()

    # ── Upload View ──────────────────────────────────────────────────────
    def _show_upload_view(self) -> None:
        self._clear_main()

        # Center container
        center = ctk.CTkFrame(self._main, fg_color="transparent")
        center.place(relx=0.5, rely=0.42, anchor="center")

        ctk.CTkLabel(
            center,
            text="Compress Your Videos",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=TEXT,
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            center,
            text="Select a video and let AI optimize compression settings",
            font=ctk.CTkFont(size=16),
            text_color=TEXT_DIM,
        ).pack(pady=(0, 40))

        # Drop zone
        drop = ctk.CTkFrame(
            center,
            width=600,
            height=220,
            fg_color=CARD_BG,
            border_color=BORDER,
            border_width=2,
            corner_radius=16,
        )
        drop.pack()
        drop.pack_propagate(False)

        inner = ctk.CTkFrame(drop, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            inner,
            text="📂",
            font=ctk.CTkFont(size=40),
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            inner,
            text="Click to select a video file",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=TEXT,
        ).pack(pady=(0, 6))

        ctk.CTkLabel(
            inner,
            text="Supports MP4, AVI, MKV, MOV, WebM, and more — no size limit",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_MUTED,
        ).pack()

        # Make the whole drop zone clickable
        for widget in [drop, inner] + inner.winfo_children():
            widget.bind("<Button-1>", lambda _: self._pick_file())

        # Change cursor on hover
        drop.configure(cursor="hand2")

    def _pick_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Select a video file",
            filetypes=[
                ("Video files",
                 "*.mp4 *.avi *.mkv *.mov *.wmv *.flv "
                 "*.webm *.m4v *.mpeg *.mpg *.3gp"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self._load_video(path)

    def _load_video(self, path: str) -> None:
        self._input_path = path
        self._clear_main()

        # Show loading
        loading = ctk.CTkFrame(self._main, fg_color="transparent")
        loading.place(relx=0.5, rely=0.45, anchor="center")
        ctk.CTkLabel(
            loading, text="Analyzing video...",
            font=ctk.CTkFont(size=18), text_color=TEXT_DIM,
        ).pack()
        self._progress_bar = ctk.CTkProgressBar(loading, width=300, mode="indeterminate")
        self._progress_bar.pack(pady=16)
        self._progress_bar.start()

        # Probe in background
        def probe():
            loop = asyncio.new_event_loop()
            try:
                meta = loop.run_until_complete(probe_video(path))
                self.after(0, lambda: self._on_probe_done(meta))
            except Exception as exc:
                msg = str(exc)
                self.after(0, lambda: self._on_probe_error(msg))
            finally:
                loop.close()

        threading.Thread(target=probe, daemon=True).start()

    def _on_probe_error(self, error: str) -> None:
        messagebox.showerror("Error", f"Failed to analyze video:\n{error}")
        self._show_upload_view()

    def _on_probe_done(self, meta) -> None:
        self._metadata = meta
        self._show_workspace_view()

    # ── Workspace View (metadata + settings + results) ───────────────────
    def _show_workspace_view(self) -> None:
        self._clear_main()

        # Scrollable container
        scroll = ctk.CTkScrollableFrame(
            self._main, fg_color="transparent",
            scrollbar_button_color=BORDER,
        )
        scroll.pack(fill="both", expand=True)

        # Two-column layout
        cols = ctk.CTkFrame(scroll, fg_color="transparent")
        cols.pack(fill="x", pady=10)
        cols.columnconfigure(0, weight=1)
        cols.columnconfigure(1, weight=1)

        # ── Left column: video info ──
        left = ctk.CTkFrame(cols, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self._build_video_info_card(left)

        # ── Right column: compression settings ──
        right = ctk.CTkFrame(cols, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self._build_settings_card(right)

        # Result area (hidden initially)
        self._result_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._result_frame.pack(fill="x", pady=(20, 0))

    def _build_video_info_card(self, parent: ctk.CTkFrame) -> None:
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12)
        card.pack(fill="x")

        # Header
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 10))

        ctk.CTkLabel(
            header, text="UPLOADED VIDEO",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_MUTED,
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text=self._metadata.filename,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=TEXT,
        ).pack(anchor="w", pady=(4, 0))

        # Divider
        ctk.CTkFrame(card, fg_color=BORDER, height=1).pack(fill="x", padx=20)

        # Metadata grid
        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=20, pady=16)

        m = self._metadata
        fields = [
            ("Codec", m.codec.upper()),
            ("Duration", f"{int(m.duration // 60)}:{int(m.duration % 60):02d}"),
            ("Resolution", f"{m.width}×{m.height}"),
            ("Bitrate", f"{m.bitrate} kbps"),
            ("FPS", str(int(m.fps))),
            ("Audio", m.audio_codec.upper() if m.audio_codec else "None"),
            ("Size", f"{m.file_size_mb:.1f} MB"),
            ("Format", m.format.upper()),
        ]

        for i, (label, value) in enumerate(fields):
            row, col = divmod(i, 2)
            f = ctk.CTkFrame(grid, fg_color="transparent")
            f.grid(row=row, column=col, sticky="w", padx=(0, 30), pady=4)

            ctk.CTkLabel(
                f, text=f"{label}:", font=ctk.CTkFont(size=13),
                text_color=TEXT_MUTED, width=80, anchor="w",
            ).pack(side="left")
            ctk.CTkLabel(
                f, text=value, font=ctk.CTkFont(size=13, weight="bold"),
                text_color=TEXT, anchor="w",
            ).pack(side="left")

    def _build_settings_card(self, parent: ctk.CTkFrame) -> None:
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12)
        card.pack(fill="x")

        # Header
        ctk.CTkLabel(
            card, text="⚙  Compression Settings",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=TEXT,
        ).pack(anchor="w", padx=20, pady=(16, 12))

        # AI section
        ai_frame = ctk.CTkFrame(card, fg_color="#1e1b4b", corner_radius=8)
        ai_frame.pack(fill="x", padx=20, pady=(0, 12))

        ctk.CTkLabel(
            ai_frame, text="✨ AI-Powered Optimization",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=ACCENT_HOVER,
        ).pack(anchor="w", padx=16, pady=(12, 4))

        # Use case + quality row
        opts_row = ctk.CTkFrame(ai_frame, fg_color="transparent")
        opts_row.pack(fill="x", padx=16, pady=(4, 8))

        ctk.CTkLabel(
            opts_row, text="Use Case", font=ctk.CTkFont(size=12),
            text_color=TEXT_DIM,
        ).pack(side="left")

        self._use_case_var = ctk.StringVar(value="General")
        ctk.CTkOptionMenu(
            opts_row, variable=self._use_case_var,
            values=["General", "Web", "Mobile", "Streaming", "Social", "Archive"],
            width=120, height=28,
            fg_color=CARD_BG, button_color=BORDER,
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=(8, 20))

        ctk.CTkLabel(
            opts_row, text="Quality", font=ctk.CTkFont(size=12),
            text_color=TEXT_DIM,
        ).pack(side="left")

        self._quality_var = ctk.StringVar(value="Balanced")
        ctk.CTkOptionMenu(
            opts_row, variable=self._quality_var,
            values=["Highest", "High", "Balanced", "Low", "Lowest"],
            width=120, height=28,
            fg_color=CARD_BG, button_color=BORDER,
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=8)

        self._ai_btn = ctk.CTkButton(
            ai_frame,
            text="✨ Get AI Recommendations",
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=38,
            command=self._get_ai_recommendations,
        )
        self._ai_btn.pack(fill="x", padx=16, pady=(4, 12))

        # AI result label (hidden initially)
        self._ai_result_label = ctk.CTkLabel(
            ai_frame, text="", font=ctk.CTkFont(size=12),
            text_color=TEXT_DIM, wraplength=400, justify="left",
        )

        # Divider
        ctk.CTkFrame(card, fg_color=BORDER, height=1).pack(fill="x", padx=20, pady=4)

        # Manual settings
        settings_grid = ctk.CTkFrame(card, fg_color="transparent")
        settings_grid.pack(fill="x", padx=20, pady=12)

        # Codec
        row1 = ctk.CTkFrame(settings_grid, fg_color="transparent")
        row1.pack(fill="x", pady=4)

        ctk.CTkLabel(
            row1, text="Video Codec", font=ctk.CTkFont(size=13),
            text_color=TEXT_DIM, width=120, anchor="w",
        ).pack(side="left")

        self._codec_var = ctk.StringVar(value="H.264")
        ctk.CTkOptionMenu(
            row1, variable=self._codec_var,
            values=["H.264", "H.265", "VP9", "AV1"],
            width=160, height=30,
            fg_color=PANEL_BG, button_color=BORDER,
        ).pack(side="left")

        # Preset
        row2 = ctk.CTkFrame(settings_grid, fg_color="transparent")
        row2.pack(fill="x", pady=4)

        ctk.CTkLabel(
            row2, text="Speed Preset", font=ctk.CTkFont(size=13),
            text_color=TEXT_DIM, width=120, anchor="w",
        ).pack(side="left")

        self._preset_var = ctk.StringVar(value="Medium")
        ctk.CTkOptionMenu(
            row2, variable=self._preset_var,
            values=["Ultrafast", "Superfast", "Veryfast", "Faster",
                    "Fast", "Medium", "Slow", "Slower", "Veryslow"],
            width=160, height=30,
            fg_color=PANEL_BG, button_color=BORDER,
        ).pack(side="left")

        # CRF slider
        row3 = ctk.CTkFrame(settings_grid, fg_color="transparent")
        row3.pack(fill="x", pady=(8, 4))

        ctk.CTkLabel(
            row3, text="Quality (CRF)", font=ctk.CTkFont(size=13),
            text_color=TEXT_DIM, width=120, anchor="w",
        ).pack(side="left")

        self._crf_var = tk.IntVar(value=23)
        self._crf_label = ctk.CTkLabel(
            row3, text="23  High Quality",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=ACCENT_HOVER,
        )
        self._crf_label.pack(side="right")

        slider_frame = ctk.CTkFrame(settings_grid, fg_color="transparent")
        slider_frame.pack(fill="x", pady=(0, 4))

        self._crf_slider = ctk.CTkSlider(
            slider_frame,
            from_=0, to=51,
            number_of_steps=51,
            variable=self._crf_var,
            progress_color=ACCENT,
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER,
            command=self._on_crf_change,
        )
        self._crf_slider.pack(fill="x", padx=(120, 0))

        labels_row = ctk.CTkFrame(settings_grid, fg_color="transparent")
        labels_row.pack(fill="x")
        ctk.CTkLabel(
            labels_row, text="Best Quality",
            font=ctk.CTkFont(size=11), text_color=TEXT_MUTED,
        ).pack(side="left", padx=(120, 0))
        ctk.CTkLabel(
            labels_row, text="Smallest File",
            font=ctk.CTkFont(size=11), text_color=TEXT_MUTED,
        ).pack(side="right")

        # Resolution (downscale)
        row4 = ctk.CTkFrame(settings_grid, fg_color="transparent")
        row4.pack(fill="x", pady=4)

        ctk.CTkLabel(
            row4, text="Resolution", font=ctk.CTkFont(size=13),
            text_color=TEXT_DIM, width=120, anchor="w",
        ).pack(side="left")

        self._resolution_var = ctk.StringVar(value="Original")
        ctk.CTkOptionMenu(
            row4, variable=self._resolution_var,
            values=["Original", "3840x2160 (4K)", "2560x1440 (2K)",
                    "1920x1080 (1080p)", "1280x720 (720p)",
                    "854x480 (480p)", "640x360 (360p)"],
            width=200, height=30,
            fg_color=PANEL_BG, button_color=BORDER,
        ).pack(side="left")

        # Compress button
        self._compress_btn = ctk.CTkButton(
            card,
            text="⚡ Compress Video",
            fg_color=SUCCESS,
            hover_color="#16a34a",
            text_color="#ffffff",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=48,
            corner_radius=10,
            command=self._start_compression,
        )
        self._compress_btn.pack(fill="x", padx=20, pady=(12, 20))

    def _on_crf_change(self, value: float) -> None:
        v = int(value)
        if v <= 18:
            quality = "Lossless-like"
        elif v <= 22:
            quality = "High Quality"
        elif v <= 27:
            quality = "Good Quality"
        elif v <= 34:
            quality = "Medium Quality"
        else:
            quality = "Low Quality"
        self._crf_label.configure(text=f"{v}  {quality}")

    # ── AI Recommendations ───────────────────────────────────────────────
    def _get_ai_recommendations(self) -> None:
        if not self._metadata:
            return

        self._ai_btn.configure(text="⏳ Analyzing...", state="disabled")

        def run():
            loop = asyncio.new_event_loop()
            try:
                req = AIAnalysisRequest(
                    metadata=self._metadata,
                    target_use=self._use_case_var.get().lower(),
                    target_quality=self._quality_var.get().lower(),
                )
                result = loop.run_until_complete(analyze_video(req))
                self.after(0, lambda: self._on_ai_done(result))
            except Exception as exc:
                msg = str(exc)
                self.after(0, lambda: self._on_ai_error(msg))
            finally:
                loop.close()

        threading.Thread(target=run, daemon=True).start()

    def _on_ai_error(self, error: str) -> None:
        self._ai_btn.configure(text="✨ Get AI Recommendations", state="normal")
        messagebox.showwarning("AI Error", f"Could not get AI recommendations:\n{error}")

    def _on_ai_done(self, result) -> None:
        self._ai_result = result
        s = result.recommended_settings

        # Update UI with recommended settings
        codec_map = {"h264": "H.264", "h265": "H.265", "vp9": "VP9", "av1": "AV1"}
        self._codec_var.set(codec_map.get(s.video_codec.value, "H.264"))
        self._preset_var.set(s.preset.value.capitalize())
        self._crf_var.set(s.crf)
        self._on_crf_change(s.crf)

        # Update resolution dropdown if AI recommends one
        if s.resolution:
            res_map = {
                "3840x2160": "3840x2160 (4K)",
                "2560x1440": "2560x1440 (2K)",
                "1920x1080": "1920x1080 (1080p)",
                "1280x720": "1280x720 (720p)",
                "854x480": "854x480 (480p)",
                "640x360": "640x360 (360p)",
            }
            self._resolution_var.set(res_map.get(s.resolution, "Original"))
        else:
            self._resolution_var.set("Original")

        # Show explanation
        self._ai_result_label.configure(text=result.explanation)
        self._ai_result_label.pack(fill="x", padx=16, pady=(0, 12))

        self._ai_btn.configure(text="✨ Get AI Recommendations", state="normal")

    # ── Compression ──────────────────────────────────────────────────────
    def _start_compression(self) -> None:
        if not self._input_path or self._compressing:
            return

        self._compressing = True
        self._compress_btn.configure(text="⏳ Compressing...", state="disabled")

        codec_map = {
            "H.264": VideoCodec.H264,
            "H.265": VideoCodec.H265,
            "VP9": VideoCodec.VP9,
            "AV1": VideoCodec.AV1,
        }
        # Parse resolution selection
        res_val = self._resolution_var.get()
        resolution = None
        if res_val != "Original":
            # Extract "WxH" from e.g. "1920x1080 (1080p)"
            resolution = res_val.split(" ")[0]

        s = CompressionSettings(
            video_codec=codec_map.get(self._codec_var.get(), VideoCodec.H264),
            preset=CompressionPreset(self._preset_var.get().lower()),
            crf=self._crf_var.get(),
            resolution=resolution,
        )

        def run():
            loop = asyncio.new_event_loop()
            try:
                job = loop.run_until_complete(
                    compress_video(self._input_path, s)
                )
                self.after(0, lambda: self._on_compress_done(job))
            except Exception as exc:
                msg = str(exc)
                self.after(0, lambda: self._on_compress_error(msg))
            finally:
                loop.close()

        threading.Thread(target=run, daemon=True).start()

    def _on_compress_error(self, error: str) -> None:
        self._compressing = False
        self._compress_btn.configure(text="⚡ Compress Video", state="normal")
        messagebox.showerror("Compression Failed", error)

    def _on_compress_done(self, job) -> None:
        self._compressing = False
        self._compress_btn.configure(text="⚡ Compress Video", state="normal")

        if job.status == "failed":
            messagebox.showerror("Compression Failed", job.error or "Unknown error")
            return

        self._show_results(job)

    # ── Results ──────────────────────────────────────────────────────────
    def _show_results(self, job) -> None:
        # Clear result frame
        for w in self._result_frame.winfo_children():
            w.destroy()

        card = ctk.CTkFrame(self._result_frame, fg_color=SUCCESS_DARK, corner_radius=12)
        card.pack(fill="x")

        # Header
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 12))

        ctk.CTkLabel(
            header, text="✅  Compression Complete",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=SUCCESS,
        ).pack(anchor="w")

        # Stats row
        stats = ctk.CTkFrame(card, fg_color="transparent")
        stats.pack(fill="x", padx=20, pady=8)
        stats.columnconfigure((0, 1, 2), weight=1)

        in_size = job.input_metadata.file_size_mb if job.input_metadata else 0
        out_size = job.output_metadata.file_size_mb if job.output_metadata else 0
        savings = in_size - out_size
        pct = (savings / in_size * 100) if in_size > 0 else 0

        # Original
        f1 = ctk.CTkFrame(stats, fg_color="transparent")
        f1.grid(row=0, column=0)
        ctk.CTkLabel(
            f1, text=f"{in_size:.1f} MB",
            font=ctk.CTkFont(size=28, weight="bold"), text_color=TEXT,
        ).pack()
        ctk.CTkLabel(
            f1, text="Original", font=ctk.CTkFont(size=12), text_color=TEXT_DIM,
        ).pack()

        # Arrow
        ctk.CTkLabel(
            stats, text="→", font=ctk.CTkFont(size=28), text_color=SUCCESS,
        ).grid(row=0, column=1)

        # Compressed
        f2 = ctk.CTkFrame(stats, fg_color="transparent")
        f2.grid(row=0, column=2)
        ctk.CTkLabel(
            f2, text=f"{out_size:.1f} MB",
            font=ctk.CTkFont(size=28, weight="bold"), text_color=SUCCESS,
        ).pack()
        ctk.CTkLabel(
            f2, text="Compressed", font=ctk.CTkFont(size=12), text_color=TEXT_DIM,
        ).pack()

        # Savings line
        savings_frame = ctk.CTkFrame(card, fg_color="#0f3d1a", corner_radius=8)
        savings_frame.pack(fill="x", padx=20, pady=8)

        inner = ctk.CTkFrame(savings_frame, fg_color="transparent")
        inner.pack(padx=16, pady=8)

        ctk.CTkLabel(
            inner,
            text=(
                f"Saved: {savings:.1f} MB ({pct:.1f}%)"
                f"    •    Ratio: {job.compression_ratio:.2f}x"
            ),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=SUCCESS,
        ).pack()

        # Output file path
        if job.output_file:
            output_path = str(Path(settings.output_dir) / job.output_file)

            path_frame = ctk.CTkFrame(card, fg_color="transparent")
            path_frame.pack(fill="x", padx=20, pady=(4, 4))
            ctk.CTkLabel(
                path_frame,
                text=f"📁 {output_path}",
                font=ctk.CTkFont(size=12),
                text_color=TEXT_DIM,
            ).pack(anchor="w")

            # Open folder button
            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(fill="x", padx=20, pady=(4, 16))

            ctk.CTkButton(
                btn_row,
                text="📂 Open Output Folder",
                fg_color=SUCCESS,
                hover_color="#16a34a",
                font=ctk.CTkFont(size=14, weight="bold"),
                height=42,
                command=lambda: self._open_folder(settings.output_dir),
            ).pack(side="left", padx=(0, 8))

            ctk.CTkButton(
                btn_row,
                text="🔄 Compress Another",
                fg_color=ACCENT,
                hover_color=ACCENT_HOVER,
                font=ctk.CTkFont(size=14, weight="bold"),
                height=42,
                command=self._reset,
            ).pack(side="left")

        # Side-by-side metadata comparison
        if job.input_metadata and job.output_metadata:
            comparison = ctk.CTkFrame(self._result_frame, fg_color="transparent")
            comparison.pack(fill="x", pady=(16, 0))
            comparison.columnconfigure((0, 1), weight=1)

            self._build_meta_comparison(comparison, job.input_metadata, "ORIGINAL", 0)
            self._build_meta_comparison(comparison, job.output_metadata, "COMPRESSED", 1)

    def _build_meta_comparison(self, parent, meta, label: str, col: int) -> None:
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=10)
        px = (0, 8) if col == 0 else (8, 0)
        card.grid(row=0, column=col, sticky="nsew", padx=px)

        ctk.CTkLabel(
            card, text=label,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=ACCENT_HOVER if col == 1 else TEXT_MUTED,
        ).pack(anchor="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            card, text=meta.filename,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT, wraplength=350, justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 8))

        ctk.CTkFrame(card, fg_color=BORDER, height=1).pack(fill="x", padx=16)

        fields = [
            ("Codec", meta.codec.upper()),
            ("Resolution", f"{meta.width}×{meta.height}"),
            ("Bitrate", f"{meta.bitrate} kbps"),
            ("FPS", str(int(meta.fps))),
            ("Audio", meta.audio_codec.upper() if meta.audio_codec else "None"),
            ("Size", f"{meta.file_size_mb:.1f} MB"),
        ]

        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=16, pady=12)

        for i, (k, v) in enumerate(fields):
            f = ctk.CTkFrame(grid, fg_color="transparent")
            f.pack(fill="x", pady=2)
            ctk.CTkLabel(
                f, text=f"{k}:", font=ctk.CTkFont(size=12),
                text_color=TEXT_MUTED, width=80, anchor="w",
            ).pack(side="left")
            ctk.CTkLabel(
                f, text=v, font=ctk.CTkFont(size=12, weight="bold"),
                text_color=TEXT,
            ).pack(side="left")

    @staticmethod
    def _open_folder(path: str) -> None:
        import subprocess

        abs_path = str(Path(path).resolve())
        if sys.platform == "win32":
            os.startfile(abs_path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", abs_path])
        else:
            subprocess.Popen(["xdg-open", abs_path])

    # ── Reset ────────────────────────────────────────────────────────────
    def _reset(self) -> None:
        self._input_path = None
        self._metadata = None
        self._ai_result = None
        self._compressing = False
        self._show_upload_view()


def main() -> None:
    app = VideoCompressorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
