"""
modulos/comparacion_metodos.py
Módulo de comparación de métodos. Versión simplificada y elegante.
Muestra tabla, gráfico de costos, tarjetas y consistencia por estado.
"""

import time
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
from algoritmos.exhaustiva import enumeracion_exhaustiva, generar_politicas
from algoritmos.programacion_lineal import resolver_pl
from algoritmos.mejoramiento_politicas import mejoramiento_politicas
from algoritmos.mejoramiento_politicas_descuento import mejoramiento_politicas_descuento
from algoritmos.aproximaciones_sucesivas import aproximaciones_sucesivas
from guardado.sesion import get_mdp, mdp_completo

# ---------- OBTENER MODELO ----------
mdp = get_mdp()

# ---------- ESTILOS ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

.coincidencia-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 2px solid #F5A800;
    border-radius: 20px;
    padding: 2rem;
    margin: 2rem 0;
    text-align: center;
    box-shadow: 0 8px 32px rgba(245, 168, 0, 0.15);
}
.coincidencia-card.warning {
    border-color: #EF4444;
    box-shadow: 0 8px 32px rgba(239, 68, 68, 0.15);
}
.method-card {
    background: #111827;
    border: 1px solid #1E2A3A;
    border-left: 5px solid #3B82F6;
    border-radius: 12px;
    padding: 1.5rem;
    flex: 1;
    min-width: 200px;
    transition: all 0.3s ease;
}
.method-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}
.method-card.optimo { border-left-color: #F5A800; }
.method-card.fallo  { border-left-color: #EF4444; opacity: 0.7; }
.method-icon  { font-size: 2rem; margin-bottom: 0.5rem; }
.method-name  { font-family:'Sora',sans-serif; font-weight:600; color:#E8EAF0; margin-bottom:0.6rem; }
.policy-text  { font-family:'IBM Plex Mono',monospace; color:#B0C0D0; font-size:0.85rem; margin-bottom:0.3rem; }
.cost-text    { font-family:'IBM Plex Mono',monospace; color:#10B981; font-size:0.85rem; margin-top:0.3rem; }
.detail-text  { font-family:'IBM Plex Mono',monospace; color:#8FA0B8; font-size:0.78rem; margin-top:0.3rem; }

.section-label {
    font-family:'IBM Plex Mono',monospace;
    font-size:.68rem;
    color:#F5A800;
    letter-spacing:.15em;
    margin-bottom:.3rem;
    margin-top:2rem;
}
.section-title {
    font-family:'Sora',sans-serif;
    font-weight:700;
    font-size:1.3rem;
    color:#E8EAF0;
    margin-bottom:1rem;
}
</style>
""", unsafe_allow_html=True)

# ---------- ENCABEZADO ----------
st.markdown("""
<div style="margin-bottom:2rem; text-align:center;">
    <div style="font-family:'IBM Plex Mono',monospace;font-size:.72rem;color:#F5A800;letter-spacing:.15em;margin-bottom:.4rem;">
        MÓDULO 08 · CONVERGENCIA DE MÉTODOS
    </div>
    <h1 style="font-family:'Sora',sans-serif;font-weight:700;font-size:2.5rem;color:#E8EAF0;margin:0;">
        ⚖️ Comparación de Métodos
    </h1>
    <p style="color:#8FA0B8;font-size:1rem;margin-top:0.5rem;">
        Resultados nativos de cada algoritmo con análisis de coincidencia.
    </p>
</div>
""", unsafe_allow_html=True)

if not mdp_completo():
    st.warning("El modelo no está completo. Ve al módulo de Ingreso de Datos para finalizarlo.")
    st.stop()

estados = mdp["estados"]
decisiones_data = mdp["decisiones_data"]
tipo = mdp["tipo"]

eps_as = st.session_state.get("eps_as", 0.01)
max_iter_as = st.session_state.get("max_iter_as", 100)
alpha_as = st.session_state.get("alpha_as", 1.0)
alpha_descuento = st.session_state.get("alpha_descuento", 0.9)
politicas_disponibles = generar_politicas(estados, decisiones_data)

def obtener_nombre(politica):
    if politica is None:
        return "—"
    for i, p in enumerate(politicas_disponibles):
        if p == politica:
            return f"R{i+1}"
    return None

def fig_style(fig, ax_list=None):
    fig.patch.set_facecolor("#0A0E1A")
    if ax_list is None:
        return
    for ax in (ax_list if isinstance(ax_list, list) else [ax_list]):
        ax.set_facecolor("#0A0E1A")
        ax.tick_params(colors="#8FA0B8")
        ax.xaxis.label.set_color("#8FA0B8")
        ax.yaxis.label.set_color("#8FA0B8")
        ax.title.set_color("#E8EAF0")
        for spine in ax.spines.values():
            spine.set_color("#1E2A3A")

# ── BOTÓN PRINCIPAL ────────────────────────────────────────
if st.button("🗳️ Iniciar Comparación Final", type="primary", use_container_width=True):
    resultados = {}
    detalles = {}
    tiempos = {}

    # 1. Enumeración Exhaustiva
    with st.spinner("🔍 Evaluando todas las políticas..."):
        t0 = time.perf_counter()
        mejor_ee, ranking_ee = enumeracion_exhaustiva(estados, decisiones_data, tipo)
        tiempos["Enumeración Exhaustiva"] = time.perf_counter() - t0
        if mejor_ee and not mejor_ee.get("error"):
            pol_ee = mejor_ee["politica"]
            resultados["Enumeración Exhaustiva"] = pol_ee
            detalles["Enumeración Exhaustiva"] = {
                "costo": mejor_ee["esperado"], "iteraciones": "—"
            }
        else:
            resultados["Enumeración Exhaustiva"] = None
            detalles["Enumeración Exhaustiva"] = {"costo": None, "iteraciones": "—"}

    # 2. Programación Lineal
    with st.spinner("📈 Resolviendo con Programación Lineal..."):
        t0 = time.perf_counter()
        res_pl = resolver_pl(estados, decisiones_data, tipo)
        tiempos["Programación Lineal"] = time.perf_counter() - t0
        if res_pl["exito"]:
            pol_pl = res_pl["politica"]
            resultados["Programación Lineal"] = pol_pl
            detalles["Programación Lineal"] = {
                "costo": res_pl["valor_optimo"], "iteraciones": "—"
            }
        else:
            resultados["Programación Lineal"] = None
            detalles["Programación Lineal"] = {"costo": None, "iteraciones": "—"}

    # 3. Mejoramiento de Políticas
    with st.spinner("🔄 Ejecutando Mejoramiento de Políticas..."):
        t0 = time.perf_counter()
        try:
            pol_inicial = politicas_disponibles[0]
            iter_mp = mejoramiento_politicas(estados, decisiones_data, tipo, pol_inicial)
            pol_mp = iter_mp[-1]["nueva_politica"]
            tiempos["Mejoramiento de Políticas"] = time.perf_counter() - t0
            resultados["Mejoramiento de Políticas"] = pol_mp
            detalles["Mejoramiento de Políticas"] = {
                "costo": iter_mp[-1]["g"], "iteraciones": len(iter_mp)
            }
        except Exception:
            tiempos["Mejoramiento de Políticas"] = time.perf_counter() - t0
            resultados["Mejoramiento de Políticas"] = None
            detalles["Mejoramiento de Políticas"] = {"costo": None, "iteraciones": None}

    # 4. Mejoramiento de Políticas con Descuento
    with st.spinner("💲 Mejoramiento de Políticas con Descuento..."):
        t0 = time.perf_counter()
        exito_mpd = False
        for pol in politicas_disponibles[:5]:
            try:
                iter_mpd = mejoramiento_politicas_descuento(
                    estados, decisiones_data, tipo, pol, alpha_descuento
                )
                pol_mpd = iter_mpd[-1]["nueva_politica"]
                V_final = iter_mpd[-1]["V"]
                tiempos["Mej. Políticas c/ Desc."] = time.perf_counter() - t0
                resultados["Mej. Políticas c/ Desc."] = pol_mpd
                detalles["Mej. Políticas c/ Desc."] = {
                    "costo": None, "iteraciones": len(iter_mpd), "extra": V_final
                }
                exito_mpd = True
                break
            except np.linalg.LinAlgError:
                continue
        if not exito_mpd:
            tiempos["Mej. Políticas c/ Desc."] = time.perf_counter() - t0
            resultados["Mej. Políticas c/ Desc."] = None
            detalles["Mej. Políticas c/ Desc."] = {"costo": None, "iteraciones": None, "extra": None}

    # 5. Aproximaciones Sucesivas
    with st.spinner("🔁 Iterando con Aproximaciones Sucesivas..."):
        t0 = time.perf_counter()
        try:
            iter_as = aproximaciones_sucesivas(
                estados, decisiones_data, tipo, eps_as, max_iter_as, alpha_as
            )
            pol_as = iter_as[-1]["paso2"]["politica"]
            V_final = iter_as[-1]["paso1"]["V"]
            tiempos["Aproximaciones Sucesivas"] = time.perf_counter() - t0
            resultados["Aproximaciones Sucesivas"] = pol_as
            detalles["Aproximaciones Sucesivas"] = {
                "costo": None, "iteraciones": len(iter_as), "extra": V_final
            }
        except Exception:
            tiempos["Aproximaciones Sucesivas"] = time.perf_counter() - t0
            resultados["Aproximaciones Sucesivas"] = None
            detalles["Aproximaciones Sucesivas"] = {"costo": None, "iteraciones": None, "extra": None}

    # ── ANÁLISIS DE COINCIDENCIA ─────────────────────────────
    politicas_exitosas = [p for p in resultados.values() if p is not None]
    if not politicas_exitosas:
        st.error("Ningún método pudo encontrar una política. Revisa el modelo.")
        st.stop()

    contador = Counter(tuple(sorted(p.items())) for p in politicas_exitosas)
    politica_coincidencia = dict(contador.most_common(1)[0][0])
    nombre_coincidencia = obtener_nombre(politica_coincidencia)
    todos_iguales = all(p == politica_coincidencia for p in politicas_exitosas)

    if todos_iguales:
        st.markdown(f"""
        <div class="coincidencia-card">
            <h2>✅ Coincidencia Total</h2>
            <p style="font-size:1.1rem; color:#E8EAF0; margin:0.8rem 0;">
                Todos los métodos devuelven la misma política óptima:
            </p>
            <p style="font-family:'IBM Plex Mono',monospace; font-size:1.4rem; color:#F5A800;">
                {nombre_coincidencia} = ({", ".join([politica_coincidencia[s] for s in estados])})
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="coincidencia-card warning">
            <h2>⚠️ No hay coincidencia total</h2>
            <p style="font-size:1rem; color:#E8EAF0; margin:0.8rem 0;">
                La política más frecuente es:
            </p>
            <p style="font-family:'IBM Plex Mono',monospace; font-size:1.4rem; color:#F5A800;">
                {nombre_coincidencia} = ({", ".join([politica_coincidencia[s] for s in estados])})
            </p>
        </div>
        """, unsafe_allow_html=True)

    # ── TABLA COMPARATIVA ────────────────────────────────────
    st.markdown('<div class="section-label">ANÁLISIS · TABLA</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📊 Tabla Comparativa</div>', unsafe_allow_html=True)

    orden_metodos = [
        "Enumeración Exhaustiva", "Programación Lineal",
        "Mejoramiento de Políticas", "Mej. Políticas c/ Desc.", "Aproximaciones Sucesivas"
    ]
    tabla = []
    for metodo in orden_metodos:
        pol = resultados.get(metodo)
        det = detalles.get(metodo, {})
        nombre_pol = obtener_nombre(pol) if pol else "—"
        if pol:
            pol_str = f"{nombre_pol} = ({', '.join([pol[s] for s in estados])})"
        else:
            pol_str = "No disponible"

        costo_nativo = det.get("costo")
        iteraciones = det.get("iteraciones")
        extra = det.get("extra")

        costo_str = f"{costo_nativo:.6f}" if costo_nativo is not None else "—"
        iter_str = str(iteraciones) if iteraciones not in (None, "—") else "—"
        tiempo_str = f"{tiempos.get(metodo, 0)*1000:.1f} ms"
        coincide_str = "✅" if pol and pol == politica_coincidencia else ("❌" if pol else "⚠️")

        tabla.append({
            "Método": metodo,
            "Política": pol_str,
            "Costo/Ganancia nativo": costo_str,
            "Iteraciones": iter_str,
            "Tiempo": tiempo_str,
            "Coincide": coincide_str,
        })

    df_tabla = pd.DataFrame(tabla)
    st.dataframe(df_tabla, use_container_width=True, hide_index=True)

    # ── GRÁFICO DE BARRAS ────────────────────────────────────
    metodos_costo = {m: d["costo"] for m, d in detalles.items() if d["costo"] is not None}
    if metodos_costo and len(set(metodos_costo.values())) > 1:
        st.markdown('<div class="section-label">VISUALIZACIÓN</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📈 Costos / Ganancias por Método</div>', unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(7, 3.5))
        fig_style(fig, ax)
        metodos = list(metodos_costo.keys())
        valores = list(metodos_costo.values())
        colores = ['#F5A800' if v == min(valores) else '#3B82F6' for v in valores]
        ax.barh(metodos, valores, color=colores, height=0.5)
        for i, (m, v) in enumerate(zip(metodos, valores)):
            ax.text(v + (max(valores)-min(valores))*0.02, i, f"{v:.6f}", va='center', color='white', fontsize=9)
        ax.set_xlabel("Costo / Ganancia esperado")
        ax.grid(True, axis="x", color="#1E2A3A", linewidth=0.5, alpha=0.6)
        st.pyplot(fig)

    # ── TARJETAS INDIVIDUALES ────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="section-label">RESUMEN</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📋 Detalles por Método</div>', unsafe_allow_html=True)

    iconos = {
        "Enumeración Exhaustiva": "🔍",
        "Programación Lineal": "📈",
        "Mejoramiento de Políticas": "🔄",
        "Mej. Políticas c/ Desc.": "💲",
        "Aproximaciones Sucesivas": "🔁",
    }

    cols = st.columns(len(resultados))
    for metodo, col in zip(resultados.keys(), cols):
        pol = resultados[metodo]
        det = detalles[metodo]
        ok = pol is not None
        nombre_pol = obtener_nombre(pol) if ok else "—"
        costo_nativo = det["costo"]
        iteraciones = det.get("iteraciones")
        extra = det.get("extra")
        clase_extra = "optimo" if ok and pol == politica_coincidencia else ("fallo" if not ok else "")

        politxt = (
            f"{nombre_pol} = ({', '.join([pol[s] for s in estados])})"
            if ok else "No disponible"
        )

        costo_html = ""
        if costo_nativo is not None:
            label = "Costo" if tipo == "costos" else "Ganancia"
            costo_html = f'<div class="cost-text">{label}: {costo_nativo:.6f}</div>'
        elif extra is not None:
            v_list = ", ".join(f"V{s}={extra[s]:.4f}" for s in estados)
            costo_html = f'<div class="cost-text">Valores V: {v_list}</div>'

        iter_html = (
            f'<div class="detail-text">Iteraciones: {iteraciones}</div>'
            if iteraciones not in (None, "—") else ""
        )

        badge = "✅ Coincide" if (ok and pol == politica_coincidencia) else ("❌ Difiere" if ok else "⚠️ Fallo")

        with col:
            st.markdown(f"""
            <div class="method-card {clase_extra}">
                <div class="method-icon">{iconos.get(metodo, '')}</div>
                <div class="method-name">{metodo}</div>
                <div class="policy-text">{politxt}</div>
                {costo_html}
                {iter_html}
            </div>
            """, unsafe_allow_html=True)
            st.write(badge)

    # ── CONSISTENCIA POR ESTADO ─────────────────────────────
    st.markdown('<div class="section-label">ANÁLISIS · ESTADOS</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🔬 Consistencia por Estado</div>', unsafe_allow_html=True)

    politicas_validas = {m: p for m, p in resultados.items() if p is not None}
    if politicas_validas:
        consistencia = []
        estados_conflicto = []
        for estado in estados:
            decisiones = {m: p[estado] for m, p in politicas_validas.items()}
            unicas = set(decisiones.values())
            consistente = len(unicas) == 1
            if not consistente:
                estados_conflicto.append(estado)
            fila = {"Estado": estado, "Consistente": "✅" if consistente else "❌"}
            for m, d in decisiones.items():
                fila[m] = d
            consistencia.append(fila)

        df_cons = pd.DataFrame(consistencia)
        st.dataframe(df_cons, use_container_width=True, hide_index=True)

        if not estados_conflicto:
            st.success("✅ Todos los métodos coinciden en la decisión para cada estado.")
        else:
            st.warning(f"⚠️ Conflicto en {len(estados_conflicto)} estado(s): " + ", ".join(estados_conflicto))
    else:
        st.info("No hay políticas válidas para analizar consistencia.")
