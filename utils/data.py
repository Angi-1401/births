import pandas as pd
import streamlit as st

from typing import Literal, overload

from utils.coercion import cast_dataframe
from utils.validation import validate_columns


@st.cache_data
def load_data(file) -> pd.DataFrame:
    """Loads data from a CSV or Excel file into a DataFrame."""

    try:
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        elif file.name.endswith(".xlsx") or file.name.endswith(".xls"):
            df = pd.read_excel(file, engine="openpyxl")
        else:
            st.error("Formato de archivo no soportado. Use CSV o Excel.")
            st.stop()
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        st.stop()

    return df


@overload
def process_data(
    df: pd.DataFrame, return_quality: Literal[False] = False
) -> pd.DataFrame: ...


@overload
def process_data(
    df: pd.DataFrame, return_quality: Literal[True]
) -> tuple[pd.DataFrame, dict]: ...


def process_data(
    df: pd.DataFrame, return_quality: bool = False
) -> pd.DataFrame | tuple[pd.DataFrame, dict]:
    """Processes data and optionally returns typed imputation quality details."""

    validation_results = validate_columns(df)

    if validation_results["missing"]:
        st.error("Faltan columnas requeridas en el archivo cargado.")
        st.write("Columnas faltantes:", validation_results["missing"])
        st.stop()

    if validation_results["extra"]:
        st.warning(
            "Se encontraron columnas adicionales que no están en la plantilla esperada."
        )
        st.write("Columnas adicionales:", validation_results["extra"])

    # Treat whitespace-only values as empty cells, then remove fully empty rows.
    df = df.replace(r"^\s*$", pd.NA, regex=True)
    rows_before = len(df)
    df = df.dropna(how="all")
    dropped_rows = rows_before - len(df)

    if dropped_rows > 0:
        st.info(
            f"Se ignoraron {dropped_rows} fila(s) completamente vacía(s) antes de validar los datos."
        )

    if df.empty:
        st.error("El archivo no contiene filas con datos válidos para analizar.")
        st.stop()

    df, quality_report = cast_dataframe(df)

    missing_filled = quality_report["totals"]["missing_filled"]
    invalid_detected = quality_report["totals"]["invalid_detected"]

    if missing_filled > 0:
        st.info(
            f"Se imputaron {missing_filled} valor(es) faltante(s) en columnas numéricas/fecha/hora usando valores por defecto."
        )

    if invalid_detected > 0:
        st.warning(
            f"Se detectaron {invalid_detected} valor(es) mal formateado(s) no vacíos en columnas numéricas/fecha/hora. Se imputaron para mantener la continuidad del análisis."
        )

        for column, details in quality_report["columns"].items():
            if details["invalid_detected"] > 0:
                st.write(
                    f"Columna '{column}': {details['invalid_detected']} valor(es) inválido(s) en índices {details['invalid_rows']}"
                )

    if return_quality:
        return df, quality_report

    return df
