import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from config.markdown import MARKDOWN_CONTENT

from utils.data import load_data, process_data
from utils.formatting import format_as_thousands
from utils.metrics import calculate_births, calculate_procedures

# -------------------------
# PAGE SETTINGS
# -------------------------

st.set_page_config(
    page_title="Análisis Epidemiológico de Nacimientos en el Estado Carabobo",
    page_icon=":bar_chart:",
    layout="wide",
)

# -------------------------
# UPLOAD DATA
# -------------------------

st.sidebar.subheader("📂 Cargar archivo de datos")
file = st.sidebar.file_uploader(
    "Cargar archivo CSV o Excel",
    type=["csv", "xlsx"],
    help="Cargar un archivo CSV o Excel que contenga los datos de nacimientos.",
)

if file is None:
    st.info("Por favor, cargue un archivo CSV o Excel para comenzar el análisis.")
    st.markdown(MARKDOWN_CONTENT)

    with open("data/template.csv", "rb") as f:
        st.download_button(
            label="📥 Descargar plantilla CSV",
            data=f,
            file_name="template.csv",
            mime="text/csv",
            help="Descargar un archivo CSV vacío con las columnas requeridas.",
        )

    st.stop()

# -------------------------
# READ DATA
# -------------------------

df = None

df = load_data(file)
df = process_data(df)

# -------------------------
# FILTERS
# -------------------------

st.sidebar.subheader("🔍 Filtros de análisis")

start_default = df["fecha_de_nacimiento"].min()
end_default = df["fecha_de_nacimiento"].max()

start_date, end_date = start_default, end_default

date_range = st.sidebar.date_input(
    "Rango de fechas",
    value=(start_default, end_default),
    min_value=start_default,
    max_value=end_default,
    help="Filtrar los datos por rango de fechas de nacimiento.",
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range

    df = df[
        (df["fecha_de_nacimiento"] >= pd.to_datetime(start_date))
        & (df["fecha_de_nacimiento"] <= pd.to_datetime(end_date))
    ]

st.caption(
    f"Mostrando datos desde {start_date.strftime('%d/%m/%Y')} hasta {end_date.strftime('%d/%m/%Y')}. Total de registros: {len(df)}"
)

# -------------------------
# EXCECUTIVE SUMMARY
# -------------------------

births = calculate_births(df)

simple_births = calculate_procedures(df, "PARTO")["simples"]
double_births = calculate_procedures(df, "PARTO")["doubles"]
triple_births = calculate_procedures(df, "PARTO")["triples"]

simple_cesarean = calculate_procedures(df, "CESAREA")["simples"]
double_cesarean = calculate_procedures(df, "CESAREA")["doubles"]
triple_cesarean = calculate_procedures(df, "CESAREA")["triples"]

total_births = simple_births + double_births + triple_births
total_cesarean = simple_cesarean + double_cesarean + triple_cesarean

total_procedures = total_births + total_cesarean

col1, col2, _ = st.columns(3)

with col1:
    st.metric(
        label="Total de nacimientos",
        value=format_as_thousands(births),
    )

with col2:
    st.metric(
        label="Total de procedimientos",
        value=format_as_thousands(total_procedures),
        delta=f"{format_as_thousands(total_births)} partos y {format_as_thousands(total_cesarean)} cesáreas",
    )

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Partos simples",
        value=format_as_thousands(simple_births),
    )

with col2:
    st.metric(
        label="Partos dobles",
        value=format_as_thousands(double_births),
    )

with col3:
    st.metric(
        label="Partos triples",
        value=format_as_thousands(triple_births),
    )

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Cesáreas simples",
        value=format_as_thousands(simple_cesarean),
    )

with col2:
    st.metric(
        label="Cesáreas dobles",
        value=format_as_thousands(double_cesarean),
    )

with col3:
    st.metric(
        label="Cesáreas triples",
        value=format_as_thousands(triple_cesarean),
    )

st.dataframe(df, width="stretch")
