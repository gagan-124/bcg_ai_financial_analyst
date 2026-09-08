"""Financial analysis API routes."""

import logging
import time

from fastapi import APIRouter, Body, HTTPException, status

from app.schemas.financial import (
    FinancialAnalysisRequest,
    FinancialAnalysisResponse,
    FinancialQuestionRequest,
    FinancialQuestionResponse,
)
from app.services.financial_analysis import FinancialAnalysisService
from app.services.llm_analysis import (
    GeminiAPIError,
    GeminiConfigurationError,
    LLMAnalysisService,
    LLMAPIError,
    LLMConfigurationError,
)

logger = logging.getLogger(__name__)
router = APIRouter()
analysis_service = FinancialAnalysisService()
llm_service = LLMAnalysisService()

ANALYSIS_BODY_EXAMPLES = {
    "Apple": {
        "summary": "Apple Inc. (AAPL)",
        "description": "Financial analysis request for Apple Inc.",
        "value": {
            "company": "Apple",
            "query": "Show financial analysis",
        },
    },
    "Microsoft": {
        "summary": "Microsoft Corporation (MSFT)",
        "description": "Financial analysis request for Microsoft Corporation",
        "value": {
            "company": "Microsoft",
            "query": "Show financial analysis",
        },
    },
    "Tesla": {
        "summary": "Tesla, Inc. (TSLA)",
        "description": "Financial analysis request for Tesla, Inc.",
        "value": {
            "company": "Tesla",
            "query": "Show financial analysis",
        },
    },
}

QUESTION_BODY_EXAMPLES = {
    "Microsoft": {
        "summary": "Microsoft operating margin follow-up",
        "description": "Follow-up question on Microsoft operating margin",
        "value": {
            "company": "Microsoft",
            "question": "Why did Microsoft's operating margin increase?",
        },
    },
    "Tesla": {
        "summary": "Tesla profitability follow-up",
        "description": "Follow-up question on Tesla profitability",
        "value": {
            "company": "Tesla",
            "question": "Why did profitability decline?",
        },
    },
}


@router.post(
    "",
    response_model=FinancialAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze company financials",
    description=(
        "Returns structured financial metrics, multi-year historical trend, "
        "and deterministic findings for supported companies (Apple, Microsoft, Tesla)."
    ),
)
async def analyze_company(
    request: FinancialAnalysisRequest = Body(
        ...,
        openapi_examples=ANALYSIS_BODY_EXAMPLES,
    ),
) -> FinancialAnalysisResponse:
    """Analyze financial performance for a designated company."""
    try:
        return analysis_service.analyze_company(request.company)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/question",
    response_model=FinancialQuestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Answer follow-up financial questions",
    description=(
        "Generates grounded analytical explanations for follow-up financial questions "
        "using active SEC-backed metrics."
    ),
)
async def ask_financial_question(
    request: FinancialQuestionRequest = Body(
        ...,
        openapi_examples=QUESTION_BODY_EXAMPLES,
    ),
) -> FinancialQuestionResponse:
    """Answer a follow-up financial question for the active company context."""
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )

    t_start = time.perf_counter()
    logger.info(f"[QUESTION] request received: company={request.company}")

    t_context_start = time.perf_counter()
    try:
        analysis = analysis_service.analyze_company(request.company)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    # Detect any secondary companies mentioned in the question for multi-company comparisons
    additional_analyses: list[FinancialAnalysisResponse] = []
    question_lower = request.question.lower()
    primary_ticker = analysis.company.ticker.upper()
    for candidate_name, candidate_ticker in [
        ("Apple", "AAPL"),
        ("Microsoft", "MSFT"),
        ("Tesla", "TSLA"),
    ]:
        if candidate_ticker != primary_ticker:
            in_question = (
                candidate_name.lower() in question_lower
                or candidate_ticker.lower() in question_lower
            )
            if in_question:
                try:
                    sec_extra = analysis_service.analyze_company(candidate_name)
                    additional_analyses.append(sec_extra)
                except ValueError:
                    pass

    t_context_end = time.perf_counter()
    context_ms = (t_context_end - t_context_start) * 1000
    logger.info(f"[QUESTION] context preparation: {context_ms:.1f} ms")

    try:
        answer = llm_service.answer_question(
            analysis,
            request.question,
            additional_analyses=additional_analyses if additional_analyses else None,
        )
    except (GeminiConfigurationError, LLMConfigurationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except (GeminiAPIError, LLMAPIError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    chart, table, metrics = analysis_service.build_question_visual_context(
        request.question,
        analysis,
        additional_analyses=additional_analyses if additional_analyses else None,
    )

    t_end = time.perf_counter()
    total_ms = (t_end - t_start) * 1000
    logger.info(f"[QUESTION] total: {total_ms:.1f} ms")

    return FinancialQuestionResponse(
        company=analysis.company,
        question=request.question,
        answer=answer,
        source=analysis.source,
        chart=chart,
        table=table,
        metrics=metrics,
    )

