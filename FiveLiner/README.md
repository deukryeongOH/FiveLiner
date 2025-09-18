# Video 3-Line Summarizer (FastAPI)

A small FastAPI service: send a short video URL (YouTube prioritized), it fetches transcript and returns a 3-line summary using OpenAI.

## Setup (Windows)

1. Install Python 3.10+
2. In PowerShell:

```powershell
cd C:\Users\deukr\deep1
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. Set environment variable (replace with your key):

```powershell
$env:OPENAI_API_KEY = "sk-..."
```

4. Run the server:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Open the UI:
- `http://127.0.0.1:8000/static/index.html`

## API

- POST `/summarize`

Request body:

```json
{ "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "language": "ko" }
```

Response body:

```json
{ "summary_lines": ["...","...","..."], "language": "ko" }
```

## Captions missing? We now fallback automatically
- First, we try YouTube captions (ko/en, auto-generated if needed).
- If no captions are available, we automatically download audio via yt-dlp and transcribe using OpenAI (`gpt-4o-mini-transcribe`).
- This can be slower and uses your OpenAI credits.

### Notes
- On some videos, yt-dlp may need ffmpeg in PATH for remuxing. If you encounter download errors:
  - Install ffmpeg and add it to PATH, or install a desktop build like `ffmpeg.exe` and add its folder to PATH.
- Corporate firewalls/VPN may block downloads.
- Only use this feature if you’re okay with audio being briefly stored in a temp folder during processing.

