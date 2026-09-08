"""Financial data retrieval and company resolution service."""

import logging

from app.data.financial_fixtures import COMPANY_ALIASES, COMPANY_METADATA, FINANCIAL_FIXTURES
from app.schemas.financial import CompanyInfo, FinancialPeriod, SourceInfo

logger = logging.getLogger(__name__)


class FinancialDataService:
    """Service for resolving companies and retrieving financial datasets (SEC or fixture)."""

    @staticmethod
    def resolve_company(company_input: str) -> CompanyInfo:
        """Resolve a raw company name, alias, or ticker symbol to a canonical CompanyInfo.

        Raises:
            ValueError: If the company is not recognized or supported.
        """
        if not company_input or not isinstance(company_input, str) or not company_input.strip():
            raise ValueError(f"Invalid company identifier: {company_input}")

        cleaned = company_input.strip().lower()
        ticker = COMPANY_ALIASES.get(cleaned)

        if not ticker:
            ticker = COMPANY_ALIASES.get(cleaned.rstrip(".,").strip())

        if not ticker:
            # Check direct uppercase match against known tickers
            upper_cleaned = company_input.strip().upper()
            if upper_cleaned in COMPANY_METADATA:
                ticker = upper_cleaned

        if not ticker or ticker not in COMPANY_METADATA:
            raise ValueError(f"Unsupported company: {company_input}")

        meta = COMPANY_METADATA[ticker]
        return CompanyInfo(name=meta["name"], ticker=meta["ticker"])

    @classmethod
    def get_company_data(cls, ticker: str) -> tuple[list[FinancialPeriod], SourceInfo]:
        """Retrieve normalized financial periods and provenance metadata for a ticker.

        When FINANCIAL_DATA_MODE is 'sec', fetches and normalizes directly from SEC EDGAR XBRL.
        If SEC retrieval fails under mode 'sec', raises ValueError with NO fixture fallback.

        Raises:
            ValueError: If no data exists or retrieval fails for the provided ticker.
        """
        upper_ticker = ticker.strip().upper()
        from app.core.config import settings

        mode = getattr(settings, "FINANCIAL_DATA_MODE", "fixture")

        if mode == "sec":
            from app.services.sec_xbrl import SEC_CIKS, fetch_company_facts
            from app.services.xbrl_normalizer import normalize_company_facts

            try:
                raw_data = fetch_company_facts(upper_ticker)
                normalized = normalize_company_facts(raw_data)
                if not normalized:
                    raise ValueError(f"No financial data available for ticker: {ticker}")
                periods = [FinancialPeriod(**p) for p in normalized]
                cik = SEC_CIKS.get(upper_ticker, "")
                source = SourceInfo(
                    name="SEC EDGAR",
                    type="sec",
                    document_type="10-K",
                    period=f"{periods[0].period} - {periods[-1].period}",
                    reference=f"Official SEC EDGAR XBRL Company Facts (CIK {cik})",
                )
                return periods, source
            except Exception as e:
                logger.error(f"SEC data retrieval failed for {upper_ticker} in SEC mode: {e}")
                raise ValueError(f"No financial data available for ticker: {ticker}") from e

        if mode == "sec_with_fixture_fallback":
            from app.services.sec_xbrl import SEC_CIKS, fetch_company_facts
            from app.services.xbrl_normalizer import normalize_company_facts

            try:
                raw_data = fetch_company_facts(upper_ticker)
                normalized = normalize_company_facts(raw_data)
                if normalized:
                    periods = [FinancialPeriod(**p) for p in normalized]
                    cik = SEC_CIKS.get(upper_ticker, "")
                    source = SourceInfo(
                        name="SEC EDGAR",
                        type="sec",
                        document_type="10-K",
                        period=f"{periods[0].period} - {periods[-1].period}",
                        reference=f"Official SEC EDGAR XBRL Company Facts (CIK {cik})",
                    )
                    return periods, source
            except Exception as e:
                logger.warning(
                    f"SEC fetch failed for {upper_ticker}, falling back to fixture: {e}"
                )

        # Fixture retrieval path (mode == "fixture" or fallback from sec_with_fixture_fallback)
        raw_periods = FINANCIAL_FIXTURES.get(upper_ticker)
        if not raw_periods:
            raise ValueError(f"No financial data available for ticker: {ticker}")

        periods = [FinancialPeriod(**p) for p in raw_periods]
        source = SourceInfo(
            name="Demo financial fixture",
            type="fixture",
            document_type=None,
            period=f"{periods[0].period} - {periods[-1].period}",
            reference="Standardized multi-year operating performance (demo fixture)",
        )
        return periods, source

    @classmethod
    def get_company_periods(cls, ticker: str) -> list[FinancialPeriod]:
        """Retrieve the sequence of normalized financial periods for a company ticker.

        Raises:
            ValueError: If no data exists for the provided ticker.
        """
        periods, _ = cls.get_company_data(ticker)
        return periods

    @staticmethod
    def get_supported_companies() -> list[CompanyInfo]:
        """Return list of all supported canonical companies."""
        return [
            CompanyInfo(name=meta["name"], ticker=meta["ticker"])
            for meta in COMPANY_METADATA.values()
        ]
