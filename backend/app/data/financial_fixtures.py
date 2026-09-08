"""Controlled local financial fixture datasets.

IMPORTANT NOTICE:
These values represent demonstration/fixture data used to establish the backend
financial-analysis pipeline and frontend data contracts. They do NOT represent live
market data or direct SEC EDGAR filings.
"""

from typing import Any

COMPANY_METADATA: dict[str, dict[str, str]] = {
    "AAPL": {
        "name": "Apple Inc.",
        "ticker": "AAPL",
    },
    "MSFT": {
        "name": "Microsoft Corporation",
        "ticker": "MSFT",
    },
    "TSLA": {
        "name": "Tesla, Inc.",
        "ticker": "TSLA",
    },
}

COMPANY_ALIASES: dict[str, str] = {
    # Apple mappings
    "apple": "AAPL",
    "apple inc": "AAPL",
    "apple inc.": "AAPL",
    "apple, inc.": "AAPL",
    "apple, inc": "AAPL",
    "apple corporation": "AAPL",
    "aapl": "AAPL",
    # Microsoft mappings
    "microsoft": "MSFT",
    "microsoft corp": "MSFT",
    "microsoft corp.": "MSFT",
    "microsoft corporation": "MSFT",
    "microsoft inc": "MSFT",
    "microsoft inc.": "MSFT",
    "msft": "MSFT",
    # Tesla mappings
    "tesla": "TSLA",
    "tesla inc": "TSLA",
    "tesla inc.": "TSLA",
    "tesla, inc": "TSLA",
    "tesla, inc.": "TSLA",
    "tesla corporation": "TSLA",
    "tsla": "TSLA",
}


FINANCIAL_FIXTURES: dict[str, list[dict[str, Any]]] = {
    "AAPL": [
        {
            "period": "2022",
            "revenue": 394.3,
            "revenue_formatted": "$394.3B",
            "net_income": 99.8,
            "net_income_formatted": "$99.8B",
            "eps": 6.11,
            "eps_formatted": "$6.11",
            "operating_margin": 30.3,
            "operating_margin_formatted": "30.3%",
        },
        {
            "period": "2023",
            "revenue": 383.3,
            "revenue_formatted": "$383.3B",
            "net_income": 97.0,
            "net_income_formatted": "$97.0B",
            "eps": 6.13,
            "eps_formatted": "$6.13",
            "operating_margin": 29.8,
            "operating_margin_formatted": "29.8%",
        },
        {
            "period": "2024",
            "revenue": 391.0,
            "revenue_formatted": "$391.0B",
            "net_income": 93.7,
            "net_income_formatted": "$93.7B",
            "eps": 6.08,
            "eps_formatted": "$6.08",
            "operating_margin": 31.5,
            "operating_margin_formatted": "31.5%",
        },
        {
            "period": "2025",
            "revenue": 410.2,
            "revenue_formatted": "$410.2B",
            "net_income": 104.5,
            "net_income_formatted": "$104.5B",
            "eps": 6.85,
            "eps_formatted": "$6.85",
            "operating_margin": 32.1,
            "operating_margin_formatted": "32.1%",
        },
    ],
    "MSFT": [
        {
            "period": "2022",
            "revenue": 198.3,
            "revenue_formatted": "$198.3B",
            "net_income": 72.7,
            "net_income_formatted": "$72.7B",
            "eps": 9.65,
            "eps_formatted": "$9.65",
            "operating_margin": 42.1,
            "operating_margin_formatted": "42.1%",
        },
        {
            "period": "2023",
            "revenue": 211.9,
            "revenue_formatted": "$211.9B",
            "net_income": 72.4,
            "net_income_formatted": "$72.4B",
            "eps": 9.68,
            "eps_formatted": "$9.68",
            "operating_margin": 41.8,
            "operating_margin_formatted": "41.8%",
        },
        {
            "period": "2024",
            "revenue": 245.1,
            "revenue_formatted": "$245.1B",
            "net_income": 88.1,
            "net_income_formatted": "$88.1B",
            "eps": 11.80,
            "eps_formatted": "$11.80",
            "operating_margin": 44.6,
            "operating_margin_formatted": "44.6%",
        },
        {
            "period": "2025",
            "revenue": 275.5,
            "revenue_formatted": "$275.5B",
            "net_income": 98.5,
            "net_income_formatted": "$98.5B",
            "eps": 13.20,
            "eps_formatted": "$13.20",
            "operating_margin": 45.2,
            "operating_margin_formatted": "45.2%",
        },
    ],
    "TSLA": [
        {
            "period": "2022",
            "revenue": 81.5,
            "revenue_formatted": "$81.5B",
            "net_income": 12.6,
            "net_income_formatted": "$12.6B",
            "eps": 3.62,
            "eps_formatted": "$3.62",
            "operating_margin": 16.8,
            "operating_margin_formatted": "16.8%",
        },
        {
            "period": "2023",
            "revenue": 96.8,
            "revenue_formatted": "$96.8B",
            "net_income": 15.0,
            "net_income_formatted": "$15.0B",
            "eps": 4.30,
            "eps_formatted": "$4.30",
            "operating_margin": 14.3,
            "operating_margin_formatted": "14.3%",
        },
        {
            "period": "2024",
            "revenue": 97.7,
            "revenue_formatted": "$97.7B",
            "net_income": 7.1,
            "net_income_formatted": "$7.1B",
            "eps": 2.04,
            "eps_formatted": "$2.04",
            "operating_margin": 8.2,
            "operating_margin_formatted": "8.2%",
        },
        {
            "period": "2025",
            "revenue": 112.4,
            "revenue_formatted": "$112.4B",
            "net_income": 10.2,
            "net_income_formatted": "$10.2B",
            "eps": 2.95,
            "eps_formatted": "$2.95",
            "operating_margin": 10.5,
            "operating_margin_formatted": "10.5%",
        },
    ],
}
