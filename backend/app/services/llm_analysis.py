"""LLM reasoning service with Gemini primary and Groq fallback providers."""

import abc
import logging
import re
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings
from app.schemas.financial import FinancialAnalysisResponse

logger = logging.getLogger(__name__)


def _sanitize_error_message(msg: str) -> str:
    """Strip API keys and authorization tokens from error text to prevent leaking."""
    cleaned = re.sub(r"key=[A-Za-z0-9_\-\.]+", "key=[REDACTED]", msg)
    cleaned = re.sub(r"Bearer\s+[A-Za-z0-9_\-\.]+", "Bearer [REDACTED]", cleaned)
    cleaned = re.sub(r"gsk_[A-Za-z0-9]+", "gsk_[REDACTED]", cleaned)
    cleaned = re.sub(r"AIza[A-Za-z0-9_\-]+", "AIza[REDACTED]", cleaned)
    return cleaned


def _clean_llm_response(text: str) -> str:
    """Clean model outputs to remove accidental ASCII plots, code blocks, or Excel steps."""
    if not text:
        return ""

    # Remove code blocks containing ASCII plots or plotting scripts
    def _strip_chart_code_block(match: re.Match) -> str:
        block = match.group(0)
        lower = block.lower()
        if any(term in lower for term in ["|", "+-", "excel", "sheet", "plot", "axis", "chart"]):
            return ""
        return block

    cleaned = re.sub(r"```[a-zA-Z]*\n[\s\S]*?```", _strip_chart_code_block, text)

    # Remove lines containing Excel / plotting instructions
    cleaned = re.sub(
        r"(?im)^.*(plotting steps|in excel|in google sheets|ascii sketch|to visualize this|"
        r"quick ascii|create a line chart|create a bar chart|secondary axis|secondary axes).*$",
        "",
        cleaned,
    )

    # Remove ASCII chart axis lines (e.g. '|   *', '|---', '+---')
    cleaned = re.sub(
        r"^[ \t]*[\|\+][\-\|\+\*#\s\d\.\$kKmMbB%]{4,}[ \t]*$",
        "",
        cleaned,
        flags=re.MULTILINE,
    )

    # Normalize multiple blank lines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned


# ==========================================
# Exception Hierarchy
# ==========================================


class LLMError(RuntimeError):
    """Base exception for all LLM reasoning errors."""


class LLMConfigurationError(LLMError):
    """Raised when required LLM credentials or configuration are missing."""


class LLMAPIError(LLMError):
    """Raised when an LLM provider returns an API error or fails."""


class LLMTransientError(LLMAPIError):
    """Raised for transient provider failures (HTTP 503, 429, timeouts, network issues).

    Triggers automatic fallback to secondary provider.
    """


# Backwards-compatible Gemini exception names
class GeminiError(LLMError):
    """Base exception for Gemini service errors."""


class GeminiConfigurationError(LLMConfigurationError, GeminiError):
    """Raised when GEMINI_API_KEY is not configured."""


class GeminiAPIError(LLMAPIError, GeminiError):
    """Raised when Gemini REST API returns an error."""


class GeminiTransientError(GeminiAPIError, LLMTransientError):
    """Raised when Gemini returns a transient error (503, 429, timeout)."""


# Groq exception names
class GroqError(LLMError):
    """Base exception for Groq service errors."""


class GroqConfigurationError(LLMConfigurationError, GroqError):
    """Raised when GROQ_API_KEY is not configured."""


class GroqAPIError(LLMAPIError, GroqError):
    """Raised when Groq REST API returns an error."""


class GroqTransientError(GroqAPIError, LLMTransientError):
    """Raised when Groq returns a transient error (503, 429, timeout)."""


# ==========================================
# Provider Interface & Implementations
# ==========================================


@dataclass
class LLMGenerationResult:
    """Output metadata and text from an LLM provider execution."""

    text: str
    provider: str
    model: str
    duration_ms: float


class BaseLLMProvider(abc.ABC):
    """Abstract interface for an LLM reasoning provider."""

    name: str

    @abc.abstractmethod
    def is_configured(self) -> bool:
        """Check if provider credentials and parameters are validly configured."""
        ...

    @abc.abstractmethod
    def generate(self, prompt: str, system_instruction: str) -> LLMGenerationResult:
        """Execute inference against the LLM provider."""
        ...


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider using REST API."""

    name = "gemini"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.api_key = (
            api_key if api_key is not None else getattr(settings, "GEMINI_API_KEY", "")
        )
        self.model = model or getattr(settings, "GEMINI_MODEL", "gemini-3.6-flash")
        self.timeout_seconds = timeout_seconds or getattr(
            settings, "LLM_REQUEST_TIMEOUT_SECONDS", 30.0
        )

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def generate(self, prompt: str, system_instruction: str) -> LLMGenerationResult:
        if not self.is_configured():
            raise GeminiConfigurationError(
                "GEMINI_API_KEY is not configured. Please set GEMINI_API_KEY in backend/.env "
                "to enable AI follow-up reasoning."
            )

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        payload: dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "systemInstruction": {
                "parts": [{"text": system_instruction}],
            },
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024,
            },
        }

        timeout = httpx.Timeout(self.timeout_seconds, connect=10.0)
        print(f"[QUESTION] Gemini API request start: model={self.model}", flush=True)
        t_start = time.perf_counter()

        try:
            response = httpx.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            safe_detail = _sanitize_error_message(exc.response.text)
            if status_code in (429, 502, 503, 504):
                raise GeminiTransientError(
                    f"Gemini transient error (HTTP {status_code}): {safe_detail}"
                ) from exc
            raise GeminiAPIError(
                f"Gemini API returned HTTP {status_code}: {safe_detail}"
            ) from exc
        except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as exc:
            raise GeminiTransientError(
                f"Gemini connection/timeout transient error: {_sanitize_error_message(str(exc))}"
            ) from exc
        except httpx.HTTPError as exc:
            raise GeminiTransientError(
                f"Gemini API request failed: {_sanitize_error_message(str(exc))}"
            ) from exc

        t_end = time.perf_counter()
        duration_ms = (t_end - t_start) * 1000
        print(f"[QUESTION] Gemini request: {duration_ms:.1f} ms", flush=True)

        t_parse_start = time.perf_counter()
        try:
            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise GeminiAPIError("Gemini response contained no candidates.")
            parts = candidates[0].get("content", {}).get("parts", [])
            text_parts = [p.get("text", "") for p in parts if "text" in p]
            answer = "".join(text_parts).strip()
            if not answer:
                raise GeminiAPIError("Gemini response contained empty text content.")
            t_parse_end = time.perf_counter()
            parse_ms = (t_parse_end - t_parse_start) * 1000
            print(f"[QUESTION] Gemini response parsing: {parse_ms:.1f} ms", flush=True)
            return LLMGenerationResult(
                text=answer,
                provider=self.name,
                model=self.model,
                duration_ms=duration_ms,
            )
        except Exception as exc:
            if isinstance(exc, GeminiAPIError):
                raise
            raise GeminiAPIError(f"Failed to parse Gemini response: {exc}") from exc


class GroqProvider(BaseLLMProvider):
    """Groq LLM provider using OpenAI-compatible REST API."""

    name = "groq"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.api_key = (
            api_key if api_key is not None else getattr(settings, "GROQ_API_KEY", "")
        )
        self.model = model or getattr(settings, "GROQ_MODEL", "openai/gpt-oss-120b")
        self.timeout_seconds = timeout_seconds or getattr(
            settings, "LLM_REQUEST_TIMEOUT_SECONDS", 30.0
        )

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def generate(self, prompt: str, system_instruction: str) -> LLMGenerationResult:
        if not self.is_configured():
            raise GroqConfigurationError(
                "GROQ_API_KEY is not configured. Please set GROQ_API_KEY in backend/.env "
                "to enable Groq AI fallback."
            )

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 1024,
        }

        timeout = httpx.Timeout(self.timeout_seconds, connect=10.0)
        print(f"[QUESTION] Groq API request start: model={self.model}", flush=True)
        t_start = time.perf_counter()

        try:
            response = httpx.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            safe_detail = _sanitize_error_message(exc.response.text)
            if status_code in (429, 502, 503, 504):
                raise GroqTransientError(
                    f"Groq transient error (HTTP {status_code}): {safe_detail}"
                ) from exc
            raise GroqAPIError(
                f"Groq API returned HTTP {status_code}: {safe_detail}"
            ) from exc
        except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as exc:
            raise GroqTransientError(
                f"Groq connection/timeout transient error: {_sanitize_error_message(str(exc))}"
            ) from exc
        except httpx.HTTPError as exc:
            raise GroqTransientError(
                f"Groq API request failed: {_sanitize_error_message(str(exc))}"
            ) from exc

        t_end = time.perf_counter()
        duration_ms = (t_end - t_start) * 1000
        print(f"[QUESTION] Groq request: {duration_ms:.1f} ms", flush=True)

        t_parse_start = time.perf_counter()
        try:
            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                raise GroqAPIError("Groq response contained no choices.")
            message = choices[0].get("message", {})
            answer = message.get("content", "").strip()
            if not answer:
                raise GroqAPIError("Groq response contained empty text content.")
            t_parse_end = time.perf_counter()
            parse_ms = (t_parse_end - t_parse_start) * 1000
            print(f"[QUESTION] Groq response parsing: {parse_ms:.1f} ms", flush=True)
            return LLMGenerationResult(
                text=answer,
                provider=self.name,
                model=self.model,
                duration_ms=duration_ms,
            )
        except Exception as exc:
            if isinstance(exc, GroqAPIError):
                raise
            raise GroqAPIError(f"Failed to parse Groq response: {exc}") from exc


# ==========================================
# Orchestration Service
# ==========================================


class LLMAnalysisService:
    """Service to generate grounded financial explanations using Gemini with Groq fallback."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        primary_provider: BaseLLMProvider | None = None,
        fallback_provider: BaseLLMProvider | None = None,
    ) -> None:
        # Backward compatibility for api_key / model args
        self.api_key = (
            api_key if api_key is not None else getattr(settings, "GEMINI_API_KEY", "")
        )
        self.model = model or getattr(settings, "GEMINI_MODEL", "gemini-3.6-flash")

        self.primary_provider = primary_provider or GeminiProvider(
            api_key=self.api_key,
            model=self.model,
        )
        self.fallback_provider = fallback_provider or GroqProvider()

    def build_system_instruction(self) -> str:
        """Construct strict grounding instructions for the financial analyst persona."""
        return (
            "You are a Senior BCG Financial Analyst providing natural-language reasoning inside "
            "an institutional BCG financial analysis web application.\n\n"
            "STRICT PRESENTATION RULES:\n"
            "- Do NOT generate charts, ASCII graphs, ASCII sketches, or Mermaid diagrams "
            "(NO ASCII charts or text-based line graphs).\n"
            "- NEVER provide instructions on how to plot or format charts in Excel/Google Sheets.\n"
            "- Do NOT generate code blocks containing diagrams, ASCII axes, or plotting scripts.\n"
            "- Do NOT describe how to manually plot a graph.\n"
            "- The application UI renders all charts and tables from verified SEC data.\n\n"
            "STRICT ANALYST GUIDELINES:\n"
            "1. Rely EXCLUSIVELY on the provided authoritative SEC filing figures.\n"
            "2. Cite exact dollar amounts, fiscal periods (e.g. FY2024), and percentages.\n"
            "3. Do NOT invent, extrapolate, or calculate conflicting primary numbers.\n"
            "4. Provide a concise, professional executive answer (2-4 focused paragraphs) "
            "explaining financial drivers, margin expansion/compression, and revenue movements.\n"
            "5. Clearly distinguish OBSERVED FACTS (the verified numbers) from ANALYST "
            "INTERPRETATION (e.g. 'operating income outpaced revenue, indicating operating "
            "leverage'). NEVER make UNSUPPORTED SPECULATIONS about unverified external causes "
            "unless explicitly documented in the provided findings. If the provided data is "
            "insufficient to establish a specific cause, state that limitation clearly.\n"
            "6. If asked about an unverified or unsupported company (e.g. OpenAI, private firms) "
            "or data absent from the verified context, state clearly that reliable SEC filing data "
            "is not available for that entity in this system, and do NOT speculate or hallucinate."
        )

    def _format_company_block(self, analysis: FinancialAnalysisResponse) -> str:
        """Format a company's SEC periods, metrics, and findings into structured text."""
        periods_text = []
        for p in analysis.table:
            periods_text.append(
                f"- Period {p.period}: Revenue = {p.revenue_formatted} (${p.revenue:.2f}B), "
                f"Net Income = {p.net_income_formatted} (${p.net_income:.2f}B), "
                f"EPS = {p.eps_formatted}, "
                f"Operating Margin = {p.operating_margin_formatted} ({p.operating_margin:.2f}%)"
            )
        periods_str = "\n".join(periods_text)

        metrics_text = []
        for m in analysis.metrics:
            change_part = f", Change: {m.change} ({m.change_label})" if m.change else ""
            metrics_text.append(f"- {m.name} ({m.period or 'Latest'}): {m.value}{change_part}")
        metrics_str = "\n".join(metrics_text)

        findings_str = "\n".join(f"- {f.text}" for f in analysis.findings)

        source_desc = f"{analysis.source.name} ({analysis.source.type})"
        if analysis.source.document_type:
            source_desc += f", Document: {analysis.source.document_type}"

        return (
            f"COMPANY: {analysis.company.name} ({analysis.company.ticker})\n"
            f"DATA SOURCE: {source_desc}\n\n"
            f"FINANCIAL SUMMARY:\n{analysis.summary}\n\n"
            f"HISTORICAL OPERATING PERFORMANCE (ANNUAL 10-K):\n{periods_str}\n\n"
            f"KEY CALCULATED METRICS & TRENDS:\n{metrics_str}\n\n"
            f"KEY AUDIT FINDINGS:\n{findings_str}"
        )

    def _format_comparison_block(
        self,
        primary: FinancialAnalysisResponse,
        secondary_list: list[FinancialAnalysisResponse],
    ) -> str:
        """Deterministically calculate comparative ratios between multiple companies."""
        lines = ["DETERMINISTIC COMPARISON SUMMARY:"]
        for sec in secondary_list:
            p_latest = primary.table[-1] if primary.table else None
            s_latest = sec.table[-1] if sec.table else None
            if p_latest and s_latest:
                rev_diff = p_latest.revenue - s_latest.revenue
                margin_diff = p_latest.operating_margin - s_latest.operating_margin
                lines.append(
                    f"- Latest Revenue (FY{p_latest.period}): {primary.company.name} "
                    f"({primary.company.ticker}) = {p_latest.revenue_formatted} vs "
                    f"{sec.company.name} ({sec.company.ticker}) = {s_latest.revenue_formatted} "
                    f"(Difference: ${abs(rev_diff):.2f}B, "
                    f"{'higher' if rev_diff > 0 else 'lower'})."
                )
                lines.append(
                    f"- Operating Margin: {primary.company.name} = "
                    f"{p_latest.operating_margin_formatted} vs "
                    f"{sec.company.name} = {s_latest.operating_margin_formatted} "
                    f"(Spread: {abs(margin_diff):.1f} percentage points)."
                )
        return "\n".join(lines)

    def build_prompt(
        self,
        analysis: FinancialAnalysisResponse,
        question: str,
        additional_analyses: list[FinancialAnalysisResponse] | None = None,
    ) -> str:
        """Format authoritative SEC financial context and question into a prompt."""
        blocks = [self._format_company_block(analysis)]

        if additional_analyses:
            for extra in additional_analyses:
                blocks.append("=" * 40)
                blocks.append(self._format_company_block(extra))
            blocks.append("=" * 40)
            blocks.append(self._format_comparison_block(analysis, additional_analyses))
            blocks.append(
                "NOTE: Rely EXCLUSIVELY on the verified comparative metrics calculated above. "
                "Do NOT invent, extrapolate, or recalculate conflicting financial numbers."
            )

        blocks.append(f"USER FOLLOW-UP QUESTION:\n{question}\n")
        blocks.append(
            "Please provide a grounded, analytical answer to the user's question based strictly "
            "on the financial data above."
        )

        return "\n\n".join(blocks)

    def answer_question(
        self,
        analysis: FinancialAnalysisResponse,
        question: str,
        additional_analyses: list[FinancialAnalysisResponse] | None = None,
    ) -> str:
        """Answer question using Gemini primary provider with automated Groq fallback."""
        prompt = self.build_prompt(analysis, question, additional_analyses=additional_analyses)
        system_instruction = self.build_system_instruction()

        # 1. Attempt Primary Provider (Gemini)
        print(
            f"[LLM] Executing request with primary provider: {self.primary_provider.name}",
            flush=True,
        )
        try:
            result = self.primary_provider.generate(prompt, system_instruction)
            return _clean_llm_response(result.text)
        except LLMTransientError as primary_exc:
            # Check if fallback is configured
            if not self.fallback_provider or not self.fallback_provider.is_configured():
                logger.warning(
                    f"Primary provider ({self.primary_provider.name}) failed with "
                    f"transient error: {primary_exc}, but no fallback provider is configured."
                )
                raise

            # 2. Trigger Fallback Provider (Groq) on Transient Failure
            error_class_name = type(primary_exc).__name__
            print(
                f"[LLM] Fallback triggered: primary provider '{self.primary_provider.name}' "
                f"failed with transient error ({error_class_name}). "
                f"Switching to fallback provider '{self.fallback_provider.name}'...",
                flush=True,
            )
            logger.info(
                f"Fallback triggered: switching from {self.primary_provider.name} to "
                f"{self.fallback_provider.name} due to transient error: {primary_exc}"
            )

            try:
                fallback_result = self.fallback_provider.generate(prompt, system_instruction)
                print(
                    f"[LLM] Fallback provider '{self.fallback_provider.name}' succeeded "
                    f"in {fallback_result.duration_ms:.1f} ms",
                    flush=True,
                )
                return _clean_llm_response(fallback_result.text)
            except Exception as fallback_exc:
                safe_primary = _sanitize_error_message(str(primary_exc))
                safe_fallback = _sanitize_error_message(str(fallback_exc))
                raise LLMAPIError(
                    f"Primary provider ({self.primary_provider.name}) failed with transient error "
                    f"[{safe_primary}] and fallback provider ({self.fallback_provider.name}) "
                    f"also failed [{safe_fallback}]."
                ) from fallback_exc
        except (LLMConfigurationError, LLMAPIError):
            # Non-transient errors (e.g. 400 Bad Request) do NOT trigger fallback
            raise
