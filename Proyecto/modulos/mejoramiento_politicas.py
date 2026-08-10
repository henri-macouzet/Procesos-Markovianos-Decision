"""
modulos/mejoramiento_politicas.py
Interfaz del algoritmo de Mejoramiento de Políticas (Policy Iteration).
Muestra iteraciones, sistema de evaluación en tres niveles y mejora detallada.
"""

import streamlit as st
import pandas as pd
from algoritmos.mejoramiento_politicas import mejoramiento_politicas
from algoritmos.exhaustiva import generar_politicas
from guardado.sesion import get_mdp, mdp_completo

def _subindice(i):
    """Convierte un número entero en subíndice Unicode (₀, ₁, ...)."""
    subs = "₀₁₂₃₄₅₆₇₈₉"
    return ''.join(subs[int(d)] for d in str(i))

st.set_page_config(page_title="Mejoramiento de Políticas — MDP", page_icon="🔄")

mdp = get_mdp()

st.markdown("""
<style>
.policy-box { background: #111827; border: 1px solid #1E2A3A; border-radius: 12px; padding: 1rem; margin-bottom: 0.8rem; }
.policy-optimal { border-left: 4px solid #F5A800; background: #0f1a24; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="margin-bottom:1.5rem;">
    <div style="font-family:'IBM Plex Mono',monospace;font-size:.72rem;color:#F5A800;letter-spacing:.15em;margin-bottom:.4rem;">MÓDULO 05</div>
    <h1 style="font-family:'Sora',sans-serif;font-weight:700;font-size:1.8rem;color:#E8EAF0;margin:0;">Mejoramiento de Políticas</h1>
    <p style="color:#8FA0B8;font-size:.9rem;margin:.4rem 0 0 0;">Aplica el algoritmo iterativo de mejora de políticas.</p>
</div>
""", unsafe_allow_html=True)

if not mdp_completo():
    st.warning("El modelo no está completo. Ve al módulo de Ingreso de Datos para finalizarlo.")
    st.stop()

estados = mdp["estados"]
decisiones_data = mdp["decisiones_data"]
tipo = mdp["tipo"]

# Generar políticas para selección inicial
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

if st.button("Ejecutar Mejoramiento de Políticas", type="primary"):
    politica_inicial = politicas_dict[politica_elegida]
    with st.spinner("Ejecutando iteraciones..."):
        iteraciones = mejoramiento_politicas(estados, decisiones_data, tipo, politica_inicial)

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

    g_opt = iteraciones[-1]["g"]
    col1, col2 = st.columns(2)
    with col1:
        tipo_valor = "Costo mínimo" if tipo == "costos" else "Ganancia máxima"
        st.metric(tipo_valor, f"{g_opt:.6f}")
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
                st.markdown(f"**g({nombre_actual}) = {it['g']:.6f}**" if nombre_actual else f"**g = {it['g']:.6f}**")
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
                costo = decisiones_data[k]["costos"].get(s, 0.0)
                trans = decisiones_data[k]["transiciones"].get(s, {})

                # Sumatoria incluyendo todas las probabilidades (excepto al último estado porque V_n=0)
                sum_terms = []
                for s2 in estados[:-1]:      # omitimos el último estado
                    prob = trans.get(s2, 0.0)
                    sum_terms.append(f"P_{{{s}{s2}}}({k}) V{_subindice(s2)}")

                rhs = f"C_{{{s}{k}}}"
                if sum_terms:
                    rhs += " + " + " + ".join(sum_terms)
                if s != estados[-1]:
                    rhs += f" - V{_subindice(s)}"

                lhs = f"g({nombre_actual})"
                st.latex(f"{lhs} = {rhs}")

            st.markdown("🔹 **Valores sustituidos:**")
            for s in estados:
                k = it["politica"][s]
                costo = decisiones_data[k]["costos"].get(s, 0.0)
                trans = decisiones_data[k]["transiciones"].get(s, {})

                terms = []
                for s2 in estados[:-1]:      # omitimos el último
                    prob = trans.get(s2, 0.0)
                    if prob != 0:
                        terms.append(f"{prob:.4f} V{_subindice(s2)}")

                rhs = f"{costo:.4f}"
                if terms:
                    rhs += " + " + " + ".join(terms)
                if s != estados[-1]:
                    rhs += f" - V{_subindice(s)}"

                lhs = f"g({nombre_actual})"
                st.latex(f"{lhs} = {rhs}")

            st.markdown("🔹 **Sistema simplificado (agrupado):**")
            for s in estados:
                k = it["politica"][s]
                costo = decisiones_data[k]["costos"].get(s, 0.0)
                trans = decisiones_data[k]["transiciones"].get(s, {})

                if s == estados[-1]:
                    # Último estado: V_n = 0, se construye la ecuación con los V_j no nulos
                    lhs_terms = [f"g({nombre_actual})"]
                    for s2 in estados[:-1]:
                        prob = trans.get(s2, 0.0)
                        if prob != 0:
                            lhs_terms.append(f"- {prob:.4f} V{_subindice(s2)}")
                    lhs = " ".join(lhs_terms)
                    rhs = f"{costo:.4f}"
                else:
                    # Para otros estados: g + (1 - P_ii) V_i - Σ_{j≠i} P_ij V_j
                    p_ii = trans.get(s, 0.0)
                    coef_Vi = 1.0 - p_ii
                    lhs_terms = [f"g({nombre_actual})"]
                    if abs(coef_Vi) > 1e-12:
                        lhs_terms.append(f"+ {coef_Vi:.4f} V{_subindice(s)}")
                    for s2 in estados[:-1]:
                        if s2 == s:
                            continue
                        prob = trans.get(s2, 0.0)
                        if prob != 0:
                            lhs_terms.append(f"- {prob:.4f} V{_subindice(s2)}")
                    lhs = " ".join(lhs_terms)
                    rhs = f"{costo:.4f}"

                st.latex(f"{lhs} = {rhs}")

            # ────────────────────────────────────────────────────────
            # PASO DE MEJORA (detallado)
            # Ahora: C_{ik} + Σ P_{ij}(k) V_j - V_i   (incluyendo P_{ii})
            # ────────────────────────────────────────────────────────
            st.markdown("**Mejora (valores por decisión):**")
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
                            formula += " + " + " + ".join(sum_sym)
                        if s != estados[-1]:
                            formula += f" - V{_subindice(s)}"

                        # --- Sustitución numérica ---
                        sum_num = []
                        for s2 in estados:
                            prob = trans.get(s2, 0.0)
                            sum_num.append(f"{prob:.4f}·({it['V'][s2]:.4f})")
                        expr_num = f"{costo:.4f}"
                        if sum_num:
                            expr_num += " + " + " + ".join(sum_num)
                        if s != estados[-1]:
                            expr_num += f" - ({it['V'][s]:.4f})"

                        # --- Valor final ---
                        suma = sum(prob * it["V"][s2] for s2, prob in trans.items())
                        valor_final = costo + suma
                        if s != estados[-1]:
                            valor_final -= it["V"][s]

                        prefijo = "✅ " if d == elegida else "   "
                        st.latex(f"{prefijo}{formula} = {expr_num} = {valor_final:.6f}")
                st.markdown("---")
