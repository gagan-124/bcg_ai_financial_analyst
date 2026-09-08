"""Tests for the financial analysis foundation backend service and API endpoint."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.schemas.financial import CompanyInfo, FinancialAnalysisResponse
from app.services.financial_analysis import FinancialAnalysisService
from app.services.financial_data import FinancialDataService


class TestCompanyResolution:
    """Tests for company alias and ticker resolution."""

    @pytest.mark.parametrize(
        ("query", "expected_ticker", "expected_name"),
        [
            # Apple variations
            ("Apple", "AAPL", "Apple Inc."),
            ("apple", "AAPL", "Apple Inc."),
            ("Apple Inc.", "AAPL", "Apple Inc."),
            ("apple inc", "AAPL", "Apple Inc."),
            ("apple inc.", "AAPL", "Apple Inc."),
            ("AAPL", "AAPL", "Apple Inc."),
            ("aapl", "AAPL", "Apple Inc."),
            # Microsoft variations
            ("Microsoft", "MSFT", "Microsoft Corporation"),
            ("microsoft", "MSFT", "Microsoft Corporation"),
            ("Microsoft Corporation", "MSFT", "Microsoft Corporation"),
            ("microsoft corp", "MSFT", "Microsoft Corporation"),
            ("microsoft corp.", "MSFT", "Microsoft Corporation"),
            ("MSFT", "MSFT", "Microsoft Corporation"),
            ("msft", "MSFT", "Microsoft Corporation"),
            # Tesla variations
            ("Tesla", "TSLA", "Tesla, Inc."),
            ("tesla", "TSLA", "Tesla, Inc."),
            ("Tesla Inc", "TSLA", "Tesla, Inc."),
            ("Tesla Inc.", "TSLA", "Tesla, Inc."),
            ("Tesla, Inc.", "TSLA", "Tesla, Inc."),
            ("Tesla, Inc", "TSLA", "Tesla, Inc."),
            ("TSLA", "TSLA", "Tesla, Inc."),
            ("tsla", "TSLA", "Tesla, Inc."),
        ],
    )
    def test_company_resolution_success(
        self, query: str, expected_ticker: str, expected_name: str
    ) -> None:
        info: CompanyInfo = FinancialDataService.resolve_company(query)
        assert info.ticker == expected_ticker
        assert info.name == expected_name

    def test_unsupported_company_raises_error(self) -> None:
        with pytest.raises(ValueError, match="Unsupported company"):
            FinancialDataService.resolve_company("Amazon")

    def test_empty_company_raises_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid company identifier"):
            FinancialDataService.resolve_company("")

    def test_whitespace_company_raises_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid company identifier"):
            FinancialDataService.resolve_company("   ")


class TestFinancialDataService:
    """Tests for financial data retrieval from local fixtures or SEC."""

    @pytest.mark.parametrize("ticker", ["AAPL", "MSFT", "TSLA"])
    def test_fixture_returns_four_periods(self, ticker: str) -> None:
        periods = FinancialDataService.get_company_periods(ticker)
        assert len(periods) == 4

        for p in periods:
            assert p.period in ["2022", "2023", "2024", "2025", "2026"]
            assert p.revenue > 0
            assert p.revenue_formatted.startswith("$")
            assert p.net_income > 0
            assert p.net_income_formatted.startswith("$")
            assert p.eps > 0
            assert p.eps_formatted.startswith("$")
            assert p.operating_margin > 0
            assert p.operating_margin_formatted.endswith("%")

    def test_unsupported_ticker_data_raises_error(self) -> None:
        with pytest.raises(ValueError, match="No financial data available"):
            FinancialDataService.get_company_periods("AMZN")


class TestFinancialAnalysisService:
    """Tests for deterministic analysis and ratio calculation."""

    @pytest.fixture
    def analysis_service(self) -> FinancialAnalysisService:
        return FinancialAnalysisService()

    @pytest.mark.parametrize("company_name", ["Apple", "Microsoft", "Tesla"])
    def test_analyze_company_structure(
        self, analysis_service: FinancialAnalysisService, company_name: str
    ) -> None:
        res: FinancialAnalysisResponse = analysis_service.analyze_company(company_name)

        # Company identity
        assert res.company.name
        assert res.company.ticker in ["AAPL", "MSFT", "TSLA"]

        # Summary
        assert len(res.summary) > 20
        if settings.FINANCIAL_DATA_MODE == "sec":
            assert "SEC EDGAR" in res.summary
            assert res.source.name == "SEC EDGAR"
            assert res.source.type == "sec"
        else:
            assert "Demo financial fixture" in res.summary
            assert res.source.name == "Demo financial fixture"
            assert res.source.type == "fixture"

        # Metrics (4 key metrics: Revenue, Net Income, EPS, Operating Margin)
        assert len(res.metrics) == 4
        metric_names = [m.name for m in res.metrics]
        assert "Revenue" in metric_names
        assert "Net Income" in metric_names
        assert "EPS" in metric_names
        assert "Operating Margin" in metric_names

        # Operating margin expressed in percentage points
        margin_metric = next(m for m in res.metrics if m.name == "Operating Margin")
        assert "percentage points" in (margin_metric.change or "")

        # Historical trend and table
        assert len(res.trend) == 4
        assert len(res.table) == 4

        # Findings
        assert len(res.findings) >= 3
        for finding in res.findings:
            assert len(finding.text) > 10

    def test_calc_pct_change_math(self) -> None:
        """Verify deterministic mathematical calculation of percentage changes."""
        # Positive change
        change, trend = FinancialAnalysisService._calc_pct_change(120.0, 100.0)
        assert change == "+20.0%"
        assert trend == "positive"

        # Negative change
        change, trend = FinancialAnalysisService._calc_pct_change(85.0, 100.0)
        assert change == "-15.0%"
        assert trend == "negative"

        # Zero change
        change, trend = FinancialAnalysisService._calc_pct_change(100.0, 100.0)
        assert change == "0.0%"
        assert trend == "neutral"

        # Previous None
        change, trend = FinancialAnalysisService._calc_pct_change(100.0, None)
        assert change is None
        assert trend == "neutral"

    def test_calc_pp_change_math(self) -> None:
        """Verify deterministic calculation of percentage point margin differences."""
        # Margin expansion
        change, trend = FinancialAnalysisService._calc_pp_change(31.5, 29.8)
        assert change == "+1.7 percentage points"
        assert trend == "positive"

        # Margin compression
        change, trend = FinancialAnalysisService._calc_pp_change(8.2, 16.8)
        assert change == "-8.6 percentage points"
        assert trend == "negative"

        # No change
        change, trend = FinancialAnalysisService._calc_pp_change(25.0, 25.0)
        assert change == "0.0 percentage points"
        assert trend == "neutral"

        # Previous None
        change, trend = FinancialAnalysisService._calc_pp_change(25.0, None)
        assert change is None
        assert trend == "neutral"


class TestAnalysisApiEndpoints:
    """Integration tests for FastAPI /api/analysis endpoints."""

    def test_analysis_apple(self, client: TestClient) -> None:
        """Verify Apple financial analysis request and structure."""
        response = client.post(
            "/api/analysis", json={"company": "Apple", "query": "Show financial analysis"}
        )
        assert response.status_code == 200
        data = response.json()

        assert data["company"]["name"] == "Apple Inc."
        assert data["company"]["ticker"] == "AAPL"
        assert len(data["metrics"]) == 4
        assert len(data["trend"]) == 4
        assert len(data["findings"]) >= 3
        is_sec = settings.FINANCIAL_DATA_MODE == "sec"
        assert data["source"]["name"] == ("SEC EDGAR" if is_sec else "Demo financial fixture")
        assert data["source"]["type"] == ("sec" if is_sec else "fixture")

    def test_analysis_microsoft(self, client: TestClient) -> None:
        """Verify Microsoft financial analysis request and structure."""
        response = client.post(
            "/api/analysis", json={"company": "Microsoft", "query": "Show financial analysis"}
        )
        assert response.status_code == 200
        data = response.json()

        assert data["company"]["name"] == "Microsoft Corporation"
        assert data["company"]["ticker"] == "MSFT"
        assert len(data["metrics"]) == 4
        assert len(data["trend"]) == 4
        assert len(data["findings"]) >= 3
        is_sec = settings.FINANCIAL_DATA_MODE == "sec"
        assert data["source"]["name"] == ("SEC EDGAR" if is_sec else "Demo financial fixture")
        assert data["source"]["type"] == ("sec" if is_sec else "fixture")

    def test_analysis_tesla(self, client: TestClient) -> None:
        """Verify Tesla financial analysis request and structure."""
        response = client.post(
            "/api/analysis", json={"company": "Tesla", "query": "Show financial analysis"}
        )
        assert response.status_code == 200
        data = response.json()

        assert data["company"]["name"] == "Tesla, Inc."
        assert data["company"]["ticker"] == "TSLA"
        assert len(data["metrics"]) == 4
        assert len(data["trend"]) == 4
        assert len(data["findings"]) >= 3
        is_sec = settings.FINANCIAL_DATA_MODE == "sec"
        assert data["source"]["name"] == ("SEC EDGAR" if is_sec else "Demo financial fixture")
        assert data["source"]["type"] == ("sec" if is_sec else "fixture")

    def test_analyze_apple_endpoint(self, client: TestClient) -> None:
        """Compatibility alias test for Apple endpoint."""
        self.test_analysis_apple(client)

    def test_analyze_microsoft_endpoint(self, client: TestClient) -> None:
        """Compatibility alias test for Microsoft endpoint."""
        self.test_analysis_microsoft(client)

    def test_analyze_tesla_endpoint(self, client: TestClient) -> None:
        """Compatibility alias test for Tesla endpoint."""
        self.test_analysis_tesla(client)

    def test_different_financial_data_across_companies(self, client: TestClient) -> None:
        """Verify that Apple, Microsoft, and Tesla return distinct isolated datasets."""
        res_apple = client.post("/api/analysis", json={"company": "Apple"})
        res_msft = client.post("/api/analysis", json={"company": "Microsoft"})
        res_tsla = client.post("/api/analysis", json={"company": "Tesla"})

        assert res_apple.status_code == 200
        assert res_msft.status_code == 200
        assert res_tsla.status_code == 200

        data_apple = res_apple.json()
        data_msft = res_msft.json()
        data_tsla = res_tsla.json()

        # Company tickers must differ
        assert data_apple["company"]["ticker"] == "AAPL"
        assert data_msft["company"]["ticker"] == "MSFT"
        assert data_tsla["company"]["ticker"] == "TSLA"

        # Financial values must differ
        apple_rev = [p["revenue"] for p in data_apple["trend"]]
        msft_rev = [p["revenue"] for p in data_msft["trend"]]
        tsla_rev = [p["revenue"] for p in data_tsla["trend"]]

        assert apple_rev != msft_rev
        assert apple_rev != tsla_rev
        assert msft_rev != tsla_rev

        apple_ni = [p["net_income"] for p in data_apple["trend"]]
        msft_ni = [p["net_income"] for p in data_msft["trend"]]
        tsla_ni = [p["net_income"] for p in data_tsla["trend"]]

        assert apple_ni != msft_ni
        assert apple_ni != tsla_ni
        assert msft_ni != tsla_ni

    def test_versioned_endpoint(self, client: TestClient) -> None:
        response = client.post("/api/v1/analysis", json={"company": "AAPL"})
        assert response.status_code == 200
        data = response.json()
        assert data["company"]["ticker"] == "AAPL"

    def test_unsupported_company_returns_404(self, client: TestClient) -> None:
        response = client.post("/api/analysis", json={"company": "Amazon"})
        assert response.status_code == 404
        data = response.json()
        assert "Unsupported company: Amazon" in data["detail"]

    def test_empty_request_body_returns_422(self, client: TestClient) -> None:
        response = client.post("/api/analysis", json={})
        assert response.status_code == 422

    def test_excessively_long_company_returns_422(self, client: TestClient) -> None:
        """Verify that payloads exceeding maximum length bounds are rejected with 422."""
        huge_company = "A" * 150
        response = client.post("/api/analysis", json={"company": huge_company})
        assert response.status_code == 422

    def test_cors_origins_configuration(self) -> None:
        """Verify that cors_origins_list correctly parses comma-separated origins."""
        assert len(settings.cors_origins_list) >= 1
        assert "http://localhost:5173" in settings.cors_origins_list


class TestSECModeContracts:
    """Explicit contract tests proving SEC mode execution, provenance, and failure behavior."""

    def test_sec_mode_contract_pipeline(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify pipeline contract:
        FINANCIAL_DATA_MODE=sec -> SEC client called -> normalized -> source.type == 'sec'.
        """
        monkeypatch.setattr(settings, "FINANCIAL_DATA_MODE", "sec")

        mock_raw = {
            "facts": {
                "us-gaap": {
                    "Revenues": {
                        "units": {
                            "USD": [
                                {
                                    "form": "10-K",
                                    "fp": "FY",
                                    "start": f"{y}-01-01",
                                    "end": f"{y}-12-31",
                                    "val": 50000000000.0,
                                    "filed": f"{y}-02-01",
                                }
                                for y in ["2021", "2022", "2023", "2024"]
                            ]
                        }
                    },
                    "OperatingIncomeLoss": {
                        "units": {
                            "USD": [
                                {
                                    "form": "10-K",
                                    "fp": "FY",
                                    "start": f"{y}-01-01",
                                    "end": f"{y}-12-31",
                                    "val": 10000000000.0,
                                    "filed": f"{y}-02-01",
                                }
                                for y in ["2021", "2022", "2023", "2024"]
                            ]
                        }
                    },
                    "NetIncomeLoss": {
                        "units": {
                            "USD": [
                                {
                                    "form": "10-K",
                                    "fp": "FY",
                                    "start": f"{y}-01-01",
                                    "end": f"{y}-12-31",
                                    "val": 8000000000.0,
                                    "filed": f"{y}-02-01",
                                }
                                for y in ["2021", "2022", "2023", "2024"]
                            ]
                        }
                    },
                    "EarningsPerShareDiluted": {
                        "units": {
                            "USD/shares": [
                                {
                                    "form": "10-K",
                                    "fp": "FY",
                                    "start": f"{y}-01-01",
                                    "end": f"{y}-12-31",
                                    "val": 2.5,
                                    "filed": f"{y}-02-01",
                                }
                                for y in ["2021", "2022", "2023", "2024"]
                            ]
                        }
                    },
                }
            }
        }
        with patch("app.services.sec_xbrl.fetch_company_facts", return_value=mock_raw):
            periods, source = FinancialDataService.get_company_data("TSLA")
            assert len(periods) == 4
            assert source.type == "sec"
            assert source.name == "SEC EDGAR"
            assert source.document_type == "10-K"

    def test_sec_failure_in_sec_mode_raises_error_without_fixture_fallback(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify contract: SEC failure under mode 'sec' raises error with NO fallback."""
        monkeypatch.setattr(settings, "FINANCIAL_DATA_MODE", "sec")

        with patch(
            "app.services.sec_xbrl.fetch_company_facts",
            side_effect=RuntimeError("SEC Service Outage"),
        ):
            with pytest.raises(ValueError, match="No financial data available for ticker: TSLA"):
                FinancialDataService.get_company_data("TSLA")
