"""
utils.py
Utilidades del Sistema de Optimización de Distribución de Huevos
Funciones de validación, formateo y generación de gráficos
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ============================================================
# PALETA DE COLORES DEL SISTEMA
# ============================================================
COLORES = {
    "amarillo": "#F4B400",
    "naranja": "#FB8C00",
    "verde": "#43A047",
    "gris_oscuro": "#020202",
    "gris_claro": "#020202",
    "blanco": "#020202",
    "rojo": "#E53935",
    "azul": "#1976D2",
    "amarillo_claro": "#FFF8E1",
    "naranja_claro": "#FFF3E0",
}

SECUENCIA_COLORES = [
    "#F4B400", "#FB8C00", "#43A047", "#1976D2",
    "#E53935", "#8E24AA", "#00ACC1", "#F06292",
    "#66BB6A", "#FFA726"
]


# ============================================================
# VALIDACIONES
# ============================================================

def validar_nombres(nombres: list[str], tipo: str) -> tuple[bool, str]:
    """Valida que los nombres no estén vacíos ni repetidos."""
    if not nombres:
        return False, f"Debe ingresar al menos un {tipo}."
    
    nombres_limpios = [n.strip() for n in nombres]
    
    if any(n == "" for n in nombres_limpios):
        return False, f"Todos los nombres de {tipo}s deben ser ingresados."
    
    if len(nombres_limpios) != len(set(nombres_limpios)):
        return False, f"Los nombres de {tipo}s no pueden repetirse."
    
    return True, ""


def validar_cantidades(cantidades: list[float], tipo: str) -> tuple[bool, str]:
    """Valida que las cantidades sean positivas."""
    if not cantidades:
        return False, f"Debe ingresar cantidades para los {tipo}s."
    
    for i, val in enumerate(cantidades):
        if val is None or val <= 0:
            return False, f"La cantidad del {tipo} {i+1} debe ser mayor a 0."
    
    return True, ""


def validar_costos(costos: list[list[float]], n_almacenes: int, n_clientes: int) -> tuple[bool, str]:
    """Valida la matriz de costos."""
    if len(costos) != n_almacenes:
        return False, "La matriz de costos no coincide con el número de almacenes."
    
    for i, fila in enumerate(costos):
        if len(fila) != n_clientes:
            return False, f"La fila {i+1} de la matriz de costos no tiene el número correcto de columnas."
        for j, val in enumerate(fila):
            if val is None or val < 0:
                return False, f"El costo [{i+1}][{j+1}] debe ser mayor o igual a 0."
    
    return True, ""


def validar_datos_completos(
    almacenes: list[str],
    clientes: list[str],
    ofertas: list[float],
    demandas: list[float],
    costos: list[list[float]]
) -> tuple[bool, list[str]]:
    """
    Realiza todas las validaciones necesarias antes de resolver.
    
    Returns:
        (es_valido, lista_de_errores)
    """
    errores = []

    # Validar número mínimo de elementos
    if len(almacenes) < 1:
        errores.append("Debe tener al menos 1 almacén.")
    if len(clientes) < 1:
        errores.append("Debe tener al menos 1 cliente.")

    # Validar nombres
    ok, msg = validar_nombres(almacenes, "almacén")
    if not ok:
        errores.append(msg)

    ok, msg = validar_nombres(clientes, "cliente")
    if not ok:
        errores.append(msg)

    # Validar cantidades
    ok, msg = validar_cantidades(ofertas, "almacén")
    if not ok:
        errores.append(msg)

    ok, msg = validar_cantidades(demandas, "cliente")
    if not ok:
        errores.append(msg)

    # Validar costos
    ok, msg = validar_costos(costos, len(almacenes), len(clientes))
    if not ok:
        errores.append(msg)

    return len(errores) == 0, errores


# ============================================================
# FORMATEO
# ============================================================

def formatear_moneda(valor: float) -> str:
    """Formatea un número como moneda boliviana."""
    return f"Bs {valor:,.2f}"


def formatear_numero(valor: float) -> str:
    """Formatea un número con separador de miles."""
    return f"{valor:,.0f}"


def calcular_kpis(resultado) -> dict:
    """Calcula los KPIs principales para mostrar en tarjetas."""
    total_enviado = resultado.plan_distribucion["Cantidad Enviada (cajas)"].sum() if not resultado.plan_distribucion.empty else 0
    n_rutas = len(resultado.plan_distribucion) if not resultado.plan_distribucion.empty else 0
    
    costo_promedio = resultado.costo_total / total_enviado if total_enviado > 0 else 0
    
    utiliz_promedio = resultado.oferta_utilizada["Utilización (%)"].mean() if not resultado.oferta_utilizada.empty else 0
    
    return {
        "costo_total": resultado.costo_total,
        "total_enviado": total_enviado,
        "n_rutas": n_rutas,
        "costo_promedio": costo_promedio,
        "utilizacion_promedio": utiliz_promedio
    }


# ============================================================
# GRÁFICOS PLOTLY
# ============================================================

def grafico_cantidad_por_cliente(plan_df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de barras: cantidad enviada por cliente.
    """
    if plan_df.empty:
        return go.Figure()

    # Agrupar por cliente
    por_cliente = plan_df.groupby("Cliente")["Cantidad Enviada (cajas)"].sum().reset_index()
    por_cliente = por_cliente.sort_values("Cantidad Enviada (cajas)", ascending=True)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=por_cliente["Cliente"],
        x=por_cliente["Cantidad Enviada (cajas)"],
        orientation='h',
        marker=dict(
            color=SECUENCIA_COLORES[:len(por_cliente)],
            line=dict(color=COLORES["gris_oscuro"], width=0.5)
        ),
        text=[f"{v:,.0f} cajas" for v in por_cliente["Cantidad Enviada (cajas)"]],
        textposition='outside',
        hovertemplate="<b>%{y}</b><br>Cajas recibidas: %{x:,.0f}<extra></extra>"
    ))

    fig.update_layout(
        title=dict(
            text="Cantidad Enviada por Cliente",
            font=dict(size=16, color=COLORES["gris_oscuro"], family="Georgia"),
            x=0.02
        ),
        xaxis=dict(
            title="Cajas",
            gridcolor="#ECEFF1",
            showgrid=True,
            zeroline=False
        ),
        yaxis=dict(
            title="",
            tickfont=dict(size=12)
        ),
        plot_bgcolor=COLORES["blanco"],
        paper_bgcolor=COLORES["blanco"],
        height=max(300, len(por_cliente) * 60 + 120),
        margin=dict(l=20, r=80, t=60, b=40),
        showlegend=False,
        font=dict(family="Georgia, serif")
    )

    return fig


def grafico_cantidad_por_almacen(oferta_df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de barras agrupadas: oferta vs enviado por almacén.
    """
    if oferta_df.empty:
        return go.Figure()

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Oferta Total",
        x=oferta_df["Almacén"],
        y=oferta_df["Oferta Total (cajas)"],
        marker_color=COLORES["gris_claro"],
        marker_line=dict(color="#B0BEC5", width=1),
        hovertemplate="<b>%{x}</b><br>Oferta: %{y:,.0f} cajas<extra></extra>"
    ))

    fig.add_trace(go.Bar(
        name="Cantidad Enviada",
        x=oferta_df["Almacén"],
        y=oferta_df["Cantidad Enviada (cajas)"],
        marker_color=COLORES["naranja"],
        marker_line=dict(color=COLORES["gris_oscuro"], width=0.5),
        hovertemplate="<b>%{x}</b><br>Enviado: %{y:,.0f} cajas<extra></extra>"
    ))

    fig.update_layout(
        title=dict(
            text="Distribución por Almacén",
            font=dict(size=16, color=COLORES["gris_oscuro"], family="Georgia"),
            x=0.02
        ),
        xaxis=dict(title="Almacén", gridcolor="#ECEFF1"),
        yaxis=dict(title="Cajas", gridcolor="#ECEFF1", showgrid=True),
        barmode='group',
        plot_bgcolor=COLORES["blanco"],
        paper_bgcolor=COLORES["blanco"],
        height=380,
        margin=dict(l=20, r=20, t=60, b=60),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        font=dict(family="Georgia, serif")
    )

    return fig


def grafico_oferta_vs_demanda(oferta_df: pd.DataFrame, demanda_df: pd.DataFrame) -> go.Figure:
    """
    Gráfico comparativo de oferta total vs demanda total con indicadores.
    """
    if oferta_df.empty or demanda_df.empty:
        return go.Figure()

    total_oferta = oferta_df["Oferta Total (cajas)"].sum()
    total_enviado = oferta_df["Cantidad Enviada (cajas)"].sum()
    total_demanda = demanda_df["Demanda (cajas)"].sum()
    total_recibido = demanda_df["Cantidad Recibida (cajas)"].sum()

    categorias = ["Oferta Total", "Enviado", "Demanda Total", "Atendido"]
    valores = [total_oferta, total_enviado, total_demanda, total_recibido]
    colores_barras = [
        COLORES["amarillo"],
        COLORES["naranja"],
        COLORES["verde"],
        "#2E7D32"
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=categorias,
        y=valores,
        marker_color=colores_barras,
        marker_line=dict(color=COLORES["gris_oscuro"], width=0.8),
        text=[f"{v:,.0f}" for v in valores],
        textposition='outside',
        textfont=dict(size=13, color=COLORES["gris_oscuro"]),
        hovertemplate="<b>%{x}</b><br>Cajas: %{y:,.0f}<extra></extra>",
        width=0.5
    ))

    fig.update_layout(
        title=dict(
            text="Comparación: Oferta vs Demanda",
            font=dict(size=16, color=COLORES["gris_oscuro"], family="Georgia"),
            x=0.02
        ),
        xaxis=dict(title="", gridcolor="#ECEFF1"),
        yaxis=dict(title="Cajas", gridcolor="#ECEFF1", showgrid=True, zeroline=False),
        plot_bgcolor=COLORES["blanco"],
        paper_bgcolor=COLORES["blanco"],
        height=380,
        margin=dict(l=20, r=20, t=60, b=60),
        showlegend=False,
        font=dict(family="Georgia, serif")
    )

    return fig


def grafico_utilizacion_almacenes(oferta_df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de dona: porcentaje de utilización por almacén.
    """
    if oferta_df.empty:
        return go.Figure()

    fig = go.Figure(data=[go.Pie(
        labels=oferta_df["Almacén"],
        values=oferta_df["Cantidad Enviada (cajas)"],
        hole=0.45,
        marker=dict(
            colors=SECUENCIA_COLORES[:len(oferta_df)],
            line=dict(color=COLORES["blanco"], width=2)
        ),
        textinfo='label+percent',
        hovertemplate="<b>%{label}</b><br>Enviado: %{value:,.0f} cajas<br>Proporción: %{percent}<extra></extra>"
    )])

    fig.update_layout(
        title=dict(
            text="Participación por Almacén",
            font=dict(size=16, color=COLORES["gris_oscuro"], family="Georgia"),
            x=0.02
        ),
        plot_bgcolor=COLORES["blanco"],
        paper_bgcolor=COLORES["blanco"],
        height=380,
        margin=dict(l=20, r=20, t=60, b=40),
        legend=dict(orientation="v"),
        font=dict(family="Georgia, serif")
    )

    return fig


def crear_matriz_calor(
    almacenes: list[str],
    clientes: list[str],
    costos: list[list[float]]
) -> go.Figure:
    """
    Heatmap de la matriz de costos.
    """
    fig = go.Figure(data=go.Heatmap(
        z=costos,
        x=clientes,
        y=almacenes,
        colorscale=[
            [0.0, "#503E04"],
            [0.5, "#FB8C00"],
            [1.0, "#263238"]
        ],
        text=[[f"Bs {costos[i][j]}" for j in range(len(clientes))] for i in range(len(almacenes))],
        texttemplate="%{text}",
        textfont=dict(size=12, color="white"),
        hovertemplate="<b>%{y} → %{x}</b><br>Costo: Bs %{z}<extra></extra>",
        showscale=True,
        colorbar=dict(title="Bs/caja")
    ))

    fig.update_layout(
        title=dict(
            text="Matriz de Costos de Transporte (Bs/caja)",
            font=dict(size=15, color=COLORES["gris_oscuro"], family="Georgia"),
            x=0.02
        ),
        plot_bgcolor=COLORES["blanco"],
        paper_bgcolor=COLORES["blanco"],
        height=max(280, len(almacenes) * 70 + 120),
        margin=dict(l=20, r=20, t=60, b=60),
        xaxis=dict(title="Clientes", side="bottom"),
        yaxis=dict(title="Almacenes"),
        font=dict(family="Georgia, serif")
    )

    return fig
