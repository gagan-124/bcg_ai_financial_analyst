"""API route definitions and router aggregator."""

from fastapi import APIRouter

from app.api.routes import analysis, chat, companies, financials

api_router = APIRouter()
api_router.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(financials.router, prefix="/financials", tags=["Financials"])
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])

__all__ = ["api_router"]
