from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Response
from fastapi.staticfiles import StaticFiles
from app.routers.summarize import router as summarize_router

app = FastAPI(title="Video 5-Line Summarizer")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Serve static UI
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(summarize_router)

@app.get("/health")
async def health() -> dict:
	return {"status": "ok"}

@app.get("/favicon.ico")
async def favicon() -> Response:
	return Response(status_code=204)

