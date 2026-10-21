import pandas as pd
import streamlit as st


def _tasa(valores: pd.Series) -> str:
    x = pd.to_numeric(valores, errors="coerce")
    return f"{x.mean():.1%}" if x.notna().any() else "N/D"


def _crear_plan(segmento: pd.DataFrame, porcentaje_piloto: int, porcentaje_control: int) -> pd.DataFrame:
    """Asigna grupos de forma reproducible; control conserva el apoyo habitual."""
    if segmento.empty:
        return segmento.copy()
    n_piloto = max(1, round(len(segmento) * porcentaje_piloto / 100))
    piloto = segmento.sample(n=n_piloto, random_state=42).copy()
    n_control = min(len(piloto) - 1, max(1, round(len(piloto) * porcentaje_control / 100))) if len(piloto) >= 2 else 0
    piloto["grupo_experimento"] = "Oferta adicional de apoyo"
    if n_control:
        indices = piloto.sample(n=n_control, random_state=43).index
        piloto.loc[indices, "grupo_experimento"] = "Control (apoyo habitual)"
    piloto["kpi_primario"] = "Continuidad en el siguiente periodo; definir y validar antes del piloto"
    piloto["ventana_medicion"] = "Siguiente periodo académico; fijar fechas y definición institucional"
    return piloto


def mostrar(df: pd.DataFrame) -> None:
    st.header("6. Toma de decisiones")
    st.markdown("Conecta segmento, evidencia, oferta de apoyo y medición. Esta pantalla prepara un plan revisable; no contacta estudiantes ni reemplaza la revisión institucional.")
    recs = st.session_state.get("recomendaciones")
    if recs is None or recs.empty:
        st.info("Revisa primero la pestaña Prescriptiva para crear los segmentos.")
        return
    filas = []
    for nombre, grupo in recs.groupby("segmento_recomendado", observed=True, dropna=False):
        fila = {
            "Segmento": str(nombre), "Estudiantes": len(grupo), "Participación": len(grupo) / len(recs),
            "Acción sugerida": grupo["accion_recomendada"].mode().iat[0],
            "Evidencia ejemplo": grupo["evidencia_regla"].iat[0],
            "Responsable": grupo["responsable_sugerido"].iat[0],
            "Límite": grupo["riesgo_medicion"].iat[0],
        }
        if "abandono_semestre" in grupo:
            fila["Abandono histórico"] = _tasa(grupo["abandono_semestre"])
        filas.append(fila)
    resumen = pd.DataFrame(filas).sort_values("Estudiantes", ascending=False)
    a, b, c = st.columns(3)
    a.metric("Estudiantes en análisis", f"{len(recs):,}")
    b.metric("Grupos de apoyo", f"{recs['segmento_recomendado'].nunique():,}")
    c.metric("Abandono histórico", _tasa(recs["abandono_semestre"]) if "abandono_semestre" in recs else "N/D")
    st.subheader("Resumen para revisión")
    st.dataframe(resumen.style.format({"Participación": "{:.1%}"}), use_container_width=True, hide_index=True)
    st.caption("El abandono histórico por segmento es descriptivo; no estima el efecto de ofrecer apoyo. La base no contiene continuidad futura ni resultado de una intervención.")

    st.subheader("Diseñar un piloto pequeño")
    elegido = st.selectbox("Grupo prioritario", resumen["Segmento"].tolist(), key="segmento_decisiones")
    a, b = st.columns(2)
    p_piloto = a.slider("Porcentaje del segmento invitado al piloto", 10, 100, 50, 5, key="porcentaje_piloto")
    p_control = b.slider("Porcentaje del piloto en control de apoyo habitual", 10, 50, 20, 5, key="porcentaje_control")
    permiso = st.checkbox("Confirmo que propósito, privacidad, exclusiones y revisión institucional se validarán antes de usar datos reales.", key="confirmar_permiso_decisiones")
    segmento = recs.loc[recs["segmento_recomendado"].astype(str).eq(elegido)].copy()
    plan = _crear_plan(segmento, p_piloto, p_control)
    n_tratamiento = int(plan["grupo_experimento"].eq("Oferta adicional de apoyo").sum()) if not plan.empty else 0
    n_control = int(plan["grupo_experimento"].eq("Control (apoyo habitual)").sum()) if not plan.empty else 0
    a, b, c = st.columns(3)
    a.metric("Tamaño del segmento", f"{len(segmento):,}")
    b.metric("Oferta adicional", f"{n_tratamiento:,}")
    c.metric("Control con apoyo habitual", f"{n_control:,}")
    if n_control == 0 or n_tratamiento == 0:
        st.warning("El segmento es demasiado pequeño para formar dos grupos. No interpretes este plan como evaluación de impacto.")
    st.subheader("Mensaje de ejemplo")
    st.info("Hola. Hay opciones de apoyo académico disponibles. Si te resulta útil, puedes conversar con tutoría para revisar qué recursos se ajustan a tus necesidades. Participar es voluntario.")
    st.write("**Acción:** ofrecer conversación de tutoría y canalizar a apoyos académicos o institucionales según lo que el estudiante solicite.")
    st.write("**Canal:** canal institucional autorizado y preferido por el estudiante, por validar.")
    st.subheader("Medición propuesta")
    st.markdown("1. Definir continuidad, periodo de medición y población antes de iniciar.\n2. Comparar la oferta adicional con el apoyo habitual, sin retirar servicios existentes.\n3. Revisar tamaños y diferencias de participación entre grupos.\n4. Vigilar privacidad, carga de contacto y efectos no deseados; detener o ajustar si aparecen señales de daño.")
    columnas = [c for c in ["alumno_id", "segmento_recomendado", "evidencia_regla", "accion_recomendada", "grupo_experimento", "kpi_primario", "ventana_medicion"] if c in plan.columns]
    st.download_button("Descargar plan piloto CSV", plan[columnas].to_csv(index=False).encode("utf-8-sig"), "plan_piloto_retencion.csv", "text/csv", disabled=(not permiso) or n_control == 0 or n_tratamiento == 0, help="Requiere confirmar la revisión previa y contar con dos grupos.", key="descargar_plan_decisiones")
    st.caption("El archivo descargable puede incluir identificadores estudiantiles: guárdalo únicamente en un lugar institucional autorizado. La casilla es una confirmación del usuario, no una validación automática.")
