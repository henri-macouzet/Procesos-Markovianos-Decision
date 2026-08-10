"""
algoritmos/mejoramiento_politicas.py
Implementación del algoritmo de Mejoramiento de Políticas (Policy Iteration) para MDPs.
"""

import numpy as np
import pandas as pd

def evaluar_politica(politica, estados, decisiones_data, tipo="costos"):
    """
    Evalúa una política determinista resolviendo el sistema:
        g + V_i - Σ_j P_{ij}(k(i)) V_j = C_{i,k(i)}   para cada estado i
    fijando V_{último} = 0.
    Retorna {g, V: {estado: valor}}.
    """
    n = len(estados)
    idx = {s: i for i, s in enumerate(estados)}
    A = np.zeros((n, n+1))
    b = np.zeros(n)

    for s in estados:
        i = idx[s]
        k = politica[s]
        costo = decisiones_data[k]["costos"].get(s, 0.0)
        trans = decisiones_data[k]["transiciones"].get(s, {})

        A[i, 0] = 1.0
        A[i, i+1] += 1.0
        for j, prob in trans.items():
            jj = idx[j]
            A[i, jj+1] -= prob
        b[i] = costo

    A_reducida = np.zeros((n, n))
    A_reducida[:, 0] = A[:, 0]
    A_reducida[:, 1:] = A[:, 1:n]
    b_reducida = b.copy()

    x = np.linalg.solve(A_reducida, b_reducida)
    g = x[0]
    V = {}
    for i in range(n-1):
        V[estados[i]] = x[i+1]
    V[estados[-1]] = 0.0

    return {"g": g, "V": V}

def mejorar_politica(politica_actual, V, estados, decisiones_data, tipo="costos"):
    """
    Mejora la política: para cada estado, elige la decisión que optimiza
        C_{ik} + Σ_j P_{ij}(k) V_j.
    Retorna la nueva política.
    """
    nueva_politica = {}
    for s in estados:
        mejor_valor = float('inf') if tipo == "costos" else float('-inf')
        mejor_d = None
        for d, data in decisiones_data.items():
            if s in data.get("estados_afectados", []):
                costo = data["costos"].get(s, 0.0)
                suma_prob = 0.0
                for s2, prob in data["transiciones"].get(s, {}).items():
                    suma_prob += prob * V[s2]
                valor = costo + suma_prob
                if tipo == "costos":
                    if valor < mejor_valor:
                        mejor_valor = valor
                        mejor_d = d
                else:
                    if valor > mejor_valor:
                        mejor_valor = valor
                        mejor_d = d
        nueva_politica[s] = mejor_d
    return nueva_politica

def mejoramiento_politicas(estados, decisiones_data, tipo="costos", politica_inicial=None):
    if politica_inicial is None:
        raise ValueError("Debe proporcionarse una política inicial.")
    politica_actual = politica_inicial.copy()
    iteraciones = []
    while True:
        eval_res = evaluar_politica(politica_actual, estados, decisiones_data, tipo)
        g = eval_res["g"]
        V = eval_res["V"]
        nueva_politica = mejorar_politica(politica_actual, V, estados, decisiones_data, tipo)
        iteraciones.append({
            "politica": politica_actual.copy(),
            "g": g,
            "V": V.copy(),
            "nueva_politica": nueva_politica.copy()
        })
        if nueva_politica == politica_actual:
            break
        politica_actual = nueva_politica.copy()
    return iteraciones
