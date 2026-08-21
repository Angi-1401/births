import pandas as pd
from typing import Literal


def calculate_births(df: pd.DataFrame) -> int:
    """Calculates the total number of births in the DataFrame."""

    return len(df)


def calculate_procedures(df: pd.DataFrame, procedure_type: Literal["PARTO", "CESAREA"]) -> dict:
    """Calculate the number of procedures performed, broken down by type and number of children born in the DataFrame."""

    procedures = {
        "simples": (
            (df["tipo_de_parto"] == procedure_type)
            & (df["doble"] != "X")
            & (df["triple"] != "X")
        ).sum(),
        "doubles": (
            (df["tipo_de_parto"] == procedure_type)
            & (df["doble"] == "X")
            & (df["triple"] != "X")
        ).sum()
        / 2,
        "triples": (
            (df["tipo_de_parto"] == procedure_type)
            & (df["doble"] != "X")
            & (df["triple"] == "X")
        ).sum()
        / 3,
    }

    return procedures

