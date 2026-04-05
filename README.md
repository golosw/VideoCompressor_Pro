# VideoCompressor Pro

Production-ready video compression application with AI-powered optimization.

## Architecture

```
VideoCompressor_Pro/
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── core/             # Config, logging, exceptions
│   │   ├── models/           # Pydantic schemas
│   │   ├── routers/          # API endpoints (video, ai)
│   │   └── services/         # Business logic (compression, AI)
│   ├── .env                  # Environment configuration
│   └── pyproject.toml        # Python dependencies
├── frontend/                 # React + Vite + Tailwind frontend
│   ├── src/
│   │   ├── components/       # UI components
│   │   ├── lib/              # API client
│   │   └── types/            # TypeScript types
│   └── package.json
└── README.md
```

## Features

- **Video Upload & Compression** — Upload videos (MP4, AVI, MKV, MOV, WebM, etc.) and compress with configurable settings
- **AI-Powered Optimization** — Get intelligent compression recommendations based on video metadata, target use case, and quality preferences
- **AI Chat Assistant** — Ask questions about video compression, codecs, and FFmpeg
- **Multiple Codecs** — H.264, H.265/HEVC, VP9 support
- **Quality Control** — CRF-based quality slider, preset selection, resolution scaling
- **Real-time Results** — Side-by-side comparison of original vs compressed metadata

## Prerequisites

- Python 3.12+
- Node.js 18+
- FFmpeg (installed on system)
- (Optional) Local LLM server (Ollama with Qwen2.5-Coder 7B) for AI features

## Setup

### Backend

```bash
cd backend
poetry install
poetry run fastapi dev app/main.py
```

The API will be available at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The UI will be available at `http://localhost:5173`.

### AI Layer (Optional)

Install [Ollama](https://ollama.ai) and pull the model:

```bash
ollama pull qwen2.5-coder:7b
ollama serve
```

The AI service auto-detects the LLM. If unavailable, it falls back to rule-based recommendations.

## API Endpoints

### Video
- `POST /video/upload` — Upload a video file
- `POST /video/compress` — Compress with settings
- `GET /video/jobs` — List compression jobs
- `GET /video/jobs/{id}` — Get job status
- `GET /video/download/{filename}` — Download compressed file
- `GET /video/formats` — List supported formats

### AI
- `POST /ai/analyze` — Get AI compression recommendations
- `POST /ai/chat` — Chat with AI assistant
- `GET /ai/health` — Check AI service status

### System
- `GET /healthz` — Health check
- `GET /` — API info

## Configuration

All settings are managed via `backend/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `true` | Enable debug logging |
| `MAX_FILE_SIZE_MB` | `500` | Max upload size |
| `AI_ENABLED` | `true` | Enable AI features |
| `AI_BASE_URL` | `http://localhost:11434/v1` | LLM API endpoint |
| `AI_MODEL` | `qwen2.5-coder:7b` | LLM model name |

## AI Usage Example

```bash
# Get AI recommendations for a video
curl -X POST http://localhost:8000/ai/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {
      "filename": "video.mp4",
      "format": "mp4",
      "duration": 120,
      "width": 1920,
      "height": 1080,
      "bitrate": 8000,
      "fps": 30,
      "codec": "h264",
      "file_size_bytes": 120000000,
      "file_size_mb": 114.4
    },
    "target_use": "web",
    "target_quality": "balanced"
  }'

# Chat with AI assistant
curl -X POST http://localhost:8000/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the difference between H.264 and H.265?"}'
```
