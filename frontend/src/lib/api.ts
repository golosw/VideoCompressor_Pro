import type {
  AIAnalysisRequest,
  AIAnalysisResponse,
  CompressionJob,
  CompressionSettings,
  VideoMetadata,
} from "../types/api";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, options);
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export async function uploadVideo(file: File): Promise<VideoMetadata> {
  const form = new FormData();
  form.append("file", file);
  return request<VideoMetadata>("/video/upload", {
    method: "POST",
    body: form,
  });
}

export async function compressVideo(
  filename: string,
  settings?: CompressionSettings
): Promise<CompressionJob> {
  const params = new URLSearchParams({ filename });
  return request<CompressionJob>(`/video/compress?${params}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: settings ? JSON.stringify(settings) : JSON.stringify({}),
  });
}

export async function getJobs(): Promise<CompressionJob[]> {
  return request<CompressionJob[]>("/video/jobs");
}

export async function getJob(jobId: string): Promise<CompressionJob> {
  return request<CompressionJob>(`/video/jobs/${jobId}`);
}

export function getDownloadUrl(filename: string): string {
  return `${API_URL}/video/download/${filename}`;
}

export async function aiAnalyze(
  req: AIAnalysisRequest
): Promise<AIAnalysisResponse> {
  return request<AIAnalysisResponse>("/ai/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}

export async function aiChat(
  message: string,
  context?: VideoMetadata
): Promise<string> {
  const res = await request<{ response: string }>("/ai/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, context: context || null }),
  });
  return res.response;
}

export async function aiHealth(): Promise<{
  status: string;
  model: string;
}> {
  return request("/ai/health");
}
