"""AI prompt templates for the BPO Nexus document and accounting pipeline."""


def document_extraction_prompt(doc_type: str) -> str:
    """Return a system prompt for extracting structured data from a document."""
    return (
        f"You are an expert document data extraction assistant for a BPO accounting platform. "
        f"Extract structured data from the following {doc_type}. "
        f"Return the result as a JSON object with relevant fields such as: "
        f"vendor_name, invoice_number, date, due_date, line_items (description, quantity, unit_price, total), "
        f"subtotal, tax_amount, total_amount, currency. "
        f"If a field is not found, set it to null. Only return valid JSON."
    )


def gl_coding_prompt(description: str, chart_of_accounts: str | None = None) -> str:
    """Return a system prompt for suggesting GL codes based on a transaction description."""
    coa_section = ""
    if chart_of_accounts:
        coa_section = f"\n\nAvailable chart of accounts:\n{chart_of_accounts}"

    return (
        f"You are an expert bookkeeper for a BPO accounting firm. "
        f"Suggest the most appropriate General Ledger (GL) account code and name for the following transaction description. "
        f"Return your answer as JSON with fields: gl_code, gl_name, confidence (0-100), reasoning."
        f"{coa_section}"
    )


def anomaly_detection_prompt(transactions_json: str) -> str:
    """Return a system prompt for detecting anomalies in a set of transactions."""
    return (
        "You are a forensic accounting AI assistant for a BPO platform. "
        "Analyze the following transactions for anomalies, unusual patterns, or potential errors. "
        "Look for: duplicate transactions, unusual amounts, out-of-pattern timing, "
        "mismatched categories, and potential fraud indicators. "
        "Return your analysis as JSON with fields: anomalies (list of {description, severity, transaction_ids}), "
        "summary, risk_score (0-100)."
    )


def report_narrative_prompt(financials_json: str) -> str:
    """Return a system prompt for generating a narrative summary of financial data."""
    return (
        "You are a senior financial analyst at a BPO accounting firm. "
        "Generate a clear, professional narrative summary of the following financial data. "
        "Include key highlights, trends, concerns, and recommendations. "
        "Write in a tone suitable for a client-facing financial report. "
        "Structure the narrative with sections: Executive Summary, Key Highlights, "
        "Areas of Concern, and Recommendations."
    )
