"""
Claude-powered month-end report narrator.

Generates 3-5 short paragraphs of management commentary explaining the
P&L and balance sheet movements, in the client's preferred language.
The narrator NEVER invents numbers — every figure cited must come from
the structured data passed in.
"""
from __future__ import annotations

from app.services.ai import ClaudeMessage, get_claude_client

from .models import ReportResult


SYSTEM_PROMPT = """You are a senior management accountant writing the \
commentary section of a monthly management report for a small business \
owner. You will be given the client's P&L and balance sheet for a period, \
including comparatives if available.

Write 3-5 short paragraphs covering:

1. Top-line summary: revenue and profit, with the direction vs. prior period
2. The two or three biggest variance items in the P&L (the ones that moved
   most in absolute or % terms vs. the prior period)
3. Balance sheet highlights: cash position, debtors, key liabilities
4. One concrete recommendation or watch-out for next month

RULES:
- NEVER invent numbers. Use ONLY numbers from the data block provided.
- When you mention a number, cite the line code (e.g. "operating expenses,
  line 5000") so the reader can drill down.
- Plain business language. No accounting jargon.
- Under 350 words total.
- Write in flowing paragraphs, not bullet lists.
- Do not mention that you are an AI."""


def _format_report_for_prompt(result: ReportResult) -> str:
    lines = [
        f"Client: {result.client_name}",
        f"Period: {result.period_start} to {result.period_end}",
        f"Currency: {result.currency}",
        "",
        "P&L Summary:",
        f"  Total revenue: {result.total_revenue.amount}",
        f"  Total expenses: {result.total_expenses.amount}",
        f"  Net profit: {result.net_profit.amount}",
        "",
        "P&L Lines:",
    ]
    for line in result.pnl_lines:
        prior = ""
        if line.prior_amount:
            prior = f" (prior: {line.prior_amount.amount})"
        lines.append(
            f"  [{line.code}] {line.label} ({line.category}): "
            f"{line.amount.amount}{prior}"
        )

    lines.extend([
        "",
        "Balance Sheet Summary:",
        f"  Total assets: {result.total_assets.amount}",
        f"  Total liabilities: {result.total_liabilities.amount}",
        f"  Total equity: {result.total_equity.amount}",
        f"  Balanced: {result.is_balanced}",
        "",
        "Balance Sheet Lines:",
    ])
    for line in result.balance_sheet_lines:
        prior = ""
        if line.prior_amount:
            prior = f" (prior: {line.prior_amount.amount})"
        lines.append(
            f"  [{line.code}] {line.label} ({line.category}): "
            f"{line.amount.amount}{prior}"
        )

    if result.comparatives:
        lines.extend([
            "",
            f"Comparative period: {result.comparatives.label} "
            f"({result.comparatives.period_start} to {result.comparatives.period_end})",
        ])

    return "\n".join(lines)


def generate_report_narrative(
    result: ReportResult,
    industry: str = "",
) -> str:
    """
    Ask Claude to write the management commentary for this report.
    Mutates result.narrative as a side-effect; also returns the text.
    """
    client = get_claude_client()
    data_block = _format_report_for_prompt(result)
    industry_note = (
        f"\nThe client operates in: {industry}\n" if industry else ""
    )

    user_content = (
        f"Here is the monthly management report data.{industry_note}\n\n"
        f"{data_block}\n\n"
        f"Write the management commentary now."
    )

    response = client.complete(
        system=SYSTEM_PROMPT,
        messages=[ClaudeMessage(role="user", content=user_content)],
        model="claude-opus-4-6",
        max_tokens=800,
        temperature=0.4,
        language=result.language,
    )

    result.narrative = response.text
    return response.text
