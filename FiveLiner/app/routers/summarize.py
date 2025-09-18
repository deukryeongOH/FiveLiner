from fastapi import APIRouter, HTTPException
from app.schemas import SummarizeRequest, SummarizeResponse
from app.services.transcript import extract_transcript_text
from app.services.summarize import summarize_text_to_three_lines

router = APIRouter(prefix="", tags=["summarize"])  # root-level

@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(req: SummarizeRequest) -> SummarizeResponse:
	try:
		text = extract_transcript_text(req.url)
		if not text or len(text.strip()) == 0:
			raise HTTPException(status_code=400, detail="Transcript not found or empty.")
		lines = await summarize_text_to_three_lines(text, req.language or "ko")
		if not lines or len(lines) == 0:
			raise HTTPException(status_code=502, detail="Failed to generate summary.")
		return SummarizeResponse(summary_lines=lines, language=req.language or "ko")
	except HTTPException:
		raise
	except RuntimeError as e:
		raise HTTPException(status_code=500, detail=str(e))
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Internal error: {e}")

