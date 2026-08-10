"""
algoritmos/mejoramiento_politicas_descuento.py
Implementación del algoritmo de Mejoramiento de Políticas con factor de descuento (Policy Iteration con descuento).

Pasos:
0. Seleccionar política inicial y fijar factor de descuento α (0 ≤ α < 1).
1. Evaluación de política: resolver V_i = C_{ik} + α Σ_j P_{ij}(k) V_j
   → Sistema (I - α P) V = c.
2. Mejora: para cada estado i, elegir la decisión que optimiza
   Q(i,k) = C_{ik} + α Σ_j P_{ij}(k) V_j.
3. Si la nueva política coincide con la anterior, termina; si no, repite.
"""

import numpy as np
import pandas as pd

def evaluar_politica_descuento(politica, estados, decisiones_data, alpha):
    """
    Evalúa una política determinista con descuento.
    Retorna el vector de valores V (dict estado -> valor) y la matriz del sistema.
    """
    n = len(estados)
    idx = {s: i for i, s in enumerate(estados)}
    P = np.zeros((n, n))
    c = np.zeros(n)

    for s in estados:
        i = idx[s]
        d = politica[s]
        data = decisiones_data[d]
        c[i] = data["costos"].get(s, 0.0)
        for s2, prob in data["transiciones"].get(s, {}).items():
            j = idx[s2]
            P[i, j] = prob

    # Sistema: (I - alpha * P) V = c
    A = np.eye(n) - alpha * P
    V = np.linalg.solve(A, c)
    return {s: V[idx[s]] for s in estados}, P, c, A

def mejorar_politica_descuento(V, estados, decisiones_data, alpha, tipo="costos"):
    """
    Mejora la política: para cada estado, elige la decisión que minimiza/maximiza
    Q(i,k) = C_{ik} + α Σ_j P_{ij}(k) V_j.
    """
    nueva_politica = {}
    for s in estados:
        mejor_valor = float('inf') if tipo == "costos" else float('-inf')
        mejor_d = None
        for d, data in decisiones_data.items():
            if s in data.get("estados_afectados", []):
                costo = data["costos"].get(s, 0.0)
                suma = sum(prob * V[s2] for s2, prob in data["transiciones"].get(s, {}).items())
                q_valor = costo + alpha * suma
                if tipo == "costos":
                    if q_valor < mejor_valor:
                        mejor_valor = q_valor
                        mejor_d = d
                else:
                    if q_valor > mejor_valor:
                        mejor_valor = q_valor
                        mejor_d = d
        nueva_politica[s] = mejor_d
    return nueva_politica

def mejoramiento_politicas_descuento(estados, decisiones_data, tipo="costos",
                                     politica_inicial=None, alpha=0.9):
    """
    Ejecuta el algoritmo completo de Mejoramiento de Políticas con descuento.
    Retorna lista de iteraciones y política óptima.
    """
    if politica_inicial is None:
        raise ValueError("Debe proporcionarse una política inicial.")

    politica_actual = politica_inicial.copy()
    iteraciones = []
    while True:
        V, P, c, A = evaluar_politica_descuento(politica_actual, estados, decisiones_data, alpha)
        costo_esperado = np.dot(list(V.values()), c)   # c es el vector de costos de la política actual
        nueva_politica = mejorar_politica_descuento(V, estados, decisiones_data, alpha, tipo)
        iteraciones.append({
            "politica": politica_actual.copy(),
            "V": V.copy(),
            "P": P,
            "c": c,
            "A": A,
            "costo_esperado": costo_esperado,
            "nueva_politica": nueva_politica.copy()
        })
        if nueva_politica == politica_actual:
            break
        politica_actual = nueva_politica.copy()
    return iteraciones
