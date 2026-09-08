"""Tests for Gemini LLM analysis service, Groq fallback provider, and question endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.financial import FinancialQuestionResponse
from app.services.financial_analysis import FinancialAnalysisService
from app.services.llm_analysis import (
    GeminiAPIError,
    GeminiConfigurationError,
    GeminiProvider,
    GeminiTransientError,
    GroqAPIError,
    GroqConfigurationError,
    GroqProvider,
    LLMAnalysisService,
    LLMAPIError,
    LLMGenerationResult,
    _clean_llm_response,
    _sanitize_error_message,
)

client = TestClient(app)


@pytest.fixture
def sample_analysis():
    """Generate a sample financial analysis for prompt testing."""
    service = FinancialAnalysisService()
    return service.analyze_company("Microsoft")


@pytest.fixture
def sample_apple_analysis():
    """Generate Apple financial analysis for multi-company comparison testing."""
    service = FinancialAnalysisService()
    return service.analyze_company("Apple")


class TestLLMAnalysisPrompt:
    """Tests for prompt and system instruction generation."""

    def test_system_instruction_contains_guardrails(self):
        service = LLMAnalysisService(api_key="test-key")
        instruction = service.build_system_instruction()
        assert "Senior BCG Financial Analyst" in instruction
        assert "EXCLUSIVELY" in instruction
        assert "Cite exact dollar amounts" in instruction

    def test_system_instruction_forbids_ascii_and_plotting(self):
        """Verify system instructions explicitly prohibit ASCII charts and Excel instructions."""
        service = LLMAnalysisService(api_key="test-key")
        instruction = service.build_system_instruction()
        assert "NO ASCII charts" in instruction
        assert "NEVER provide instructions on how to plot" in instruction
        assert "Excel/Google Sheets" in instruction
        assert "Do NOT generate code blocks containing diagrams" in instruction

    def test_system_instruction_distinguishes_facts_and_unsupported_companies(self):
        """Verify instructions require distinguishing observed facts from speculation
        and handling unsupported firms."""
        service = LLMAnalysisService(api_key="test-key")
        instruction = service.build_system_instruction()
        assert "OBSERVED FACTS" in instruction
        assert "ANALYST INTERPRETATION" in instruction
        assert "UNSUPPORTED SPECULATIONS" in instruction
        assert "unsupported company" in instruction.lower()

    def test_clean_llm_response_removes_ascii_and_excel(self):
        """Verify _clean_llm_response purges ASCII plots, code blocks, and Excel directions."""
        dirty_text = (
            "Apple delivered strong performance in FY2024.\n\n"
            "```\n"
            "|   *\n"
            "|  * *\n"
            "+-------\n"
            "```\n"
            "Plotting steps (e.g., in Excel or Google Sheets):\n"
            "1. Enter years 2022 to 2025\n"
            "Operating margin expanded by 1.2 percentage points."
        )
        cleaned = _clean_llm_response(dirty_text)
        assert "Apple delivered strong performance in FY2024." in cleaned
        assert "Operating margin expanded by 1.2 percentage points." in cleaned
        assert "Plotting steps" not in cleaned
        assert "|   *" not in cleaned
        assert "+-------" not in cleaned

    def test_clean_llm_response_preserves_executive_narrative(self):
        """Verify clean narrative text with bullet points is left intact."""
        clean_text = (
            "Microsoft's operating margin expanded to 44.6% (+2.8pp YoY).\n\n"
            "Key operational drivers:\n"
            "• Cloud infrastructure revenue expanded by +28.9%.\n"
            "• SG&A discipline reduced operating overhead.\n"
            "• Operating income reached $109.4B."
        )
        assert _clean_llm_response(clean_text) == clean_text

    def test_prompt_contains_authoritative_financial_data(self, sample_analysis):
        service = LLMAnalysisService(api_key="test-key")
        question = "Why did Microsoft's operating margin increase?"
        prompt = service.build_prompt(sample_analysis, question)

        assert "Microsoft Corporation (MSFT)" in prompt
        assert "HISTORICAL OPERATING PERFORMANCE (ANNUAL 10-K):" in prompt
        assert "Operating Margin =" in prompt
        assert "Revenue =" in prompt
        assert "USER FOLLOW-UP QUESTION:" in prompt
        assert question in prompt

    def test_multi_company_prompt_contains_deterministic_comparison(
        self, sample_analysis, sample_apple_analysis
    ):
        """Verify multi-company prompt includes verified deterministic numbers for both."""
        service = LLMAnalysisService(api_key="test-key")
        question = "Compare Apple and Microsoft revenue growth"
        prompt = service.build_prompt(
            sample_apple_analysis,
            question,
            additional_analyses=[sample_analysis],
        )

        assert "Apple Inc. (AAPL)" in prompt
        assert "Microsoft Corporation (MSFT)" in prompt
        assert "DETERMINISTIC COMPARISON SUMMARY:" in prompt
        assert "Latest Revenue" in prompt
        assert "Spread:" in prompt or "Operating Margin:" in prompt
        assert "Rely EXCLUSIVELY on the verified comparative metrics" in prompt


class TestQuestionVisualContext:
    """Tests for deterministic chart and table generation in build_question_visual_context."""

    def test_single_company_revenue_trend_returns_chart(self, sample_apple_analysis):
        service = FinancialAnalysisService()
        chart, table, metrics = service.build_question_visual_context(
            "Show Apple revenue trend over the years",
            sample_apple_analysis,
        )
        assert chart is not None
        assert "Apple Inc. Revenue Trend" in chart.title
        assert len(chart.data) > 0
        assert table is None
        assert metrics is not None

    def test_single_company_margin_trend_returns_margin_chart(self, sample_apple_analysis):
        service = FinancialAnalysisService()
        chart, table, metrics = service.build_question_visual_context(
            "How has Apple's operating margin changed?",
            sample_apple_analysis,
        )
        assert chart is not None
        assert "Operating Margin" in chart.title
        assert chart.unit == "%"
        assert table is None
        assert metrics is not None

    def test_single_company_net_income_trend_returns_income_chart(self, sample_apple_analysis):
        service = FinancialAnalysisService()
        chart, table, metrics = service.build_question_visual_context(
            "Why did Apple's net income and profit increase over the years?",
            sample_apple_analysis,
        )
        assert chart is not None
        assert "Net Income" in chart.title
        assert table is None
        assert metrics is not None

    def test_multi_company_comparison_returns_multiseries_chart_and_table(
        self, sample_apple_analysis, sample_analysis
    ):
        service = FinancialAnalysisService()
        chart, table, metrics = service.build_question_visual_context(
            "Compare Apple and Microsoft revenue growth",
            sample_apple_analysis,
            additional_analyses=[sample_analysis],
        )
        assert chart is not None
        assert chart.series is not None
        assert len(chart.series) == 2
        assert {s.dataKey for s in chart.series} == {"AAPL", "MSFT"}
        assert table is not None
        assert len(table.columns) == 3  # Metric, AAPL, MSFT
        assert len(table.rows) == 4  # Revenue, Operating Margin, Net Income, EPS

    def test_conceptual_question_without_trend_keywords_returns_none(self, sample_apple_analysis):
        service = FinancialAnalysisService()
        chart, table, metrics = service.build_question_visual_context(
            "Who is the CEO?",
            sample_apple_analysis,
        )
        assert chart is None
        assert table is None
        assert metrics is None


class TestProvidersDirect:
    """Direct unit tests for GeminiProvider and GroqProvider."""

    def test_gemini_provider_unconfigured_raises_error(self):
        provider = GeminiProvider(api_key="")
        with pytest.raises(GeminiConfigurationError, match="GEMINI_API_KEY is not configured"):
            provider.generate("prompt", "sys")

    def test_gemini_provider_successful_generation(self):
        provider = GeminiProvider(api_key="fake-gemini-key")
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Gemini response"}]}}]
        }
        with patch("httpx.post", return_value=mock_res) as mock_post:
            result = provider.generate("prompt", "sys")
            assert result.provider == "gemini"
            assert result.text == "Gemini response"
            mock_post.assert_called_once()

    def test_groq_provider_unconfigured_raises_error(self):
        provider = GroqProvider(api_key="")
        with pytest.raises(GroqConfigurationError, match="GROQ_API_KEY is not configured"):
            provider.generate("prompt", "sys")

    def test_groq_provider_successful_generation(self):
        provider = GroqProvider(api_key="fake-groq-key", model="openai/gpt-oss-120b")
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = {
            "choices": [{"message": {"content": "Groq analytical response based on 10-K figures."}}]
        }

        with patch("httpx.post", return_value=mock_res) as mock_post:
            result = provider.generate("Test prompt", "Test instruction")
            assert result.provider == "groq"
            assert result.model == "openai/gpt-oss-120b"
            assert "Groq analytical response" in result.text
            assert result.duration_ms >= 0

            # Verify OpenAI-compatible request structure
            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args[1]
            assert call_kwargs["headers"]["Authorization"] == "Bearer fake-groq-key"
            assert call_kwargs["json"]["model"] == "openai/gpt-oss-120b"


class TestLLMFallbackOrchestration:
    """Explicit tests for Gemini primary -> Groq fallback behaviors A through F."""

    def test_case_a_gemini_succeeds_groq_not_called(self, sample_analysis):
        """A. Gemini succeeds -> Gemini response returned -> Groq is not called."""
        mock_primary = MagicMock(spec=GeminiProvider)
        mock_primary.name = "gemini"
        mock_primary.is_configured.return_value = True
        mock_primary.generate.return_value = LLMGenerationResult(
            text="Gemini authoritative response.",
            provider="gemini",
            model="gemini-3.6-flash",
            duration_ms=120.0,
        )

        mock_fallback = MagicMock(spec=GroqProvider)
        mock_fallback.name = "groq"
        mock_fallback.is_configured.return_value = True

        service = LLMAnalysisService(
            primary_provider=mock_primary,
            fallback_provider=mock_fallback,
        )

        answer = service.answer_question(sample_analysis, "Why did revenue grow?")
        assert answer == "Gemini authoritative response."
        mock_primary.generate.assert_called_once()
        mock_fallback.generate.assert_not_called()

    def test_case_b_gemini_503_groq_fallback_succeeds(self, sample_analysis):
        """B. Gemini returns transient 503 -> Groq is called -> Groq response returned."""
        mock_primary = MagicMock(spec=GeminiProvider)
        mock_primary.name = "gemini"
        mock_primary.is_configured.return_value = True
        mock_primary.generate.side_effect = GeminiTransientError(
            "Gemini transient error (HTTP 503): Service Unavailable"
        )

        mock_fallback = MagicMock(spec=GroqProvider)
        mock_fallback.name = "groq"
        mock_fallback.is_configured.return_value = True
        mock_fallback.generate.return_value = LLMGenerationResult(
            text="Groq fallback response: Operating margin expanded to 44.6%.",
            provider="groq",
            model="openai/gpt-oss-120b",
            duration_ms=85.0,
        )

        service = LLMAnalysisService(
            primary_provider=mock_primary,
            fallback_provider=mock_fallback,
        )

        answer = service.answer_question(sample_analysis, "Why did operating margin increase?")
        assert "Groq fallback response" in answer
        mock_primary.generate.assert_called_once()
        mock_fallback.generate.assert_called_once()

    def test_case_c_gemini_429_groq_fallback_succeeds(self, sample_analysis):
        """C. Gemini returns transient 429 -> Groq is called -> Groq response returned."""
        mock_primary = MagicMock(spec=GeminiProvider)
        mock_primary.name = "gemini"
        mock_primary.is_configured.return_value = True
        mock_primary.generate.side_effect = GeminiTransientError(
            "Gemini transient error (HTTP 429): Resource Exhausted / Rate limit"
        )

        mock_fallback = MagicMock(spec=GroqProvider)
        mock_fallback.name = "groq"
        mock_fallback.is_configured.return_value = True
        mock_fallback.generate.return_value = LLMGenerationResult(
            text="Groq rate-limit fallback explanation.",
            provider="groq",
            model="openai/gpt-oss-120b",
            duration_ms=90.0,
        )

        service = LLMAnalysisService(
            primary_provider=mock_primary,
            fallback_provider=mock_fallback,
        )

        answer = service.answer_question(sample_analysis, "Explain net income trend.")
        assert answer == "Groq rate-limit fallback explanation."
        mock_primary.generate.assert_called_once()
        mock_fallback.generate.assert_called_once()

    def test_case_d_gemini_non_transient_error_does_not_call_groq(self, sample_analysis):
        """D. Gemini returns a non-transient error -> Groq is NOT called -> error preserved."""
        mock_primary = MagicMock(spec=GeminiProvider)
        mock_primary.name = "gemini"
        mock_primary.is_configured.return_value = True
        mock_primary.generate.side_effect = GeminiAPIError(
            "Gemini API returned HTTP 400: Bad Request - invalid argument"
        )

        mock_fallback = MagicMock(spec=GroqProvider)
        mock_fallback.name = "groq"
        mock_fallback.is_configured.return_value = True

        service = LLMAnalysisService(
            primary_provider=mock_primary,
            fallback_provider=mock_fallback,
        )

        with pytest.raises(GeminiAPIError, match="Gemini API returned HTTP 400"):
            service.answer_question(sample_analysis, "Why did revenue grow?")

        mock_primary.generate.assert_called_once()
        mock_fallback.generate.assert_not_called()

    def test_case_e_both_providers_fail_returns_clean_error_without_leaking_keys(
        self, sample_analysis
    ):
        """E. Groq also fails -> return clean LLM error -> never expose API keys."""
        mock_primary = MagicMock(spec=GeminiProvider)
        mock_primary.name = "gemini"
        mock_primary.is_configured.return_value = True
        mock_primary.generate.side_effect = GeminiTransientError(
            "Gemini transient error (HTTP 503)"
        )

        mock_fallback = MagicMock(spec=GroqProvider)
        mock_fallback.name = "groq"
        mock_fallback.is_configured.return_value = True
        mock_fallback.generate.side_effect = GroqAPIError(
            "Groq API returned HTTP 500: Internal Server Error"
        )

        service = LLMAnalysisService(
            primary_provider=mock_primary,
            fallback_provider=mock_fallback,
        )

        with pytest.raises(LLMAPIError) as exc_info:
            service.answer_question(sample_analysis, "Why did revenue grow?")

        error_msg = str(exc_info.value)
        assert "Primary provider (gemini) failed with transient error" in error_msg
        assert "fallback provider (groq) also failed" in error_msg
        # Critical security check: ensure no keys leaked
        assert "gsk_" not in error_msg
        assert "AQ." not in error_msg

    def test_case_f_both_providers_receive_same_verified_context(self, sample_analysis):
        """F. Both providers receive identical verified financial context."""
        mock_primary = MagicMock(spec=GeminiProvider)
        mock_primary.name = "gemini"
        mock_primary.is_configured.return_value = True
        mock_primary.generate.side_effect = GeminiTransientError("503")

        mock_fallback = MagicMock(spec=GroqProvider)
        mock_fallback.name = "groq"
        mock_fallback.is_configured.return_value = True
        mock_fallback.generate.return_value = LLMGenerationResult(
            text="Answer", provider="groq", model="model", duration_ms=10.0
        )

        service = LLMAnalysisService(
            primary_provider=mock_primary,
            fallback_provider=mock_fallback,
        )

        service.answer_question(sample_analysis, "What caused the margin growth?")

        primary_prompt, primary_system = mock_primary.generate.call_args[0]
        fallback_prompt, fallback_system = mock_fallback.generate.call_args[0]

        assert primary_prompt == fallback_prompt
        assert primary_system == fallback_system
        assert "HISTORICAL OPERATING PERFORMANCE (ANNUAL 10-K):" in fallback_prompt
        assert "Senior BCG Financial Analyst" in fallback_system


class TestQuestionApiEndpoint:
    """Integration tests for POST /api/analysis/question."""

    def test_question_endpoint_success_microsoft(self):
        mock_answer = (
            "Microsoft's operating margin rose from 41.8% to 44.6% in FY2024, "
            "driven by cloud revenue acceleration."
        )
        with patch.object(LLMAnalysisService, "answer_question", return_value=mock_answer):
            response = client.post(
                "/api/analysis/question",
                json={
                    "company": "Microsoft",
                    "question": "Why did Microsoft's operating margin increase?",
                },
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            validated = FinancialQuestionResponse(**data)
            assert validated.company.ticker == "MSFT"
            assert validated.company.name == "Microsoft Corporation"
            assert validated.question == "Why did Microsoft's operating margin increase?"
            assert validated.answer == mock_answer
            assert validated.source.name is not None

    def test_question_endpoint_success_tesla(self):
        mock_answer = (
            "Tesla's operating margin declined to 8.2% in 2024 as automotive pricing reductions "
            "compressed gross margins despite total revenues reaching $97.7B."
        )
        with patch.object(LLMAnalysisService, "answer_question", return_value=mock_answer):
            response = client.post(
                "/api/analysis/question",
                json={
                    "company": "Tesla",
                    "question": "Why did profitability decline?",
                },
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["company"]["ticker"] == "TSLA"
            assert data["answer"] == mock_answer

    def test_question_endpoint_success_apple(self):
        mock_answer = (
            "Apple's operating margin increased to 31.5% in FY2024 from 29.8% in FY2023, "
            "supported by high-margin Services growth."
        )
        with patch.object(LLMAnalysisService, "answer_question", return_value=mock_answer):
            response = client.post(
                "/api/analysis/question",
                json={
                    "company": "Apple",
                    "question": "What changed in Apple's operating margin?",
                },
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["company"]["ticker"] == "AAPL"
            assert data["answer"] == mock_answer
            assert data["chart"] is not None
            assert "Operating Margin" in data["chart"]["title"]
            assert data["chart"]["unit"] == "%"

    def test_question_endpoint_multi_company_comparison(self):
        """Integration test: multi-company comparison passes secondary company SEC analysis
        and returns visuals."""
        mock_answer = (
            "Comparing FY2024 results, Apple generated $391.0B in revenue (+2.0% YoY) "
            "with a 31.5% operating margin, while Microsoft generated $245.1B (+15.7% YoY) "
            "with a 44.6% operating margin."
        )
        with patch.object(
            LLMAnalysisService, "answer_question", return_value=mock_answer
        ) as mock_ask:
            response = client.post(
                "/api/analysis/question",
                json={
                    "company": "Apple",
                    "question": "Compare Apple and Microsoft revenue growth",
                },
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["answer"] == mock_answer
            # Verify structured chart and table are attached
            assert data["chart"] is not None
            assert data["chart"]["series"] is not None
            assert len(data["chart"]["series"]) == 2
            assert data["table"] is not None
            assert len(data["table"]["columns"]) == 3
            # Verify additional_analyses contained Microsoft
            mock_ask.assert_called_once()
            call_kwargs = mock_ask.call_args[1]
            add_analyses = call_kwargs.get("additional_analyses")
            assert add_analyses is not None
            assert len(add_analyses) == 1
            assert add_analyses[0].company.ticker == "MSFT"

    def test_question_endpoint_unsupported_company(self):
        response = client.post(
            "/api/analysis/question",
            json={
                "company": "Amazon",
                "question": "Why did margins increase?",
            },
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Unsupported company" in response.json()["detail"]

    def test_question_endpoint_missing_api_key_returns_503(self):
        with patch.object(
            LLMAnalysisService,
            "answer_question",
            side_effect=GeminiConfigurationError("GEMINI_API_KEY is not configured"),
        ):
            response = client.post(
                "/api/analysis/question",
                json={
                    "company": "Microsoft",
                    "question": "Why did operating margin increase?",
                },
            )
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            assert "GEMINI_API_KEY is not configured" in response.json()["detail"]

    def test_question_endpoint_gemini_api_error_returns_502(self):
        with patch.object(
            LLMAnalysisService,
            "answer_question",
            side_effect=GeminiAPIError("Gemini API request failed: timeout"),
        ):
            response = client.post(
                "/api/analysis/question",
                json={
                    "company": "Microsoft",
                    "question": "Why did operating margin increase?",
                },
            )
            assert response.status_code == status.HTTP_502_BAD_GATEWAY
            assert "Gemini API request failed" in response.json()["detail"]

    def test_question_endpoint_empty_question_returns_400(self):
        """Verify empty question text returns HTTP 400 Bad Request."""
        response = client.post(
            "/api/analysis/question",
            json={
                "company": "Microsoft",
                "question": "   ",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Question cannot be empty" in response.json()["detail"]

    def test_question_endpoint_excessively_long_question_returns_422(self):
        """Verify questions exceeding max length (2000 chars) are rejected with 422."""
        huge_question = "Why? " * 500  # 2500 chars
        response = client.post(
            "/api/analysis/question",
            json={
                "company": "Microsoft",
                "question": huge_question,
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_sanitize_error_message_redacts_all_secrets(self):
        """Verify _sanitize_error_message scrubs Gemini keys, Groq keys, and Bearer tokens."""
        raw_err = (
            "Error contacting https://api.google.com/models?key=AIzaSyD12345 "
            "with Bearer gsk_abc123456789xyz and token Bearer mySecretToken123"
        )
        cleaned = _sanitize_error_message(raw_err)
        assert "AIzaSyD12345" not in cleaned
        assert "gsk_abc123456789xyz" not in cleaned
        assert "mySecretToken123" not in cleaned
        assert "[REDACTED]" in cleaned
