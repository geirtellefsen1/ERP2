"""
Claude-powered cashflow narrative generator.

Produces a short plain-language explanation of the 13-week forecast
in the client's preferred language (nb-NO / sv-SE / fi-FI / en).

The narrator never invents numbers — it gets every number from the
forecast result and asks Claude only to wrap them in business prose.
The system prompt instructs Claude to refuse to make up data and to
always cite the specific week index when mentioning a number.
"""
from __future__ import annotations

from app.services.ai import (
    ClaudeMessage,
    get_claude_client,
)

from .models import ForecastResult


SYSTEM_PROMPT = """You are a senior financial controller writing a short \
cashflow commentary for a small business owner. You will be given a \
13-week cash forecast as structured data. Your job is to write 3-5 \
short paragraphs of plain business language explaining:

1. The current cash position and where it ends in 13 weeks
2. The biggest cash event in the forecast (largest single inflow or outflow)
3. Whether and when cash is projected to drop below the alert threshold
4. One concrete recommendation if cash is tight, or a brief positive note if not

RULES:
- Never invent numbers. Use ONLY numbers from the data provided.
- When you mention a number, refer to the specific week (e.g. "in week 7").
- Keep it short — under 250 words total.
- Plain business English (or the requested language). No accounting jargon.
- No bullet lists. Write in flowing paragraphs.
- Do not mention that you are an AI."""


def _format_forecast_for_prompt(result: ForecastResult) -> str:
    """Render the forecast as a deterministic data block for Claude."""
    lines = [
        f"Currency: {result.currency}",
        f"Forecast period: {result.forecast_start} to {result.forecast_end}",
        f"Opening balance: {result.opening_balance.amount} {result.currency}",
        f"Closing balance (end of week {len(result.weeks) - 1}): "
        f"{result.closing_balance.amount} {result.currency}",
        f"Total inflows: {result.total_inflows.amount} {result.currency}",
        f"Total outflows: {result.total_outflows.amount} {result.currency}",
    ]

    if result.threshold:
        lines.append(
            f"Alert threshold: {result.threshold.amount} {result.currency}"
        )
        if result.breach_weeks:
            lines.append(
                f"Threshold breached in weeks: {', '.join(map(str, result.breach_weeks))}"
            )
        else:
            lines.append("Threshold not breached at any point.")

    lowest = result.lowest_balance
    if lowest:
        lines.append(
            f"Lowest projected closing balance: {lowest[1].amount} {result.currency} "
            f"in week {lowest[0]}"
        )

    lines.append("")
    lines.append("Week-by-week:")
    for w in result.weeks:
        lines.append(
            f"  Week {w.week_index} ({w.week_start}): "
            f"open={w.opening_balance.amount}, "
            f"in={w.inflows.amount}, "
            f"out={w.outflows.amount}, "
            f"close={w.closing_balance.amount}"
            + (" [BELOW THRESHOLD]" if w.below_threshold else "")
        )

    return "\n".join(lines)


def generate_narrative(
    result: ForecastResult,
    language: str = "en",
    industry: str = "",
) -> str:
    """
    Ask Claude to write a narrative for this forecast.

    Returns the narrative as a string. Mutates `result.narrative` as a
    side-effect for convenience but the return value is the canonical
    output.
    """
    client = get_claude_client()

    data_block = _format_forecast_for_prompt(result)
    industry_note = (
        f"\nThe client operates in: {industry}\n" if industry else ""
    )

    user_content = (
        f"Here is the cash forecast data for a client.{industry_note}\n\n"
        f"{data_block}\n\n"
        f"Write the cashflow commentary now."
    )

    response = client.complete(
        system=SYSTEM_PROMPT,
        messages=[ClaudeMessage(role="user", content=user_content)],
        model="claude-opus-4-6",
        max_tokens=600,
        temperature=0.5,
        language=language,
    )

    result.narrative = response.text
    return response.text
