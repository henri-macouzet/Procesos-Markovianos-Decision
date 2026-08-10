"""
modulos/visualizacion.py
Muestra tablas resumen de costos/ganancias y matrices de transición del MDP ingresado,
así como un grafo interactivo por decisión que utiliza Cytoscape.js.

La visualización se organiza en:
- Resumen general (número de estados, decisiones, objetivo).
- Tabla consolidada de costos/ganancias para todos los pares (estado, decisión).
- Matriz de transición de la decisión seleccionada mediante un selectbox.
- Grafo dirigido de la misma decisión, con nodos destacados (afectados vs no afectados)
  y aristas coloreadas según dirección (estándar vs inversa).
"""

import streamlit as st
import pandas as pd
import json
import math
from guardado.sesion import get_mdp

# ---------- ESTILOS MÍNIMOS ----------
st.markdown("""
<style>
#cy {
    border-radius: 12px;
    border: 1px solid #1E2A3A;
}
</style>
""", unsafe_allow_html=True)

mdp = get_mdp()

# ---------- ENCABEZADO ----------
st.markdown("""
<div style="margin-bottom:1.5rem;">
    <div style="font-family:'IBM Plex Mono',monospace;font-size:.72rem;color:#F5A800;letter-spacing:.15em;margin-bottom:.4rem;">MÓDULO 02</div>
    <h1 style="font-family:'Sora',sans-serif;font-weight:700;font-size:1.8rem;color:#E8EAF0;margin:0;">Visualización del Modelo</h1>
<p style="color:#8FA0B8;font-size:.9rem;margin:.4rem 0 0 0;">Explora el modelo con tablas detalladas y un grafo interactivo.</p>
</div>
""", unsafe_allow_html=True)

# Verificar que existan datos mínimos
if not mdp["estados"] or not mdp["decisiones"]:
    st.markdown("""
    <div style="text-align:center;padding:4rem;color:#8FA0B8;">
        <div style="font-size:2.5rem;margin-bottom:1rem;">📭</div>
        <div style="font-family:'Sora',sans-serif;font-size:1.1rem;margin-bottom:.5rem;">No hay datos ingresados.</div>
        <div style="font-size:.85rem;">Ve al módulo de <b>Ingreso de Datos</b> para comenzar.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

estados = mdp["estados"]
decisiones = mdp["decisiones"]
tipo = mdp["tipo"]
tipo_label = "Costo" if tipo == "costos" else "Ganancia"

# ---------- RESUMEN GENERAL ----------
st.markdown("""
<div class="section-header">
    <div class="accent-bar"></div>
    <h3>Resumen General</h3>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="unam-card">
        <div style="font-family:'IBM Plex Mono',monospace;font-size:.7rem;color:#8FA0B8;letter-spacing:.1em;margin-bottom:.75rem;">ESTADOS · {len(estados)}</div>
        {''.join([f'<span class="chip">{s}</span>' for s in estados])}
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="unam-card">
        <div style="font-family:'IBM Plex Mono',monospace;font-size:.7rem;color:#8FA0B8;letter-spacing:.1em;margin-bottom:.75rem;">DECISIONES · {len(decisiones)}</div>
        {''.join([f'<span class="chip" style="background:rgba(245,168,0,.1);border-color:rgba(245,168,0,.4);color:#F5A800;">{d}</span>' for d in decisiones])}
    </div>
    """, unsafe_allow_html=True)

with col3:
    obj = "Minimizar costos" if tipo == "costos" else "Maximizar ganancias"
    icon = "💸" if tipo == "costos" else "💰"
    st.markdown(f"""
    <div class="unam-card">
        <div style="font-family:'IBM Plex Mono',monospace;font-size:.7rem;color:#8FA0B8;letter-spacing:.1em;margin-bottom:.75rem;">OBJETIVO</div>
        <div style="font-family:'Sora',sans-serif;font-size:1rem;font-weight:600;color:#E8EAF0;">{icon} {obj}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ---------- TABLA DE COSTOS / GANANCIAS ----------
st.markdown(f"""
<div class="section-header">
    <div class="accent-bar"></div>
    <h3>Tabla de {tipo_label}s</h3>
</div>
""", unsafe_allow_html=True)

costo_rows = []
for s in estados:
    row = {"Estado": s}
    for d in decisiones:
        data = mdp["decisiones_data"].get(d, {})
        if s in data.get("estados_afectados", []):
            row[d] = data["costos"].get(s, 0.0)
        else:
            row[d] = "—"
    costo_rows.append(row)

df_costos = pd.DataFrame(costo_rows).set_index("Estado")
st.dataframe(
    df_costos,
    use_container_width=True,
    height=min(50 + len(estados) * 38, 400)
)

st.markdown("<hr>", unsafe_allow_html=True)

# ---------- MATRIZ DE TRANSICIÓN Y GRAFO (SELECCIÓN ÚNICA) ----------
st.markdown("""
<div class="section-header">
    <div class="accent-bar"></div>
    <h3>Matriz de Transición</h3>
</div>
""", unsafe_allow_html=True)

# Selector de decisión
selected_d = st.selectbox(
    "Elegir decisión",
    decisiones,
    key="grafo_decision"
)

data = mdp["decisiones_data"].get(selected_d, {})
afectados = data.get("estados_afectados", [])

if not afectados:
    st.info(f"La decisión '{selected_d}' no tiene estados afectados asignados.")
else:
    # Construir matriz de transición para la decisión seleccionada
    rows = []
    valida = True
    for s in afectados:
        fila = data["transiciones"].get(s, {})
        row = {}
        total = 0.0
        for s2 in estados:
            p = fila.get(s2, 0.0)
            row[s2] = p
            total += p
        row["Σ"] = round(total, 6)
        if abs(total - 1.0) > 1e-6:
            valida = False
        rows.append({"Estado": s, **row})

    df_trans = pd.DataFrame(rows).set_index("Estado")

    def highlight_sum(val):
        """Resalta en verde la columna Σ si suma 1, en rojo si no."""
        if isinstance(val, float):
            if abs(val - 1.0) < 1e-6:
                return "color: #10B981; font-weight: 600;"
            elif val > 0:
                return "color: #EF4444;"
        return ""

    col_vis, col_info = st.columns([3, 1])

    with col_vis:
        styled_df = df_trans.style.map(highlight_sum, subset=["Σ"]).format("{:.4f}")
        st.dataframe(
            styled_df,
            use_container_width=True,
            height=min(50 + len(afectados) * 38, 350)
        )

    with col_info:
        st.markdown(f"""
        <div style="padding:.5rem 0;">
            <div style="font-family:'IBM Plex Mono',monospace;font-size:.7rem;color:#8FA0B8;
                        letter-spacing:.08em;margin-bottom:.75rem;">VALIDACIÓN</div>
        """, unsafe_allow_html=True)
        if valida:
            st.markdown('<span class="badge-ok">✓ Matriz válida</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span style="display:inline-flex;align-items:center;gap:4px;background:rgba(239,68,68,.12);border:1px solid rgba(239,68,68,.3);color:#EF4444;font-size:.75rem;padding:2px 10px;border-radius:20px;">✗ Filas inválidas</span>', unsafe_allow_html=True)

        st.markdown(f"""
        <div style="margin-top:1rem;font-size:.8rem;color:#8FA0B8;font-family:'Sora',sans-serif;">
            <div><b style="color:#E8EAF0;">{len(afectados)}</b> estados afectados</div>
            <div><b style="color:#E8EAF0;">{len(estados)}</b> estados destino</div>
        </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ---------- GRAFO CON CYTOSCAPE.JS ----------
    st.markdown("""
    <div class="section-header">
        <div class="accent-bar"></div>
        <h3>Grafo</h3>
    </div>
    """, unsafe_allow_html=True)

    # Construir elementos para Cytoscape
    nodes = []
    edges = []

    # Nodos: se marcan como 'affected' si el estado está en la lista de afectados
    for s in estados:
        is_affected = s in afectados
        nodes.append({
            "data": {"id": s},
            "classes": "affected" if is_affected else "normal"
        })

    # Aristas: solo se agregan aquellas con probabilidad > 0
    for s in afectados:
        fila = data["transiciones"].get(s, {})
        for s2, p in fila.items():
            if p > 1e-6:
                edges.append({
                    "data": {
                        "id": f"{s}->{s2}",
                        "source": s,
                        "target": s2,
                        "label": f"{p:.3f}"
                    }
                })

    # Detectar aristas bidireccionales para asignar color dorado a la segunda
    edge_list = list(edges)
    edge_map = {}
    for e in edge_list:
        key = (e["data"]["source"], e["data"]["target"])
        if key not in edge_map:
            edge_map[key] = []
        edge_map[key].append(e)

    for key, group in edge_map.items():
        if len(group) > 1:
            # Varias aristas entre el mismo par: la primera azul, la segunda dorada
            for i, e in enumerate(group):
                if i == 1:
                    e["data"]["color"] = "#F5A800"
                    e["data"]["targetArrowColor"] = "#F5A800"
                else:
                    e["data"]["color"] = "#5B9BD5"
                    e["data"]["targetArrowColor"] = "#5B9BD5"
        else:
            src, tgt = key
            opposite_key = (tgt, src)
            if opposite_key in edge_map:
                # Par bidireccional: según orden lexicográfico asigna color
                if src < tgt:
                    group[0]["data"]["color"] = "#5B9BD5"
                    group[0]["data"]["targetArrowColor"] = "#5B9BD5"
                else:
                    group[0]["data"]["color"] = "#F5A800"
                    group[0]["data"]["targetArrowColor"] = "#F5A800"
            else:
                # Sin opuesto: azul por defecto
                group[0]["data"]["color"] = "#5B9BD5"
                group[0]["data"]["targetArrowColor"] = "#5B9BD5"

    elements = nodes + edges
    elements_json = json.dumps(elements)

    # HTML + Cytoscape
    graph_html = f"""
    <div id="cy" style="width:100%; height:500px; background:#0A0E1A; border-radius:12px; border:1px solid #1E2A3A;"></div>

    <script src="https://unpkg.com/cytoscape@3.26.0/dist/cytoscape.min.js"></script>

    <script>
    const elements = {elements_json};

    const cy = cytoscape({{
        container: document.getElementById('cy'),
        elements: elements,
        style: [
            {{
                selector: 'node',
                style: {{
                    'background-color': '#0a1020',
                    'border-width': 2,
                    'border-color': '#1E3A5A',
                    'label': 'data(id)',
                    'color': '#8FA0B8',
                    'font-family': 'IBM Plex Mono, monospace',
                    'font-size': '13px',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'width': '52px',
                    'height': '52px'
                }}
            }},
            {{
                selector: 'node.affected',
                style: {{
                    'border-color': '#F5A800',
                    'color': '#F5A800',
                    'font-weight': 'bold'
                }}
            }},
            {{
                selector: 'edge',
                style: {{
                    'width': 2,
                    'line-color': 'data(color)',
                    'target-arrow-color': 'data(targetArrowColor)',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'control-point-step-size': 60,
                    'label': 'data(label)',
                    'font-family': 'IBM Plex Mono, monospace',
                    'font-size': '10px',
                    'color': '#E8EAF0',
                    'text-background-color': '#111827',
                    'text-background-opacity': 0.8,
                    'text-background-padding': '2px',
                    'text-background-shape': 'roundrectangle'
                }}
            }}
        ],
        layout: {{
            name: 'circle',
            fit: true,
            padding: 30
        }},
        userZoomingEnabled: true,
        userPanningEnabled: true,
        boxSelectionEnabled: false
    }});
    </script>
    """

    st.components.v1.html(graph_html, height=550)

    # Leyenda
    st.markdown(f"""
    <div style="display:flex;gap:1.5rem;margin-top:.5rem;font-size:.78rem;font-family:'Sora',sans-serif;color:#8FA0B8;">
        <span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#0a1020;border:2px solid #F5A800;margin-right:6px;"></span>Estado afectado</span>
        <span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#0a1020;border:2px solid #1E3A5A;margin-right:6px;"></span>Estado no afectado</span>
        <span><span style="color:#5B9BD5;">→</span> Transición estándar</span>
        <span><span style="color:#F5A800;">→</span> Transición inversa</span>
    </div>
    """, unsafe_allow_html=True)

# ---------- LISTADO DE POLÍTICAS ----------
st.markdown("---")
st.markdown("""
<div class="section-header">
    <div class="accent-bar"></div>
    <h3>Políticas del modelo</h3>
</div>
""", unsafe_allow_html=True)

with st.expander("Ver todas las políticas", expanded=False):
    from algoritmos.exhaustiva import generar_politicas
    politicas = generar_politicas(estados, mdp["decisiones_data"])
    if not politicas:
        st.write("No se pueden generar políticas (algún estado no tiene decisiones aplicables).")
    else:
        # Mostrar en 2 columnas para aprovechar espacio
        cols = st.columns(2)
        for i, pol in enumerate(politicas):
            nombre = f"R{i+1}"
            decisiones_str = ", ".join(pol[s] for s in estados)
            # Tarjeta estilizada
            with cols[i % 2]:
                st.markdown(f"""
                <div class="unam-card" style="padding:0.75rem 1rem; margin-bottom:0.5rem; border-left:3px solid #F5A800;">
                    <span style="font-family:'IBM Plex Mono',monospace; color:#F5A800; font-weight:600;">{nombre}</span>
                    <span style="font-family:'IBM Plex Mono',monospace; color:#B0C0D0; margin-left:0.5rem;">= ({decisiones_str})</span>
                </div>
                """, unsafe_allow_html=True)
