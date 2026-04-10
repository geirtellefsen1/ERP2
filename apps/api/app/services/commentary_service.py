from app.services.ai_client import ClaudeClient


def get_tone_guidance(tone: str) -> str:
    """Returns instruction text for each tone style."""
    guidance = {
        "formal": (
            "Write in a formal, professional tone suitable for board-level "
            "management reporting. Use precise financial terminology, passive "
            "voice where appropriate, and structured paragraphs."
        ),
        "conversational": (
            "Write in a friendly, approachable tone as if explaining the "
            "financials to a small business owner. Avoid jargon, use plain "
            "language, and keep sentences short and clear."
        ),
        "technical": (
            "Write in a detailed, technical accounting tone aimed at qualified "
            "accountants and auditors. Reference accounting standards where "
            "relevant, include ratio analysis, and use precise financial metrics."
        ),
    }
    return guidance.get(tone, guidance["formal"])


async def generate_commentary(
    client_name: str,
    period: str,
    financial_data: dict,
    tone: str = "formal",
    length: str = "full",
) -> str:
    """Generate management commentary using ClaudeClient.

    Falls back to template-based narrative if no API key is configured.
    """
    token_limits = {
        "executive_summary": 400,
        "full": 1200,
        "extended": 2000,
    }
    max_tokens = token_limits.get(length, 1200)
    tone_text = get_tone_guidance(tone)

    # Build financial summary for the prompt
    data_summary = _format_financial_data(financial_data)

    system_prompt = (
        "You are a management accountant writing narrative commentary for "
        "financial reports. Generate insightful, accurate commentary based "
        "on the financial data provided.\n\n"
        f"Tone guidance: {tone_text}"
    )

    user_message = (
        f"Write a management commentary report for {client_name} "
        f"covering the period {period}.\n\n"
        f"Financial data:\n{data_summary}\n\n"
        f"Please provide analysis of performance, key trends, and "
        f"recommendations where appropriate."
    )

    try:
        ai_client = ClaudeClient()
        result = await ai_client.complete(
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=max_tokens,
        )
        return result
    except Exception:
        # Fallback to template-based narrative
        return _generate_fallback_commentary(client_name, period, financial_data, tone)


def _format_financial_data(financial_data: dict) -> str:
    """Format financial data dict into a readable string for the AI prompt."""
    lines = []
    for key, value in financial_data.items():
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for sub_key, sub_value in value.items():
                lines.append(f"  {sub_key}: {sub_value}")
        elif isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines) if lines else "No detailed financial data provided."


def _generate_fallback_commentary(
    client_name: str,
    period: str,
    financial_data: dict,
    tone: str,
) -> str:
    """Generate template-based commentary when AI is unavailable."""
    revenue = financial_data.get("total_revenue", "N/A")
    expenses = financial_data.get("total_expenses", "N/A")
    net_income = financial_data.get("net_income", "N/A")

    return (
        f"Management Commentary for {client_name}\n"
        f"Period: {period}\n\n"
        f"During the reporting period, {client_name} recorded total revenue of "
        f"{revenue} against total expenses of {expenses}, resulting in a net "
        f"income of {net_income}.\n\n"
        f"This report was generated using template-based analysis. "
        f"For AI-powered narrative commentary, please configure the API key."
    )


def build_report_html(
    client_name: str,
    period: str,
    commentary: str,
    financial_data: dict,
) -> str:
    """Generate an HTML report with styled tables and commentary section."""
    # Build financial data table rows
    table_rows = ""
    for key, value in financial_data.items():
        if not isinstance(value, (dict, list)):
            formatted_key = key.replace("_", " ").title()
            table_rows += (
                f"      <tr>\n"
                f"        <td style=\"padding: 8px 12px; border-bottom: 1px solid #e5e7eb;\">"
                f"{formatted_key}</td>\n"
                f"        <td style=\"padding: 8px 12px; border-bottom: 1px solid #e5e7eb; "
                f"text-align: right;\">{value}</td>\n"
                f"      </tr>\n"
            )

    # Convert commentary newlines to HTML
    commentary_html = commentary.replace("\n", "<br>\n")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Financial Report - {client_name}</title>
  <style>
    body {{ font-family: Arial, Helvetica, sans-serif; margin: 40px; color: #1f2937; }}
    .header {{ border-bottom: 3px solid #2563eb; padding-bottom: 16px; margin-bottom: 24px; }}
    .header h1 {{ color: #1e40af; margin: 0 0 4px 0; }}
    .header p {{ color: #6b7280; margin: 0; }}
    .section {{ margin-bottom: 32px; }}
    .section h2 {{ color: #1e40af; font-size: 18px; border-bottom: 1px solid #e5e7eb; padding-bottom: 8px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th {{ background: #eff6ff; padding: 10px 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #2563eb; }}
    .commentary {{ background: #f9fafb; padding: 20px; border-radius: 8px; line-height: 1.7; }}
    .footer {{ margin-top: 40px; padding-top: 16px; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 12px; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>Financial Report</h1>
    <p>{client_name} &mdash; {period}</p>
  </div>

  <div class="section">
    <h2>Financial Summary</h2>
    <table>
      <thead>
        <tr>
          <th>Metric</th>
          <th style="text-align: right;">Value</th>
        </tr>
      </thead>
      <tbody>
{table_rows}
      </tbody>
    </table>
  </div>

  <div class="section">
    <h2>Management Commentary</h2>
    <div class="commentary">
      {commentary_html}
    </div>
  </div>

  <div class="footer">
    <p>Generated by BPO Nexus &mdash; Narrative Report Engine</p>
  </div>
</body>
</html>"""
    return html
