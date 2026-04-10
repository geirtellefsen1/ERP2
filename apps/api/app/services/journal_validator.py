from decimal import Decimal


def validate_entry(lines: list) -> tuple[bool, list[str]]:
    """Validate journal entry lines.

    Args:
        lines: List of line objects/dicts with debit_amount and credit_amount.

    Returns:
        Tuple of (is_valid, errors list).
    """
    errors = []

    if len(lines) < 2:
        errors.append("Journal entry must have at least 2 lines")

    debit_total = Decimal("0")
    credit_total = Decimal("0")

    for i, line in enumerate(lines):
        debit = Decimal(str(line.debit_amount))
        credit = Decimal(str(line.credit_amount))

        if debit == 0 and credit == 0:
            errors.append(f"Line {i + 1}: amount cannot be zero for both debit and credit")

        debit_total += debit
        credit_total += credit

    if debit_total != credit_total:
        errors.append(
            f"Entry is not balanced: debits ({debit_total}) != credits ({credit_total})"
        )

    is_valid = len(errors) == 0
    return is_valid, errors
