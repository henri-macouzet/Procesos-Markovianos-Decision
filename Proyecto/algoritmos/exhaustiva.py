"""
algoritmos/exhaustiva.py
Implementación del algoritmo de Enumeración Exhaustiva para MDPs.

Funciones principales:
- generar_politicas: obtiene todas las políticas deterministas posibles.
- evaluar_politica: evalúa una política dada resolviendo el sistema de ecuaciones
  estacionarias (π = π·P) y calculando el costo/ganancia esperado.
- enumeracion_exhaustiva: orquesta la evaluación de un conjunto de políticas
  y selecciona la óptima según el tipo de modelo (costos o ganancias).

Se incluye manejo de matrices singulares y errores numéricos.
"""

import itertools
import pandas as pd
import numpy as np
from fractions import Fraction

def _subindice(i):
    """Convierte un número entero en subíndice Unicode (para π₀, π₁, ...)."""
    subs = "₀₁₂₃₄₅₆₇₈₉"
    return ''.join(subs[int(d)] for d in str(i))

def generar_politicas(estados, decisiones_data):
    """
    Genera todas las políticas deterministas posibles.

    Una política es un diccionario {estado: decision} donde cada estado
    tiene asignada una de las decisiones que lo afectan.

    Args:
        estados (list): Nombres de los estados.
        decisiones_data (dict): Datos por decisión, con la clave 'estados_afectados'.

    Returns:
        list: Lista de políticas, cada una como dict {estado: decision}.
              Retorna lista vacía si algún estado no tiene decisiones aplicables.
    """
    opciones_por_estado = {}
    for s in estados:
        opciones = []
        for d, data in decisiones_data.items():
            if s in data.get("estados_afectados", []):
                opciones.append(d)
        if not opciones:
            return []
        opciones_por_estado[s] = opciones

    claves = estados
    valores = [opciones_por_estado[s] for s in estados]
    politicas = []
    for combo in itertools.product(*valores):
        politicas.append(dict(zip(claves, combo)))
    return politicas

def evaluar_politica(politica, estados, decisiones_data, tipo="costos"):
    """
    Evalúa una política determinista.

    Para la política dada:
    - Construye la matriz de transición P (filas = origen, columnas = destino).
    - Construye el vector de costos/ganancias c por estado.
    - Resuelve el sistema π = π·P con Σπ = 1 para obtener las probabilidades
      estacionarias.
    - Calcula el valor esperado E = Σ π(s)·c(s).

    Si el sistema no tiene solución única (matriz singular), retorna un
    diccionario con clave "error": True.

    Args:
        politica (dict): {estado: decision}
        estados (list): Nombres de los estados.
        decisiones_data (dict): Datos completos de decisiones.
        tipo (str): "costos" o "ganancias" (solo informativo en este nivel).

    Returns:
        dict: Resultado de la evaluación, con claves:
            - error (bool): True si no se pudo resolver.
            - mensaje (str, opcional): Descripción del error.
            - politica (dict): La política evaluada.
            - P (DataFrame): Matriz de transición.
            - c (dict): Costos/ganancias por estado.
            - sistema (list): Representación textual del sistema de ecuaciones.
            - pi (dict): Probabilidades estacionarias por estado (None si error).
            - esperado (float): Valor esperado (None si error).
            - gauss_steps (list): Pasos del método Gauss‑Jordan (opcional).
    """
    n = len(estados)
    # Inicializar matriz P y vector c
    P = [[0.0] * n for _ in range(n)]
    c = [0.0] * n
    idx = {s: i for i, s in enumerate(estados)}

    for s in estados:
        i = idx[s]
        d = politica[s]
        data = decisiones_data[d]
        c[i] = data["costos"].get(s, 0.0)
        trans = data["transiciones"].get(s, {})
        for s2, prob in trans.items():
            j = idx[s2]
            P[i][j] = prob

    # Construir sistema de ecuaciones estacionarias: (I - P^T) π = 0, Σπ = 1
    A = []
    b = []
    # Ecuaciones de balance: n ecuaciones, una por cada estado
    for j in range(n):
        fila = []
        for i in range(n):
            if i == j:
                fila.append(1.0 - P[i][j])
            else:
                fila.append(-P[i][j])
        A.append(fila)
        b.append(0.0)
    # Reemplazar la última ecuación por la de normalización Σπ = 1
    A[-1] = [1.0] * n
    b[-1] = 1.0

    try:
        A_np = np.array(A, dtype=float)
        b_np = np.array(b, dtype=float)

        # Intentar resolver directamente
        pi = np.linalg.solve(A_np, b_np)

        # Asegurar no negatividad y normalizar (por posibles errores numéricos)
        pi = np.maximum(pi, 0)
        pi = pi / pi.sum()

        esperado = np.dot(pi, c)

        # Generar representación textual del sistema
        sistema_str = []
        for j in range(n - 1):
            terminos = []
            for i in range(n):
                coef = 1.0 - P[i][j] if i == j else -P[i][j]
                if abs(coef) > 1e-12:
                    terminos.append(f"({coef:.4f})π{_subindice(i)}")
            ec = " + ".join(terminos) if terminos else "0"
            sistema_str.append(f"π{_subindice(j)} = {ec}")
        sistema_str.append(" + ".join([f"π{_subindice(i)}" for i in range(n)]) + " = 1")

        # Pasos de Gauss-Jordan para mostrar en la UI (opcional)
        def to_frac(x):
            return Fraction(x).limit_denominator(1000000)

        M = []
        for i in range(n):
            fila = [to_frac(A[i][j]) for j in range(n)] + [to_frac(b[i])]
            M.append(fila)

        pasos_gauss = []
        def guardar_estado(descripcion):
            matriz_actual = [[float(M[i][j]) for j in range(n+1)] for i in range(n)]
            pasos_gauss.append((descripcion, matriz_actual))

        guardar_estado("Matriz aumentada inicial")

        for col in range(n):
            max_row = col
            for row in range(col+1, n):
                if abs(M[row][col]) > abs(M[max_row][col]):
                    max_row = row
            if max_row != col:
                M[col], M[max_row] = M[max_row], M[col]
                guardar_estado(f"Intercambio fila {col+1} ↔ fila {max_row+1}")

            pivote = M[col][col]
            if pivote == 0:
                raise ValueError("Matriz singular")
            for j in range(n+1):
                M[col][j] /= pivote
            guardar_estado(f"Fila {col+1} dividida por {float(pivote):.4f}")

            for row in range(n):
                if row != col:
                    factor = M[row][col]
                    if factor != 0:
                        for j in range(n+1):
                            M[row][j] -= factor * M[col][j]
                        guardar_estado(f"Fila {row+1} ← fila {row+1} - ({float(factor):.4f})·fila {col+1}")

        return {
            "error": False,
            "politica": politica,
            "P": pd.DataFrame(P, index=estados, columns=estados),
            "c": dict(zip(estados, c)),
            "sistema": sistema_str,
            "pi": dict(zip(estados, pi.tolist())),
            "esperado": esperado,
            "gauss_steps": pasos_gauss,
        }

    except np.linalg.LinAlgError:
        return {
            "error": True,
            "mensaje": "Matriz singular (sin solución única)",
            "politica": politica,
            "P": pd.DataFrame(P, index=estados, columns=estados),
            "c": dict(zip(estados, c)),
            "sistema": [],
            "pi": None,
            "esperado": None,
            "gauss_steps": []
        }
    except Exception as e:
        return {
            "error": True,
            "mensaje": f"Error inesperado: {str(e)}",
            "politica": politica,
            "P": pd.DataFrame(P, index=estados, columns=estados),
            "c": dict(zip(estados, c)),
            "sistema": [],
            "pi": None,
            "esperado": None,
            "gauss_steps": []
        }

def enumeracion_exhaustiva(estados, decisiones_data, tipo="costos", politicas_seleccionadas=None):
    """
    Ejecuta la enumeración exhaustiva sobre un conjunto de políticas.

    Args:
        estados (list): Nombres de los estados.
        decisiones_data (dict): Datos de decisiones.
        tipo (str): "costos" o "ganancias".
        politicas_seleccionadas (list, opcional): Lista de políticas a evaluar.
            Si es None, se generan y evalúan todas.

    Returns:
        tuple: (mejor_politica, lista_resultados)
            - mejor_politica (dict): Resultado de la política óptima, o None si no hay válidas.
            - lista_resultados (list): Resultados de todas las políticas evaluadas.
    """
    if politicas_seleccionadas is not None:
        politicas = politicas_seleccionadas
    else:
        politicas = generar_politicas(estados, decisiones_data)

    if not politicas:
        return None, []

    resultados = []
    for pol in politicas:
        res = evaluar_politica(pol, estados, decisiones_data, tipo)
        resultados.append(res)

    # Filtrar políticas válidas
    resultados_validos = [r for r in resultados if not r.get("error", False)]

    if not resultados_validos:
        return None, resultados

    # Seleccionar óptima según tipo de modelo
    if tipo == "costos":
        mejor = min(resultados_validos, key=lambda x: x["esperado"])
    else:
        mejor = max(resultados_validos, key=lambda x: x["esperado"])

    return mejor, resultados
