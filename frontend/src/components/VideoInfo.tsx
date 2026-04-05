import { Film, Clock, Monitor, Gauge, Volume2, HardDrive } from "lucide-react";
import type { VideoMetadata } from "../types/api";

interface Props {
  metadata: VideoMetadata;
  label?: string;
}

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function formatSize(mb: number): string {
  if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`;
  return `${mb.toFixed(1)} MB`;
}

export function VideoInfo({ metadata, label }: Props) {
  const items = [
    { icon: Film, label: "Codec", value: metadata.codec.toUpperCase() },
    { icon: Clock, label: "Duration", value: formatDuration(metadata.duration) },
    { icon: Monitor, label: "Resolution", value: `${metadata.width}x${metadata.height}` },
    { icon: Gauge, label: "Bitrate", value: `${metadata.bitrate} kbps` },
    { icon: Film, label: "FPS", value: `${metadata.fps}` },
    { icon: Volume2, label: "Audio", value: metadata.audio_codec?.toUpperCase() || "None" },
    { icon: HardDrive, label: "Size", value: formatSize(metadata.file_size_mb) },
  ];

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      {label && (
        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
          {label}
        </h3>
      )}
      <p className="font-medium text-gray-900 mb-4 truncate" title={metadata.filename}>
        {metadata.filename}
      </p>
      <div className="grid grid-cols-2 gap-3">
        {items.map((item) => (
          <div key={item.label} className="flex items-center gap-2 text-sm">
            <item.icon size={14} className="text-gray-400 shrink-0" />
            <span className="text-gray-500">{item.label}:</span>
            <span className="font-medium text-gray-800">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
