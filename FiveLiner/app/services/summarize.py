import os
from typing import List
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_PROMPT_TEMPLATE = (
	"You are a helpful assistant. Given a video transcript, write exactly 5 bullet lines summary in {lang}. "
	"Each line must be concise, factual, and under 24 Korean characters (or 18 English words). "
	"Include the most useful insights (who/what/why/how/results), numbers, and concrete takeaways. "
	"Avoid generic phrasing, avoid timestamps/speakers, no extra lines."
)

_MAX_CHARS = 12000  # avoid sending overly long inputs that can error out
_CHUNK_SIZE = 3500

async def summarize_text_to_three_lines(transcript: str, language: str = "ko") -> List[str]:
	api_key = os.getenv("OPENAI_API_KEY")
	if not api_key:
		raise RuntimeError("OPENAI_API_KEY not set in server process")
	client = OpenAI(api_key=api_key)

	# Normalize
	clean = (transcript or "").replace("\r", " ").replace("\n", " ")
	if not clean.strip():
		raise RuntimeError("Transcript empty after normalization")

	prompt = _PROMPT_TEMPLATE.format(lang=language)

	def _chat(messages):
		return client.chat.completions.create(
			model="gpt-4o-mini",
			messages=messages,
			temperature=0.1,
		)

	# If short enough, synthesize directly
	if len(clean) <= _MAX_CHARS:
		resp = _chat([
			{"role": "system", "content": "Summarize transcripts into exactly 5 highly useful bullet lines."},
			{"role": "user", "content": f"Language: {language}. {prompt}\nTranscript:\n{clean}"},
		])
		text = (resp.choices[0].message.content or "").strip()
		lines = [line.strip("- •\t ") for line in text.splitlines() if line.strip()]
		return lines[:5]

	# For longer content, do a two-pass map-reduce
	chunks: List[str] = []
	for i in range(0, len(clean), _CHUNK_SIZE):
		chunks.append(clean[i:i + _CHUNK_SIZE])

	# 1) Extract key facts per chunk
	chunk_notes: List[str] = []
	for idx, ch in enumerate(chunks):
		r = _chat([
			{"role": "system", "content": "Extract 5-8 factual, non-overlapping key points with numbers/names if present."},
			{"role": "user", "content": f"Language: {language}. From this transcript segment, list key facts as dash bullets, no fluff.\nSegment {idx+1}/{len(chunks)}:\n{ch}"},
		])
		notes = (r.choices[0].message.content or "").strip()
		chunk_notes.append(notes)

	# 2) Synthesize final 5 lines
	notes_joined = "\n".join(chunk_notes)
	resp2 = _chat([
		{"role": "system", "content": "Synthesize exactly 5 most useful bullet lines for a busy viewer."},
		{"role": "user", "content": f"Language: {language}. {prompt}\nKey facts collected from segments:\n{notes_joined}"},
	])
	text = (resp2.choices[0].message.content or "").strip()
	lines = [line.strip("- •\t ") for line in text.splitlines() if line.strip()]
	return lines[:5]

