"""
modulos/programacion_lineal.py
Interfaz de Programación Lineal. Muestra modelo, solución Y, D, política y construcción detallada.
"""

import streamlit as st
import pandas as pd
from algoritmos.programacion_lineal import resolver_pl
from guardado.sesion import get_mdp, mdp_completo

st.set_page_config(page_title="Programación Lineal — MDP", page_icon="📈")

mdp = get_mdp()

st.markdown("""
<style>
.policy-box { background: #111827; border: 1px solid #1E2A3A; border-radius: 12px; padding: 1rem; margin-bottom: 0.8rem; }
.policy-optimal { border-left: 4px solid #F5A800; background: #0f1a24; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="margin-bottom:1.5rem;">
    <div style="font-family:'IBM Plex Mono',monospace;font-size:.72rem;color:#F5A800;letter-spacing:.15em;margin-bottom:.4rem;">MÓDULO 04</div>
    <h1 style="font-family:'Sora',sans-serif;font-weight:700;font-size:1.8rem;color:#E8EAF0;margin:0;">Programación Lineal</h1>
    <p style="color:#8FA0B8;font-size:.9rem;margin:.4rem 0 0 0;">Resuelve el MDP usando un modelo de programación lineal.</p>
</div>
""", unsafe_allow_html=True)

if not mdp_completo():
    st.warning("El modelo no está completo. Ve al módulo de Ingreso de Datos para finalizarlo.")
    st.stop()

estados = mdp["estados"]
decisiones_data = mdp["decisiones_data"]
tipo = mdp["tipo"]

# Resolver el modelo una vez
resultado = resolver_pl(estados, decisiones_data, tipo)

if not resultado["exito"]:
    st.error(f"Error al construir/resolver: {resultado['mensaje']}")
    st.stop()

# ---------- Pestañas ----------
tab_modelo, tab_construccion, tab_resultados = st.tabs([
    "📐 Formulación",
    "🔍 Construcción detallada",
    "📊 Solución y política"
])

with tab_modelo:
    st.markdown("### Función objetivo")
    st.latex(resultado["modelo"]["funcion_objetivo"])
    st.markdown("### Sujeta a:")
    st.markdown("**Restricciones de balance (para cada estado excepto el último):**")
    for ec in resultado["modelo"]["restricciones_desarrollo"]:
        st.latex(ec)
    st.markdown("**Normalización:**")
    st.latex(resultado["modelo"]["normalizacion"])
    st.markdown("**No negatividad:**")
    st.latex(resultado["modelo"]["no_negatividad"])

with tab_construccion:
    st.markdown("#### Desarrollo de las restricciones de balance")
    st.write("La fórmula general para cada estado \\(i\\) (excepto el último) es:")
    st.latex(resultado["modelo"]["formula_general"])
    st.markdown("Aplicando a nuestro modelo:")

    for idx, s in enumerate(estados[:-1]):
        with st.expander(f"Estado {s}"):
            st.markdown("**Forma completa (todos los términos simbólicos):**")
            st.latex(resultado["modelo"]["restricciones_completas"][idx])
            st.markdown("**Eliminando términos con probabilidad cero:**")
            st.latex(resultado["modelo"]["restricciones_sin_ceros"][idx])
            st.markdown("**Forma final (coeficientes numéricos):**")
            st.latex(resultado["modelo"]["restricciones_desarrollo"][idx])

    st.markdown("---")
    st.markdown("**Normalización:**")
    st.latex(resultado["modelo"]["normalizacion"])
    st.markdown("**No negatividad:**")
    st.latex(resultado["modelo"]["no_negatividad"])

with tab_resultados:
    st.success("Solución óptima encontrada.")
    st.markdown("### Política Óptima")
    nombre = resultado.get("nombre_politica", "")
    if nombre:
        st.markdown(f"""
        <div class="policy-box policy-optimal">
            {nombre} = ({", ".join([resultado["politica"][s] for s in estados])})
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="policy-box policy-optimal">
            ({", ".join([resultado["politica"][s] for s in estados])})
        </div>
        """, unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        tipo_valor = "Costo mínimo" if tipo == "costos" else "Ganancia máxima"
        st.metric(tipo_valor, f"{resultado['valor_optimo']:.6f}")
    with col2:
        st.metric("Tipo de modelo", "Costos (minimizar)" if tipo == "costos" else "Ganancias (maximizar)")

    st.markdown("### Variables Y (probabilidad conjunta)")
    df_y = pd.DataFrame(
        [(s, d, resultado["variables_y"].get((s, d), 0.0))
         for s in estados for d in decisiones_data
         if (s, d) in resultado["variables_y"]],
        columns=["Estado", "Decisión", "Y"]
    )
    pivote_y = df_y.pivot(index="Estado", columns="Decisión", values="Y").fillna(0)
    st.dataframe(pivote_y, use_container_width=True)

    st.markdown("### Coeficientes D (probabilidad de decisión por estado)")
    df_D = resultado["D"].fillna(0)
    st.dataframe(df_D, use_container_width=True)

    st.caption("La decisión para cada estado es aquella con mayor coeficiente D.")
