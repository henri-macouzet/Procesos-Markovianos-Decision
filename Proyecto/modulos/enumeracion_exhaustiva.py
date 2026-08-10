"""
modulos/enumeracion_exhaustiva.py
Interfaz para Enumeración Exhaustiva de políticas.
Permite seleccionar manualmente las políticas a evaluar,
mostrar detalles de cálculo y determinar la política óptima.
Incluye análisis comparativo al final.
"""

import streamlit as st
import pandas as pd
from algoritmos.exhaustiva import generar_politicas, enumeracion_exhaustiva
from guardado.sesion import get_mdp, mdp_completo

def _subindice(i):
    """Convierte un número entero en subíndice Unicode."""
    subs = "₀₁₂₃₄₅₆₇₈₉"
    return ''.join(subs[int(d)] for d in str(i))

st.set_page_config(page_title="Enumeración Exhaustiva — MDP", page_icon="🔍")

mdp = get_mdp()

# ---------- ESTILOS ----------
st.markdown("""
<style>
.policy-box {
    background: #111827;
    border: 1px solid #1E2A3A;
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 0.8rem;
}
.policy-optimal {
    border-left: 4px solid #F5A800;
    background: #0f1a24;
}
</style>
""", unsafe_allow_html=True)

# ---------- ENCABEZADO ----------
st.markdown("""
<div style="margin-bottom:1.5rem;">
    <div style="font-family:'IBM Plex Mono',monospace;font-size:.72rem;color:#F5A800;letter-spacing:.15em;margin-bottom:.4rem;">MÓDULO 03</div>
    <h1 style="font-family:'Sora',sans-serif;font-weight:700;font-size:1.8rem;color:#E8EAF0;margin:0;">Enumeración Exhaustiva</h1>
    <p style="color:#8FA0B8;font-size:.9rem;margin:.4rem 0 0 0;">Evalúa todas las combinaciones posibles para hallar la política óptima.</p>
</div>
""", unsafe_allow_html=True)

# Verificar que el modelo esté completo
if not mdp_completo():
    st.warning("El modelo no está completo. Ve al módulo de Ingreso de Datos para finalizarlo.")
    st.stop()

estados = mdp["estados"]
decisiones_data = mdp["decisiones_data"]
tipo = mdp["tipo"]

# Generar todas las políticas posibles
politicas = generar_politicas(estados, decisiones_data)
if not politicas:
    st.error("No se pueden generar políticas: algún estado no tiene decisiones aplicables.")
    st.stop()

# Crear diccionario de nombres de políticas R1, R2, ...
politicas_dict = {}
for i, pol in enumerate(politicas):
    nombre = f"R{i+1}"
    politicas_dict[nombre] = pol

# Mostrar políticas disponibles como chips
st.markdown("### Políticas disponibles")
cols = st.columns(4)
for i, (nombre, pol) in enumerate(politicas_dict.items()):
    with cols[i % 4]:
        texto = f"({', '.join([pol[s] for s in estados])})"
        st.markdown(f'<span class="chip chip-gold" style="margin:4px;">{nombre} = {texto}</span>', unsafe_allow_html=True)

st.markdown("---")

# Selección de políticas a evaluar
st.markdown("### Seleccionar políticas a evaluar")
opciones = list(politicas_dict.keys())
seleccionadas = st.multiselect(
    "Elige una o más políticas (si no seleccionas ninguna, se evaluarán todas)",
    options=opciones,
    default=opciones   # Todas seleccionadas por defecto
)

politicas_a_evaluar = []
if seleccionadas:
    for nombre in seleccionadas:
        politicas_a_evaluar.append(politicas_dict[nombre])
else:
    politicas_a_evaluar = politicas

# Opción para mostrar cálculos detallados
mostrar_detalles = st.checkbox("Mostrar cálculos detallados (Gauss-Jordan y pasos intermedios)", value=False)

# Botón para ejecutar
if st.button("Ejecutar Enumeración Exhaustiva", type="primary"):
    with st.spinner("Evaluando políticas..."):
        mejor, resultados = enumeracion_exhaustiva(
            estados, decisiones_data, tipo,
            politicas_seleccionadas=politicas_a_evaluar
        )

    if mejor is None:
        st.warning("No se encontró ninguna política con solución válida.")
    else:
        st.success("Evaluación completada.")

        # Mostrar política óptima
        st.markdown("## Política Óptima")
        nombre_optimo = [k for k, v in politicas_dict.items() if v == mejor["politica"]][0]
        st.markdown(f"""
        <div class="policy-box policy-optimal">
            {nombre_optimo} = ({", ".join([mejor["politica"][s] for s in estados])})
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Valor esperado", f"{mejor['esperado']:.6f}")
        with col2:
            st.metric("Tipo de modelo", "Costos (minimizar)" if tipo == "costos" else "Ganancias (maximizar)")

        # Mostrar probabilidades estacionarias de la política óptima
        st.markdown("#### Probabilidades estacionarias (π)")
        pi_df = pd.DataFrame.from_dict(mejor["pi"], orient="index", columns=["π"])
        st.dataframe(pi_df, use_container_width=True)

        st.markdown("---")
        st.markdown("### Políticas evaluadas")

        # Ordenar resultados (los válidos primero, luego los inválidos)
        resultados_validos = [r for r in resultados if not r.get("error", False)]
        resultados_invalidos = [r for r in resultados if r.get("error", False)]

        if tipo == "costos":
            resultados_validos = sorted(resultados_validos, key=lambda x: x["esperado"])
        else:
            resultados_validos = sorted(resultados_validos, key=lambda x: x["esperado"], reverse=True)

        # Mostrar primero los válidos
        for res in resultados_validos:
            nombre = [k for k, v in politicas_dict.items() if v == res["politica"]][0]
            is_optimal = (res == mejor)
            border_style = "border-left: 4px solid #F5A800;" if is_optimal else ""

            with st.expander(f"{nombre}: {res['esperado']:.6f}" + (" (ÓPTIMA)" if is_optimal else "")):
                st.markdown(f"""
                <div style="{border_style} padding-left: 1rem;">
                    <p><b>{nombre} =</b> ({", ".join([res["politica"][s] for s in estados])})</p>
                </div>
                """, unsafe_allow_html=True)

                tab1, tab2, tab3, tab4 = st.tabs(["Matriz de Transición", "Sistema de Ecuaciones", "Probabilidades π", "Costo / Ganancia Esperado"])

                with tab1:
                    st.dataframe(res["P"], use_container_width=True)

                with tab2:
                    for linea in res["sistema"]:
                        st.markdown(f"`{linea}`")

                with tab3:
                    pi_df = pd.DataFrame.from_dict(res["pi"], orient="index", columns=["π"])
                    st.dataframe(pi_df, use_container_width=True)

                with tab4:
                    tipo_valor = "Costo" if tipo == "costos" else "Ganancia"
                    st.markdown(f"**{tipo_valor} esperado:** `{res['esperado']:.6f}`")
                    expr = " + ".join([f"({res['c'][s]:.4f})·({res['pi'][s]:.4f})" for s in estados])
                    st.markdown(f"E = {expr} = {res['esperado']:.6f}")

                if mostrar_detalles and res.get("gauss_steps"):
                    with st.expander("🔍 Ver pasos de Gauss‑Jordan"):
                        for desc, matriz in res["gauss_steps"]:
                            st.markdown(f"**{desc}**")
                            cols = [f"π{_subindice(i)}" for i in range(len(estados))] + ["b"]
                            df_matriz = pd.DataFrame(matriz, columns=cols)
                            st.dataframe(df_matriz, use_container_width=True)

        # Luego mostrar los inválidos
        for res in resultados_invalidos:
            nombre = [k for k, v in politicas_dict.items() if v == res["politica"]][0]
            with st.expander(f"{nombre} — ⚠️ {res.get('mensaje', 'Sin solución')}"):
                st.markdown(f"**{nombre} =** ({', '.join([res['politica'][s] for s in estados])})")
                st.dataframe(res["P"], use_container_width=True)
