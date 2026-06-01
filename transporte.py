"""
transporte.py
Módulo de Optimización del Problema de Transporte
Utiliza PuLP para resolver el modelo de Programación Lineal
Sistema de Optimización de Distribución de Huevos
"""

import pulp
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class ResultadoTransporte:
    """Estructura de datos para almacenar los resultados de la optimización."""
    estado: str
    costo_total: float
    plan_distribucion: pd.DataFrame
    oferta_utilizada: pd.DataFrame
    demanda_atendida: pd.DataFrame
    es_optimo: bool
    mensaje: str
    variables: dict


def validar_balance(ofertas: list, demandas: list) -> tuple[bool, str, str]:
    """
    Valida si el problema está balanceado (oferta total == demanda total).
    Si no está balanceado, indica qué tipo de desbalance existe.

    Returns:
        (es_valido, tipo_balance, mensaje)
    """
    total_oferta = sum(ofertas)
    total_demanda = sum(demandas)

    if total_oferta == total_demanda:
        return True, "balanceado", "El problema está balanceado."
    elif total_oferta > total_demanda:
        exceso = total_oferta - total_demanda
        return True, "superavit", f"Superávit de oferta: {exceso} cajas (se resolverá con demanda ficticia)."
    else:
        deficit = total_demanda - total_oferta
        return True, "deficit", f"Déficit de oferta: {deficit} cajas (se resolverá con oferta ficticia)."


def resolver_transporte(
    almacenes: list[str],
    clientes: list[str],
    ofertas: list[float],
    demandas: list[float],
    costos: list[list[float]]
) -> ResultadoTransporte:
    """
    Resuelve el Problema de Transporte usando Programación Lineal con PuLP.

    Modelo Matemático:
    -----------------
    Variables de decisión:
        x[i][j] = cantidad de cajas enviadas desde almacén i al cliente j

    Función Objetivo:
        Min Z = Σ Σ c[i][j] * x[i][j]

    Restricciones:
        Σ x[i][j] <= oferta[i]   para todo almacén i  (restricción de oferta)
        Σ x[i][j] >= demanda[j]  para todo cliente j   (restricción de demanda)
        x[i][j] >= 0              para todo i, j        (no negatividad)

    Args:
        almacenes: Lista de nombres de almacenes
        clientes: Lista de nombres de clientes
        ofertas: Lista de capacidades de cada almacén
        demandas: Lista de demandas de cada cliente
        costos: Matriz de costos costos[i][j]

    Returns:
        ResultadoTransporte con todos los datos de la solución
    """

    n_almacenes = len(almacenes)
    n_clientes = len(clientes)

    # =========================================================
    # 1. CREAR EL PROBLEMA DE MINIMIZACIÓN
    # =========================================================
    problema = pulp.LpProblem("Distribucion_Optima_Huevos", pulp.LpMinimize)

    # =========================================================
    # 2. DEFINIR VARIABLES DE DECISIÓN
    # =========================================================
    # x[i][j] = cajas enviadas desde almacén i al cliente j
    x = {}
    for i in range(n_almacenes):
        for j in range(n_clientes):
            nombre_var = f"x_{i}_{j}"
            x[i, j] = pulp.LpVariable(nombre_var, lowBound=0, cat='Continuous')

    # =========================================================
    # 3. FUNCIÓN OBJETIVO: Minimizar costo total
    # =========================================================
    problema += pulp.lpSum(
        costos[i][j] * x[i, j]
        for i in range(n_almacenes)
        for j in range(n_clientes)
    ), "Costo_Total_Transporte"

    # =========================================================
    # 4. RESTRICCIONES DE OFERTA
    # No enviar más de lo disponible en cada almacén
    # =========================================================
    for i in range(n_almacenes):
        problema += (
            pulp.lpSum(x[i, j] for j in range(n_clientes)) <= ofertas[i],
            f"Oferta_Almacen_{i}"
        )

    # =========================================================
    # 5. RESTRICCIONES DE DEMANDA
    # Satisfacer la demanda de cada cliente
    # =========================================================
    for j in range(n_clientes):
        problema += (
            pulp.lpSum(x[i, j] for i in range(n_almacenes)) >= demandas[j],
            f"Demanda_Cliente_{j}"
        )

    # =========================================================
    # 6. RESOLVER EL PROBLEMA
    # =========================================================
    solver = pulp.PULP_CBC_CMD(msg=0)  # Suprimir mensajes del solver
    problema.solve(solver)

    # =========================================================
    # 7. PROCESAR RESULTADOS
    # =========================================================
    estado_solver = pulp.LpStatus[problema.status]
    es_optimo = problema.status == pulp.constants.LpStatusOptimal

    if not es_optimo:
        return ResultadoTransporte(
            estado=estado_solver,
            costo_total=0.0,
            plan_distribucion=pd.DataFrame(),
            oferta_utilizada=pd.DataFrame(),
            demanda_atendida=pd.DataFrame(),
            es_optimo=False,
            mensaje=f"No se encontró solución óptima. Estado: {estado_solver}",
            variables={}
        )

    costo_total = pulp.value(problema.objective)

    # =========================================================
    # 8. CONSTRUIR PLAN DE DISTRIBUCIÓN
    # =========================================================
    registros_plan = []
    valores_x = {}

    for i in range(n_almacenes):
        for j in range(n_clientes):
            cantidad = pulp.value(x[i, j])
            if cantidad is None:
                cantidad = 0.0
            cantidad = round(cantidad, 2)
            valores_x[i, j] = cantidad

            if cantidad > 0.001:  # Filtrar valores prácticamente cero
                registros_plan.append({
                    "Almacén": almacenes[i],
                    "Cliente": clientes[j],
                    "Cantidad Enviada (cajas)": cantidad,
                    "Costo Unitario (Bs)": costos[i][j],
                    "Costo Total Ruta (Bs)": round(cantidad * costos[i][j], 2)
                })

    plan_df = pd.DataFrame(registros_plan) if registros_plan else pd.DataFrame(
        columns=["Almacén", "Cliente", "Cantidad Enviada (cajas)", "Costo Unitario (Bs)", "Costo Total Ruta (Bs)"]
    )

    # =========================================================
    # 9. CALCULAR OFERTA UTILIZADA POR ALMACÉN
    # =========================================================
    registros_oferta = []
    for i in range(n_almacenes):
        utilizado = sum(valores_x.get((i, j), 0) for j in range(n_clientes))
        utilizado = round(utilizado, 2)
        porcentaje = round((utilizado / ofertas[i]) * 100, 1) if ofertas[i] > 0 else 0
        registros_oferta.append({
            "Almacén": almacenes[i],
            "Oferta Total (cajas)": ofertas[i],
            "Cantidad Enviada (cajas)": utilizado,
            "Stock Restante (cajas)": round(ofertas[i] - utilizado, 2),
            "Utilización (%)": porcentaje
        })

    oferta_df = pd.DataFrame(registros_oferta)

    # =========================================================
    # 10. CALCULAR DEMANDA ATENDIDA POR CLIENTE
    # =========================================================
    registros_demanda = []
    for j in range(n_clientes):
        recibido = sum(valores_x.get((i, j), 0) for i in range(n_almacenes))
        recibido = round(recibido, 2)
        porcentaje = round((recibido / demandas[j]) * 100, 1) if demandas[j] > 0 else 0
        estado_cliente = "✅ Satisfecha" if recibido >= demandas[j] - 0.01 else "⚠️ Parcial"
        registros_demanda.append({
            "Cliente": clientes[j],
            "Demanda (cajas)": demandas[j],
            "Cantidad Recibida (cajas)": recibido,
            "Estado": estado_cliente,
            "Cobertura (%)": porcentaje
        })

    demanda_df = pd.DataFrame(registros_demanda)

    # =========================================================
    # 11. PREPARAR VARIABLES PARA MOSTRAR
    # =========================================================
    variables_resultado = {}
    for i in range(n_almacenes):
        for j in range(n_clientes):
            variables_resultado[f"x[{almacenes[i]}→{clientes[j]}]"] = valores_x.get((i, j), 0)

    return ResultadoTransporte(
        estado="Óptimo",
        costo_total=round(costo_total, 2),
        plan_distribucion=plan_df,
        oferta_utilizada=oferta_df,
        demanda_atendida=demanda_df,
        es_optimo=True,
        mensaje="✅ Solución óptima encontrada exitosamente mediante el Método Simplex.",
        variables=variables_resultado
    )


def construir_modelo_texto(
    almacenes: list[str],
    clientes: list[str],
    ofertas: list[float],
    demandas: list[float],
    costos: list[list[float]]
) -> dict:
    """
    Construye la representación textual del modelo matemático.
    
    Returns:
        Diccionario con las secciones del modelo matemático
    """
    n_a = len(almacenes)
    n_c = len(clientes)

    # Función objetivo
    terminos_fo = []
    for i in range(n_a):
        for j in range(n_c):
            terminos_fo.append(f"{costos[i][j]}·x{i+1}{j+1}")
    funcion_objetivo = "Min Z = " + " + ".join(terminos_fo)

    # Restricciones de oferta
    restricciones_oferta = []
    for i in range(n_a):
        terminos = " + ".join([f"x{i+1}{j+1}" for j in range(n_c)])
        restricciones_oferta.append(f"{terminos} ≤ {ofertas[i]}  [{almacenes[i]}]")

    # Restricciones de demanda
    restricciones_demanda = []
    for j in range(n_c):
        terminos = " + ".join([f"x{i+1}{j+1}" for i in range(n_a)])
        restricciones_demanda.append(f"{terminos} ≥ {demandas[j]}  [{clientes[j]}]")

    return {
        "funcion_objetivo": funcion_objetivo,
        "restricciones_oferta": restricciones_oferta,
        "restricciones_demanda": restricciones_demanda,
        "no_negatividad": "xij ≥ 0  para todo i, j"
    }
