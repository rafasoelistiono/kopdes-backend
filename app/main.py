from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.routes import auth, health, meta, lookups, dashboards, etl, ui_screens, komi

setup_logging()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_prefix = settings.api_prefix

app.include_router(auth.router, prefix=api_prefix, tags=["Auth"])
app.include_router(health.router, tags=["Health"])
app.include_router(meta.router, prefix=api_prefix, tags=["Meta"])
app.include_router(lookups.router, prefix=api_prefix, tags=["Lookups"])
app.include_router(etl.router, prefix=api_prefix, tags=["ETL"])
app.include_router(ui_screens.router, prefix=api_prefix, tags=["UI Screens"])
app.include_router(dashboards.router, prefix=api_prefix, tags=["Dashboards"])
app.include_router(komi.router, prefix="/api/komi", tags=["KOMI"])
app.include_router(komi.router, prefix=f"{api_prefix}/komi", tags=["KOMI"])


@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
    }
