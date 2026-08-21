import pandas as pd
import streamlit as st

from config.structure import COLUMN_DEFINITION


def _normalize_type(raw_type) -> str:
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


def _parse_mixed_dates(series: pd.Series) -> pd.Series:
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


def _parse_mixed_times(series: pd.Series) -> pd.Series:
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


def validate_columns(df: pd.DataFrame) -> dict:
    """Validates the columns of a DataFrame against the expected column definitions."""

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


def cast_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Casts the columns of a DataFrame to the expected data types based on column definitions."""

    df = df.copy()

    for column, info in COLUMN_DEFINITION.items():

        if column not in df.columns:
            continue

        dtype = _normalize_type(info["type"])

        if dtype == "numeric":
            df[column] = pd.to_numeric(df[column], errors="coerce")

        elif dtype == "date":
            df[column] = _parse_mixed_dates(df[column])

        elif dtype == "time":
            df[column] = _parse_mixed_times(df[column])

        elif dtype == "string":
            df[column] = df[column].astype("string")

    return df


def validate_types(df: pd.DataFrame) -> dict:
    """Validates the data types of the columns in a DataFrame against the expected column definitions."""

    errors = {}

    for column, info in COLUMN_DEFINITION.items():

        if column not in df.columns:
            continue

        dtype = _normalize_type(info["type"])

        if dtype in {"numeric", "date", "time"}:

            invalid = df[df[column].isna()].index.tolist()

            if invalid:
                errors[column] = invalid

    return errors


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


def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """Processes the DataFrame by validating columns, casting data types, and validating types."""

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

    df = cast_dataframe(df)

    type_errors = validate_types(df)

    if type_errors:
        st.error(
            "Se detectaron valores inválidos para columnas numéricas, de fecha u hora."
        )
        for column, rows in type_errors.items():
            st.write(
                f"Columna '{column}': {len(rows)} fila(s) con valor inválido en los índices {rows}"
            )
        st.stop()

    return df
