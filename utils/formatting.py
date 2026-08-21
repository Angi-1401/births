def format_as_thousands(value: float) -> str:
    """Formats a numeric value with thousands (es) separators."""

    return f"{value:,.0f}".replace(",", ".")
