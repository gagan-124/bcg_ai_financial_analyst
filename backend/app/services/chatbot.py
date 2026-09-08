class ChatbotService:
    """Service handling conversational AI financial analysis and query orchestration."""

    def __init__(self) -> None:
        pass

    async def generate_response(
        self,
        message: str,
        company_symbol: str | None = None,
        session_id: str | None = None,
    ) -> dict:
        """Generate response for financial queries."""
        raise NotImplementedError("Chatbot service implementation pending.")
