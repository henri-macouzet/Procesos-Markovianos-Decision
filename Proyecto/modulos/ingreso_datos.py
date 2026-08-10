"""
modulos/ingreso_datos.py
Interfaz para definir los componentes del MDP: estados, decisiones, costos/ganancias y matrices de transición.

Características:
- Selección del tipo de modelo (costos o ganancias).
- Ingreso de nombres de estados y decisiones mediante texto separado por comas.
- Configuración por decisión: estados afectados, costos/ganancias y probabilidades de transición.
- Acepta fracciones (ej. 1/3) en los campos numéricos.
- Validación visual de que cada fila de transición sume 1.0.
- Botones para guardar (validar) y limpiar todo el modelo.
"""

import streamlit as st
from guardado.sesion import get_mdp, reset_mdp, mdp_completo, init_session
from fractions import Fraction

# Inicializar la sesión para acceder al modelo
init_session()
mdp = get_mdp()

# ---------- ESTILOS LOCALES ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Sora:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Sora', sans-serif; }
.main .block-container { padding-top: 2rem; max-width: 1100px; }
.unam-card { background:#111827; border:1px solid #1E2A3A; border-radius:12px; padding:1.5rem; margin-bottom:1rem; }
.section-header { display:flex; align-items:center; gap:.75rem; margin-bottom:1.25rem; }
.section-header .accent-bar { width:4px; height:28px; background:linear-gradient(180deg,#F5A800,#003F8A); border-radius:2px; flex-shrink:0; }
.section-header h3 { margin:0; font-family:'Sora',sans-serif; font-size:1rem; font-weight:600; color:#E8EAF0; letter-spacing:.03em; }
div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea { font-family:'IBM Plex Mono',monospace !important; font-size:.85rem; background:#0A0E1A !important; border-color:#1E2A3A !important; }
div[data-baseweb="input"] input:focus { border-color:#F5A800 !important; box-shadow:0 0 0 1px #F5A800 !important; }
.stButton > button[kind="primary"] { background:linear-gradient(135deg,#F5A800,#E09600) !important; color:#0A0E1A !important; font-family:'Sora',sans-serif; font-weight:600; border:none; border-radius:8px; }
.stButton > button { font-family:'Sora',sans-serif; border-radius:8px; }
[data-testid="stTabs"] [data-baseweb="tab"] { font-family:'Sora',sans-serif; font-size:.875rem; color:#8FA0B8; }
[data-testid="stTabs"] [aria-selected="true"] { color:#F5A800 !important; border-bottom-color:#F5A800 !important; }
.chip { display:inline-block; background:rgba(0,63,138,.3); border:1px solid rgba(0,63,138,.6); color:#7EB3FF; font-family:'IBM Plex Mono',monospace; font-size:.78rem; padding:2px 10px; border-radius:20px; margin:2px; }
.badge-ok { display:inline-flex; align-items:center; gap:4px; background:rgba(16,185,129,.12); border:1px solid rgba(16,185,129,.3); color:#10B981; font-size:.75rem; padding:2px 10px; border-radius:20px; }
.badge-warn { display:inline-flex; align-items:center; gap:4px; background:rgba(245,168,0,.12); border:1px solid rgba(245,168,0,.3); color:#F5A800; font-size:.75rem; padding:2px 10px; border-radius:20px; }
.badge-err { display:inline-flex; align-items:center; gap:4px; background:rgba(239,68,68,.12); border:1px solid rgba(239,68,68,.3); color:#EF4444; font-size:.75rem; padding:2px 10px; border-radius:20px; }
hr { border-color:#1E2A3A; margin:1.5rem 0; }
</style>
""", unsafe_allow_html=True)

# ---------- FUNCIONES AUXILIARES PARA MANEJO DE NÚMEROS ----------
def evaluar_numero(valor_str: str, valor_actual: float = 0.0, permitir_fraccion: bool = True) -> float:
    """
    Convierte una cadena de texto en un número flotante.
    Acepta fracciones escritas como '1/3' y decimales.

    Args:
        valor_str (str): Texto ingresado por el usuario.
        valor_actual (float): Valor por defecto si la cadena está vacía o es inválida.
        permitir_fraccion (bool): Si es True, interpreta el símbolo '/'.

    Returns:
        float: Número evaluado, o valor_actual en caso de error.
    """
    if not valor_str.strip():
        return valor_actual
    try:
        if permitir_fraccion and '/' in valor_str:
            num, den = valor_str.split('/')
            return float(num) / float(den)
        else:
            return float(valor_str)
    except (ValueError, ZeroDivisionError):
        st.warning(f"Valor inválido '{valor_str}'. Se usará {valor_actual}")
        return valor_actual

def formatear_numero(valor: float) -> str:
    """
    Convierte un flotante a una cadena legible.
    Si el valor es cercano a cero, retorna cadena vacía.
    Si es una fracción exacta (denominador <= 1000), la muestra como 'num/den'.

    Args:
        valor (float): Número a formatear.

    Returns:
        str: Representación en texto.
    """
    if abs(valor) < 1e-12:
        return ""
    frac = Fraction(valor).limit_denominator(1000)
    if frac.denominator == 1:
        return str(frac.numerator)
    else:
        return f"{frac.numerator}/{frac.denominator}"

# ---------- ENCABEZADO ----------
st.markdown("""
<div style="margin-bottom:1.5rem;">
    <div style="font-family:'IBM Plex Mono',monospace;font-size:.72rem;color:#F5A800;letter-spacing:.15em;margin-bottom:.4rem;">MÓDULO 01</div>
    <h1 style="font-family:'Sora',sans-serif;font-weight:700;font-size:1.8rem;color:#E8EAF0;margin:0;">Ingreso de Datos</h1>
    <p style="color:#8FA0B8;font-size:.9rem;margin:.4rem 0 0 0;">Define los elementos del modelo: estados, decisiones, costos y transiciones.</p>
</div>
""", unsafe_allow_html=True)

# ---------- SECCIÓN 1: ESTADOS Y DECISIONES ----------
st.markdown("""
<div class="section-header">
    <div class="accent-bar"></div>
    <h3>1 · Estados y Decisiones</h3>
</div>
""", unsafe_allow_html=True)

col_tipo, col_est, col_dec = st.columns([1, 2, 2])

with col_tipo:
    tipo_actual = mdp.get("tipo", "costos")
    tipo = st.radio(
        "Tipo de modelo",
        ["costos", "ganancias"],
        index=0 if tipo_actual == "costos" else 1,
        format_func=lambda x: "Costos (minimizar)" if x == "costos" else "Ganancias (maximizar)",
        help="Define si el objetivo es minimizar costos o maximizar ganancias."
    )
    mdp["tipo"] = tipo

with col_est:
    estados_str = st.text_input(
        "Estados del sistema",
        value=", ".join(mdp["estados"]) if mdp["estados"] else "",
        placeholder="s0, s1, s2, ...",
        help="Ingresa los nombres de los estados separados por comas."
    )
    if estados_str.strip():
        nuevos_estados = [s.strip() for s in estados_str.split(",") if s.strip()]
        if nuevos_estados != mdp["estados"]:
            # Limpiar datos de estados eliminados en todas las decisiones
            eliminados = set(mdp["estados"]) - set(nuevos_estados)
            for estado in eliminados:
                for d, data in mdp["decisiones_data"].items():
                    if estado in data["estados_afectados"]:
                        data["estados_afectados"].remove(estado)
                    data["costos"].pop(estado, None)
                    data["transiciones"].pop(estado, None)
                    for origen in data["transiciones"]:
                        data["transiciones"][origen].pop(estado, None)
            mdp["estados"] = nuevos_estados

    if mdp["estados"]:
        chips = " ".join([f'<span class="chip">{s}</span>' for s in mdp["estados"]])
        st.markdown(f'<div style="margin-top:.5rem;">{chips}</div>', unsafe_allow_html=True)

with col_dec:
    decisiones_str = st.text_input(
        "Decisiones posibles",
        value=", ".join(mdp["decisiones"]) if mdp["decisiones"] else "",
        placeholder="d0, d1, d2, ...",
        help="Ingresa las decisiones posibles separadas por comas."
    )
    if decisiones_str.strip():
        nuevas_dec = [d.strip() for d in decisiones_str.split(",") if d.strip()]
        if nuevas_dec != mdp["decisiones"]:
            # Agregar nuevas decisiones con estructura vacía
            for d in nuevas_dec:
                if d not in mdp["decisiones_data"]:
                    mdp["decisiones_data"][d] = {
                        "estados_afectados": [],
                        "costos": {},
                        "transiciones": {}
                    }
            # Eliminar decisiones que ya no están
            for d in list(mdp["decisiones_data"].keys()):
                if d not in nuevas_dec:
                    del mdp["decisiones_data"][d]
            mdp["decisiones"] = nuevas_dec

    if mdp["decisiones"]:
        chips = " ".join([f'<span class="chip" style="background:rgba(245,168,0,.1);border-color:rgba(245,168,0,.4);color:#F5A800;">{d}</span>' for d in mdp["decisiones"]])
        st.markdown(f'<div style="margin-top:.5rem;">{chips}</div>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ---------- SECCIÓN 2: CONFIGURACIÓN POR DECISIÓN ----------
if not mdp["estados"] or not mdp["decisiones"]:
    st.markdown("""
    <div style="text-align:center;padding:3rem;color:#8FA0B8;">
        <div style="font-size:2rem;margin-bottom:.5rem;">⚙️</div>
        <div style="font-family:'Sora',sans-serif;">Ingresa estados y decisiones para continuar.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

st.markdown("""
<div class="section-header">
    <div class="accent-bar"></div>
    <h3>2 · Configuración por Decisión</h3>
</div>
""", unsafe_allow_html=True)

tabs = st.tabs([f"  {d}  " for d in mdp["decisiones"]])

for tab, d in zip(tabs, mdp["decisiones"]):
    with tab:
        data = mdp["decisiones_data"][d]

        # --- Estados afectados ---
        st.markdown(f"""
        <div style="font-family:'IBM Plex Mono',monospace;font-size:.75rem;color:#8FA0B8;
                    letter-spacing:.08em;margin-bottom:.75rem;">
            ESTADOS AFECTADOS POR <span style="color:#F5A800;">{d}</span>
        </div>
        """, unsafe_allow_html=True)

        afectados = st.multiselect(
            "Selecciona los estados en los que aplica esta decisión",
            options=mdp["estados"],
            default=[s for s in data.get("estados_afectados", []) if s in mdp["estados"]],
            key=f"afect_{d}",
            label_visibility="collapsed"
        )
        data["estados_afectados"] = afectados

        if not afectados:
            st.info("Selecciona al menos un estado para continuar con esta decisión.")
            continue

        st.markdown("<hr>", unsafe_allow_html=True)

        col_costos, col_trans = st.columns([1, 2])

        # --- Costos / Ganancias ---
        with col_costos:
            tipo_label = "Costo" if mdp["tipo"] == "costos" else "Ganancia"
            st.markdown(f"""
            <div style="font-family:'IBM Plex Mono',monospace;font-size:.75rem;color:#8FA0B8;
                        letter-spacing:.08em;margin-bottom:.75rem;">
                {tipo_label.upper()}S
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="background:#0A0E1A;border:1px solid #1E2A3A;border-radius:8px;padding:.75rem;
                        margin-bottom:1rem;font-size:.78rem;color:#8FA0B8;font-family:'Sora',sans-serif;">
                Ingresa el {tipo_label.lower()} de estar en cada estado y aplicar la decisión <b style="color:#F5A800;">{d}</b>.
            </div>
            """, unsafe_allow_html=True)

            for s in afectados:
                current = data["costos"].get(s, 0.0)
                default_str = formatear_numero(current)
                val_str = st.text_input(
                    f"{tipo_label} en {s} con {d}",
                    value=default_str,
                    key=f"costo_{d}_{s}",
                    placeholder="0.0"
                )
                val = evaluar_numero(val_str, current, permitir_fraccion=True)
                data["costos"][s] = val

        # --- Matriz de transición ---
        with col_trans:
            st.markdown(f"""
            <div style="font-family:'IBM Plex Mono',monospace;font-size:.75rem;color:#8FA0B8;
                        letter-spacing:.08em;margin-bottom:.75rem;">
                MATRIZ DE TRANSICIÓN
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="background:#0A0E1A;border:1px solid #1E2A3A;border-radius:8px;padding:.75rem;
                        margin-bottom:1rem;font-size:.78rem;color:#8FA0B8;font-family:'Sora',sans-serif;">
                Para cada estado origen <b style="color:#E8EAF0;">s</b>, ingresa las probabilidades de 
                transición hacia cada estado destino <b style="color:#E8EAF0;">s'</b>.
                Cada fila debe sumar <b style="color:#10B981;">1.0</b>. Acepta fracciones (ej. 1/3).
            </div>
            """, unsafe_allow_html=True)

            todos_estados = mdp["estados"]

            for s in afectados:
                if s not in data["transiciones"]:
                    data["transiciones"][s] = {}

                fila = data["transiciones"][s]

                st.markdown(f"""
                <div style="font-family:'IBM Plex Mono',monospace;font-size:.8rem;
                            color:#E8EAF0;margin:.75rem 0 .4rem 0;">
                    Desde <span style="color:#F5A800;">{s}</span> →
                </div>
                """, unsafe_allow_html=True)

                # Encabezados de columna (estados destino)
                header_cols = st.columns(len(todos_estados))
                for col_i, s2 in zip(header_cols, todos_estados):
                    with col_i:
                        st.markdown(f"<div style='text-align:center;color:#8FA0B8;font-size:0.7rem;'>{s2}</div>", unsafe_allow_html=True)

                # Campos de entrada de probabilidad
                input_cols = st.columns(len(todos_estados))
                fila_sum = 0.0
                for col_i, s2 in zip(input_cols, todos_estados):
                    with col_i:
                        current_p = fila.get(s2, 0.0)
                        default_str = formatear_numero(current_p)
                        p_str = st.text_input(
                            f"→{s2}",
                            value=default_str,
                            key=f"trans_{d}_{s}_{s2}",
                            placeholder="0",
                            label_visibility="collapsed"
                        )
                        p = evaluar_numero(p_str, current_p, permitir_fraccion=True)
                        p = max(0.0, min(1.0, p))   # Acotar entre 0 y 1
                        fila[s2] = p
                        fila_sum += p

                # Validación de suma
                diff = abs(fila_sum - 1.0)
                if diff < 1e-6:
                    st.markdown('<span class="badge-ok">Suma = 1.0000</span>', unsafe_allow_html=True)
                elif fila_sum == 0.0:
                    st.markdown('<span class="badge-warn">Sin ingresar</span>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<span class="badge-err">Suma = {fila_sum:.4f} (debe ser 1.0)</span>', unsafe_allow_html=True)

# ---------- SECCIÓN 3: GUARDAR / REINICIAR ----------
st.markdown("<hr>", unsafe_allow_html=True)

listo = mdp_completo()

col_save, col_reset, col_status = st.columns([2, 1, 3])

with col_save:
    if st.button("Guardar datos del sistema", type="primary", use_container_width=True):
        if listo:
            st.success("Datos guardados correctamente. Puedes ir al módulo de Visualización.")
        else:
            st.warning("El modelo tiene datos incompletos. Revisa que todas las filas de transición sumen 1.0 y que cada estado afectado tenga un costo/ganancia asignado.")

with col_reset:
    if st.button("Limpiar todo", use_container_width=True):
        reset_mdp()
        st.rerun()

with col_status:
    if listo:
        st.markdown('<div style="padding:.5rem 0;"><span class="badge-ok">Modelo completo y válido</span></div>', unsafe_allow_html=True)
    else:
        missing = []
        if not mdp["estados"]:
            missing.append("estados")
        if not mdp["decisiones"]:
            missing.append("decisiones")
        else:
            for d in mdp["decisiones"]:
                data = mdp["decisiones_data"].get(d, {})
                afectados = data.get("estados_afectados", [])
                if not afectados:
                    missing.append(f"estados de {d}")
                    continue
                for s in afectados:
                    if s not in data.get("costos", {}):
                        missing.append(f"costo({s},{d})")
                    probs = data.get("transiciones", {}).get(s, {})
                    total = sum(probs.values())
                    if abs(total - 1.0) > 1e-6:
                        missing.append(f"P(·|{s},{d})")
        if missing:
            st.markdown(f'<div style="padding:.5rem 0;font-size:.8rem;color:#8FA0B8;">Pendiente: {", ".join(missing[:4])}{"..." if len(missing)>4 else ""}</div>', unsafe_allow_html=True)
