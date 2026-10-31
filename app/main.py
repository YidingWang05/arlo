from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app = FastAPI(
    title="Arlo Multimodal Assistant (Gemini 4 Argon Core)",
    description="Track 2 — Multimodal & Human-Centric AI powered by Gemini 4 Argon",
    version="4.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def root():
    return {
        "project": "Arlo Multimodal Living Assistant",
        "foundation_model": "gemini-4-argon",
        "version": "4.0.0",
        "status": "ready",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
