export interface VideoMetadata {
  filename: string;
  format: string;
  duration: number;
  width: number;
  height: number;
  bitrate: number;
  fps: number;
  codec: string;
  audio_codec: string | null;
  audio_bitrate: number | null;
  file_size_bytes: number;
  file_size_mb: number;
}

export interface CompressionSettings {
  video_codec: "h264" | "h265" | "vp9" | "av1";
  audio_codec: "aac" | "opus" | "mp3" | "copy";
  preset:
    | "ultrafast"
    | "superfast"
    | "veryfast"
    | "faster"
    | "fast"
    | "medium"
    | "slow"
    | "slower"
    | "veryslow";
  crf: number;
  resolution: string | null;
  max_bitrate: number | null;
  audio_bitrate: number;
  fps: number | null;
  strip_audio: boolean;
}

export interface CompressionJob {
  job_id: string;
  status: string;
  input_file: string;
  output_file: string | null;
  settings: CompressionSettings;
  input_metadata: VideoMetadata | null;
  output_metadata: VideoMetadata | null;
  compression_ratio: number | null;
  progress: number;
  error: string | null;
}

export interface AIAnalysisRequest {
  metadata: VideoMetadata;
  target_use: string;
  target_quality: string;
  max_file_size_mb: number | null;
}

export interface AIAnalysisResponse {
  recommended_settings: CompressionSettings;
  explanation: string;
  estimated_output_size_mb: number | null;
  estimated_compression_ratio: number | null;
}

export interface AIChatMessage {
  role: "user" | "assistant";
  content: string;
}
