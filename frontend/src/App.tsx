import { useState } from "react";
import { Film, MessageSquare, X } from "lucide-react";
import type {
  VideoMetadata,
  CompressionSettings,
  CompressionJob,
} from "./types/api";
import { compressVideo } from "./lib/api";
import { VideoUploader } from "./components/VideoUploader";
import { VideoInfo } from "./components/VideoInfo";
import { CompressionForm } from "./components/CompressionForm";
import { CompressionResult } from "./components/CompressionResult";
import { AIChat } from "./components/AIChat";

function App() {
  const [metadata, setMetadata] = useState<VideoMetadata | null>(null);
  const [uploadedFilename, setUploadedFilename] = useState<string | null>(null);
  const [compressing, setCompressing] = useState(false);
  const [job, setJob] = useState<CompressionJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showChat, setShowChat] = useState(false);

  const handleUpload = (meta: VideoMetadata, filename: string) => {
    setMetadata(meta);
    setUploadedFilename(filename);
    setJob(null);
    setError(null);
  };

  const handleCompress = async (settings: CompressionSettings) => {
    if (!uploadedFilename) return;
    setCompressing(true);
    setError(null);
    setJob(null);

    try {
      const result = await compressVideo(uploadedFilename, settings);
      setJob(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Compression failed");
    } finally {
      setCompressing(false);
    }
  };

  const handleReset = () => {
    setMetadata(null);
    setUploadedFilename(null);
    setJob(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 p-2 rounded-xl">
              <Film className="text-white" size={24} />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                VideoCompressor Pro
              </h1>
              <p className="text-xs text-gray-500">
                AI-powered video compression
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {metadata && (
              <button
                onClick={handleReset}
                className="text-sm text-gray-600 hover:text-gray-800 px-3 py-1.5 rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors"
              >
                New Video
              </button>
            )}
            <button
              onClick={() => setShowChat(!showChat)}
              className={`flex items-center gap-2 text-sm font-medium px-3 py-1.5 rounded-lg transition-colors ${
                showChat
                  ? "bg-purple-100 text-purple-700 border border-purple-200"
                  : "text-gray-600 hover:text-gray-800 border border-gray-300 hover:bg-gray-50"
              }`}
            >
              <MessageSquare size={16} />
              AI Chat
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="flex gap-6">
          <div className={`space-y-6 ${showChat ? "flex-1" : "w-full"}`}>
            {!metadata ? (
              <div>
                <div className="text-center mb-8">
                  <h2 className="text-3xl font-bold text-gray-900 mb-2">
                    Compress Your Videos
                  </h2>
                  <p className="text-gray-600">
                    Upload a video and let AI optimize compression settings for
                    the best quality-to-size ratio.
                  </p>
                </div>
                <VideoUploader onUpload={handleUpload} />
              </div>
            ) : (
              <>
                <VideoInfo metadata={metadata} label="Uploaded Video" />

                {!job && (
                  <CompressionForm
                    metadata={metadata}
                    onCompress={handleCompress}
                    compressing={compressing}
                  />
                )}

                {error && (
                  <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">
                    {error}
                  </div>
                )}

                {job && <CompressionResult job={job} />}
              </>
            )}
          </div>

          {showChat && (
            <div className="w-96 shrink-0">
              <div className="sticky top-8">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-500">
                    AI Assistant
                  </span>
                  <button
                    onClick={() => setShowChat(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X size={16} />
                  </button>
                </div>
                <AIChat videoContext={metadata || undefined} />
              </div>
            </div>
          )}
        </div>
      </main>

      <footer className="border-t border-gray-200 mt-16">
        <div className="max-w-5xl mx-auto px-6 py-4 text-center text-sm text-gray-400">
          VideoCompressor Pro &mdash; AI-powered video compression
        </div>
      </footer>
    </div>
  );
}

export default App;
