from typing import Any

from pydantic import BaseModel, Field


class CompanyInfo(BaseModel):
    """Company identification schema."""

    name: str = Field(
        ...,
        description="Full legal company name",
        examples=["Apple Inc.", "Microsoft Corporation", "Tesla, Inc."],
    )
    ticker: str = Field(
        ...,
        description="Stock ticker symbol",
        examples=["AAPL", "MSFT", "TSLA"],
    )


class FinancialMetric(BaseModel):
    """Individual financial metric with value, change, and trend metadata."""

    name: str = Field(..., description="Metric label", examples=["Revenue"])
    value: str = Field(..., description="Formatted metric value", examples=["$391.0B"])
    raw_value: float | None = Field(default=None, description="Unformatted numeric value")
    unit: str | None = Field(default="USD", description="Unit of measurement")
    period: str | None = Field(
        default=None, description="Fiscal period or year", examples=["FY2024"]
    )
    change: str | None = Field(default=None, description="YoY or period change", examples=["+2.0%"])
    change_label: str | None = Field(
        default=None, description="Context label for change", examples=["YoY"]
    )
    trend: str | None = Field(
        default="neutral", description="Trend direction: positive, negative, neutral"
    )


class FinancialPeriod(BaseModel):
    """Normalized financial metrics for a single reporting period."""

    period: str = Field(..., description="Period identifier / fiscal year", examples=["2024"])
    revenue: float = Field(..., description="Revenue in billions USD", examples=[391.0])
    revenue_formatted: str = Field(
        ..., description="Formatted revenue string", examples=["$391.0B"]
    )
    net_income: float = Field(..., description="Net income in billions USD", examples=[93.7])
    net_income_formatted: str = Field(
        ..., description="Formatted net income string", examples=["$93.7B"]
    )
    eps: float = Field(..., description="Diluted earnings per share in USD", examples=[6.08])
    eps_formatted: str = Field(..., description="Formatted EPS string", examples=["$6.08"])
    operating_margin: float = Field(..., description="Operating margin percentage", examples=[31.5])
    operating_margin_formatted: str = Field(
        ..., description="Formatted margin string", examples=["31.5%"]
    )


class FinancialFinding(BaseModel):
    """Key qualitative or quantitative finding derived from the analysis."""

    text: str = Field(..., description="Finding statement")
    type: str = Field(
        default="observation", description="Finding category: observation, positive, risk, trend"
    )


class SourceInfo(BaseModel):
    """Data provenance and source citation metadata."""

    name: str = Field(
        default="Demo financial fixture", description="Source provider or dataset name"
    )
    type: str = Field(
        default="fixture", description="Source type: fixture, sec_edgar, xbrl, estimated"
    )
    document_type: str | None = Field(default=None, description="Underlying filing document type")
    period: str | None = Field(default=None, description="Source reporting period")
    reference: str | None = Field(default=None, description="Document or filing reference")


class FinancialAnalysisRequest(BaseModel):
    """Request payload for company financial analysis."""

    company: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description=(
            "Company name or ticker symbol (supported: "
            "Apple / AAPL, Microsoft / MSFT, Tesla / TSLA)"
        ),
        examples=["Apple", "Microsoft", "Tesla"],
    )
    query: str | None = Field(
        default="Show financial analysis",
        max_length=500,
        description="Optional natural language query",
        examples=["Show financial analysis"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "company": "Apple",
                    "query": "Show financial analysis",
                },
                {
                    "company": "Microsoft",
                    "query": "Show financial analysis",
                },
                {
                    "company": "Tesla",
                    "query": "Show financial analysis",
                },
            ]
        }
    }


class FinancialAnalysisResponse(BaseModel):
    """Structured response payload for financial analysis."""

    company: CompanyInfo
    summary: str
    metrics: list[FinancialMetric]
    trend: list[FinancialPeriod]
    table: list[FinancialPeriod]
    findings: list[FinancialFinding]
    source: SourceInfo


class FinancialQuestionRequest(BaseModel):
    """Request payload for follow-up financial questions."""

    company: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Company name or ticker symbol for active context",
        examples=["Microsoft", "Apple", "Tesla"],
    )
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Follow-up financial or analytical question",
        examples=[
            "Why did Microsoft's operating margin increase?",
            "What caused the revenue growth?",
        ],
    )


class ChartSeries(BaseModel):
    """Data series specification for multi-line financial charts."""

    dataKey: str
    label: str
    stroke: str | None = None


class StructuredChartData(BaseModel):
    """Structured financial visualization configuration for frontend Recharts."""

    title: str
    subtitle: str | None = None
    data: list[dict[str, Any]]
    valueKey: str | None = "value"
    unit: str | None = "$B"
    series: list[ChartSeries] | None = None


class StructuredTableData(BaseModel):
    """Structured financial table breakdown for frontend FinancialTable."""

    title: str
    subtitle: str | None = None
    columns: list[dict[str, Any]]
    rows: list[dict[str, Any]]


class FinancialQuestionResponse(BaseModel):
    """Response payload for grounded follow-up financial questions."""

    company: CompanyInfo
    question: str
    answer: str
    source: SourceInfo
    chart: StructuredChartData | None = None
    table: StructuredTableData | None = None
    metrics: list[FinancialMetric] | None = None


# Backwards compatibility schemas
class FinancialMetricResponse(BaseModel):
    """Schema for individual financial metric item."""

    metric_name: str
    value: float | None = None
    unit: str = "USD"
    period: str
    year: int


class FinancialStatementResponse(BaseModel):
    """Schema for financial statements response payload."""

    company_symbol: str
    statement_type: str = Field(..., description="income_statement, balance_sheet, cash_flow")
    data: list[dict[str, Any]] = Field(default_factory=list)
