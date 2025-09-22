# FiveLiner

**프로젝트 개요: 사용자가 제공한 영상 링크의 내용을 AI가 분석해 핵심 내용을 5줄 이내의 텍스트로 자동 요약하여 제공하는 FastAPI 웹 기반 서비스를 구현해 사용자의 시간 절약 및 정보 습득 효율성 증대를 목표로 한다.**


# 주요 기능

**자막 기반 요약: 입력된 동영상의 자막(캡션)을 자동으로 추출하고 이 자막을 바탕으로 OpenAI의 AI 모델을 활용해 내용을 요약한다.**

**음성 전사: 유튜브에 제공되는 자막(ko or en, 자동 생성 자막 포함)을 사용하려 시도한다. 만약 자막이 없다면, yt-dlp를 이용해 비디오 오디오를 자동으로 다운로드 한 뒤 OpenAI의 음성 변환 모델(gpt-4o-mini-transcribe)로 변환한다.**

**5줄 요약: 변환된 텍스트 내용을 핵심적인 5개의 문장으로 간결하게 요약하여 제공한다.**

**다국어 지원: 영어(en)와 한국어(ko)를 포함한 다양한 언어로 요약 기능을 제공한다.**




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



<img width="1686" height="1001" alt="스크린샷 2025-09-18 172457" src="https://github.com/user-attachments/assets/69ed21ca-cd03-48c2-ae13-b3e0e139c7a3" />

<img width="1642" height="1047" alt="스크린샷 2025-09-18 172441" src="https://github.com/user-attachments/assets/dc420528-cc2d-4d22-a1b8-d03cc064676f" />
