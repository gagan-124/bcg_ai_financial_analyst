"""XBRL Normalizer Service

Transforms SEC Company Facts JSON into a list of normalized financial period dictionaries
compatible with the FinancialPeriod Pydantic model.
"""

from datetime import datetime
from typing import Any, Dict, List


def _extract_metric(us_gaap: Dict[str, Any], tag_candidates: List[str]) -> Dict[str, float]:
    """Extract a mapping of fiscal year (string) to metric value for annual 10-K filings.

    Filters for 10-K filings and full-year periods (~330-390 days) to ensure accurate
    annual metrics. When multiple filings report for the same year, the latest is retained.
    """
    result: Dict[str, Dict[str, Any]] = {}
    for tag in tag_candidates:
        if tag not in us_gaap:
            continue
        units = us_gaap[tag].get("units", {})
        for unit_entries in units.values():
            for entry in unit_entries:
                if entry.get("form") == "10-K" and entry.get("fp") == "FY":
                    start_str = entry.get("start")
                    end_str = entry.get("end")
                    val = entry.get("val")
                    filed = entry.get("filed", "")
                    if start_str and end_str and isinstance(val, (int, float)):
                        try:
                            d_start = datetime.strptime(start_str, "%Y-%m-%d")
                            d_end = datetime.strptime(end_str, "%Y-%m-%d")
                            days = (d_end - d_start).days
                            if 330 <= days <= 390:
                                year = str(d_end.year)
                                if year not in result or filed > result[year]["filed"]:
                                    result[year] = {"val": float(val), "filed": filed}
                        except Exception:
                            pass
    return {k: v["val"] for k, v in result.items()}


def _format_billions(value: float) -> str:
    """Format a raw USD amount as billions with one decimal place, e.g. $391.0B."""
    billions = value / 1_000_000_000
    return f"${billions:.1f}B"


def normalize_company_facts(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize SEC Company Facts JSON into the structure expected by the app.

    Extracts annual revenue, net income, diluted EPS, and calculates operating margin
    for each fiscal year present in 10-K filings.
    """
    if not isinstance(data, dict) or "facts" not in data:
        return []

    us_gaap = data["facts"].get("us-gaap", {})
    if not us_gaap:
        return []

    rev_tags = [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
    ]
    op_tags = ["OperatingIncomeLoss"]
    ni_tags = ["NetIncomeLoss"]
    eps_tags = ["EarningsPerShareDiluted"]

    rev_series = _extract_metric(us_gaap, rev_tags)
    op_series = _extract_metric(us_gaap, op_tags)
    ni_series = _extract_metric(us_gaap, ni_tags)
    eps_series = _extract_metric(us_gaap, eps_tags)

    common_years = sorted(
        set(rev_series.keys())
        & set(op_series.keys())
        & set(ni_series.keys())
        & set(eps_series.keys())
    )

    # Take the most recent 4 fiscal years
    selected_years = common_years[-4:]
    normalized: List[Dict[str, Any]] = []

    for fy in selected_years:
        revenue = rev_series[fy]
        op_income = op_series[fy]
        net_income = ni_series[fy]
        eps = eps_series[fy]

        margin = (op_income / revenue) * 100.0 if revenue else 0.0

        period_dict = {
            "period": fy,
            "revenue": round(revenue / 1_000_000_000, 1),
            "revenue_formatted": _format_billions(revenue),
            "net_income": round(net_income / 1_000_000_000, 1),
            "net_income_formatted": _format_billions(net_income),
            "eps": round(eps, 2),
            "eps_formatted": f"${eps:.2f}",
            "operating_margin": round(margin, 1),
            "operating_margin_formatted": f"{margin:.1f}%",
        }
        normalized.append(period_dict)

    return normalized
