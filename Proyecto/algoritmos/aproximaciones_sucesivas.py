"""
algoritmos/aproximaciones_sucesivas.py
Implementación del método de Aproximaciones Sucesivas (Value Iteration).
Estructura por iteraciones:
  Iteración 1:
    Paso 1: V_i^1 = min/max C_{ik}
    Paso 2: Política evaluando C_{ik} + alpha * Σ P_{ij}(k) * V_j^1
  Iteración n>1:
    Paso 1: V_i^n = min/max [ C_{ik} + alpha * Σ P_{ij}(k) * V_j^{n-1} ]
    Paso 2: Política evaluando la misma expresión con V_j^n
"""

import numpy as np

def inicializar_valores(estados, decisiones_data, tipo="costos"):
    """Paso 1 de la primera iteración: V_i^1 = min/max C_{ik}"""
    V = {}
    detalle = {}
    for s in estados:
        opciones = []
        for d, data in decisiones_data.items():
            if s in data.get("estados_afectados", []):
                costo = data["costos"].get(s, 0.0)
                opciones.append({"decision": d, "costo": costo})
        if tipo == "costos":
            mejor = min(opciones, key=lambda x: x["costo"])
        else:
            mejor = max(opciones, key=lambda x: x["costo"])
        V[s] = mejor["costo"]
        detalle[s] = {
            "opciones": opciones,
            "elegida": mejor["decision"]
        }
    return V, detalle

def evaluar_politica(V, estados, decisiones_data, alpha, tipo="costos"):
    """
    Evalúa las decisiones para obtener la política y el detalle.
    """
    politica = {}
    detalle = {}
    for s in estados:
        opciones = []
        for d, data in decisiones_data.items():
            if s in data.get("estados_afectados", []):
                costo = data["costos"].get(s, 0.0)
                suma_prob = 0.0
                terminos = []
                for s2, prob in data["transiciones"].get(s, {}).items():
                    if prob != 0:
                        valor_actual = V.get(s2, 0.0)
                        suma_prob += prob * valor_actual
                        terminos.append((s2, prob, valor_actual))
                valor_q = costo + alpha * suma_prob
                opciones.append({
                    "decision": d,
                    "costo": costo,
                    "terminos": terminos,
                    "suma_prob": suma_prob,
                    "valor_q": valor_q
                })
        if tipo == "costos":
            mejor = min(opciones, key=lambda x: x["valor_q"])
        else:
            mejor = max(opciones, key=lambda x: x["valor_q"])
        politica[s] = mejor["decision"]
        detalle[s] = {
            "opciones": opciones,
            "elegida": mejor["decision"]
        }
    return politica, detalle

def calcular_paso1(V_anterior, estados, decisiones_data, alpha, tipo="costos"):
    """
    Paso 1 de iteraciones n>1: calcula V_i^n usando V^{n-1} y devuelve detalle.
    """
    V_nuevo = {}
    detalle = {}
    for s in estados:
        opciones = []
        for d, data in decisiones_data.items():
            if s in data.get("estados_afectados", []):
                costo = data["costos"].get(s, 0.0)
                suma_prob = 0.0
                terminos = []
                for s2, prob in data["transiciones"].get(s, {}).items():
                    if prob != 0:
                        valor_ant = V_anterior.get(s2, 0.0)
                        suma_prob += prob * valor_ant
                        terminos.append((s2, prob, valor_ant))
                valor_q = costo + alpha * suma_prob
                opciones.append({
                    "decision": d,
                    "costo": costo,
                    "terminos": terminos,
                    "suma_prob": suma_prob,
                    "valor_q": valor_q
                })
        if tipo == "costos":
            mejor = min(opciones, key=lambda x: x["valor_q"])
        else:
            mejor = max(opciones, key=lambda x: x["valor_q"])
        V_nuevo[s] = mejor["valor_q"]
        detalle[s] = {
            "opciones": opciones,
            "elegida": mejor["decision"]
        }
    return V_nuevo, detalle

def aproximaciones_sucesivas(estados, decisiones_data, tipo="costos",
                             epsilon=0.01, max_iter=100, alpha=1.0):
    iteraciones = []

    # Iteración 1
    V1, detalle_paso1 = inicializar_valores(estados, decisiones_data, tipo)
    politica1, detalle_paso2 = evaluar_politica(V1, estados, decisiones_data, alpha, tipo)
    iter1 = {
        "iter": 1,
        "paso1": {"V": V1.copy(), "detalle": detalle_paso1},
        "paso2": {"politica": politica1.copy(), "detalle": detalle_paso2},
        "max_diff": None
    }
    iteraciones.append(iter1)

    V_anterior = V1
    for n in range(2, max_iter + 1):
        V_nuevo, detalle_paso1_n = calcular_paso1(V_anterior, estados, decisiones_data, alpha, tipo)
        politica_nueva, detalle_paso2_n = evaluar_politica(V_nuevo, estados, decisiones_data, alpha, tipo)
        max_diff = max(abs(V_nuevo[s] - V_anterior[s]) for s in estados)
        iter_n = {
            "iter": n,
            "paso1": {"V": V_nuevo.copy(), "detalle": detalle_paso1_n},
            "paso2": {"politica": politica_nueva.copy(), "detalle": detalle_paso2_n},
            "max_diff": max_diff
        }
        iteraciones.append(iter_n)
        if max_diff < epsilon:
            break
        V_anterior = V_nuevo

    return iteraciones

    ultima = iteraciones[-1]
    pol_final = ultima["paso2"]["politica"]
    costo_esperado = sum(decisiones_data[pol_final[s]]["costos"].get(s, 0.0) for s in estados)
    ultima["costo_esperado"] = costo_esperado
