import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.api.routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="AI Request Classifier",
    description="Classifies internal team requests using a local LLM (Qwen2.5-3B via llama.cpp).",
    version="1.0.0",
)

app.include_router(router)

app.mount("/", StaticFiles(directory="src/static", html=True), name="static")
