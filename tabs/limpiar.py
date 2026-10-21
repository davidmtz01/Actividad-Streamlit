import pandas as pd
import streamlit as st


RANGOS = {
    "edad": (15, 100),
    "semestre": (1, 20),
    "asistencia_pct": (0, 100),
    "promedio": (0, 10),
    "tareas_entregadas_ultimas_12": (0, 12),
    "sesiones_plataforma_30_dias": (0, None),
    "abandono_semestre": (0, 1),
}


def _mascara_fuera_rango(df: pd.DataFrame) -> pd.Series:
    fuera = pd.Series(False, index=df.index)
    for col, (minimo, maximo) in RANGOS.items():
        if col not in df:
            continue
        valores = pd.to_numeric(df[col], errors="coerce")
        col_fuera = valores.lt(minimo)
        if maximo is not None:
            col_fuera |= valores.gt(maximo)
        fuera |= col_fuera.fillna(False)
    return fuera


def mostrar(df: pd.DataFrame) -> None:
    st.header("2. Limpiar los datos")
    st.markdown("Revisa la calidad primero. Las decisiones se aplican a una copia; el CSV fuente permanece intacto.")
    if "df_limpio" not in st.session_state:
        st.session_state.df_limpio = df.copy()
        st.session_state.limpieza_acciones = ["Se creó una copia sin cambios."]

    faltantes = int(df.isna().sum().sum())
    duplicados = int(df.duplicated().sum())
    fuera = int(_mascara_fuera_rango(df).sum())
    a, b, c = st.columns(3)
    a.metric("Celdas faltantes", faltantes)
    b.metric("Duplicados exactos", duplicados)
    c.metric("Filas fuera de rango", fuera)
    reporte = pd.DataFrame({"Variable": df.columns, "Tipo": df.dtypes.astype(str).to_numpy(), "Faltantes": df.isna().sum().to_numpy(), "Únicos": df.nunique(dropna=True).to_numpy()})
    st.dataframe(reporte, use_container_width=True, hide_index=True)
    st.caption("Rangos de revisión: edad 15–100, semestre 1–20, asistencia 0–100%, promedio 0–10, tareas 0–12 y abandono 0/1. Un extremo estadístico no se elimina automáticamente.")

    with st.form("formulario_limpieza"):
        quitar_duplicados = st.checkbox("Quitar filas duplicadas exactas", value=False)
        excluir_fuera = st.checkbox("Excluir filas fuera de los rangos mostrados", value=False)
        imputar = st.checkbox("Imputar nulos numéricos con mediana y categóricos con ‘No informado’", value=False)
        aplicar = st.form_submit_button("Aplicar a copia de trabajo")
    if aplicar:
        limpio = df.copy()
        acciones = []
        if quitar_duplicados:
            antes = len(limpio)
            limpio = limpio.drop_duplicates()
            acciones.append(f"Se quitaron {antes - len(limpio)} filas duplicadas exactas.")
        if excluir_fuera:
            mascara = _mascara_fuera_rango(limpio)
            limpio = limpio.loc[~mascara].copy()
            acciones.append(f"Se excluyeron {int(mascara.sum())} filas fuera de rango.")
        if imputar:
            for col in limpio.select_dtypes(include="number").columns:
                if col not in {"alumno_id", "abandono_semestre"}:
                    limpio[col] = limpio[col].fillna(limpio[col].median())
            for col in limpio.select_dtypes(include="object").columns:
                limpio[col] = limpio[col].fillna("No informado")
            acciones.append("Nulos de variables descriptivas imputados con mediana/‘No informado’; el resultado abandono_semestre se dejó intacto.")
        if not acciones:
            acciones.append("No se aplicaron cambios.")
        st.session_state.df_limpio = limpio
        st.session_state.limpieza_acciones = acciones
        st.success("Copia de trabajo actualizada.")

    limpio = st.session_state.df_limpio
    a, b, c = st.columns(3)
    a.metric("Filas de trabajo", f"{len(limpio):,}")
    b.metric("Nulos restantes", int(limpio.isna().sum().sum()))
    c.metric("Duplicados restantes", int(limpio.duplicated().sum()))
    for accion in st.session_state.limpieza_acciones:
        st.write(f"- {accion}")
    st.download_button("Descargar copia de trabajo CSV", limpio.to_csv(index=False).encode("utf-8-sig"), "estudiantes_limpios.csv", "text/csv", key="descargar_limpieza")
