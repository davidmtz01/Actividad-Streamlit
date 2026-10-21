import pandas as pd
import streamlit as st


def mostrar(df: pd.DataFrame) -> None:
    st.header("1. Entender los datos")
    st.markdown(
        "### Pregunta guía\n\n"
        "**¿Qué señales académicas pueden ayudar a identificar quién podría "
        "beneficiarse de apoyo para continuar sus estudios?**\n\n"
        "La base es sintética; esta primera revisión describe su contenido y calidad."
    )
    a, b, c = st.columns(3)
    a.metric("Estudiantes", f"{len(df):,}")
    b.metric("Variables", f"{len(df.columns):,}")
    tasa = pd.to_numeric(df.get("abandono_semestre"), errors="coerce").mean()
    c.metric("Abandono observado", f"{tasa:.1%}" if pd.notna(tasa) else "N/D")

    st.subheader("Vista previa del dataset")
    st.dataframe(df.head(10), use_container_width=True, hide_index=True)
    st.subheader("Diagnóstico de variables")
    diagnostico = pd.DataFrame({
        "Variable": df.columns,
        "Tipo": df.dtypes.astype(str).to_numpy(),
        "Valores únicos": df.nunique(dropna=True).to_numpy(),
        "Faltantes": df.isna().sum().to_numpy(),
    })
    st.dataframe(diagnostico, use_container_width=True, hide_index=True)
    st.caption("Variables de interés: asistencia, promedio, tareas entregadas, sesiones en plataforma y abandono_semestre. ID solo identifica registros; no debe usarse como predictor.")
    st.metric("Filas duplicadas exactas", f"{int(df.duplicated().sum()):,}")

    variable = st.selectbox("Explora una variable", df.columns.tolist(), key="variable_entender")
    serie = df[variable]
    if pd.api.types.is_numeric_dtype(serie):
        st.dataframe(serie.describe().to_frame("Estadístico"), use_container_width=True)
    else:
        frecuencias = serie.value_counts(dropna=False).rename_axis("Valor").rename("Frecuencia").reset_index()
        frecuencias["Valor"] = frecuencias["Valor"].where(frecuencias["Valor"].notna(), "(sin dato)")
        st.dataframe(frecuencias, use_container_width=True, hide_index=True)
