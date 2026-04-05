import { Settings, Sparkles, Loader2, Zap } from "lucide-react";
import { useState } from "react";
import type {
  CompressionSettings,
  VideoMetadata,
  AIAnalysisResponse,
} from "../types/api";
import { aiAnalyze } from "../lib/api";

interface Props {
  metadata: VideoMetadata;
  onCompress: (settings: CompressionSettings) => void;
  compressing: boolean;
}

const PRESETS = [
  { value: "ultrafast", label: "Ultra Fast" },
  { value: "veryfast", label: "Very Fast" },
  { value: "fast", label: "Fast" },
  { value: "medium", label: "Medium" },
  { value: "slow", label: "Slow" },
  { value: "veryslow", label: "Very Slow" },
] as const;

const CODECS = [
  { value: "h264", label: "H.264 (Best Compatibility)" },
  { value: "h265", label: "H.265/HEVC (Smaller Files)" },
  { value: "vp9", label: "VP9 (Web Optimized)" },
] as const;

const QUALITIES = [
  { value: "highest", label: "Highest" },
  { value: "high", label: "High" },
  { value: "balanced", label: "Balanced" },
  { value: "low", label: "Low" },
  { value: "lowest", label: "Lowest" },
] as const;

const USE_CASES = [
  { value: "general", label: "General" },
  { value: "web", label: "Web" },
  { value: "mobile", label: "Mobile" },
  { value: "streaming", label: "Streaming" },
  { value: "social", label: "Social Media" },
  { value: "archive", label: "Archive" },
] as const;

export function CompressionForm({ metadata, onCompress, compressing }: Props) {
  const [settings, setSettings] = useState<CompressionSettings>({
    video_codec: "h264",
    audio_codec: "aac",
    preset: "medium",
    crf: 23,
    resolution: null,
    max_bitrate: null,
    audio_bitrate: 128,
    fps: null,
    strip_audio: false,
  });

  const [aiLoading, setAiLoading] = useState(false);
  const [aiResult, setAiResult] = useState<AIAnalysisResponse | null>(null);
  const [targetUse, setTargetUse] = useState("general");
  const [targetQuality, setTargetQuality] = useState("balanced");
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleAiOptimize = async () => {
    setAiLoading(true);
    setAiResult(null);
    try {
      const result = await aiAnalyze({
        metadata,
        target_use: targetUse,
        target_quality: targetQuality,
        max_file_size_mb: null,
      });
      setSettings(result.recommended_settings);
      setAiResult(result);
    } catch {
      // Silently fail - user can still set manually
    } finally {
      setAiLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Settings size={20} />
          Compression Settings
        </h3>
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          {showAdvanced ? "Simple Mode" : "Advanced Mode"}
        </button>
      </div>

      {/* AI Optimization Section */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-4 border border-purple-100">
        <h4 className="text-sm font-semibold text-purple-800 flex items-center gap-2 mb-3">
          <Sparkles size={16} />
          AI-Powered Optimization
        </h4>
        <div className="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Use Case
            </label>
            <select
              value={targetUse}
              onChange={(e) => setTargetUse(e.target.value)}
              className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-purple-300 focus:border-purple-400 outline-none"
            >
              {USE_CASES.map((uc) => (
                <option key={uc.value} value={uc.value}>
                  {uc.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Quality
            </label>
            <select
              value={targetQuality}
              onChange={(e) => setTargetQuality(e.target.value)}
              className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-purple-300 focus:border-purple-400 outline-none"
            >
              {QUALITIES.map((q) => (
                <option key={q.value} value={q.value}>
                  {q.label}
                </option>
              ))}
            </select>
          </div>
        </div>
        <button
          onClick={handleAiOptimize}
          disabled={aiLoading}
          className="w-full flex items-center justify-center gap-2 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-400 text-white text-sm font-medium py-2.5 px-4 rounded-lg transition-colors"
        >
          {aiLoading ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Sparkles size={16} />
              Get AI Recommendations
            </>
          )}
        </button>
        {aiResult && (
          <div className="mt-3 text-sm text-purple-800 bg-white bg-opacity-60 rounded-lg p-3">
            <p>{aiResult.explanation}</p>
            {aiResult.estimated_output_size_mb && (
              <p className="mt-1 font-medium">
                Estimated output: ~{aiResult.estimated_output_size_mb} MB
                {aiResult.estimated_compression_ratio &&
                  ` (${aiResult.estimated_compression_ratio}x compression)`}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Manual Settings */}
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Video Codec
            </label>
            <select
              value={settings.video_codec}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  video_codec: e.target.value as CompressionSettings["video_codec"],
                })
              }
              className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-300 focus:border-blue-400 outline-none"
            >
              {CODECS.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Speed Preset
            </label>
            <select
              value={settings.preset}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  preset: e.target.value as CompressionSettings["preset"],
                })
              }
              className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-300 focus:border-blue-400 outline-none"
            >
              {PRESETS.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Quality (CRF): {settings.crf}
            <span className="text-gray-400 ml-2 font-normal">
              {settings.crf <= 18
                ? "Near Lossless"
                : settings.crf <= 23
                  ? "High Quality"
                  : settings.crf <= 28
                    ? "Balanced"
                    : settings.crf <= 35
                      ? "Low Quality"
                      : "Very Low"}
            </span>
          </label>
          <input
            type="range"
            min={0}
            max={51}
            value={settings.crf}
            onChange={(e) =>
              setSettings({ ...settings, crf: Number(e.target.value) })
            }
            className="w-full accent-blue-500"
          />
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>Best Quality</span>
            <span>Smallest File</span>
          </div>
        </div>

        {showAdvanced && (
          <div className="space-y-4 pt-4 border-t border-gray-100">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Resolution
                </label>
                <select
                  value={settings.resolution || ""}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      resolution: e.target.value || null,
                    })
                  }
                  className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-300 focus:border-blue-400 outline-none"
                >
                  <option value="">Original</option>
                  <option value="3840x2160">4K (3840x2160)</option>
                  <option value="1920x1080">1080p (1920x1080)</option>
                  <option value="1280x720">720p (1280x720)</option>
                  <option value="854x480">480p (854x480)</option>
                  <option value="640x360">360p (640x360)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Audio Bitrate (kbps)
                </label>
                <select
                  value={settings.audio_bitrate}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      audio_bitrate: Number(e.target.value),
                    })
                  }
                  className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-300 focus:border-blue-400 outline-none"
                >
                  <option value={64}>64 kbps</option>
                  <option value={96}>96 kbps</option>
                  <option value={128}>128 kbps</option>
                  <option value={192}>192 kbps</option>
                  <option value={256}>256 kbps</option>
                  <option value={320}>320 kbps</option>
                </select>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="strip-audio"
                checked={settings.strip_audio}
                onChange={(e) =>
                  setSettings({ ...settings, strip_audio: e.target.checked })
                }
                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
              />
              <label htmlFor="strip-audio" className="text-sm text-gray-700">
                Remove audio track
              </label>
            </div>
          </div>
        )}
      </div>

      <button
        onClick={() => onCompress(settings)}
        disabled={compressing}
        className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-3 px-6 rounded-xl transition-colors text-base"
      >
        {compressing ? (
          <>
            <Loader2 size={20} className="animate-spin" />
            Compressing...
          </>
        ) : (
          <>
            <Zap size={20} />
            Compress Video
          </>
        )}
      </button>
    </div>
  );
}
