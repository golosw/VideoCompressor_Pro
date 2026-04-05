# Testing VideoCompressor Pro

## Overview
End-to-end testing of the VideoCompressor Pro application (FastAPI backend + React frontend).

## Prerequisites
- FFmpeg installed (`/usr/bin/ffmpeg`)
- Poetry installed for backend dependency management
- Node.js + npm for frontend

## Environment Setup

### 1. Start Backend
```bash
cd backend
cp .env.example .env  # if .env doesn't exist
poetry run fastapi dev app/main.py
# Runs on http://localhost:8000
# Verify: curl http://localhost:8000/healthz
```

### 2. Start Frontend
```bash
cd frontend
npm run dev
# Runs on http://localhost:5173
```

### 3. Create Test Video
```bash
ffmpeg -y -f lavfi -i testsrc=duration=5:size=640x480:rate=30 \
  -f lavfi -i sine=frequency=440:duration=5 \
  -c:v libx264 -c:a aac -shortest test_sample.mp4
```
This creates a small (~80KB) 5-second test video suitable for quick testing.

## Test Flow

### Upload
1. Open http://localhost:5173
2. Click the upload area or drag-drop a video file
3. Verify metadata card shows: codec, resolution, duration, bitrate, FPS, audio codec, file size

### AI Recommendations
1. Click "Get AI Recommendations" button
2. If no local LLM (Ollama) is running, expect **rule-based fallback** response
3. Verify explanation text appears below the button
4. Note: The estimated output size might show "0" for very small test files — this is a known cosmetic issue with the fallback formula

### Compression
1. Click "Compress Video" button
2. Wait for compression to complete (button shows spinner)
3. Verify "Compression Complete" banner appears with:
   - Original and compressed file sizes
   - Savings in MB and percentage
   - Compression ratio
   - Side-by-side metadata comparison (Original vs Compressed)

### Download
1. Click "Download Compressed Video" button
2. Verify browser initiates file download

### AI Chat
1. Click "AI Chat" button in header
2. Verify panel opens with greeting message and video context badge
3. Type a message and press Enter
4. Without LLM: expect "AI service is currently unreachable" fallback
5. Close panel via X button or clicking "AI Chat" again

### Reset
1. Click "New Video" button in header
2. Verify app returns to initial upload state

## Known Behaviors
- **No LLM available**: AI features degrade gracefully — `/ai/analyze` returns rule-based settings, `/ai/chat` returns a friendly error
- **File naming**: Backend saves uploads with UUID filenames. The compress endpoint finds files by extension fallback, which works when only one file of that type exists
- **Compression is synchronous**: Long videos will block the HTTP response. Not an issue for small test files

## Devin Secrets Needed
None — all testing is local with no authentication required.
