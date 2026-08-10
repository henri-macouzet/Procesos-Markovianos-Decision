"""
modulos/agradecimientos.py
Página de agradecimientos del proyecto Herramienta MDP.
"""

import streamlit as st

st.set_page_config(page_title="Agradecimientos — MDP", page_icon="🙏")

st.markdown("""
<style>
.thanks-card {
    background: linear-gradient(145deg, #0D1321 0%, #0A0E1A 100%);
    border: 1px solid #1E2A3A;
    border-radius: 16px;
    padding: 2rem;
    margin-bottom: 1.5rem;
    text-align: center;
}
.thanks-text {
    color: #B0C0D0;
    line-height: 1.8;
    font-size: 1rem;
}
.highlight {
    color: #F5A800;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="margin-bottom:1.5rem;">
    <div style="font-family:'IBM Plex Mono',monospace;font-size:.72rem;color:#F5A800;letter-spacing:.15em;margin-bottom:.4rem;">MÓDULO 10</div>
    <h1 style="font-family:'Sora',sans-serif;font-weight:700;font-size:1.8rem;color:#E8EAF0;margin:0;">Agradecimientos</h1>
</div>
""", unsafe_allow_html=True)

# Tarjeta principal de agradecimiento
st.markdown("""
<div class="thanks-card">
    <p class="thanks-text">
        <span class="highlight">Muchas gracias por su atención</span> 
    </p>
</div>
""", unsafe_allow_html=True)

# Animación de globos nativa de Streamlit
st.balloons()
