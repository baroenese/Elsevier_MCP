"""FastAPI application entry point."""
import sys
from pathlib import Path

# Ensure packages/elsevier-mcp is importable even without a venv editable install
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'packages' / 'elsevier-mcp'))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import load_config_into_env, settings
from app.routers import health, journals, papers, trends

load_config_into_env()

app = FastAPI(
    title='Elsevier Academic API',
    version='2.0.0',
    docs_url='/api/docs',
    openapi_url='/api/openapi.json'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(papers.router, prefix="/api")
app.include_router(trends.router, prefix="/api")
app.include_router(journals.router, prefix="/api")
