import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import BASE_DIR, GROQ_API_KEY
from app.services.pipeline import get_retriever

logger = logging.getLogger("rulebook_qa")

app = FastAPI(title="Bannerworth University Rulebook QA")
app.include_router(router)


@app.on_event("startup")
def startup() -> None:
    if not GROQ_API_KEY:
        logger.warning(
            "GROQ_API_KEY is not set — answers will fall back to a "
            "template built directly from retrieved passages instead of "
            "an LLM-written response. Copy .env.example to .env and set "
            "GROQ_API_KEY to enable generation."
        )
    # Warm up the embedding model + corpus index at startup rather than on
    # the first request.
    get_retriever()


app.mount("/", StaticFiles(directory=str(BASE_DIR / "static"), html=True), name="static")
