"""
modulos/mejoramiento_politicas_descuento.py
Interfaz del algoritmo de Mejoramiento de Políticas con descuento.
Muestra iteraciones, sistema de evaluación en tres niveles y mejora detallada.
"""

import streamlit as st
import pandas as pd
import numpy as np
from algoritmos.mejoramiento_politicas_descuento import mejoramiento_politicas_descuento
from algoritmos.exhaustiva import generar_politicas
from guardado.sesion import get_mdp, mdp_completo

def _subindice(i):
    subs = "₀₁₂₃₄₅₆₇₈₉"
    return ''.join(subs[int(d)] for d in str(i))

st.set_page_config(page_title="Mejoramiento de Políticas c/ Desc. — MDP", page_icon="💲")

mdp = get_mdp()

st.markdown("""
<style>
.policy-box { background: #111827; border: 1px solid #1E2A3A; border-radius: 12px; padding: 1rem; margin-bottom: 0.8rem; }
.policy-optimal { border-left: 4px solid #F5A800; background: #0f1a24; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="margin-bottom:1.5rem;">
    <div style="font-family:'IBM Plex Mono',monospace;font-size:.72rem;color:#F5A800;letter-spacing:.15em;margin-bottom:.4rem;">MÓDULO 06</div>
    <h1 style="font-family:'Sora',sans-serif;font-weight:700;font-size:1.8rem;color:#E8EAF0;margin:0;">Mejoramiento de Políticas con Descuento</h1>
    <p style="color:#8FA0B8;font-size:.9rem;margin:.4rem 0 0 0;">Mejoramiento de políticas con factor de descuento.</p>
</div>
""", unsafe_allow_html=True)

if not mdp_completo():
    st.warning("El modelo no está completo. Ve al módulo de Ingreso de Datos para finalizarlo.")
    st.stop()

estados = mdp["estados"]
decisiones_data = mdp["decisiones_data"]
tipo = mdp["tipo"]

# --- Factor de descuento ---
st.markdown("### Factor de descuento α")
modo_alpha = st.radio("Selecciona cómo ingresar el factor de descuento:",
                       ["Directamente (α)", "Mediante tasa de interés i"])
if modo_alpha == "Directamente (α)":
    alpha = st.number_input("α (entre 0 y 1)", min_value=0.0, max_value=0.9999, value=0.9, step=0.01)
else:
    i = st.number_input("Tasa de interés i (ej. 0.05 para 5%)", min_value=0.0, value=0.0, step=0.001)
    if i >= 0:
        alpha = 1.0 / (1.0 + i)
        st.write(f"α calculado = 1/(1+{i}) = {alpha:.6f}")
    else:
        alpha = 1.0
st.markdown("---")
st.session_state["alpha_descuento"] = alpha

# --- Generar políticas para selección inicial ---
politicas = generar_politicas(estados, decisiones_data)
politicas_dict = {}
for i, pol in enumerate(politicas):
    nombre = f"R{i+1}"
    politicas_dict[nombre] = pol

# Mostrar políticas disponibles
st.markdown("### Política Inicial")
cols = st.columns(min(len(politicas_dict), 5))
for i, (nombre, pol) in enumerate(politicas_dict.items()):
    with cols[i % len(cols)]:
        texto = f"({', '.join([pol[s] for s in estados])})"
        st.markdown(f'<span class="chip chip-gold">{nombre} = {texto}</span>', unsafe_allow_html=True)

politica_elegida = st.selectbox(
    "Selecciona la política inicial",
    list(politicas_dict.keys()),
    help="La profesora indicará cuál elegir."
)

if st.button("Ejecutar Mejoramiento de Políticas con Descuento", type="primary"):
    politica_inicial = politicas_dict[politica_elegida]
    with st.spinner("Ejecutando iteraciones..."):
        iteraciones = mejoramiento_politicas_descuento(
            estados, decisiones_data, tipo,
            politica_inicial=politica_inicial, alpha=alpha
        )

    st.success(f"Algoritmo completado en {len(iteraciones)} iteraciones.")

    # Política óptima
    optima = iteraciones[-1]["nueva_politica"]
    nombre_optima = None
    for n, p in politicas_dict.items():
        if p == optima:
            nombre_optima = n
            break

    st.markdown("## Política Óptima")
    if nombre_optima:
        st.markdown(f"""
        <div class="policy-box policy-optimal">
            {nombre_optima} = ({", ".join([optima[s] for s in estados])})
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="policy-box policy-optimal">
            ({", ".join([optima[s] for s in estados])})
        </div>
        """, unsafe_allow_html=True)

    # Valores V de la política óptima
    V_opt = iteraciones[-1]["V"]
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Valores V de la política óptima**")
        for s in estados:
            st.write(f"V{_subindice(s)} = {V_opt[s]:.6f}")
    with col2:
        st.metric("Tipo de modelo", "Costos (minimizar)" if tipo == "costos" else "Ganancias (maximizar)")

    st.markdown("---")
    st.markdown("### Iteraciones")

    for idx_it, it in enumerate(iteraciones):
        nombre_actual = None
        for n, p in politicas_dict.items():
            if p == it["politica"]:
                nombre_actual = n
                break

        with st.expander(f"Iteración {idx_it+1} — Política evaluada: {nombre_actual if nombre_actual else ''}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Política evaluada**")
                if nombre_actual:
                    st.write(f"{nombre_actual} = ({', '.join([it['politica'][s] for s in estados])})")
                else:
                    st.write("---")
                st.markdown("**Valores V:**")
                for s in estados:
                    st.write(f"V{_subindice(s)} = {it['V'][s]:.6f}")

            with col2:
                nueva = it["nueva_politica"]
                nombre_nueva = None
                for n, p in politicas_dict.items():
                    if p == nueva:
                        nombre_nueva = n
                        break
                st.markdown("**Nueva política**")
                if nombre_nueva:
                    st.write(f"{nombre_nueva} = ({', '.join([nueva[s] for s in estados])})")
                else:
                    st.write("---")
                igual = (nueva == it["politica"])
                if igual:
                    st.success("✓ Se mantiene la política (óptima)")
                else:
                    st.info("Se actualiza la política")

            # ────────────────────────────────────────────────────────
            # SISTEMA DE ECUACIONES DE EVALUACIÓN (tres niveles)
            # ────────────────────────────────────────────────────────
            st.markdown("---")
            st.markdown("**Sistema de ecuaciones (evaluación):**")
            st.markdown("🔹 **Formación (estructura general):**")
            for s in estados:
                k = it["politica"][s]
                costo = it["c"][estados.index(s)]
                trans = decisiones_data[k]["transiciones"].get(s, {})

                # Sumatoria incluyendo todos los estados (sin omitir el último)
                sum_terms = []
                for s2 in estados:
                    prob = trans.get(s2, 0.0)
                    sum_terms.append(f"P_{{{s}{s2}}}({k}) V{_subindice(s2)}")

                rhs = f"C_{{{s}{k}}}"
                if sum_terms:
                    rhs += f" + {alpha:.4f}·(" + " + ".join(sum_terms) + ")"

                lhs = f"V{_subindice(s)}"
                st.latex(f"{lhs} = {rhs}")

            st.markdown("🔹 **Valores sustituidos:**")
            for s in estados:
                k = it["politica"][s]
                costo = it["c"][estados.index(s)]
                trans = decisiones_data[k]["transiciones"].get(s, {})

                terms = []
                for s2 in estados:
                    prob = trans.get(s2, 0.0)
                    if prob != 0:
                        terms.append(f"{prob:.4f} V{_subindice(s2)}")

                rhs = f"{costo:.4f}"
                if terms:
                    rhs += f" + {alpha:.4f}·(" + " + ".join(terms) + ")"

                lhs = f"V{_subindice(s)}"
                st.latex(f"{lhs} = {rhs}")

            st.markdown("🔹 **Sistema simplificado (agrupado):**")
            for s in estados:
                k = it["politica"][s]
                costo = it["c"][estados.index(s)]
                trans = decisiones_data[k]["transiciones"].get(s, {})

                # Construir: V_i - α Σ_j P_{ij} V_j = costo
                p_ii = trans.get(s, 0.0)
                coef_Vi = 1.0 - alpha * p_ii
                lhs_terms = []
                if abs(coef_Vi) > 1e-12:
                    lhs_terms.append(f"{coef_Vi:+.4f} V{_subindice(s)}")
                for s2 in estados:
                    if s2 == s:
                        continue
                    prob = trans.get(s2, 0.0)
                    if prob != 0:
                        coef = -alpha * prob
                        lhs_terms.append(f"{coef:+.4f} V{_subindice(s2)}")

                lhs = " ".join(lhs_terms) if lhs_terms else f"V{_subindice(s)}"
                if not lhs.startswith(('+', '-')):
                    lhs = "+ " + lhs
                rhs = f"{costo:.4f}"
                st.latex(f"{lhs} = {rhs}")

            # ────────────────────────────────────────────────────────
            # PASO DE MEJORA (detallado)
            # ────────────────────────────────────────────────────────
            st.markdown("**Mejora (valores Q por decisión):**")
            for s in estados:
                st.markdown(f"**Estado {s}:**")
                elegida = it["nueva_politica"][s]
                for d in decisiones_data:
                    if s in decisiones_data[d]["estados_afectados"]:
                        costo = decisiones_data[d]["costos"].get(s, 0.0)
                        trans = decisiones_data[d]["transiciones"].get(s, {})

                        # --- Fórmula simbólica ---
                        sum_sym = []
                        for s2 in estados:
                            prob = trans.get(s2, 0.0)
                            # Incluir todas las probabilidades (incluso 0)
                            sum_sym.append(f"P_{{{s}{s2}}}({d}) V{_subindice(s2)}")
                        formula = f"C_{{{s}{d}}}"
                        if sum_sym:
                            formula += f" + {alpha:.4f}·(" + " + ".join(sum_sym) + ")"

                        # --- Sustitución numérica ---
                        sum_num = []
                        for s2 in estados:
                            prob = trans.get(s2, 0.0)
                            sum_num.append(f"{prob:.4f}·({it['V'][s2]:.4f})")
                        expr_num = f"{costo:.4f}"
                        if sum_num:
                            expr_num += f" + {alpha:.4f}·(" + " + ".join(sum_num) + ")"

                        # --- Valor final ---
                        suma = sum(prob * it["V"][s2] for s2, prob in trans.items())
                        valor_final = costo + alpha * suma

                        prefijo = "✅ " if d == elegida else "   "
                        st.latex(f"{prefijo}{formula} = {expr_num} = {valor_final:.6f}")
                st.markdown("---")
