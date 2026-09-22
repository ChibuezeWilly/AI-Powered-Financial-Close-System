"""FastAPI application entry point for the TallyFlow financial close platform."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database.config import settings
from .lifespan import app_lifespan
from .routers.auth import router as auth_router
from .routers.financial_close import router as financial_close_router
from .routers.integrations import router as integrations_router, slack_callback_router
from .routers.transactions import router as transactions_router
from .routers.workspace import router as workspace_router

app = FastAPI(
    title="TallyFlow API",
    description="AI-powered financial close and reconciliation platform.",
    version="0.3.0",
    lifespan=app_lifespan,
)


@app.get("/", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "tallyflow-api"}



app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_ORIGIN,
        "https://ai-powered-financial-close-system.vercel.app/",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
)

app.include_router(auth_router)
app.include_router(financial_close_router)
app.include_router(transactions_router)
app.include_router(workspace_router)
app.include_router(integrations_router)
app.include_router(slack_callback_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
