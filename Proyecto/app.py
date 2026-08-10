"""
app.py
Punto de entrada principal de la aplicacion Herramienta MDP.
Configura la pagina, aplica estilos globales, define la navegacion y la barra lateral.
La sesion del usuario se inicializa desde guardado.sesion.
"""

import streamlit as st
from guardado.sesion import init_session

# Configuracion inicial de la pagina
st.set_page_config(
    page_title="Herramienta MDP · FES Acatlán",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar el estado de sesion (modelo MDP)
init_session()

# ---------- ESTILOS CSS GLOBALES ----------
# Se define el tema visual UNAM (azul marino y dorado) para toda la aplicacion.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Sora:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Sora', sans-serif;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D1321 0%, #0A0E1A 100%);
    border-right: 1px solid #1E2A3A;
}

[data-testid="stSidebarNav"] a {
    font-family: 'Sora', sans-serif;
    font-size: 0.875rem;
    letter-spacing: 0.02em;
    color: #8FA0B8 !important;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    transition: all 0.2s ease;
}
[data-testid="stSidebarNav"] a:hover,
[data-testid="stSidebarNav"] a[aria-current="page"] {
    color: #F5A800 !important;
    background: rgba(245, 168, 0, 0.08) !important;
}

.main .block-container {
    padding-top: 2rem;
    max-width: 1100px;
}

.unam-card {
    background: #111827;
    border: 1px solid #1E2A3A;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}

.section-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1.25rem;
}
.section-header .accent-bar {
    width: 4px;
    height: 28px;
    background: linear-gradient(180deg, #F5A800, #003F8A);
    border-radius: 2px;
    flex-shrink: 0;
}
.section-header h3 {
    margin: 0;
    font-family: 'Sora', sans-serif;
    font-size: 1rem;
    font-weight: 600;
    color: #E8EAF0;
    letter-spacing: 0.03em;
}

div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.85rem;
    background: #0A0E1A !important;
    border-color: #1E2A3A !important;
}
div[data-baseweb="input"] input:focus,
div[data-baseweb="textarea"] textarea:focus {
    border-color: #F5A800 !important;
    box-shadow: 0 0 0 1px #F5A800 !important;
}

div[data-testid="stNumberInput"] input {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.9rem;
    text-align: center;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #F5A800, #E09600) !important;
    color: #0A0E1A !important;
    font-family: 'Sora', sans-serif;
    font-weight: 600;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1.5rem;
    transition: all 0.2s ease;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(245, 168, 0, 0.3);
}

.stButton > button {
    font-family: 'Sora', sans-serif;
    border-radius: 8px;
    border-color: #1E2A3A;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    border-color: #F5A800;
    color: #F5A800;
}

[data-testid="stTabs"] [data-baseweb="tab"] {
    font-family: 'Sora', sans-serif;
    font-size: 0.875rem;
    color: #8FA0B8;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: #F5A800 !important;
    border-bottom-color: #F5A800 !important;
}

.chip {
    display: inline-block;
    background: rgba(0, 63, 138, 0.3);
    border: 1px solid rgba(0, 63, 138, 0.6);
    color: #7EB3FF;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    padding: 2px 10px;
    border-radius: 20px;
    margin: 2px;
}
.chip-gold {
    background: rgba(245, 168, 0, 0.12);
    border: 1px solid rgba(245, 168, 0, 0.4);
    color: #F5A800;
}

.badge-ok {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: #10B981;
    font-size: 0.75rem;
    font-family: 'Sora', sans-serif;
    padding: 2px 10px;
    border-radius: 20px;
}
.badge-warn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(245, 168, 0, 0.12);
    border: 1px solid rgba(245, 168, 0, 0.3);
    color: #F5A800;
    font-size: 0.75rem;
    font-family: 'Sora', sans-serif;
    padding: 2px 10px;
    border-radius: 20px;
}
.badge-err {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(239, 68, 68, 0.12);
    border: 1px solid rgba(239, 68, 68, 0.3);
    color: #EF4444;
    font-size: 0.75rem;
    font-family: 'Sora', sans-serif;
    padding: 2px 10px;
    border-radius: 20px;
}

[data-testid="stDataFrame"] {
    font-family: 'IBM Plex Mono', monospace;
}

hr {
    border-color: #1E2A3A;
    margin: 1.5rem 0;
}

.mono {
    font-family: 'IBM Plex Mono', monospace;
}

[data-testid="stAlert"] {
    border-radius: 8px;
    font-family: 'Sora', sans-serif;
    font-size: 0.875rem;
}
</style>
""", unsafe_allow_html=True)

# ---------- BARRA LATERAL (MARCA Y LOGOTIPO) ----------
with st.sidebar:
    st.markdown("""
    <div style="padding: 1rem 0 1.5rem 0; border-bottom: 1px solid #1E2A3A; margin-bottom: 1rem;">
        <div style="display:flex; align-items:center; gap:12px;">
            <div style="width:36px; height:36px; background:linear-gradient(135deg,#003F8A,#0056C7);
                        border-radius:8px; display:flex; align-items:center; justify-content:center;
                        font-size:1.1rem;">🎓</div>
            <div>
                <div style="font-family:'Sora',sans-serif; font-weight:700; font-size:0.95rem;
                            color:#E8EAF0; letter-spacing:0.05em;">HERRAMIENTA MDP</div>
                <div style="font-family:'IBM Plex Mono',monospace; font-size:0.65rem;
                            color:#F5A800; letter-spacing:0.1em;">FES ACATLÁN · UNAM</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------- NAVEGACION ENTRE PAGINAS ----------
# Se definen las paginas disponibles en la aplicacion.
# La navegacion se gestiona con el componente nativo st.navigation.

pg = st.navigation(
    {
        "Inicio": [
            st.Page("modulos/inicio.py", title="Panel Principal", icon="🎓")
        ],
        "Módulos": [
            st.Page("modulos/ingreso_datos.py", title="Ingreso de Datos", icon="📥"),
            st.Page("modulos/importar_excel.py", title="Importar desde Excel", icon="📂"),
            st.Page("modulos/visualizacion.py", title="Visualización", icon="📊"),
            st.Page("modulos/enumeracion_exhaustiva.py", title="Enumeración Exhaustiva", icon="🔍"),
            st.Page("modulos/programacion_lineal.py", title="Programación Lineal", icon="📈"),
            st.Page("modulos/mejoramiento_politicas.py", title="Mejoramiento de Políticas", icon="🔄"),
            st.Page("modulos/mejoramiento_politicas_descuento.py", title="Mej. de Políticas c/ Desc.", icon="💲"),
            st.Page("modulos/aproximaciones_sucesivas.py", title="Aproximaciones Sucesivas", icon="🔁"),
            st.Page("modulos/comparacion_metodos.py", title="Comparación de Métodos", icon="⚖️"),
            st.Page("modulos/exportar_excel.py", title="Exportar a Excel", icon="📤"),
            st.Page("modulos/agradecimientos.py", title="Agradecimientos", icon="🙏")            
        ]
    }
)
pg.run()
