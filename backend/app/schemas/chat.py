from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Schema for chat query requests."""

    message: str = Field(..., description="User query or financial question")
    company_symbol: str | None = Field(default=None, description="Target company ticker/symbol")
    session_id: str | None = Field(default=None, description="Chat session identifier")


class ChatResponse(BaseModel):
    """Schema for chat response payload."""

    response: str = Field(..., description="Assistant response text")
    session_id: str | None = Field(default=None, description="Chat session identifier")
    sources: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Referenced data points or citations",
    )
