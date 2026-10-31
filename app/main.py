from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config import settings

app = FastAPI(
    title="Arlo Multimodal Assistant (Gemini 4 Argon Core)",
    description="Track 2 — Multimodal & Human-Centric AI powered by Gemini 4 Argon",
    version="4.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def root():
    return {
        "project": "Arlo Multimodal Living Assistant",
        "foundation_model": settings.GEMINI_MODEL_NAME,
        "version": "4.0.0",
        "status": "ready",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
