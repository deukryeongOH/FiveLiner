from typing import List, Optional
import re
import os
import tempfile
from contextlib import contextmanager
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from openai import OpenAI

_YT_REGEX = re.compile(r"(?:v=|youtu\.be/|youtube\.com/watch\?v=)([\w-]{11})")


def _extract_video_id(url: str) -> str:
	# Ensure plain string (Pydantic HttpUrl may be passed)
	url = str(url)
	match = _YT_REGEX.search(url)
	if match:
		return match.group(1)
	candidate = url.strip().split("/")[-1]
	return candidate[:11]


def _extract_captions_text(video_id: str) -> str:
	try:
		transcripts: List[dict] = YouTubeTranscriptApi.get_transcript(video_id, languages=["ko", "en"])  # type: ignore
		return " ".join(chunk.get("text", "") for chunk in transcripts)
	except (TranscriptsDisabled, NoTranscriptFound):
		try:
			alt = YouTubeTranscriptApi.list_transcripts(video_id)
			en_sub = alt.find_generated_transcript(["en"])  # type: ignore
			trans = en_sub.fetch()  # type: ignore
			return " ".join(chunk.get("text", "") for chunk in trans)
		except Exception:
			return ""
	except VideoUnavailable:
		return ""
	except Exception:
		return ""


@contextmanager
def _temp_dir(prefix: str = "yt_audio_"):
	d = tempfile.mkdtemp(prefix=prefix)
	try:
		yield d
	finally:
		import shutil
		shutil.rmtree(d, ignore_errors=True)


class _YDLLogger:
	def __init__(self) -> None:
		self.messages: List[str] = []
	def debug(self, msg):
		self.messages.append(str(msg))
	def warning(self, msg):
		self.messages.append(f"WARN: {msg}")
	def error(self, msg):
		self.messages.append(f"ERROR: {msg}")


def _download_audio_with_ytdlp(url: str) -> Optional[str]:
	try:
		from yt_dlp import YoutubeDL  # type: ignore
	except Exception:
		return None
	logger = _YDLLogger()
	with _temp_dir() as d:
		outtmpl = os.path.join(d, "%(id)s.%(ext)s")
		ffmpeg_dir = os.getenv("FFMPEG_BIN")  # path to folder containing ffmpeg.exe
		cookiefile = os.getenv("YTDLP_COOKIES_PATH")  # optional Netscape cookie file
		proxy = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
		ydl_opts = {
			"format": "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best",
			"noplaylist": True,
			"outtmpl": outtmpl,
			"quiet": True,
			"retries": 3,
			"fragment_retries": 3,
			"geo_bypass": True,
			"nocheckcertificate": True,
			"logger": logger,
		}
		if ffmpeg_dir and os.path.isdir(ffmpeg_dir):
			ydl_opts["ffmpeg_location"] = ffmpeg_dir
		if cookiefile and os.path.isfile(cookiefile):
			ydl_opts["cookiefile"] = cookiefile
		if proxy:
			ydl_opts["proxy"] = proxy
		try:
			with YoutubeDL(ydl_opts) as ydl:
				info = ydl.extract_info(str(url), download=True)
				filepath = None
				if isinstance(info, dict):
					if "requested_downloads" in info and info["requested_downloads"]:
						filepath = info["requested_downloads"][0].get("filepath")
					elif "_filename" in info:
						filepath = info.get("_filename")
					else:
						vid = info.get("id")
						ext = info.get("ext", "m4a")
						candidate = os.path.join(d, f"{vid}.{ext}")
						filepath = candidate if os.path.exists(candidate) else None
				if filepath and os.path.exists(filepath):
					final_dir = tempfile.mkdtemp(prefix="yt_audio_final_")
					final_path = os.path.join(final_dir, os.path.basename(filepath))
					import shutil
					shutil.move(filepath, final_path)
					return final_path
				return None
		except Exception:
			# Persist last few log lines to help diagnose
			errlog = " | ".join(logger.messages[-6:]) if logger.messages else ""
			os.environ["YTDLP_LAST_ERROR"] = errlog
			return None


def _transcribe_with_openai(audio_path: str) -> str:
	api_key = os.getenv("OPENAI_API_KEY")
	if not api_key:
		raise RuntimeError("OPENAI_API_KEY not set in server process")
	client = OpenAI(api_key=api_key)
	try:
		with open(audio_path, "rb") as f:
			resp = client.audio.transcriptions.create(
				model="gpt-4o-mini-transcribe",
				file=f,
			)
			text = getattr(resp, "text", "") or ""
			return text
	except Exception as e:
		raise RuntimeError(f"OpenAI transcription failed: {e}")
	finally:
		try:
			import shutil
			shutil.rmtree(os.path.dirname(audio_path), ignore_errors=True)
		except Exception:
			pass


def extract_transcript_text(url: str) -> str:
	# Ensure string
	url = str(url)
	video_id = _extract_video_id(url)
	if video_id and len(video_id) >= 5:
		cap = _extract_captions_text(video_id)
		if cap.strip():
			return cap
	# Fallback: download audio and transcribe
	audio = _download_audio_with_ytdlp(url)
	if not audio:
		last = os.getenv("YTDLP_LAST_ERROR", "")
		raise RuntimeError(f"Audio download failed (yt-dlp). Install ffmpeg and check network/URL. {last}")
	text = _transcribe_with_openai(audio)
	if not text.strip():
		raise RuntimeError("Transcription returned empty text.")
	return text

