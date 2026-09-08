"""Tests for conversational routing and multi-turn financial question flows.

Verifies:
- Initial company analysis routes to /api/analysis returning full FinancialResponse structure.
- Follow-up financial questions route to /api/analysis/question returning text-only answer.
- Active company context is preserved across follow-up questions.
- Follow-up questions without company names use the active company context.
- Switching companies routes to a new /api/analysis call and updates active company.
"""

from unittest.mock import patch

from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.services.llm_analysis import LLMAnalysisService

client = TestClient(app)


class TestConversationalRoutingFlows:
    """End-to-end routing simulation for multi-turn user conversations."""

    def test_case_a_analyze_microsoft_then_operating_margin_followup(self):
        """Case A:

        1. User: 'Analyze Microsoft' -> POST /api/analysis -> returns full overview.
        2. User: 'Why did Microsoft's operating margin increase?' -> POST /api/analysis/question
           -> returns text-only answer (NO FinancialResponse graph/table payload).
        """
        # Step 1: Initial company analysis
        initial_res = client.post("/api/analysis", json={"company": "Microsoft"})
        assert initial_res.status_code == status.HTTP_200_OK
        initial_data = initial_res.json()
        assert initial_data["company"]["ticker"] == "MSFT"
        assert "metrics" in initial_data
        assert "trend" in initial_data
        assert "table" in initial_data
        assert "findings" in initial_data
        active_company = initial_data["company"]["name"]

        # Step 2: Follow-up question
        mock_answer = (
            "Microsoft's operating margin increased from 41.8% in FY2023 to 44.6% in FY2024 "
            "as cloud gross profit expansion outpaced operating expense growth."
        )
        with patch.object(LLMAnalysisService, "answer_question", return_value=mock_answer):
            followup_res = client.post(
                "/api/analysis/question",
                json={
                    "company": active_company,
                    "question": "Why did Microsoft's operating margin increase?",
                },
            )
            assert followup_res.status_code == status.HTTP_200_OK
            followup_data = followup_res.json()

            # Verify question response: no full company overview structures (trend, findings)
            assert followup_data["answer"] == mock_answer
            assert followup_data["company"]["ticker"] == "MSFT"
            assert "trend" not in followup_data
            assert "findings" not in followup_data

    def test_case_b_analyze_microsoft_then_compare_revenue(self):
        """Case B:

        1. Analyze Microsoft
        2. Compare Microsoft's revenue between 2024 and 2025.
        -> Text answer using Microsoft's existing financial context.
        """
        initial_res = client.post("/api/analysis", json={"company": "Microsoft"})
        assert initial_res.status_code == status.HTTP_200_OK
        active_company = initial_res.json()["company"]["name"]

        mock_answer = (
            "In FY2024 Microsoft reported $245.1B in revenue (+15.7% YoY) "
            "compared to $211.9B in FY2023."
        )
        with patch.object(LLMAnalysisService, "answer_question", return_value=mock_answer):
            followup_res = client.post(
                "/api/analysis/question",
                json={
                    "company": active_company,
                    "question": "Compare Microsoft's revenue between 2024 and 2025.",
                },
            )
            assert followup_res.status_code == status.HTTP_200_OK
            followup_data = followup_res.json()
            assert followup_data["company"]["ticker"] == "MSFT"
            assert followup_data["answer"] == mock_answer
            assert "trend" not in followup_data

    def test_case_c_analyze_tesla_then_profitability_decline(self):
        """Case C:

        1. Analyze Tesla -> activeCompany = TSLA
        2. Why did profitability decline? -> Text answer using Tesla context.
        """
        initial_res = client.post("/api/analysis", json={"company": "Tesla"})
        assert initial_res.status_code == status.HTTP_200_OK
        active_company = initial_res.json()["company"]["name"]

        mock_answer = (
            "Tesla's operating margin declined to 8.2% in 2024 from 16.8% in 2022 "
            "primarily due to reduced average selling prices across vehicle lines."
        )
        with patch.object(LLMAnalysisService, "answer_question", return_value=mock_answer):
            followup_res = client.post(
                "/api/analysis/question",
                json={
                    "company": active_company,
                    "question": "Why did profitability decline?",
                },
            )
            assert followup_res.status_code == status.HTTP_200_OK
            followup_data = followup_res.json()
            assert followup_data["company"]["ticker"] == "TSLA"
            assert followup_data["answer"] == mock_answer

    def test_case_d_analyze_apple_then_operating_margin_question(self):
        """Case D:

        1. Analyze Apple -> activeCompany = AAPL
        2. What changed in Apple's operating margin? -> Text answer using Apple context.
        """
        initial_res = client.post("/api/analysis", json={"company": "Apple"})
        assert initial_res.status_code == status.HTTP_200_OK
        active_company = initial_res.json()["company"]["name"]

        mock_answer = (
            "Apple's operating margin expanded to 31.5% in FY2024 from 29.8% in FY2023, "
            "driven by higher Services revenue mix."
        )
        with patch.object(LLMAnalysisService, "answer_question", return_value=mock_answer):
            followup_res = client.post(
                "/api/analysis/question",
                json={
                    "company": active_company,
                    "question": "What changed in Apple's operating margin?",
                },
            )
            assert followup_res.status_code == status.HTTP_200_OK
            followup_data = followup_res.json()
            assert followup_data["company"]["ticker"] == "AAPL"
            assert followup_data["answer"] == mock_answer

    def test_case_e_analyze_microsoft_then_switch_to_analyze_tesla(self):
        """Case E:

        1. Analyze Microsoft -> active company = MSFT
        2. Analyze Tesla -> Tesla gets a new financial overview and active company changes to TSLA.
        """
        # Step 1: Microsoft
        msft_res = client.post("/api/analysis", json={"company": "Microsoft"})
        assert msft_res.status_code == status.HTTP_200_OK
        assert msft_res.json()["company"]["ticker"] == "MSFT"

        # Step 2: Switch to Tesla via new analysis request
        tsla_res = client.post("/api/analysis", json={"company": "Tesla"})
        assert tsla_res.status_code == status.HTTP_200_OK
        tsla_data = tsla_res.json()
        assert tsla_data["company"]["ticker"] == "TSLA"
        assert "metrics" in tsla_data
        assert "trend" in tsla_data
        # Active company is now Tesla
        active_company = tsla_data["company"]["name"]
        assert "Tesla" in active_company

    def test_case_f_analyze_microsoft_then_followup_without_company_name(self):
        """Case F:

        1. Analyze Microsoft -> active company = MSFT
        2. 'Why did operating margin increase?' (contains no company name)
        -> Uses active company context (MSFT) to answer.
        """
        msft_res = client.post("/api/analysis", json={"company": "Microsoft"})
        assert msft_res.status_code == status.HTTP_200_OK
        active_company = msft_res.json()["company"]["name"]

        mock_answer = (
            "Operating margin expanded by 2.8 percentage points to 44.6% in FY2024 "
            "as revenue growth exceeded operating expense increases."
        )
        with patch.object(LLMAnalysisService, "answer_question", return_value=mock_answer):
            followup_res = client.post(
                "/api/analysis/question",
                json={
                    "company": active_company,
                    "question": "Why did operating margin increase?",
                },
            )
            assert followup_res.status_code == status.HTTP_200_OK
            followup_data = followup_res.json()
            assert followup_data["company"]["ticker"] == "MSFT"
            assert followup_data["answer"] == mock_answer

    def test_acceptance_a_analyze_apple_then_net_income_followup(self):
        """Acceptance A:

        1. Analyze Apple -> returns Apple graphs + metrics.
        2. 'Why did Apple's net income increase over the years?' -> routes to /api/analysis/question
           -> returns smart text explanation, NO graph, NO 'Unsupported company'.
        """
        apple_res = client.post("/api/analysis", json={"company": "Apple"})
        assert apple_res.status_code == status.HTTP_200_OK
        apple_data = apple_res.json()
        assert apple_data["company"]["ticker"] == "AAPL"
        assert "metrics" in apple_data
        assert "trend" in apple_data
        active_company = apple_data["company"]["name"]

        mock_answer = (
            "Apple's net income expanded to $93.7B in FY2024 from $97.0B in FY2023, "
            "supported by high-margin Services revenue expansion reaching $96.2B."
        )
        with patch.object(LLMAnalysisService, "answer_question", return_value=mock_answer):
            followup_res = client.post(
                "/api/analysis/question",
                json={
                    "company": active_company,
                    "question": "Why did Apple's net income increase over the years?",
                },
            )
            assert followup_res.status_code == status.HTTP_200_OK
            followup_data = followup_res.json()
            assert followup_data["company"]["ticker"] == "AAPL"
            assert followup_data["answer"] == mock_answer
            # Strict guarantee: question endpoint response, no full company overview structures
            assert "trend" not in followup_data
            assert "findings" not in followup_data
