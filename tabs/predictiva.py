import pandas as pd
import streamlit as st


def mostrar(df: pd.DataFrame) -> None:
    st.header("4. Señales asociadas con continuidad")
    st.markdown("La guía original entrena un clasificador. En esta base no es responsable ajustarlo todavía: el resultado está muy desbalanceado y solo hay unos pocos eventos.")
    if df.empty or "abandono_semestre" not in df:
        st.warning("No hay datos suficientes para explorar el resultado.")
        return
    y = pd.to_numeric(df["abandono_semestre"], errors="coerce")
    conteo = y.value_counts()
    n_eventos = int(conteo.get(1, 0))
    n_total = int(y.isin([0, 1]).sum())
    tasa = n_eventos / n_total if n_total else 0.0
    st.warning(f"Hay {n_eventos} abandonos entre {n_total} resultados válidos ({tasa:.1%}). Con tan pocos positivos, una partición entrenamiento/prueba daría métricas muy inestables. No se presenta un modelo ni probabilidades individuales.")

    st.subheader("Exploración de señales")
    umbral_asistencia = st.slider("Señal de asistencia baja (%)", 40, 90, 75, 5, key="umbral_asistencia_pred")
    umbral_promedio = st.slider("Señal de promedio bajo", 5.0, 9.0, 8.0, 0.5, key="umbral_promedio_pred")
    temp = df.copy()
    temp["abandono"] = y
    temp["asistencia_baja"] = pd.to_numeric(temp["asistencia_pct"], errors="coerce").lt(umbral_asistencia)
    temp["promedio_bajo"] = pd.to_numeric(temp["promedio"], errors="coerce").lt(umbral_promedio)
    temp["pocas_tareas"] = pd.to_numeric(temp["tareas_entregadas_ultimas_12"], errors="coerce").lt(7)
    temp["poco_uso_plataforma"] = pd.to_numeric(temp["sesiones_plataforma_30_dias"], errors="coerce").lt(10)
    temp["senales"] = temp[["asistencia_baja", "promedio_bajo", "pocas_tareas", "poco_uso_plataforma"]].sum(axis=1)
    temp["nivel_senales"] = pd.cut(temp["senales"], [-1, 1, 2, 4], labels=["0–1 señales", "2 señales", "3–4 señales"])
    resumen = temp.groupby("nivel_senales", observed=True).agg(
        estudiantes=("abandono", "size"), abandonos=("abandono", "sum"),
        tasa_observada=("abandono", "mean"), asistencia_media=("asistencia_pct", "mean"),
        promedio_medio=("promedio", "mean"),
    ).reset_index()
    st.bar_chart(resumen.set_index("nivel_senales")[["tasa_observada"]], y_label="Proporción con abandono")
    st.dataframe(resumen.style.format({"tasa_observada": "{:.1%}", "asistencia_media": "{:.1f}%", "promedio_medio": "{:.2f}"}), use_container_width=True, hide_index=True)
    st.caption("Es una comparación descriptiva de señales elegidas para explorar, no una validación predictiva. Los umbrales son hipótesis, no criterios institucionales.")
