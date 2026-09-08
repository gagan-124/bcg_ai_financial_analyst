"""Deterministic financial analysis calculation and response synthesis service."""

import logging
from typing import Any

from app.schemas.financial import (
    ChartSeries,
    CompanyInfo,
    FinancialAnalysisResponse,
    FinancialFinding,
    FinancialMetric,
    FinancialPeriod,
    SourceInfo,
    StructuredChartData,
    StructuredTableData,
)
from app.services.financial_data import FinancialDataService

logger = logging.getLogger(__name__)


class FinancialAnalysisService:
    """Service handling financial calculations, ratios, YoY metrics, and deterministic findings."""

    def __init__(self, data_service: FinancialDataService | None = None) -> None:
        self.data_service = data_service or FinancialDataService()

    def analyze_company(self, company_identifier: str) -> FinancialAnalysisResponse:
        """Perform comprehensive deterministic financial analysis for a supported company.

        Raises:
            ValueError: If the company is unsupported or data cannot be retrieved.
        """
        company: CompanyInfo = self.data_service.resolve_company(company_identifier)

        if hasattr(self.data_service, "get_company_data"):
            periods, source = self.data_service.get_company_data(company.ticker)
        else:
            periods = self.data_service.get_company_periods(company.ticker)
            source = SourceInfo(
                name="Demo financial fixture",
                type="fixture",
                period=f"{periods[0].period} - {periods[-1].period}",
                reference="Standardized multi-year operating performance (demo fixture)",
            )

        if not periods:
            raise ValueError(f"Insufficient period data to analyze company: {company.name}")

        latest = periods[-1]
        previous = periods[-2] if len(periods) > 1 else None

        metrics = self._calculate_latest_metrics(latest, previous)
        findings = self._generate_findings(company, latest, previous, source)
        summary = self._generate_summary(company, latest, previous, source)

        return FinancialAnalysisResponse(
            company=company,
            summary=summary,
            metrics=metrics,
            trend=periods,
            table=periods,
            findings=findings,
            source=source,
        )

    def _calculate_latest_metrics(
        self,
        latest: FinancialPeriod,
        previous: FinancialPeriod | None,
    ) -> list[FinancialMetric]:
        """Compute latest metrics and calculate period-over-period differences."""
        # 1. Revenue
        rev_change, rev_trend = self._calc_pct_change(
            latest.revenue, previous.revenue if previous else None
        )
        rev_metric = FinancialMetric(
            name="Revenue",
            value=latest.revenue_formatted,
            raw_value=latest.revenue,
            unit="$B",
            period=f"FY{latest.period}",
            change=rev_change,
            change_label="YoY",
            trend=rev_trend,
        )

        # 2. Net Income
        ni_change, ni_trend = self._calc_pct_change(
            latest.net_income, previous.net_income if previous else None
        )
        ni_metric = FinancialMetric(
            name="Net Income",
            value=latest.net_income_formatted,
            raw_value=latest.net_income,
            unit="$B",
            period=f"FY{latest.period}",
            change=ni_change,
            change_label="YoY",
            trend=ni_trend,
        )

        # 3. Diluted EPS
        eps_change, eps_trend = self._calc_pct_change(
            latest.eps, previous.eps if previous else None
        )
        eps_metric = FinancialMetric(
            name="EPS",
            value=latest.eps_formatted,
            raw_value=latest.eps,
            unit="USD",
            period=f"FY{latest.period}",
            change=eps_change,
            change_label="YoY",
            trend=eps_trend,
        )

        # 4. Operating Margin (expressed in percentage points difference)
        margin_change, margin_trend = self._calc_pp_change(
            latest.operating_margin, previous.operating_margin if previous else None
        )
        margin_metric = FinancialMetric(
            name="Operating Margin",
            value=latest.operating_margin_formatted,
            raw_value=latest.operating_margin,
            unit="%",
            period=f"FY{latest.period}",
            change=margin_change,
            change_label=f"vs FY{previous.period}" if previous else "YoY",
            trend=margin_trend,
        )

        return [rev_metric, ni_metric, eps_metric, margin_metric]

    @staticmethod
    def _calc_pct_change(current: float, previous: float | None) -> tuple[str | None, str]:
        """Calculate percentage change between two figures."""
        if previous is None or previous == 0:
            return None, "neutral"

        pct = ((current - previous) / abs(previous)) * 100.0
        trend = "positive" if pct > 0 else "negative" if pct < 0 else "neutral"
        sign = "+" if pct > 0 else ""
        return f"{sign}{pct:.1f}%", trend

    @staticmethod
    def _calc_pp_change(current: float, previous: float | None) -> tuple[str | None, str]:
        """Calculate percentage point difference between two percentage figures."""
        if previous is None:
            return None, "neutral"

        diff = current - previous
        trend = "positive" if diff > 0 else "negative" if diff < 0 else "neutral"
        sign = "+" if diff > 0 else ""
        return f"{sign}{diff:.1f} percentage points", trend

    @staticmethod
    def _generate_findings(
        company: CompanyInfo,
        latest: FinancialPeriod,
        previous: FinancialPeriod | None,
        source: SourceInfo | None = None,
    ) -> list[FinancialFinding]:
        """Generate deterministic analytical findings based on calculated metrics."""
        findings: list[FinancialFinding] = []

        # Revenue finding
        if previous:
            rev_diff = latest.revenue - previous.revenue
            if rev_diff > 0:
                rev_pct = ((latest.revenue - previous.revenue) / previous.revenue) * 100
                findings.append(
                    FinancialFinding(
                        text=(
                            f"Revenue expanded to {latest.revenue_formatted} in {latest.period}, "
                            f"growing by +{rev_pct:.1f}% compared to {previous.period}."
                        ),
                        type="positive",
                    )
                )
            else:
                rev_pct = ((latest.revenue - previous.revenue) / previous.revenue) * 100
                findings.append(
                    FinancialFinding(
                        text=(
                            f"Revenue contracted to {latest.revenue_formatted} in {latest.period} "
                            f"({rev_pct:.1f}% YoY)."
                        ),
                        type="observation",
                    )
                )

        # Profitability & Margin finding
        if previous:
            margin_diff = latest.operating_margin - previous.operating_margin
            if margin_diff >= 0:
                findings.append(
                    FinancialFinding(
                        text=(
                            f"Operating margin expanded to {latest.operating_margin_formatted} "
                            f"(+{margin_diff:.1f} percentage points), "
                            "demonstrating operational cost discipline."
                        ),
                        type="positive",
                    )
                )
            else:
                findings.append(
                    FinancialFinding(
                        text=(
                            f"Operating margin declined to {latest.operating_margin_formatted} "
                            f"({margin_diff:.1f} percentage points vs prior period), "
                            "reflecting cost pressures."
                        ),
                        type="observation",
                    )
                )

        # Net Income / Bottom-line finding
        if previous:
            if latest.net_income > previous.net_income:
                findings.append(
                    FinancialFinding(
                        text=(
                            f"Net income reached {latest.net_income_formatted} "
                            f"alongside diluted EPS of {latest.eps_formatted}."
                        ),
                        type="positive",
                    )
                )
            else:
                findings.append(
                    FinancialFinding(
                        text=(
                            f"Net income stood at {latest.net_income_formatted} "
                            f"with diluted EPS of {latest.eps_formatted}."
                        ),
                        type="observation",
                    )
                )

        # Source provenance finding
        if source and source.type == "sec":
            findings.append(
                FinancialFinding(
                    text=(
                        "Metrics normalized directly from SEC EDGAR XBRL filings "
                        f"for {company.name}."
                    ),
                    type="observation",
                )
            )
        else:
            findings.append(
                FinancialFinding(
                    text=(
                        "Metrics generated from standardized demo financial fixtures "
                        "for pipeline testing."
                    ),
                    type="observation",
                )
            )

        return findings

    @staticmethod
    def _generate_summary(
        company: CompanyInfo,
        latest: FinancialPeriod,
        previous: FinancialPeriod | None,
        source: SourceInfo | None = None,
    ) -> str:
        """Construct executive narrative summary for the financial overview."""
        if not previous:
            return (
                f"{company.name} ({company.ticker}) reported revenue of {latest.revenue_formatted} "
                f"with an operating margin of {latest.operating_margin_formatted}."
            )

        rev_growth = ((latest.revenue - previous.revenue) / previous.revenue) * 100
        margin_diff = latest.operating_margin - previous.operating_margin

        growth_direction = "an increase" if rev_growth >= 0 else "a decline"
        margin_direction = "expanded" if margin_diff >= 0 else "compressed"
        sign = "+" if margin_diff >= 0 else ""

        source_label = (
            " (Source: SEC EDGAR)"
            if source and source.type == "sec"
            else " (Demo financial fixture)"
        )

        return (
            f"{company.name} ({company.ticker}) delivered revenue of {latest.revenue_formatted} "
            f"in {latest.period}, representing {growth_direction} of {abs(rev_growth):.1f}% YoY. "
            f"Operating margin {margin_direction} to {latest.operating_margin_formatted} "
            f"({sign}{margin_diff:.1f} percentage points vs {previous.period}), "
            f"yielding net income of {latest.net_income_formatted} and diluted EPS of "
            f"{latest.eps_formatted}.{source_label}"
        )

    def build_question_visual_context(
        self,
        question: str,
        primary: FinancialAnalysisResponse,
        additional_analyses: list[FinancialAnalysisResponse] | None = None,
    ) -> tuple[
        StructuredChartData | None,
        StructuredTableData | None,
        list[FinancialMetric] | None,
    ]:
        """Construct structured chart and table data for questions requiring visualizations."""
        q_lower = question.lower()

        # 1. Multi-Company Comparison Visualization
        if additional_analyses:
            all_companies = [primary] + additional_analyses
            period_set: set[str] = set()
            for comp in all_companies:
                for p in comp.table:
                    period_set.add(p.period)
            sorted_periods = sorted(period_set)

            # Build comparison chart data points
            chart_data: list[dict[str, Any]] = []
            for period in sorted_periods:
                point: dict[str, Any] = {"period": period}
                for comp in all_companies:
                    matching = next((p for p in comp.table if p.period == period), None)
                    if matching:
                        point[comp.company.ticker] = matching.revenue
                        point[f"{comp.company.ticker}_formatted"] = matching.revenue_formatted
                chart_data.append(point)

            palette = ["#8BBB92", "#5D8480", "#9EBDB9", "#3D6E68"]
            series: list[ChartSeries] = [
                ChartSeries(
                    dataKey=comp.company.ticker,
                    label=f"{comp.company.name} ({comp.company.ticker})",
                    stroke=palette[idx % len(palette)],
                )
                for idx, comp in enumerate(all_companies)
            ]

            tickers_str = " vs ".join(comp.company.ticker for comp in all_companies)
            chart = StructuredChartData(
                title=f"Revenue Comparison ({tickers_str})",
                subtitle="Annual reported revenue in billions USD",
                data=chart_data,
                valueKey=primary.company.ticker,
                unit="$B",
                series=series,
            )

            # Build side-by-side comparison table
            columns: list[dict[str, Any]] = [
                {"key": "metric", "header": "Metric", "align": "left"}
            ]
            for comp in all_companies:
                columns.append({
                    "key": comp.company.ticker,
                    "header": f"{comp.company.name} ({comp.company.ticker})",
                    "align": "right",
                    "isNumeric": True,
                })

            table_rows: list[dict[str, Any]] = [
                {
                    "id": "row-rev",
                    "metric": "Latest Revenue",
                    "values": {
                        comp.company.ticker: comp.table[-1].revenue_formatted
                        if comp.table else "—"
                        for comp in all_companies
                    },
                    "isHighlight": True,
                },
                {
                    "id": "row-margin",
                    "metric": "Operating Margin",
                    "values": {
                        comp.company.ticker: comp.table[-1].operating_margin_formatted
                        if comp.table else "—"
                        for comp in all_companies
                    },
                    "isHighlight": True,
                },
                {
                    "id": "row-ni",
                    "metric": "Net Income",
                    "values": {
                        comp.company.ticker: comp.table[-1].net_income_formatted
                        if comp.table else "—"
                        for comp in all_companies
                    },
                },
                {
                    "id": "row-eps",
                    "metric": "Diluted EPS",
                    "values": {
                        comp.company.ticker: comp.table[-1].eps_formatted
                        if comp.table else "—"
                        for comp in all_companies
                    },
                },
            ]

            table = StructuredTableData(
                title=f"Comparative Financial Performance ({tickers_str})",
                subtitle="Authoritative SEC 10-K reported performance comparison",
                columns=columns,
                rows=table_rows,
            )

            combined_metrics = list(primary.metrics)
            return chart, table, combined_metrics

        # 2. Single-Company Trend / Visualization Questions
        trend_keywords = [
            "growth", "trend", "decline", "increase", "decrease", "change",
            "history", "historical", "over the years", "trajectory", "performance",
            "compare", "chart", "graph", "plot", "revenue", "margin", "profit",
        ]
        warrants_visualization = any(kw in q_lower for kw in trend_keywords)

        if not warrants_visualization or not primary.table:
            return None, None, None

        # Check metric focus: margin
        if "operating margin" in q_lower or "margin" in q_lower:
            chart_data = [
                {
                    "period": p.period,
                    "value": p.operating_margin,
                    "formattedValue": p.operating_margin_formatted,
                }
                for p in primary.table
            ]
            chart = StructuredChartData(
                title=f"{primary.company.name} Operating Margin Trend",
                subtitle="Annual operating margin percentage",
                data=chart_data,
                valueKey="value",
                unit="%",
            )
            matched_metrics = [m for m in primary.metrics if "Margin" in m.name]
            return chart, None, matched_metrics or primary.metrics[:2]

        # Check metric focus: net income / profit
        if "net income" in q_lower or "profit" in q_lower or "earnings" in q_lower:
            chart_data = [
                {
                    "period": p.period,
                    "value": p.net_income,
                    "formattedValue": p.net_income_formatted,
                }
                for p in primary.table
            ]
            chart = StructuredChartData(
                title=f"{primary.company.name} Net Income Trend",
                subtitle="Annual net income in billions USD",
                data=chart_data,
                valueKey="value",
                unit="$B",
            )
            matched_metrics = [m for m in primary.metrics if "Net Income" in m.name]
            return chart, None, matched_metrics or primary.metrics[:2]

        # Default to Revenue Trend for revenue or general trend questions
        chart_data = [
            {
                "period": p.period,
                "value": p.revenue,
                "formattedValue": p.revenue_formatted,
            }
            for p in primary.table
        ]
        chart = StructuredChartData(
            title=f"{primary.company.name} Revenue Trend",
            subtitle="Annual reported revenue in billions USD",
            data=chart_data,
            valueKey="value",
            unit="$B",
        )
        matched_metrics = [m for m in primary.metrics if "Revenue" in m.name]
        return chart, None, matched_metrics or primary.metrics[:2]
