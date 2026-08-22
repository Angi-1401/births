import pandas as pd

from config.structure import COLUMN_DEFINITION


def validate_columns(df: pd.DataFrame) -> dict:
    """Validates DataFrame columns against expected schema."""

    expected = {
        column for column, info in COLUMN_DEFINITION.items() if info["required"]
    }

    received = set(df.columns)

    missing = expected - received
    extra = received - expected

    return {
        "valid": len(missing) == 0,
        "missing": sorted(missing),
        "extra": sorted(extra),
    }
