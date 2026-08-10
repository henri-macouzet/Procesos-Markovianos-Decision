"""
modulos/inicio.py
Página de inicio (Panel Principal) de la aplicación Herramienta MDP.
"""

import streamlit as st
from guardado.sesion import get_mdp, mdp_completo

st.set_page_config(page_title="Inicio — Herramienta MDP", page_icon="🎓")

# ---------- ESTILOS ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Sora:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Sora', sans-serif; }
.main .block-container { padding-top: 2rem; max-width: 1100px; }
.unam-card { background:#111827; border:1px solid #1E2A3A; border-radius:12px; padding:1.5rem; margin-bottom:1rem; }
.badge-ok { display:inline-flex; align-items:center; gap:4px; background:rgba(16,185,129,.12); border:1px solid rgba(16,185,129,.3); color:#10B981; font-size:.75rem; font-family:'Sora',sans-serif; padding:2px 10px; border-radius:20px; }
.badge-warn { display:inline-flex; align-items:center; gap:4px; background:rgba(245,168,0,.12); border:1px solid rgba(245,168,0,.3); color:#F5A800; font-size:.75rem; font-family:'Sora',sans-serif; padding:2px 10px; border-radius:20px; }
hr { border-color:#1E2A3A; margin:1.5rem 0; }
.team-card {
    background: linear-gradient(145deg, #0D1321 0%, #0A0E1A 100%);
    border: 1px solid #1E2A3A;
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 2rem;
}
.intro-text {
    color: #B0C0D0;
    line-height: 1.6;
    font-size: 0.95rem;
}
</style>
""", unsafe_allow_html=True)

mdp = get_mdp()

# ---------- ENCABEZADO PRINCIPAL ----------
st.markdown("""
<div style="margin-bottom: 2rem;">
    <div style="font-family:'IBM Plex Mono',monospace; font-size:0.75rem;
                color:#F5A800; letter-spacing:0.15em; margin-bottom:0.5rem;">
        PROCESOS MARKOVIANOS DE DECISIÓN
    </div>
    <h1 style="font-family:'Sora',sans-serif; font-weight:700; font-size:2.2rem;
               color:#E8EAF0; margin:0 0 0.5rem 0; line-height:1.2;">
        Herramienta MDP
    </h1>
    <p style="color:#8FA0B8; font-size:1rem; margin:0; max-width:600px;">
        Modelado y solución de Procesos Markovianos de Decisión.
    </p>
</div>
""", unsafe_allow_html=True)

# ---------- TARJETA DE PRESENTACIÓN ----------
st.markdown("""
<div class="team-card">
    <div style="display:flex; flex-wrap:wrap; gap:2rem; align-items:flex-start;">
        <div style="flex:1; min-width:200px;">
            <div style="font-family:'IBM Plex Mono',monospace; font-size:0.7rem; color:#F5A800; letter-spacing:0.1em; margin-bottom:0.75rem;">
                🎓 FACULTAD
            </div>
            <div style="color:#E8EAF0; font-weight:600; margin-bottom:0.25rem;">FES Acatlán</div>
            <div style="color:#8FA0B8; font-size:0.9rem;">UNAM</div>
        </div>
        <div style="flex:1; min-width:200px;">
            <div style="font-family:'IBM Plex Mono',monospace; font-size:0.7rem; color:#F5A800; letter-spacing:0.1em; margin-bottom:0.75rem;">
                👩‍🏫 PROFESORA
            </div>
            <div style="color:#E8EAF0; font-weight:600; margin-bottom:0.25rem;">Cuéllar Aguayo Ada Ruth</div>
            <div style="color:#8FA0B8; font-size:0.9rem;">Procesos Estocásticos</div>
        </div>
        <div style="flex:2; min-width:250px;">
            <div style="font-family:'IBM Plex Mono',monospace; font-size:0.7rem; color:#F5A800; letter-spacing:0.1em; margin-bottom:0.75rem;">
                👥 INTEGRANTES
            </div>
            <div style="display:flex; flex-wrap:wrap; gap:0.5rem 1.5rem;">
                <div style="color:#E8EAF0;">• Hernández Pérez Victoria</div>
                <div style="color:#E8EAF0;">• Martínez Macouzet Enrique</div>            
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------- INTRODUCCIÓN A LOS MDP ----------
with st.expander("📘 ¿Qué son los Procesos Markovianos de Decisión?", expanded=False):
    st.markdown("""
    <div class="intro-text">
    <p>Un <strong>Proceso Markoviano de Decisión (MDP)</strong> es un modelo matemático para la toma de decisiones 
    secuenciales en entornos donde los resultados son parcialmente aleatorios y parcialmente controlados por un 
    agente decisor.</p>
    
    <p>Un MDP se define mediante:</p>
    <ul>
        <li><strong>Estados</strong> — representan las situaciones posibles del sistema.</li>
        <li><strong>Decisiones</strong> — acciones que el agente puede tomar en cada estado.</li>
        <li><strong>Matriz de transición</strong> — probabilidades de pasar de un estado a otro bajo cada decisión.</li>
        <li><strong>Costos / Ganancias</strong> — valor inmediato asociado a cada transición.</li>
    </ul>
    
    <p>El objetivo es encontrar una <strong>política óptima</strong> (regla que indica qué decisión tomar en cada estado) 
    que minimice el costo total esperado o maximice la ganancia total esperada a lo largo del tiempo.</p>
    
    <p>Los MDP tienen aplicaciones en robótica, finanzas, logística, inteligencia artificial, entre muchas otras áreas.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ---------- RESUMEN DEL MODELO ----------
col1, col2, col3, col4 = st.columns(4)

with col1:
    n_estados = len(mdp["estados"])
    st.markdown(f"""
    <div class="unam-card" style="text-align:center;">
        <div style="font-size:2rem; font-weight:700; color:#F5A800;
                    font-family:'IBM Plex Mono',monospace;">{n_estados}</div>
        <div style="color:#8FA0B8; font-size:0.8rem; margin-top:4px;">Estados</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    n_dec = len(mdp["decisiones"])
    st.markdown(f"""
    <div class="unam-card" style="text-align:center;">
        <div style="font-size:2rem; font-weight:700; color:#003F8A;
                    font-family:'IBM Plex Mono',monospace;
                    -webkit-text-stroke: 1px #0056C7; color:#5B9BD5;">{n_dec}</div>
        <div style="color:#8FA0B8; font-size:0.8rem; margin-top:4px;">Decisiones</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    tipo = mdp.get("tipo", "costos").capitalize()
    st.markdown(f"""
    <div class="unam-card" style="text-align:center;">
        <div style="font-size:1.1rem; font-weight:600; color:#E8EAF0;
                    font-family:'Sora',sans-serif; margin-top:6px;">{tipo}</div>
        <div style="color:#8FA0B8; font-size:0.8rem; margin-top:4px;">Tipo de modelo</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    listo = mdp_completo()
    badge = '<span class="badge-ok">● Listo</span>' if listo else '<span class="badge-warn">● Incompleto</span>'
    st.markdown(f"""
    <div class="unam-card" style="text-align:center;">
        <div style="margin-top:8px;">{badge}</div>
        <div style="color:#8FA0B8; font-size:0.8rem; margin-top:6px;">Estado del modelo</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ---------- TARJETAS DE MÓDULOS ----------
st.markdown("### Módulos disponibles")

# Primera fila (5 tarjetas)
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown("""
    <div class="unam-card" style="border-left: 3px solid #3B82F6;">
        <div style="font-family:'Sora',sans-serif; font-weight:600; color:#E8EAF0; margin-bottom:6px;">
            📥 Ingreso de Datos
        </div>
        <div style="color:#8FA0B8; font-size:0.85rem;">
            Define los elementos del modelo: estados, decisiones, costos y transiciones.
        </div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="unam-card" style="border-left: 3px solid #0EA5E9;">
        <div style="font-family:'Sora',sans-serif; font-weight:600; color:#E8EAF0; margin-bottom:6px;">
            📂 Importar desde Excel
        </div>
        <div style="color:#8FA0B8; font-size:0.85rem;">
            Carga un modelo MDP desde un archivo Excel con el formato de la plantilla.
        </div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div class="unam-card" style="border-left: 3px solid #10B981;">
        <div style="font-family:'Sora',sans-serif; font-weight:600; color:#E8EAF0; margin-bottom:6px;">
            📊 Visualización
        </div>
        <div style="color:#8FA0B8; font-size:0.85rem;">
            Explora el modelo con tablas detalladas y un grafo interactivo.
        </div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown("""
    <div class="unam-card" style="border-left: 3px solid #8B5CF6;">
        <div style="font-family:'Sora',sans-serif; font-weight:600; color:#E8EAF0; margin-bottom:6px;">
            🔍 Enumeración Exhaustiva
        </div>
        <div style="color:#8FA0B8; font-size:0.85rem;">
            Evalúa todas las combinaciones posibles para hallar la política óptima.
        </div>
    </div>
    """, unsafe_allow_html=True)

with c5:
    st.markdown("""
    <div class="unam-card" style="border-left: 3px solid #F59E0B;">
        <div style="font-family:'Sora',sans-serif; font-weight:600; color:#E8EAF0; margin-bottom:6px;">
            📈 Programación Lineal
        </div>
        <div style="color:#8FA0B8; font-size:0.85rem;">
            Resuelve el MDP usando un modelo de programación lineal.
        </div>
    </div>
    """, unsafe_allow_html=True)


# Segunda fila (4 tarjetas)
c6, c7, c8, c9 = st.columns(4)

with c6:
    st.markdown("""
    <div class="unam-card" style="border-left: 3px solid #EF4444;">
        <div style="font-family:'Sora',sans-serif; font-weight:600; color:#E8EAF0; margin-bottom:6px;">
            🔄 Mejoramiento de Políticas
        </div>
        <div style="color:#8FA0B8; font-size:0.85rem;">
            Aplica el algoritmo iterativo de mejora de políticas.
        </div>
    </div>
    """, unsafe_allow_html=True)

with c7:
    st.markdown("""
    <div class="unam-card" style="border-left: 3px solid #EC4899;">
        <div style="font-family:'Sora',sans-serif; font-weight:600; color:#E8EAF0; margin-bottom:6px;">
            💲 Mej. Políticas c/ Descuento
        </div>
        <div style="color:#8FA0B8; font-size:0.85rem;">
            Mejoramiento de políticas con factor de descuento.
        </div>
    </div>
    """, unsafe_allow_html=True)

with c8:
    st.markdown("""
    <div class="unam-card" style="border-left: 3px solid #06B6D4;">
        <div style="font-family:'Sora',sans-serif; font-weight:600; color:#E8EAF0; margin-bottom:6px;">
            🔁 Aproximaciones Sucesivas
        </div>
        <div style="color:#8FA0B8; font-size:0.85rem;">
            Iteración de valores para encontrar la política óptima.
        </div>
    </div>
    """, unsafe_allow_html=True)

with c9:
    st.markdown("""
    <div class="unam-card" style="border-left: 3px solid #84CC16;">
        <div style="font-family:'Sora',sans-serif; font-weight:600; color:#E8EAF0; margin-bottom:6px;">
            ⚖️ Comparación de Métodos
        </div>
        <div style="color:#8FA0B8; font-size:0.85rem;">
            Reúne los resultados de todos los algoritmos aplicados.
        </div>
    </div>
    """, unsafe_allow_html=True)


# Tercera fila (2 tarjetas) 
c10, c11 = st.columns(2)
with c10:
    st.markdown("""
    <div class="unam-card" style="border-left: 3px solid #F5A800;">
        <div style="font-family:'Sora',sans-serif; font-weight:600; color:#E8EAF0; margin-bottom:6px;">
            📤 Exportar a Excel
        </div>
        <div style="color:#8FA0B8; font-size:0.85rem;">
            Descarga el modelo y las soluciones en un libro de Excel.
        </div>
    </div>
    """, unsafe_allow_html=True)

with c11:
    st.markdown("""
    <div class="unam-card" style="border-left: 3px solid #A855F7; text-align: center;">
        <div style="font-family:'Sora',sans-serif; font-weight:600; color:#E8EAF0; margin-bottom:6px;">
            🙏 Agradecimientos
        </div> 
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div style="margin-top:2rem; padding:1rem; background:#111827;
            border-radius:8px; border:1px solid #1E2A3A;">
    <div style="font-family:'IBM Plex Mono',monospace; font-size:0.72rem;
                color:#8FA0B8; letter-spacing:0.05em;">
        Usa el menú lateral para navegar entre módulos.
        Los datos se conservan durante toda la sesión.
    </div>
</div>
""", unsafe_allow_html=True)
