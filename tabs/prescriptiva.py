import pandas as pd
import streamlit as st


def construir_recomendaciones(df: pd.DataFrame, asistencia_minima: int = 75, promedio_minimo: float = 8.0) -> pd.DataFrame:
    """Genera segmentos explicables para ofrecer apoyos; no predice abandono."""
    r = df.copy()
    asis = pd.to_numeric(r.get("asistencia_pct", pd.Series(index=r.index, dtype=float)), errors="coerce")
    prom = pd.to_numeric(r.get("promedio", pd.Series(index=r.index, dtype=float)), errors="coerce")
    tareas = pd.to_numeric(r.get("tareas_entregadas_ultimas_12", pd.Series(index=r.index, dtype=float)), errors="coerce")
    uso = pd.to_numeric(r.get("sesiones_plataforma_30_dias", pd.Series(index=r.index, dtype=float)), errors="coerce")
    r["senales_revision"] = (
        asis.lt(asistencia_minima).astype(int) + prom.lt(promedio_minimo).astype(int)
        + tareas.lt(7).astype(int) + uso.lt(10).astype(int)
    )
    r["segmento_recomendado"] = pd.cut(r["senales_revision"], [-1, 1, 2, 4], labels=["Apoyo general", "Invitación a revisión", "Priorizar oferta de apoyo"])
    acciones = {
        "Apoyo general": "Compartir recursos y mantener canales de ayuda accesibles.",
        "Invitación a revisión": "Invitar a una conversación voluntaria para identificar barreras y ofrecer asesoría académica.",
        "Priorizar oferta de apoyo": "Ofrecer contacto privado con tutoría y preguntar qué apoyo sería útil; canalizar solo con acuerdo del estudiante.",
    }
    r["accion_recomendada"] = r["segmento_recomendado"].astype(str).map(acciones)
    r["evidencia_regla"] = r["senales_revision"].astype(str) + " de 4 señales académicas bajo los umbrales seleccionados."
    r["mensaje_borrador"] = "Hola. Queremos compartir opciones de apoyo académico disponibles. Si te resulta útil, puedes conversar con tutoría; participar es voluntario."
    r["canal_a_validar"] = "Canal institucional autorizado; verificar preferencia y reglas de contacto."
    r["responsable_sugerido"] = "Tutoría / acompañamiento estudiantil"
    r["riesgo_medicion"] = "Regla exploratoria; evaluar continuidad futura con datos temporales y participación voluntaria."
    return r


def mostrar(df: pd.DataFrame) -> None:
    st.header("5. Estadística prescriptiva")
    st.markdown("Reglas claras para priorizar una **oferta de apoyo**, no para etiquetar, sancionar ni decidir la trayectoria académica de una persona.")
    if df.empty:
        st.info("No hay estudiantes para segmentar.")
        return
    a, b = st.columns(2)
    asistencia = a.slider("Umbral de asistencia baja (%)", 40, 90, 75, 5, key="umbral_asistencia_pres")
    promedio = b.slider("Umbral de promedio bajo", 5.0, 9.0, 8.0, 0.5, key="umbral_promedio_pres")
    r = construir_recomendaciones(df, asistencia, promedio)
    st.session_state.recomendaciones = r
    st.session_state.parametros_prescriptiva = {"asistencia": asistencia, "promedio": promedio}

    conteos = r["segmento_recomendado"].value_counts().rename_axis("Segmento").rename("Estudiantes").reset_index()
    st.subheader("Tamaño de cada grupo")
    st.bar_chart(conteos.set_index("Segmento"))
    st.dataframe(conteos, use_container_width=True, hide_index=True)
    st.subheader("Reglas aplicadas")
    st.dataframe(pd.DataFrame([
        {"Señal": f"Asistencia < {asistencia}%", "Acción": "Suma una señal"},
        {"Señal": f"Promedio < {promedio}", "Acción": "Suma una señal"},
        {"Señal": "Menos de 7 tareas de las últimas 12", "Acción": "Suma una señal"},
        {"Señal": "Menos de 10 sesiones de plataforma en 30 días", "Acción": "Suma una señal"},
        {"Señal": "3–4 señales / 2 señales / 0–1 señales", "Acción": "Priorizar oferta / invitar a revisión / apoyo general"},
    ]), use_container_width=True, hide_index=True)
    st.subheader("Ejemplos de recomendación")
    opcion = st.selectbox("Ver segmento", conteos["Segmento"].tolist(), key="segmento_muestra_prescriptiva")
    columnas = [c for c in ["segmento_recomendado", "evidencia_regla", "accion_recomendada", "mensaje_borrador", "responsable_sugerido"] if c in r]
    st.dataframe(r.loc[r["segmento_recomendado"].eq(opcion), columnas].head(20), use_container_width=True, hide_index=True)
    st.caption("No se incluye identificador en la vista compartible. Antes de contactar, valida propósito, acceso, preferencia del estudiante y reglas institucionales.")
