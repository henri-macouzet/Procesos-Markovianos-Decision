"""
modulos/aproximaciones_sucesivas.py
Interfaz de Aproximaciones Sucesivas mostrando los dos pasos por iteración.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from algoritmos.aproximaciones_sucesivas import aproximaciones_sucesivas
from algoritmos.exhaustiva import generar_politicas
from guardado.sesion import get_mdp, mdp_completo

def _subindice(i):
    subs = "₀₁₂₃₄₅₆₇₈₉"
    return ''.join(subs[int(d)] for d in str(i))

st.set_page_config(page_title="Aproximaciones Sucesivas — MDP", page_icon="🔁")

mdp = get_mdp()

st.markdown("""
<style>
.policy-box { background: #111827; border: 1px solid #1E2A3A; border-radius: 12px; padding: 1rem; margin-bottom: 0.8rem; }
.policy-optimal { border-left: 4px solid #F5A800; background: #0f1a24; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="margin-bottom:1.5rem;">
    <div style="font-family:'IBM Plex Mono',monospace;font-size:.72rem;color:#F5A800;letter-spacing:.15em;margin-bottom:.4rem;">MÓDULO 07</div>
    <h1 style="font-family:'Sora',sans-serif;font-weight:700;font-size:1.8rem;color:#E8EAF0;margin:0;">Aproximaciones Sucesivas</h1>
    <p style="color:#8FA0B8;font-size:.9rem;margin:.4rem 0 0 0;">Iteración de valores con dos pasos por iteración.</p>
</div>
""", unsafe_allow_html=True)

if not mdp_completo():
    st.warning("El modelo no está completo.")
    st.stop()

estados = mdp["estados"]
decisiones_data = mdp["decisiones_data"]
tipo = mdp["tipo"]

st.markdown("### Parámetros")
col1, col2, col3 = st.columns(3)
with col1:
    epsilon = st.number_input("Tolerancia ε", min_value=0.0001, value=0.01, step=0.001, format="%.4f")
with col2:
    max_iter = st.number_input("Máx. iteraciones", min_value=1, max_value=1000, value=100)
with col3:
    usar_alpha = st.checkbox("Usar factor de descuento α", value=False)
    if usar_alpha:
        alpha = st.number_input("α (0-1)", min_value=0.0, max_value=1.0, value=0.9, step=0.01)
    else:
        alpha = 1.0
        st.markdown("α = 1.0 (sin descuento)")

st.markdown("---")

if st.button("Ejecutar Aproximaciones Sucesivas", type="primary"):
    # Guardar parámetros en sesión para comparación
    st.session_state["eps_as"] = epsilon
    st.session_state["max_iter_as"] = max_iter
    st.session_state["alpha_as"] = alpha
    with st.spinner("Calculando..."):
        iteraciones = aproximaciones_sucesivas(
            estados, decisiones_data, tipo,
            epsilon=epsilon, max_iter=max_iter, alpha=alpha
        )

    st.success(f"Completado en {len(iteraciones)} iteraciones (máx. {max_iter}).")

    final_politica = iteraciones[-1]["paso2"]["politica"]
    politicas = generar_politicas(estados, decisiones_data)
    nombre_optima = None
    for i, pol in enumerate(politicas):
        if pol == final_politica:
            nombre_optima = f"R{i+1}"
            break

    st.markdown("## Política Óptima")
    if nombre_optima:
        st.markdown(f"""
        <div class="policy-box policy-optimal">
            {nombre_optima} = ({", ".join([final_politica[s] for s in estados])})
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="policy-box policy-optimal">
            ({", ".join([final_politica[s] for s in estados])})
        </div>
        """, unsafe_allow_html=True)

    final_V = iteraciones[-1]["paso1"]["V"]
    st.markdown("**Valores V finales:**")
    for s in estados:
        st.write(f"V{_subindice(s)} = {final_V[s]:.6f}")
    st.metric("Tipo de modelo", "Costos (minimizar)" if tipo == "costos" else "Ganancias (maximizar)")

    st.markdown("---")
    st.markdown("### Iteraciones")
    for it in iteraciones:
        n = it["iter"]
        titulo = f"Iteración {n}"
        if it["max_diff"] is not None:
            titulo += f" — dif máx = {it['max_diff']:.6f}"
        with st.expander(titulo):
            # Paso 1
            st.markdown("**Paso 1: Cálculo de V^{%d}**" % n)
            if n == 1:
                st.latex(r"V_i^1 = \min_k C_{ik}" if tipo == "costos" else r"V_i^1 = \max_k C_{ik}")
                for s in estados:
                    det = it["paso1"]["detalle"][s]
                    st.markdown(f"**Estado {s}:**")
                    for op in det["opciones"]:
                        st.latex(f"C_{{{s},{op['decision']}}} = {op['costo']:.4f}")
                    st.success(f"Elegida: {det['elegida']} = {it['paso1']['V'][s]:.4f}")
            else:
                st.latex(r"V_i^n = \min_k \left[ C_{ik} + \alpha \sum_j P_{ij}(k) V_j^{n-1} \right]" if tipo == "costos" else r"V_i^n = \max_k \left[ C_{ik} + \alpha \sum_j P_{ij}(k) V_j^{n-1} \right]")
                for s in estados:
                    det = it["paso1"]["detalle"][s]
                    st.markdown(f"**Estado {s}:**")
                    for op in det["opciones"]:
                        expr = f"{op['costo']:.4f}"
                        if op['terminos']:
                            terminos_str = " + ".join(
                                f"{alpha}·{prob:.4f}·({valor:.4f})" for _, prob, valor in op['terminos']
                            )
                            expr += f" + ({terminos_str})"
                        expr += f" = {op['valor_q']:.4f}"
                        st.latex(f"C_{{{s},{op['decision']}}} + {alpha}·\\Sigma P V = {expr}")
                    st.success(f"Elegida: {det['elegida']} = {it['paso1']['V'][s]:.4f}")

            # Paso 2
            st.markdown("**Paso 2: Política resultante**")
            # Mostrar detalle del paso 2 (evaluación con los V del paso 1 de esta iteración)
            detalle_p2 = it["paso2"]["detalle"]
            for s in estados:
                det = detalle_p2[s]
                st.markdown(f"**Estado {s}:**")
                for op in det["opciones"]:
                    expr = f"{op['costo']:.4f}"
                    if op['terminos']:
                        terminos_str = " + ".join(
                            f"{alpha}·{prob:.4f}·({valor:.4f})" for _, prob, valor in op['terminos']
                        )
                        expr += f" + ({terminos_str})"
                    expr += f" = {op['valor_q']:.4f}"
                    st.latex(f"C_{{{s},{op['decision']}}} + {alpha}·\\Sigma P V = {expr}")
                st.success(f"Elegida: {det['elegida']} → Política actualizada")
            # También mostrar la política completa
            pol_dict = it["paso2"]["politica"]
            nombre_pol = None
            for i, p in enumerate(politicas):
                if p == pol_dict:
                    nombre_pol = f"R{i+1}"
                    break
            if nombre_pol:
                st.write(f"**Política:** {nombre_pol} = ({', '.join([pol_dict[s] for s in estados])})")
            else:
                st.write(f"**Política:** {', '.join([f'{s} → {d}' for s, d in pol_dict.items()])}")

    # Gráfica de convergencia
    diffs = [it["max_diff"] for it in iteraciones if it["max_diff"] is not None]
    if diffs:
        st.markdown("---")
        st.markdown("### Convergencia")
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.plot(range(2, len(diffs)+2), diffs, marker='o', color='#F5A800')
        ax.axhline(y=epsilon, color='#EF4444', linestyle='--', label=f'ε = {epsilon}')
        ax.set_xlabel("Iteración")
        ax.set_ylabel("Diferencia máxima")
        ax.legend()
        ax.set_facecolor('#0A0E1A')
        fig.patch.set_facecolor('#0A0E1A')
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.tick_params(colors='white')
        ax.yaxis.label.set_color('white')
        ax.xaxis.label.set_color('white')
        st.pyplot(fig)
