import { Download, CheckCircle, TrendingDown, ArrowRight } from "lucide-react";
import type { CompressionJob } from "../types/api";
import { getDownloadUrl } from "../lib/api";
import { VideoInfo } from "./VideoInfo";

interface Props {
  job: CompressionJob;
}

export function CompressionResult({ job }: Props) {
  if (job.status === "failed") {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-5">
        <h3 className="text-lg font-semibold text-red-800 mb-2">
          Compression Failed
        </h3>
        <p className="text-sm text-red-700">{job.error || "Unknown error"}</p>
      </div>
    );
  }

  const inputSize = job.input_metadata?.file_size_mb || 0;
  const outputSize = job.output_metadata?.file_size_mb || 0;
  const savings = inputSize - outputSize;
  const savingsPercent =
    inputSize > 0 ? ((savings / inputSize) * 100).toFixed(1) : "0";

  return (
    <div className="space-y-4">
      <div className="bg-green-50 border border-green-200 rounded-xl p-5">
        <div className="flex items-center gap-2 mb-4">
          <CheckCircle className="text-green-600" size={24} />
          <h3 className="text-lg font-semibold text-green-800">
            Compression Complete
          </h3>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">
              {inputSize.toFixed(1)} MB
            </p>
            <p className="text-xs text-gray-500">Original</p>
          </div>
          <div className="text-center flex flex-col items-center justify-center">
            <ArrowRight className="text-green-500" size={24} />
            <TrendingDown className="text-green-500" size={16} />
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-700">
              {outputSize.toFixed(1)} MB
            </p>
            <p className="text-xs text-gray-500">Compressed</p>
          </div>
        </div>

        <div className="flex items-center justify-between bg-white bg-opacity-60 rounded-lg p-3 mb-4">
          <div className="text-sm">
            <span className="text-gray-600">Saved: </span>
            <span className="font-semibold text-green-700">
              {savings.toFixed(1)} MB ({savingsPercent}%)
            </span>
          </div>
          <div className="text-sm">
            <span className="text-gray-600">Ratio: </span>
            <span className="font-semibold text-green-700">
              {job.compression_ratio}x
            </span>
          </div>
        </div>

        {job.output_file && (
          <a
            href={getDownloadUrl(job.output_file)}
            download
            className="w-full flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-xl transition-colors"
          >
            <Download size={20} />
            Download Compressed Video
          </a>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        {job.input_metadata && (
          <VideoInfo metadata={job.input_metadata} label="Original" />
        )}
        {job.output_metadata && (
          <VideoInfo metadata={job.output_metadata} label="Compressed" />
        )}
      </div>
    </div>
  );
}
