from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analysis, api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Enable CORS (defaults to localhost:5173 / 127.0.0.1:5173, configurable via CORS_ORIGINS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Versioned API routes (/api/v1)
app.include_router(api_router, prefix=settings.API_V1_STR)

# Top-level API alias (/api/analysis)
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint to verify backend service status."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }
