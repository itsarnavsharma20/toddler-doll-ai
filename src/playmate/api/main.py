"""FastAPI app. Run: uvicorn playmate.api.main:app --app-dir src --reload"""
import threading
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from playmate.core import config, languages, metrics
from playmate.pipeline import chat as chat_pipeline
from playmate.pipeline import voice as voice_pipeline
from playmate.services import llm


def _warmup_quietly():
    try:
        llm.warmup()
    except llm.LLMError:
        pass


@asynccontextmanager
async def lifespan(app):
    if config.load_settings()["llm"].get("warmup_on_start"):
        threading.Thread(target=_warmup_quietly, daemon=True).start()
    yield


app = FastAPI(title="Playmate", lifespan=lifespan)


class ChatRequest(BaseModel):
    text: str
    language: Optional[str] = None


@app.get("/v1/health")
def health():
    return {"status": "ok", "llm": llm.health()}


@app.get("/v1/languages")
def get_languages():
    return languages.describe()


@app.post("/v1/warmup")
def warmup():
    try:
        llm.warmup()
    except llm.LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {"status": "ready"}


@app.get("/v1/stats")
def stats():
    return metrics.snapshot()


@app.post("/v1/voice")
async def voice(request: Request, language: Optional[str] = None):
    """Body is the raw audio (wav, mp3, ogg...). Returns transcript, reply and base64 audio. Nothing is stored."""
    audio = await request.body()
    if len(audio) > config.load_settings()["voice"]["max_audio_bytes"]:
        raise HTTPException(status_code=413, detail="audio too large")
    return await voice_pipeline.handle(audio, language)


@app.post("/v1/chat")
@app.post("/chat", include_in_schema=False)  # old path, kept so existing callers still work
def chat(request: ChatRequest):
    return chat_pipeline.respond(request.text, request.language)
