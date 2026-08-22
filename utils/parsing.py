import pandas as pd


def normalize_type(raw_type) -> str:
    """Normalizes schema type aliases to internal canonical names."""

    if raw_type in (int, float, "numeric", "number"):
        return "numeric"

    if raw_type in (str, "string", "text"):
        return "string"

    if raw_type in ("date", "datetime"):
        return "date"

    if raw_type in ("time", "hour"):
        return "time"

    return str(raw_type)


def parse_mixed_dates(series: pd.Series) -> pd.Series:
    """Parses dates from mixed sources (Excel serials and CSV date strings)."""

    parsed = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")

    numeric = pd.to_numeric(series, errors="coerce")
    numeric_mask = numeric.notna()

    if numeric_mask.any():
        parsed.loc[numeric_mask] = pd.to_datetime(
            numeric.loc[numeric_mask],
            unit="D",
            origin="1899-12-30",
            errors="coerce",
        )

    text_mask = ~numeric_mask

    if text_mask.any():
        text_values = series.loc[text_mask]

        parsed_text = pd.to_datetime(text_values, errors="coerce", dayfirst=True)

        # Fallback for ISO/us-like formats when day-first parsing fails.
        fallback_mask = parsed_text.isna()
        if fallback_mask.any():
            parsed_text.loc[fallback_mask] = pd.to_datetime(
                text_values.loc[fallback_mask], errors="coerce", dayfirst=False
            )

        parsed.loc[text_mask] = parsed_text

    return parsed


def parse_mixed_times(series: pd.Series) -> pd.Series:
    """Parses times from mixed sources (Excel serials/fractions and CSV strings)."""

    parsed = pd.Series(pd.NaT, index=series.index, dtype="object")

    numeric = pd.to_numeric(series, errors="coerce")
    numeric_mask = numeric.notna()

    if numeric_mask.any():
        # Excel stores time as fraction of a day; keep only the time-of-day component.
        time_fraction = numeric.loc[numeric_mask] % 1
        time_as_datetime = pd.Timestamp("1970-01-01") + pd.to_timedelta(
            time_fraction, unit="D"
        )
        parsed.loc[numeric_mask] = time_as_datetime.dt.time

    text_mask = ~numeric_mask

    if text_mask.any():
        text_values = series.loc[text_mask]

        parsed_text = pd.to_datetime(text_values, format="%H:%M", errors="coerce")

        fallback_mask = parsed_text.isna()
        if fallback_mask.any():
            parsed_text.loc[fallback_mask] = pd.to_datetime(
                text_values.loc[fallback_mask], errors="coerce"
            )

        parsed.loc[text_mask] = parsed_text.dt.time

    return parsed
