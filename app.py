# Importación de librerias
# Librerias para la ejecución de código
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns

# Visualización
import streamlit as st
from plotly.subplots import make_subplots

#Api con inteligencia artificial

import google.generativeai as genai

st.set_page_config(
    page_title="Mi app", layout="wide", initial_sidebar_state="collapsed"
)

# Se realiza la carga y limpieza de datos
@st.cache_data
def cargar_datos():

    df_task = pd.read_excel("Datos/sc_task.xlsx")
    df_inc = pd.read_excel("Datos/incident.xlsx")
    df_metric = pd.read_excel("Datos/metric_instance.xlsx")

    # Excluir grupos no deseados
    df_task = df_task[
        ~df_task["Grupo de asignación"]
        .fillna("")
        .isin(["ServiceNow Administration", "AutoRemediation"])
    ]

    df_inc = df_inc[
        df_inc["Grupo de asignación"].fillna("") != "ServiceNow MCA Support-APAC-IND"
    ]

    # Extraer número de caso desde métricas
    df_metric["Caso"] = df_metric["ID"].str.extract(r"(INC\d+|TASK\d+)")

    # Casos que sí pasaron por Mesa de Ayuda
    set_metric = set(df_metric["Caso"].dropna())

    # Marcar casos mal creados
    df_inc["Mal Creado"] = ~df_inc["Número"].isin(set_metric)

    df_task["Mal Creado"] = ~df_task["Número"].isin(set_metric)

    # Identificar uso de KB
    df_inc["Usa KB"] = df_inc["Knowledge Article"].fillna("").str.strip() != ""

    return df_task, df_inc, df_metric


# Pantalla principal
def main():

    # Cargar datos limpios
    df_task, df_inc, df_metric = cargar_datos()

    # ======================
    # FILTRO POR AGENTE
    # ======================

    agentes = sorted(
        set(df_inc["Abierto por"].dropna()) | set(df_task["Abierto por"].dropna())
    )

    agentes_seleccionados = st.sidebar.multiselect("👤 Agente", agentes, default=agentes)

    # Aplicar filtro
    df_inc = df_inc[df_inc["Abierto por"].isin(agentes_seleccionados)]

    df_task = df_task[df_task["Abierto por"].isin(agentes_seleccionados)]

    # Verificar si se seleccionó un único agente
    agente_individual = len(agentes_seleccionados) == 1

    # Totales de mal creados
    total_task_mal = df_task["Mal Creado"].sum()
    total_inc_mal = df_inc["Mal Creado"].sum()

    st.title("📊 Desempeño de la gestión de mesa de ayuda - Julio")

    if agente_individual:

        agente = agentes_seleccionados[0]

        st.header(f"👤 Desempeño Individual - {agente}")

        total_inc_agente = len(df_inc)

        total_task_agente = len(df_task)

        inc_mal_agente = df_inc["Mal Creado"].sum()

        task_mal_agente = df_task["Mal Creado"].sum()

        error_inc = (
            round((inc_mal_agente / total_inc_agente) * 100, 2)
            if total_inc_agente > 0
            else 0
        )

        error_task = (
            round((task_mal_agente / total_task_agente) * 100, 2)
            if total_task_agente > 0
            else 0
        )

        uso_kb = (
            round((df_inc["Usa KB"].sum() / total_inc_agente) * 100, 2)
            if total_inc_agente > 0
            else 0
        )

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("INC", total_inc_agente)

        with col2:
            st.metric("TASK", total_task_agente)

        with col3:
            st.metric("% Error INC", f"{error_inc}%")

        with col4:
            st.metric("% Error TASK", f"{error_task}%")

        with col5:
            st.metric("% Uso KB", f"{uso_kb}%")

        # ======================
    # KPIS GENERALES
    # ======================

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("TASK", len(df_task))

    with col2:
        st.metric("INC", len(df_inc))

    with col3:
        st.metric("TASK Mal Creadas", total_task_mal)

    with col4:
        st.metric("INC Mal Creados", total_inc_mal)


    # ======================
    # DASHBOARD INDIVIDUAL
    # ======================

    if agente_individual:

        calidad_inc = round(
            100 - error_inc,
            2
        )

        calidad_task = round(
            100 - error_task,
            2
        )

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "🎯 Calidad INC",
                f"{calidad_inc}%"
            )

        with col2:
            st.metric(
                "🎯 Calidad TASK",
                f"{calidad_task}%"
            )

        st.subheader(
            "📋 Retroalimentación automática"
        )

        if error_inc <= 2:

            st.success(
                "✅ Excelente calidad en la creación de incidentes."
            )

        elif error_inc <= 5:

            st.warning(
                "⚠️ Hay oportunidades de mejora en la creación de incidentes."
            )

        else:

            st.error(
                "🚨 Alto porcentaje de error en incidentes."
            )

    # Casos mal creados formato de tabla
    task_agente = (
        df_task[df_task["Mal Creado"]]
        .groupby("Abierto por")
        .size()
        .reset_index(name="TASK")
    )

    inc_agente = (
        df_inc[df_inc["Mal Creado"]]
        .groupby("Abierto por")
        .size()
        .reset_index(name="INC")
    )

    resumen_agentes = task_agente.merge(
        inc_agente, on="Abierto por", how="outer"
    ).fillna(0)

    resumen_agentes["TASK"] = resumen_agentes["TASK"].astype(int)
    resumen_agentes["INC"] = resumen_agentes["INC"].astype(int)

    resumen_agentes["TOTAL"] = resumen_agentes["TASK"] + resumen_agentes["INC"]

    resumen_agentes = resumen_agentes.sort_values("TOTAL", ascending=False)

    st.subheader("👥 Casos mal creados por agente")

    st.dataframe(resumen_agentes, use_container_width=True)

    # Crear columnas
    col1, col2 = st.columns(2)

    # Gráfico de INCIDENTES
    fig_inc = px.bar(
        resumen_agentes.sort_values("INC", ascending=False).head(10),
        x="Abierto por",
        y="INC",
        color="INC",
        title="Top agentes con incidentes mal creados",
    )

    # Gráfico de TASKS
    fig_task = px.bar(
        resumen_agentes.sort_values("TASK", ascending=False).head(10),
        x="Abierto por",
        y="TASK",
        color="TASK",
        title="Top agentes con tareas mal creadas",
    )

    # Mostrar gráficos lado a lado
    with col1:
        st.plotly_chart(fig_inc, use_container_width=True)

    with col2:
        st.plotly_chart(fig_task, use_container_width=True)

    inc_total = (
        df_inc.groupby("Abierto por").size().reset_index(name="Total Incidentes")
    )

    inc_error = (
        df_inc[df_inc["Mal Creado"]]
        .groupby("Abierto por")
        .size()
        .reset_index(name="Incidentes Mal Creados")
    )

    ranking_inc = inc_total.merge(inc_error, on="Abierto por", how="left").fillna(0)

    ranking_inc["Incidentes Mal Creados"] = ranking_inc[
        "Incidentes Mal Creados"
    ].astype(int)

    ranking_inc["% Error"] = (
        ranking_inc["Incidentes Mal Creados"] / ranking_inc["Total Incidentes"] * 100
    ).round(2)

    ranking_inc = ranking_inc.sort_values("% Error", ascending=False)

    task_total = df_task.groupby("Abierto por").size().reset_index(name="Total Tareas")

    task_error = (
        df_task[df_task["Mal Creado"]]
        .groupby("Abierto por")
        .size()
        .reset_index(name="Tareas Mal Creadas")
    )

    ranking_task = task_total.merge(task_error, on="Abierto por", how="left").fillna(0)

    ranking_task["Tareas Mal Creadas"] = ranking_task["Tareas Mal Creadas"].astype(int)

    ranking_task["% Error"] = (
        ranking_task["Tareas Mal Creadas"] / ranking_task["Total Tareas"] * 100
    ).round(2)

    ranking_task = ranking_task.sort_values("% Error", ascending=False)

    st.header("📈 Indicadores de calidad en la creación de casos por agente")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Incidentes")

        st.dataframe(ranking_inc, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("Tareas")

        st.dataframe(ranking_task, use_container_width=True, hide_index=True)

    st.header("📚 Utilización de la Base de Conocimiento (KB)")

    total_inc = len(df_inc)

    inc_con_kb = df_inc["Usa KB"].sum()

    inc_sin_kb = total_inc - inc_con_kb

    porcentaje_kb = round((inc_con_kb / total_inc) * 100, 2)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Incidentes", total_inc)

    with col2:
        st.metric("Incidentes con KB", inc_con_kb)

    with col3:
        st.metric("% Uso KB", f"{porcentaje_kb}%")

    kb_resumen = pd.DataFrame(
        {"Estado": ["Con KB", "Sin KB"], "Cantidad": [inc_con_kb, inc_sin_kb]}
    )

    fig = px.pie(
        kb_resumen,
        names="Estado",
        values="Cantidad",
        title="Distribución de utilización de KB",
        hole=0.4,
    )

    st.plotly_chart(fig, use_container_width=True)

    kb_agente_total = (
        df_inc.groupby("Abierto por").size().reset_index(name="Total Incidentes")
    )

    kb_agente_uso = (
        df_inc[df_inc["Usa KB"]]
        .groupby("Abierto por")
        .size()
        .reset_index(name="Incidentes con KB")
    )

    ranking_kb = kb_agente_total.merge(
        kb_agente_uso, on="Abierto por", how="left"
    ).fillna(0)

    ranking_kb["% Uso KB"] = (
        ranking_kb["Incidentes con KB"] / ranking_kb["Total Incidentes"] * 100
    ).round(2)

    ranking_kb = ranking_kb.sort_values("% Uso KB", ascending=False)

    st.subheader("📖 Utilización de KB por Agente")

    st.dataframe(ranking_kb, use_container_width=True, hide_index=True)

    st.header("💬 Distribución de incidentes mal creados por canal")

    # Incidentes mal creados por canal
    inc_canal = (
        df_inc[df_inc["Mal Creado"]]
        .groupby("Canal")
        .size()
        .reset_index(name="Incidentes")
    )

    # Calcular porcentaje
    inc_canal["% Participación"] = (
        inc_canal["Incidentes"] / inc_canal["Incidentes"].sum() * 100
    ).round(1)

    # Ordenar
    inc_canal = inc_canal.sort_values("Incidentes", ascending=False)

    col1, col2 = st.columns([2, 1])

    with col1:

        fig = px.pie(
            inc_canal,
            names="Canal",
            values="Incidentes",
            hole=0.55,
            title="Participación de incidentes mal creados por canal",
        )

        fig.update_traces(textposition="inside", textinfo="percent+label")

        st.plotly_chart(fig, use_container_width=True)

    with col2:

        st.dataframe(inc_canal, use_container_width=True, hide_index=True)


st.sidebar.header("🔎 Filtros")

if __name__ == "__main__":
    main()
