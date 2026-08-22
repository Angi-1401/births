import pandas as pd

from datetime import date, time
from typing import Any

from config.structure import COLUMN_DEFINITION
from utils.parsing import normalize_type, parse_mixed_dates, parse_mixed_times


def typed_default_value(dtype: str) -> Any:
    """Returns the fallback value for missing/invalid typed fields."""

    if dtype == "numeric":
        return 0

    if dtype == "date":
        return pd.Timestamp(date.today())

    if dtype == "time":
        return time(0, 0)

    return None


def coerce_typed_series(series: pd.Series, dtype: str) -> tuple[pd.Series, dict]:
    """Coerces typed columns while tracking missing and malformed values separately."""

    missing_mask = series.isna()

    if dtype == "numeric":
        parsed = pd.to_numeric(series, errors="coerce")
    elif dtype == "date":
        parsed = parse_mixed_dates(series)
    elif dtype == "time":
        parsed = parse_mixed_times(series)
    else:
        return series, {
            "missing_filled": 0,
            "invalid_detected": 0,
            "invalid_rows": [],
            "invalid_filled": 0,
            "default_applied": None,
        }

    invalid_mask = (~missing_mask) & parsed.isna()
    default_value = typed_default_value(dtype)

    coerced = parsed.copy()
    coerced.loc[missing_mask] = default_value

    # Keep the app flow resilient: malformed non-empty values are flagged and then imputed.
    if invalid_mask.any():
        coerced.loc[invalid_mask] = default_value

    quality = {
        "missing_filled": int(missing_mask.sum()),
        "invalid_detected": int(invalid_mask.sum()),
        "invalid_rows": series.index[invalid_mask].tolist(),
        "invalid_filled": int(invalid_mask.sum()),
        "default_applied": str(default_value),
    }

    return coerced, quality


def cast_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Casts columns and returns a quality report for typed imputations."""

    df = df.copy()
    quality_report = {
        "columns": {},
        "totals": {
            "missing_filled": 0,
            "invalid_detected": 0,
            "invalid_filled": 0,
        },
    }

    for column, info in COLUMN_DEFINITION.items():

        if column not in df.columns:
            continue

        dtype = normalize_type(info["type"])

        if dtype in {"numeric", "date", "time"}:
            coerced, quality = coerce_typed_series(df[column], dtype)
            df[column] = coerced

            quality_report["columns"][column] = quality
            quality_report["totals"]["missing_filled"] += quality["missing_filled"]
            quality_report["totals"]["invalid_detected"] += quality["invalid_detected"]
            quality_report["totals"]["invalid_filled"] += quality["invalid_filled"]

        elif dtype == "string":
            df[column] = df[column].fillna("").astype(str).str.upper()

    return df, quality_report
