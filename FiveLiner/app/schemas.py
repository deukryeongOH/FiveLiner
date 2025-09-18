from typing import List, Optional
from pydantic import BaseModel, HttpUrl

class SummarizeRequest(BaseModel):
	url: HttpUrl
	language: Optional[str] = "ko"

class SummarizeResponse(BaseModel):
	summary_lines: List[str]
	language: str

