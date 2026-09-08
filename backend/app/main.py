from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from app.api.routes import analysis, api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Enable CORS (defaults to localhost:5173 / 127.0.0.1:5173,
# configurable via CORS_ORIGINS & CORS_ORIGIN_REGEX)
cors_kwargs: dict[str, Any] = {
    "allow_origins": settings.cors_origins_list,
    "allow_credentials": "*" not in settings.cors_origins_list,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
if settings.CORS_ORIGIN_REGEX:
    cors_kwargs["allow_origin_regex"] = settings.CORS_ORIGIN_REGEX

app.add_middleware(CORSMiddleware, **cors_kwargs)

# Versioned API routes (/api/v1)
app.include_router(api_router, prefix=settings.API_V1_STR)

# Top-level API alias (/api/analysis)
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])


@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"], include_in_schema=False)
async def health_check() -> dict[str, str]:
    """Health check endpoint to verify backend service status."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/api/docs", include_in_schema=False)
async def api_docs_redirect() -> RedirectResponse:
    """Redirect /api/docs to /docs for interactive Swagger UI."""
    return RedirectResponse(url="/docs")


@app.get("/openapi.json", include_in_schema=False)
async def openapi_alias() -> JSONResponse:
    """Provide root /openapi.json alias for OpenAPI specification."""
    return JSONResponse(app.openapi())
