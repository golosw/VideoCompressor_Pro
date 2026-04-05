import { Upload, Film, AlertCircle } from "lucide-react";
import { useState, useCallback } from "react";
import type { VideoMetadata } from "../types/api";
import { uploadVideo } from "../lib/api";

interface Props {
  onUpload: (meta: VideoMetadata, filename: string) => void;
}

export function VideoUploader({ onUpload }: Props) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const handleFile = useCallback(
    async (file: File) => {
      setError(null);
      setUploading(true);
      setProgress(10);

      try {
        const interval = setInterval(() => {
          setProgress((p) => Math.min(p + 15, 90));
        }, 300);

        const meta = await uploadVideo(file);
        clearInterval(interval);
        setProgress(100);

        setTimeout(() => {
          setUploading(false);
          setProgress(0);
          onUpload(meta, meta.filename);
        }, 400);
      } catch (err) {
        setUploading(false);
        setProgress(0);
        setError(err instanceof Error ? err.message : "Upload failed");
      }
    },
    [onUpload]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div className="w-full">
      <div
        className={`
          relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer
          transition-all duration-300 ease-in-out
          ${
            dragging
              ? "border-blue-400 bg-blue-50 scale-[1.02]"
              : "border-gray-300 hover:border-blue-300 hover:bg-gray-50"
          }
          ${uploading ? "pointer-events-none opacity-80" : ""}
        `}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() =>
          !uploading &&
          document.getElementById("video-file-input")?.click()
        }
      >
        <input
          id="video-file-input"
          type="file"
          accept="video/*,.mp4,.avi,.mkv,.mov,.wmv,.flv,.webm,.m4v,.mpeg,.mpg,.3gp"
          className="hidden"
          onChange={handleInput}
        />

        {uploading ? (
          <div className="space-y-4">
            <Film className="mx-auto text-blue-500 animate-pulse" size={48} />
            <p className="text-lg font-medium text-gray-700">
              Uploading video...
            </p>
            <div className="w-64 mx-auto bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <Upload className="mx-auto text-gray-400" size={48} />
            <div>
              <p className="text-lg font-medium text-gray-700">
                Drop your video here or click to browse
              </p>
              <p className="text-sm text-gray-500 mt-1">
                Supports MP4, AVI, MKV, MOV, WebM, and more (up to 500MB)
              </p>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <AlertCircle size={16} />
          {error}
        </div>
      )}
    </div>
  );
}
