"""FastAPI app. Run: uvicorn playmate.api.main:app --app-dir src --reload"""
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

from playmate.pipeline import chat as chat_pipeline

app = FastAPI(title="Playmate")


class ChatRequest(BaseModel):
    text: str
    language: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(request: ChatRequest):
    return chat_pipeline.respond(request.text, request.language)
