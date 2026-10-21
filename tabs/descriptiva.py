import pandas as pd
import streamlit as st


def mostrar(df: pd.DataFrame) -> None:
    st.header("3. Estadística descriptiva")
    st.markdown("Resume lo observado en la cohorte. Las diferencias describen asociaciones y no explican causalidad.")
    if df.empty:
        st.warning("No hay registros para resumir.")
        return
    abandono = pd.to_numeric(df.get("abandono_semestre"), errors="coerce")
    valido = abandono.isin([0, 1])
    total = int(valido.sum())
    eventos = int(abandono.eq(1).sum())
    tasa = eventos / total if total else float("nan")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Estudiantes", f"{len(df):,}")
    c2.metric("Abandonos observados", f"{eventos:,} de {total:,}")
    c3.metric("Tasa de abandono", f"{tasa:.1%}" if pd.notna(tasa) else "N/D")
    c4.metric("Asistencia promedio", f"{pd.to_numeric(df['asistencia_pct'], errors='coerce').mean():.1f}%")

    st.subheader("Distribución por programa")
    conteos = df["programa"].fillna("No informado").value_counts().rename_axis("Programa").rename("Estudiantes").reset_index()
    st.bar_chart(conteos.set_index("Programa"))
    st.dataframe(conteos, use_container_width=True, hide_index=True)

    st.subheader("Exploración por segmento")
    opciones = [c for c in ["programa", "semestre", "apoyo_recibido", "tiempo_traslado", "beca"] if c in df]
    grupo = st.selectbox("Agrupar por", opciones, key="grupo_descriptiva")
    temp = df[[grupo]].copy()
    temp["abandono"] = abandono
    temp["asistencia"] = pd.to_numeric(df["asistencia_pct"], errors="coerce")
    temp["promedio"] = pd.to_numeric(df["promedio"], errors="coerce")
    resumen = temp.groupby(grupo, dropna=False).agg(
        estudiantes=("abandono", "size"), abandonos=("abandono", "sum"),
        tasa_abandono=("abandono", "mean"), asistencia_media=("asistencia", "mean"),
        promedio_academico=("promedio", "mean"),
    ).reset_index()
    st.bar_chart(resumen.set_index(grupo)[["tasa_abandono"]], y_label="Proporción con abandono")
    st.dataframe(resumen.style.format({"tasa_abandono": "{:.1%}", "asistencia_media": "{:.1f}%", "promedio_academico": "{:.2f}"}), use_container_width=True, hide_index=True)
    st.caption("El KPI usa abandonos observados / registros con resultado 0 o 1. La muestra tiene pocos eventos; compara siempre la tasa con el tamaño del segmento.")
