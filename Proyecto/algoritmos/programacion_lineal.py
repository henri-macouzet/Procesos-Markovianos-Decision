"""
algoritmos/programacion_lineal.py
Implementación del método de Programación Lineal para MDPs.
Formulación:
    Optimizar Z = Σ_i Σ_k C_{ik} Y_{ik}
    s.a.
    Σ_k Y_{ik} - Σ_j Σ_l Y_{jl} · P(i | j, l) = 0, para cada estado i (excepto el último)
    Σ_i Σ_k Y_{ik} = 1
    Y_{ik} ≥ 0
"""

import numpy as np
from scipy.optimize import linprog
import pandas as pd
from algoritmos.exhaustiva import generar_politicas  # para obtener el nombre Rn

def _subindice(num_str):
    """Convierte una cadena numérica en subíndice Unicode (ej. '0' → '₀', '10' → '₁₀')."""
    subs = "₀₁₂₃₄₅₆₇₈₉"
    return ''.join(subs[int(d)] for d in str(num_str))

def _var_str(estado, decision):
    """Cadena Y_{estado,decisión} con subíndices (ej. Y₀₁)."""
    return f"Y{_subindice(estado)}{_subindice(decision)}"

def _prob_str(origen, destino, decision):
    """Cadena P_{origen,destino}(decisión) (ej. P₀₁(d₁))."""
    return f"P{_subindice(origen)}{_subindice(destino)}({decision})"

def construir_modelo_pl(estados, decisiones_data, tipo="costos"):
    """
    Construye el modelo de programación lineal.
    Retorna:
        c (list): Coeficientes de la función objetivo.
        A_eq (list of list): Matriz de restricciones de igualdad.
        b_eq (list): Lados derechos de las igualdades.
        bounds (list): Tuplas de cotas (0, None) para cada variable.
        variables (list of tuples): Lista de pares (estado, decisión) de cada variable.
        idx_map (dict): Mapeo (estado, decisión) → índice de variable.
    """
    variables = []          # (estado, decision)
    idx_map = {}            # (estado, decision) → índice
    for s in estados:
        for d, data in decisiones_data.items():
            if s in data.get("estados_afectados", []):
                idx = len(variables)
                variables.append((s, d))
                idx_map[(s, d)] = idx

    n_vars = len(variables)
    if n_vars == 0:
        raise ValueError("No hay variables: ningún estado tiene decisiones asignadas.")

    c = []
    for s, d in variables:
        costo = decisiones_data[d]["costos"].get(s, 0.0)
        c.append(costo)

    if tipo == "ganancias":
        c = [-x for x in c]

    A_eq = []
    b_eq = []

    # Normalización
    A_eq.append([1.0] * n_vars)
    b_eq.append(1.0)

    # Restricciones de balance (excepto último estado)
    idx_estado = {s: i for i, s in enumerate(estados)}
    ultimo_estado = estados[-1]

    for s in estados:
        if s == ultimo_estado:
            continue
        fila = [0.0] * n_vars
        for d in decisiones_data:
            if (s, d) in idx_map:
                fila[idx_map[(s, d)]] = 1.0
        for (j, l), idx in idx_map.items():
            prob = decisiones_data[l]["transiciones"].get(j, {}).get(s, 0.0)
            if prob > 0:
                fila[idx] -= prob
        A_eq.append(fila)
        b_eq.append(0.0)

    bounds = [(0, None) for _ in range(n_vars)]

    return c, A_eq, b_eq, bounds, variables, idx_map

def resolver_pl(estados, decisiones_data, tipo="costos"):
    """
    Resuelve el modelo de PL y retorna resultados más información de apoyo para la UI.
    """
    c, A_eq, b_eq, bounds, variables, idx_map = construir_modelo_pl(estados, decisiones_data, tipo)

    res = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')

    if not res.success:
        return {
            "exito": False,
            "mensaje": res.message,
            "valor_optimo": None,
            "variables_y": {},
            "D": None,
            "politica": {},
            "modelo": None
        }

    y_vals = res.x
    valor_optimo = res.fun if tipo == "costos" else -res.fun

    variables_y = {}
    for (s, d), idx in idx_map.items():
        variables_y[(s, d)] = y_vals[idx]

    D = {}
    for s in estados:
        suma = sum(variables_y.get((s, d), 0.0) for d in decisiones_data if (s, d) in idx_map)
        for d in decisiones_data:
            if (s, d) in idx_map:
                D[(s, d)] = variables_y[(s, d)] / suma if suma > 1e-12 else 0.0

    politica = {}
    for s in estados:
        mejor_d = None
        mejor_val = -1
        for d in decisiones_data:
            if (s, d) in D and D[(s, d)] > mejor_val:
                mejor_val = D[(s, d)]
                mejor_d = d
        if mejor_d is not None:
            politica[s] = mejor_d

    # Buscar el nombre Rn correspondiente a esta política
    nombre_politica = None
    todas_politicas = generar_politicas(estados, decisiones_data)
    for i, pol in enumerate(todas_politicas):
        if pol == politica:
            nombre_politica = f"R{i+1}"
            break

    # Construcción de representaciones textuales (usando nombres originales)
    if tipo == "costos":
        objetivo = "Minimizar Z = "
    else:
        objetivo = "Maximizar Z = "
    terminos_obj = []
    for idx, (s, d) in enumerate(variables):
        coef = decisiones_data[d]["costos"].get(s, 0.0)
        var = _var_str(s, d)
        if idx == 0:
            if coef >= 0:
                terminos_obj.append(f"{abs(coef):g}{var}" if abs(coef) != 1 else var)
            else:
                terminos_obj.append(f"-{abs(coef):g}{var}" if abs(coef) != 1 else f"-{var}")
        else:
            if coef >= 0:
                terminos_obj.append(f"+ {abs(coef):g}{var}" if abs(coef) != 1 else f"+ {var}")
            else:
                terminos_obj.append(f"- {abs(coef):g}{var}" if abs(coef) != 1 else f"- {var}")
    objetivo += " ".join(terminos_obj)

    # Restricciones
    formula_general = (
        r"\sum_{k=1}^{K} Y_{ik} - \sum_{j=0}^{m} \sum_{l=1}^{K} "
        r"Y_{jl} \cdot P(i \mid j, l) = 0"
    )

    restricciones_completas = []
    restricciones_sin_ceros = []
    restricciones_desarrollo = []
    ultimo_estado = estados[-1]

    for idx_fila, s in enumerate(estados):
        if s == ultimo_estado:
            continue

        positivos = [d for d in decisiones_data if (s, d) in idx_map]
        pos_str = " + ".join([_var_str(s, d) for d in positivos])

        todos_neg = []
        for (j, l) in variables:
            prob = decisiones_data[l]["transiciones"].get(j, {}).get(s, 0.0)
            todos_neg.append((j, l, prob))

        # Completa
        neg_str_completa = " - (" + " + ".join([
            f"{_var_str(j, l)}·{_prob_str(j, s, l)}"
            for j, l, _ in todos_neg
        ]) + ")"
        ec_completa = f"{pos_str}{neg_str_completa} = 0"
        restricciones_completas.append(ec_completa)

        # Sin ceros
        neg_sin_ceros = [(j, l, prob) for (j, l, prob) in todos_neg if prob > 0]
        if neg_sin_ceros:
            neg_str_sin = " - (" + " + ".join([
                f"{_var_str(j, l)}·{_prob_str(j, s, l)}"
                for j, l, _ in neg_sin_ceros
            ]) + ")"
        else:
            neg_str_sin = ""
        ec_sin_ceros = f"{pos_str}{neg_str_sin} = 0"
        restricciones_sin_ceros.append(ec_sin_ceros)

        # Desarrollo
        fila = A_eq[1 + idx_fila]
        terminos_des = []
        for jdx, coef in enumerate(fila):
            if abs(coef) > 1e-12:
                s2, d2 = variables[jdx]
                var = _var_str(s2, d2)
                if not terminos_des:
                    if coef == 1:
                        terminos_des.append(var)
                    elif coef == -1:
                        terminos_des.append(f"-{var}")
                    else:
                        terminos_des.append(f"{coef:g}{var}")
                else:
                    if coef == 1:
                        terminos_des.append(f"+ {var}")
                    elif coef == -1:
                        terminos_des.append(f"- {var}")
                    elif coef > 0:
                        terminos_des.append(f"+ {abs(coef):g}{var}")
                    else:
                        terminos_des.append(f"- {abs(coef):g}{var}")
        ec_des = " ".join(terminos_des) + " = 0"
        restricciones_desarrollo.append(ec_des)

    norm = " + ".join([_var_str(s, d) for (s, d) in variables]) + " = 1"
    no_neg = ", ".join([_var_str(s, d) for (s, d) in variables]) + " ≥ 0"

    modelo_info = {
        "funcion_objetivo": objetivo,
        "formula_general": formula_general,
        "restricciones_completas": restricciones_completas,
        "restricciones_sin_ceros": restricciones_sin_ceros,
        "restricciones_desarrollo": restricciones_desarrollo,
        "normalizacion": norm,
        "no_negatividad": no_neg,
        "variables": variables
    }

    return {
        "exito": True,
        "mensaje": res.message,
        "valor_optimo": valor_optimo,
        "variables_y": variables_y,
        "D": pd.DataFrame([
            (s, d, D.get((s, d), 0.0))
            for s in estados
            for d in decisiones_data
            if (s, d) in idx_map
        ], columns=["Estado", "Decisión", "D"]).pivot(index="Estado", columns="Decisión", values="D"),
        "politica": politica,
        "nombre_politica": nombre_politica,
        "modelo": modelo_info
    }
