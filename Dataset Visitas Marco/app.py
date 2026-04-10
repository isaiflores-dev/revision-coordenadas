import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Analisis de Visitas Marzo", layout="wide")

st.title("📊 Auditoria Marzo 2026")
st.markdown("### Análisis de ejecución en campo")

# =========================
# 📂 LECTURA UNIVERSAL CSV
# =========================
def read_csv_smart(file):
    encodings = ['utf-8', 'utf-8-sig', 'cp1252', 'latin-1']

    for enc in encodings:
        try:
            file.seek(0)
            df = pd.read_csv(file, encoding=enc, sep=None, engine='python')
            return df
        except Exception:
            continue

    st.error("❌ No se pudo leer el archivo. Verifica el formato.")
    st.stop()

# 📂 Cargar archivo
file = st.file_uploader("Sube tu CSV", type=["csv"])

if file:
    df = read_csv_smart(file)
    df.columns = df.columns.str.strip()

    # =========================
    # 🧹 Limpieza
    # =========================
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors='coerce')
    df["Duración"] = pd.to_numeric(df["Duración"], errors='coerce')

    # Filtrar marzo
    df = df[df["Fecha"].dt.month == 3]

    # =========================
    # 📊 KPIs
    # =========================
    total_visitas = len(df)
    tiendas = df["Tienda"].nunique()
    duracion_prom = df["Duración"].mean()
    visitas_cortas = df[df["Duración"] < 5]

    st.markdown("## 📊 KPIs Clave")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Visitas Totales", total_visitas)
    col2.metric("Tiendas Únicas", tiendas)
    col3.metric("Duración Promedio", round(duracion_prom, 2) if pd.notnull(duracion_prom) else 0)
    
    if total_visitas > 0:
        porcentaje_cortas = round(len(visitas_cortas)/total_visitas*100, 2)
    else:
        porcentaje_cortas = 0

    col4.metric("% Visitas <5 min", porcentaje_cortas)

    # =========================
    # 🚦 SEMÁFORO GENERAL
    # =========================
    st.markdown("## 🚦 Estado General")

    score = 0

    if duracion_prom > 10:
        score += 1
    if total_visitas > 0 and (len(visitas_cortas)/total_visitas < 0.2):
        score += 1
    if total_visitas > 1000:
        score += 1

    if score == 3:
        st.success("🟢 Operación saludable")
    elif score == 2:
        st.warning("🟡 Operación con áreas de mejora")
    else:
        st.error("🔴 Operación crítica")

    # =========================
    # 🚨 ALERTAS
    # =========================
    st.markdown("## 🚨 Alertas clave")

    if len(visitas_cortas) > 0:
        st.error(f"⚠️ {len(visitas_cortas)} visitas con duración menor a 5 minutos")

    # Concentración
    if "Regional" in df.columns:
        top_region = df["Regional"].value_counts(normalize=True).max()
        if top_region > 0.5:
            st.warning("⚠️ Alta concentración en una sola región")
    else:
        top_region = 0

    # Variabilidad
    visitas_fecha = df.groupby("Fecha").size()
    if len(visitas_fecha) > 0 and visitas_fecha.std() > visitas_fecha.mean():
        st.warning("⚠️ Alta variabilidad diaria en visitas")

    # =========================
    # 📈 GRÁFICOS
    # =========================
    st.markdown("## 📈 Comportamiento")

    col1, col2 = st.columns(2)

    with col1:
        if "Regional" in df.columns:
            st.subheader("Visitas por Regional")
            st.bar_chart(df["Regional"].value_counts())

    with col2:
        if "Canal" in df.columns:
            st.subheader("Visitas por Canal")
            st.bar_chart(df["Canal"].value_counts())

    st.subheader("Tendencia diaria")
    st.line_chart(visitas_fecha)

    # =========================
    # 🏆 RANKING
    # =========================
    st.markdown("## 🏆 Ranking de desempeño")

    if "Regional" in df.columns:
        ranking = df.groupby("Regional").agg({
            "Duración": "mean",
            "Tienda": "count"
        }).rename(columns={"Tienda": "Visitas"})

        ranking = ranking.sort_values(by="Duración", ascending=False)
        st.dataframe(ranking)

    # =========================
    # 📍 MAPA
    # =========================
    st.markdown("## 🗺️ Mapa de ejecución")

    if "Latitud" in df.columns and "Longitud" in df.columns:
        mapa = df[["Latitud", "Longitud"]].dropna()
        mapa.columns = ["lat", "lon"]

        if len(mapa) > 0:
            st.map(mapa)

    # =========================
    # 🧠 INSIGHTS AUTOMÁTICOS
    # =========================
    st.markdown("## 🧠 Insights automáticos")

    insights = []

    if duracion_prom < 10:
        insights.append("Duración promedio baja → posible baja calidad de visitas")

    if total_visitas > 0 and (len(visitas_cortas)/total_visitas > 0.3):
        insights.append("Alto porcentaje de visitas cortas → riesgo de ejecución deficiente")

    if top_region > 0.5:
        insights.append("Dependencia fuerte de una sola región")

    if len(visitas_fecha) > 0 and visitas_fecha.std() > visitas_fecha.mean():
        insights.append("Operación inconsistente a lo largo del mes")

    if len(insights) == 0:
        st.success("Operación estable sin anomalías relevantes")
    else:
        for i in insights:
            st.warning(i)

    # =========================
    # 📥 DESCARGA
    # =========================
    st.markdown("## 📥 Exportar")

    st.download_button(
        "Descargar datos filtrados",
        df.to_csv(index=False),
        "marzo_limpio.csv"
    )

    # =========================
    # 📋 DETALLE
    # =========================
    st.markdown("## 📋 Detalle de datos")

    st.dataframe(df)
