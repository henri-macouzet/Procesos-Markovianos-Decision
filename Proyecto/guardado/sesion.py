"""
guardado/sesion.py
Manejo del estado global del MDP durante la sesión de Streamlit.

Este módulo se encarga de:
- Inicializar el diccionario `mdp` en st.session_state.
- Proporcionar funciones para leer y modificar el modelo.
- Validar si el modelo está completo para ejecutar algoritmos.
- Ofrecer funciones auxiliares para agregar/eliminar estados y decisiones,
  así como para actualizar costos/ganancias y matrices de transición.

La estructura del estado `mdp` es:
{
    "estados": [str],                     # Lista de nombres de estados
    "decisiones": [str],                  # Lista de nombres de decisiones
    "tipo": "costos" | "ganancias",       # Objetivo del modelo
    "decisiones_data": {                  # Datos por decisión
        "d1": {
            "estados_afectados": [str],           # Estados donde aplica d1
            "costos": {estado: float},            # Costo/ganancia de aplicar d1 en ese estado
            "transiciones": {                     # Matriz de transición para d1
                estado_origen: {estado_destino: probabilidad}
            }
        },
        ...
    }
}
"""

import streamlit as st

# ----------------------------------------------------------------------
# Inicialización y acceso
# ----------------------------------------------------------------------

def init_session():
    """
    Inicializa la estructura del MDP en st.session_state si no existe.
    Se llama al comienzo de la aplicación y en cada módulo que accede al estado.
    """
    if "mdp" not in st.session_state:
        st.session_state.mdp = {
            "estados": [],
            "decisiones": [],
            "tipo": "costos",
            "decisiones_data": {}
        }

def get_mdp():
    """
    Retorna el diccionario completo del MDP almacenado en la sesión.
    Garantiza que la sesión esté inicializada.
    """
    init_session()
    return st.session_state.mdp

def reset_mdp():
    """
    Reinicia completamente el modelo, eliminando todos los datos ingresados.
    Vuelve al estado inicial vacío.
    """
    if "mdp" in st.session_state:
        del st.session_state.mdp
    init_session()

def mdp_completo():
    """
    Verifica si el MDP contiene toda la información necesaria para ejecutar algoritmos.

    Condiciones:
    - Existe al menos un estado y una decisión.
    - Cada decisión tiene al menos un estado afectado.
    - Para cada estado afectado por una decisión, existe un costo/ganancia asignado.
    - Las probabilidades de transición desde cada estado afectado suman 1.0.

    Returns:
        bool: True si el modelo está completo, False en caso contrario.
    """
    mdp = get_mdp()
    if not mdp["estados"] or not mdp["decisiones"]:
        return False

    for d, data in mdp["decisiones_data"].items():
        afectados = data.get("estados_afectados", [])
        if not afectados:
            return False
        for s in afectados:
            # Verificar costo/ganancia
            if s not in data.get("costos", {}):
                return False
            # Verificar suma de probabilidades
            probs = data.get("transiciones", {}).get(s, {})
            if not probs:
                return False
            total = sum(probs.values())
            if abs(total - 1.0) > 1e-6:
                return False
    return True

# ----------------------------------------------------------------------
# Funciones auxiliares para modificar el modelo de forma segura
# ----------------------------------------------------------------------

def agregar_estado(nombre: str):
    """
    Agrega un nuevo estado a la lista de estados si no existe ya.

    Args:
        nombre (str): Nombre del estado a agregar.
    """
    mdp = get_mdp()
    if nombre and nombre not in mdp["estados"]:
        mdp["estados"].append(nombre)

def agregar_decision(nombre: str):
    """
    Agrega una nueva decisión y crea su estructura de datos asociada.

    Args:
        nombre (str): Nombre de la decisión a agregar.
    """
    mdp = get_mdp()
    if nombre and nombre not in mdp["decisiones"]:
        mdp["decisiones"].append(nombre)
        mdp["decisiones_data"][nombre] = {
            "estados_afectados": [],
            "costos": {},
            "transiciones": {}
        }

def eliminar_estado(nombre: str):
    """
    Elimina un estado y limpia todas las referencias a él en los datos de las decisiones.

    Args:
        nombre (str): Nombre del estado a eliminar.
    """
    mdp = get_mdp()
    if nombre in mdp["estados"]:
        mdp["estados"].remove(nombre)
        for d, data in mdp["decisiones_data"].items():
            if nombre in data["estados_afectados"]:
                data["estados_afectados"].remove(nombre)
            data["costos"].pop(nombre, None)
            data["transiciones"].pop(nombre, None)
            for origen in data["transiciones"]:
                data["transiciones"][origen].pop(nombre, None)

def eliminar_decision(nombre: str):
    """
    Elimina una decisión y todos sus datos asociados.

    Args:
        nombre (str): Nombre de la decisión a eliminar.
    """
    mdp = get_mdp()
    if nombre in mdp["decisiones"]:
        mdp["decisiones"].remove(nombre)
        mdp["decisiones_data"].pop(nombre, None)

def set_estados_afectados(decision: str, estados: list):
    """
    Asigna la lista de estados a los que aplica una decisión.

    Args:
        decision (str): Nombre de la decisión.
        estados (list): Lista de nombres de estados afectados.
    """
    mdp = get_mdp()
    if decision in mdp["decisiones_data"]:
        mdp["decisiones_data"][decision]["estados_afectados"] = estados

def set_costo(estado: str, decision: str, valor: float):
    """
    Guarda el costo o ganancia de aplicar una decisión en un estado.

    Args:
        estado (str): Nombre del estado.
        decision (str): Nombre de la decisión.
        valor (float): Valor numérico del costo/ganancia.
    """
    mdp = get_mdp()
    if decision in mdp["decisiones_data"]:
        mdp["decisiones_data"][decision]["costos"][estado] = valor

def set_transicion(origen: str, decision: str, destino: str, probabilidad: float):
    """
    Establece la probabilidad de transición desde un estado origen a un destino
    bajo una decisión específica.

    Args:
        origen (str): Estado de partida.
        decision (str): Decisión aplicada.
        destino (str): Estado de llegada.
        probabilidad (float): Probabilidad de transición (entre 0 y 1).
    """
    mdp = get_mdp()
    if decision in mdp["decisiones_data"]:
        trans = mdp["decisiones_data"][decision]["transiciones"]
        if origen not in trans:
            trans[origen] = {}
        trans[origen][destino] = probabilidad
