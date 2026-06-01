"""
app.py
Sistema de Optimización de Distribución de Huevos
Aplicación principal Streamlit

Materia: Investigación Operativa - Ingeniería de Sistemas
Modelo: Problema de Transporte con Programación Lineal (PuLP)
"""

import streamlit as st
import pandas as pd
import numpy as np

from transporte import resolver_transporte, construir_modelo_texto, validar_balance
from utils import (
    validar_datos_completos,
    formatear_moneda,
    formatear_numero,
    calcular_kpis,
    grafico_cantidad_por_cliente,
    grafico_cantidad_por_almacen,
    grafico_oferta_vs_demanda,
    grafico_utilizacion_almacenes,
    crear_matriz_calor,
    COLORES
)

# ============================================================
# CONFIGURACIÓN INICIAL DE STREAMLIT
# ============================================================

st.set_page_config(
    page_title="Distribución de Huevos — IO",
    page_icon="🥚",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CARGAR ESTILOS CSS
# ============================================================

def cargar_estilos():
    """Carga los estilos CSS externos."""
    try:
        with open("styles.css", "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass  # Si no encuentra el archivo, continúa sin él


cargar_estilos()


# ============================================================
# ESTADO DE SESIÓN — DATOS PREDETERMINADOS
# ============================================================

def inicializar_estado():
    """Inicializa los valores por defecto en session_state."""

    if "pagina" not in st.session_state:
        st.session_state.pagina = "Inicio"

    if "n_almacenes" not in st.session_state:
        st.session_state.n_almacenes = 3

    if "n_clientes" not in st.session_state:
        st.session_state.n_clientes = 4

    if "almacenes" not in st.session_state:
        st.session_state.almacenes = [
            "Almacén Central Miraflores",
            "Almacén Norte El Alto",
            "Almacén Sur Viacha"
        ]

    if "ofertas" not in st.session_state:
        st.session_state.ofertas = [300, 250, 200]

    if "clientes" not in st.session_state:
        st.session_state.clientes = [
            "Mercado Rodríguez",
            "Supermercado Ketal",
            "Tiendas Barrio Obrero",
            "Distribuidora El Alto"
        ]

    if "demandas" not in st.session_state:
        st.session_state.demandas = [180, 220, 150, 160]

    if "costos" not in st.session_state:
        st.session_state.costos = [
            [8,  12, 6,  15],
            [10, 9,  13, 7 ],
            [14, 11, 8,  10]
        ]

    if "resultado" not in st.session_state:
        st.session_state.resultado = None

    if "datos_validos" not in st.session_state:
        st.session_state.datos_validos = False


inicializar_estado()


# ============================================================
# SIDEBAR — NAVEGACIÓN
# ============================================================

def renderizar_sidebar():
    """Construye el sidebar con navegación y estado del sistema."""
    with st.sidebar:
        # Logo del sistema
        st.markdown("""
        <div class="sidebar-logo">
            <div class="sidebar-emoji">🥚</div>
            <h2>SistDistribución</h2>
            <p>Optimización Logística</p>
        </div>
        """, unsafe_allow_html=True)

        # Sección: Navegación
        st.markdown('<p class="sidebar-section-title">📋 Menú Principal</p>', unsafe_allow_html=True)

        paginas = {
            "🏠 Inicio": "Inicio",
            "📊 Datos": "Datos",
            "⚙️ Optimización": "Optimización",
            "📈 Resultados": "Resultados"
        }

        for etiqueta, pagina in paginas.items():
            activo = "→ " if st.session_state.pagina == pagina else "   "
            if st.button(f"{activo}{etiqueta}", key=f"nav_{pagina}", use_container_width=True):
                st.session_state.pagina = pagina
                st.rerun()

        st.markdown("---")

        # Estado del sistema
        st.markdown('<p class="sidebar-section-title">📌 Estado del Sistema</p>', unsafe_allow_html=True)

        n_alm = st.session_state.n_almacenes
        n_cli = st.session_state.n_clientes
        total_oferta = sum(st.session_state.ofertas[:n_alm])
        total_demanda = sum(st.session_state.demandas[:n_cli])

        st.markdown(f"""
        <div style="padding: 0.6rem 0.8rem; background: #37474F; border-radius: 6px; margin-bottom: 0.5rem;">
            <div style="color: #90A4AE; font-size: 0.75rem;">Almacenes / Clientes</div>
            <div style="color: #F4B400; font-weight: 700; font-size: 1rem;">{n_alm} / {n_cli}</div>
        </div>
        <div style="padding: 0.6rem 0.8rem; background: #37474F; border-radius: 6px; margin-bottom: 0.5rem;">
            <div style="color: #90A4AE; font-size: 0.75rem;">Oferta Total</div>
            <div style="color: #FB8C00; font-weight: 700; font-size: 1rem;">{total_oferta:,} cajas</div>
        </div>
        <div style="padding: 0.6rem 0.8rem; background: #37474F; border-radius: 6px; margin-bottom: 0.5rem;">
            <div style="color: #90A4AE; font-size: 0.75rem;">Demanda Total</div>
            <div style="color: #43A047; font-weight: 700; font-size: 1rem;">{total_demanda:,} cajas</div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.resultado and st.session_state.resultado.es_optimo:
            costo = st.session_state.resultado.costo_total
            st.markdown(f"""
            <div style="padding: 0.6rem 0.8rem; background: #1B5E20; border-radius: 6px; border: 1px solid #43A047;">
                <div style="color: #A5D6A7; font-size: 0.75rem;">✅ Costo Óptimo</div>
                <div style="color: #FFFFFF; font-weight: 700; font-size: 1rem;">Bs {costo:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="padding: 0.6rem 0.8rem; background: #37474F; border-radius: 6px; border: 1px solid #546E7A;">
                <div style="color: #90A4AE; font-size: 0.75rem;">⏳ Sin optimizar</div>
                <div style="color: #B0BEC5; font-size: 0.82rem;">Ejecute la optimización</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("""
        <div style="color: #546E7A; font-size: 0.72rem; text-align: center; padding: 0.5rem;">
            Investigación Operativa<br>
            Ingeniería de Sistemas<br>
            <span style="color: #F4B400;">v1.0</span>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# PÁGINA: INICIO
# ============================================================

def pagina_inicio():
    """Pantalla de presentación del sistema."""
    st.markdown("""
    <div class="system-header">
        <div style="font-size: 3rem;">🥚</div>
        <div>
            <h1>Sistema de Optimización de Distribución de Huevos</h1>
            <p>Modelo de Transporte · Programación Lineal · Método Simplex</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Columnas de información principal
    col_izq, col_der = st.columns([3, 2], gap="large")

    with col_izq:
        st.markdown("""
        <div class="section-card">
            <h3>📌 Objetivo del Sistema</h3>
            <p style="font-size: 0.95rem; line-height: 1.7; color: #37474F;">
                Determinar la <strong>distribución óptima</strong> de cajas de huevos desde almacenes 
                ubicados en La Paz y El Alto hacia diferentes clientes, minimizando el 
                <strong>costo total de transporte</strong> mediante la aplicación del 
                <strong>Modelo de Transporte</strong> y la <strong>Programación Lineal</strong>.
            </p>
            <div class="divider"></div>
            <p style="font-size: 0.9rem; line-height: 1.7; color: #546E7A;">
                El sistema aplica el <em>Método Simplex</em> a través de la librería <strong>PuLP</strong>, 
                garantizando una solución matemáticamente óptima y verificada. Los resultados 
                se presentan en tablas interactivas y visualizaciones gráficas.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="section-card">
            <h3>📦 ¿Qué es el Problema de Transporte?</h3>
            <p style="font-size: 0.9rem; line-height: 1.7; color: #37474F;">
                El <strong>Problema de Transporte</strong> es un caso especial de Programación Lineal 
                que busca encontrar el plan de distribución de menor costo para mover un bien 
                desde múltiples <em>orígenes</em> (almacenes) hacia múltiples <em>destinos</em> (clientes).
            </p>
            <p style="font-size: 0.9rem; line-height: 1.7; color: #37474F;">
                Cada origen posee una <strong>oferta limitada</strong> y cada destino tiene una 
                <strong>demanda específica</strong> que debe ser satisfecha. El objetivo es minimizar 
                el costo total respetando ambas restricciones.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_der:
        # Modelo matemático resumido
        st.markdown("""
        <div class="section-card">
            <h3>📐 Modelo de Transporte</h3>
            
            <div class="math-label">Variables de Decisión</div>
            <div class="math-block">xᵢⱼ = Cajas enviadas desde
almacén i al cliente j</div>
            
            <div class="math-label">Función Objetivo</div>
            <div class="math-block">Min Z = Σᵢ Σⱼ cᵢⱼ · xᵢⱼ</div>
            
            <div class="math-label">Restricciones de Oferta</div>
            <div class="math-block">Σⱼ xᵢⱼ ≤ Oᵢ  ∀i</div>
            
            <div class="math-label">Restricciones de Demanda</div>
            <div class="math-block">Σᵢ xᵢⱼ ≥ Dⱼ  ∀j</div>
            
            <div class="math-label">No Negatividad</div>
            <div class="math-block">xᵢⱼ ≥ 0  ∀i, j</div>
        </div>
        """, unsafe_allow_html=True)

        # Método de solución
        st.markdown("""
        <div class="info-box naranja">
            <strong>⚙️ Método de Solución:</strong> Simplex mediante PuLP<br>
            <strong>🎯 Garantía:</strong> Solución matemáticamente óptima global
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Pasos del proceso
    st.markdown("### 🔄 Flujo de Trabajo del Sistema")
    col1, col2, col3, col4 = st.columns(4)

    pasos = [
        ("1", "📊 Ingresar Datos", "Almacenes, clientes, ofertas, demandas y matriz de costos de transporte."),
        ("2", "✅ Validar", "El sistema verifica automáticamente que los datos sean correctos y completos."),
        ("3", "⚙️ Optimizar", "PuLP construye y resuelve el modelo de Programación Lineal con Simplex."),
        ("4", "📈 Analizar", "Se presentan el plan óptimo, KPIs y gráficas de distribución.")
    ]

    for col, (num, titulo, desc) in zip([col1, col2, col3, col4], pasos):
        with col:
            st.markdown(f"""
            <div class="section-card" style="text-align: center; min-height: 160px;">
                <div style="width: 38px; height: 38px; background: #FB8C00; border-radius: 50%; 
                    color: white; font-weight: 700; font-size: 1.1rem; display: flex; 
                    align-items: center; justify-content: center; margin: 0 auto 0.8rem auto;">
                    {num}
                </div>
                <strong style="font-size: 0.9rem; color: #263238;">{titulo}</strong>
                <p style="font-size: 0.82rem; color: #546E7A; margin-top: 0.5rem; line-height: 1.5;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    # Tecnologías
    st.markdown("---")
    st.markdown("### 🛠️ Tecnologías Utilizadas")
    techs = [
        ("Python", "#3776AB", "Lenguaje base"),
        ("Streamlit", "#FF4B4B", "Interfaz web"),
        ("PuLP", "#F4B400", "Solver LP / Simplex"),
        ("Pandas", "#150458", "Gestión de datos"),
        ("NumPy", "#013243", "Cálculos numéricos"),
        ("Plotly", "#3F4F75", "Visualizaciones")
    ]
    cols = st.columns(len(techs))
    for col, (nombre, color, desc) in zip(cols, techs):
        with col:
            st.markdown(f"""
            <div style="text-align: center; padding: 0.8rem 0.5rem; background: {color}15; 
                border-radius: 8px; border: 1px solid {color}40;">
                <div style="font-weight: 700; color: {color}; font-size: 0.95rem;">{nombre}</div>
                <div style="font-size: 0.75rem; color: #546E7A; margin-top: 0.2rem;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)


# ============================================================
# PÁGINA: DATOS
# ============================================================

def pagina_datos():
    """Formularios para ingresar almacenes, clientes y costos."""
    st.markdown("""
    <div class="system-header">
        <div style="font-size: 2rem;">📊</div>
        <div>
            <h1>Ingreso de Datos</h1>
            <p>Configure almacenes, clientes y la matriz de costos de transporte</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------
    # CONFIGURACIÓN: Número de almacenes y clientes
    # -------------------------------------------------------
    st.markdown("#### ⚙️ Dimensiones del Problema")
    col_conf1, col_conf2, _ = st.columns([1, 1, 2])

    with col_conf1:
        n_alm = st.number_input(
            "Número de Almacenes",
            min_value=1, max_value=8, value=st.session_state.n_almacenes,
            step=1, help="Entre 1 y 8 almacenes"
        )
    with col_conf2:
        n_cli = st.number_input(
            "Número de Clientes",
            min_value=1, max_value=10, value=st.session_state.n_clientes,
            step=1, help="Entre 1 y 10 clientes"
        )

    # Ajustar listas si cambia el número
    if n_alm != st.session_state.n_almacenes:
        while len(st.session_state.almacenes) < n_alm:
            st.session_state.almacenes.append(f"Almacén {len(st.session_state.almacenes)+1}")
            st.session_state.ofertas.append(100)
            st.session_state.costos.append([5] * st.session_state.n_clientes)
        st.session_state.n_almacenes = int(n_alm)

    if n_cli != st.session_state.n_clientes:
        while len(st.session_state.clientes) < n_cli:
            st.session_state.clientes.append(f"Cliente {len(st.session_state.clientes)+1}")
            st.session_state.demandas.append(100)
        for fila in st.session_state.costos:
            while len(fila) < n_cli:
                fila.append(5)
        st.session_state.n_clientes = int(n_cli)

    n_alm = int(n_alm)
    n_cli = int(n_cli)

    st.markdown("---")

    # -------------------------------------------------------
    # SECCIÓN: ALMACENES
    # -------------------------------------------------------
    col_alm, col_cli = st.columns(2, gap="large")

    with col_alm:
        st.markdown("""
        <div style="background: #FFF8E1; border: 1px solid #FFE082; border-top: 4px solid #F4B400; 
            border-radius: 8px; padding: 1rem 1.2rem; margin-bottom: 1rem;">
            <strong style="color: #263238;">🏭 Almacenes</strong>
            <p style="color: #546E7A; font-size: 0.82rem; margin: 0.3rem 0 0 0;">
                Ingrese nombre y oferta disponible de cada almacén
            </p>
        </div>
        """, unsafe_allow_html=True)

        for i in range(n_alm):
            c1, c2 = st.columns([2, 1])
            with c1:
                val = st.session_state.almacenes[i] if i < len(st.session_state.almacenes) else f"Almacén {i+1}"
                nuevo = st.text_input(f"Almacén {i+1}", value=val, key=f"alm_nom_{i}",
                                      placeholder="Nombre del almacén")
                if i < len(st.session_state.almacenes):
                    st.session_state.almacenes[i] = nuevo
            with c2:
                val_of = st.session_state.ofertas[i] if i < len(st.session_state.ofertas) else 100
                nueva_of = st.number_input("Oferta (cajas)", value=int(val_of),
                                           min_value=1, step=10, key=f"alm_of_{i}")
                if i < len(st.session_state.ofertas):
                    st.session_state.ofertas[i] = int(nueva_of)

        # Total oferta
        total_oferta = sum(st.session_state.ofertas[:n_alm])
        st.markdown(f"""
        <div style="background: #37474F; color: #F4B400; padding: 0.6rem 1rem; 
            border-radius: 6px; font-weight: 700; text-align: right; margin-top: 0.5rem;">
            Total Oferta: {total_oferta:,} cajas
        </div>
        """, unsafe_allow_html=True)

    # -------------------------------------------------------
    # SECCIÓN: CLIENTES
    # -------------------------------------------------------
    with col_cli:
        st.markdown("""
        <div style="background: #E8F5E9; border: 1px solid #A5D6A7; border-top: 4px solid #43A047; 
            border-radius: 8px; padding: 1rem 1.2rem; margin-bottom: 1rem;">
            <strong style="color: #263238;">🛒 Clientes</strong>
            <p style="color: #546E7A; font-size: 0.82rem; margin: 0.3rem 0 0 0;">
                Ingrese nombre y demanda requerida de cada cliente
            </p>
        </div>
        """, unsafe_allow_html=True)

        for j in range(n_cli):
            c1, c2 = st.columns([2, 1])
            with c1:
                val = st.session_state.clientes[j] if j < len(st.session_state.clientes) else f"Cliente {j+1}"
                nuevo = st.text_input(f"Cliente {j+1}", value=val, key=f"cli_nom_{j}",
                                      placeholder="Nombre del cliente")
                if j < len(st.session_state.clientes):
                    st.session_state.clientes[j] = nuevo
            with c2:
                val_dem = st.session_state.demandas[j] if j < len(st.session_state.demandas) else 100
                nueva_dem = st.number_input("Demanda (cajas)", value=int(val_dem),
                                            min_value=1, step=10, key=f"cli_dem_{j}")
                if j < len(st.session_state.demandas):
                    st.session_state.demandas[j] = int(nueva_dem)

        # Total demanda
        total_demanda = sum(st.session_state.demandas[:n_cli])
        st.markdown(f"""
        <div style="background: #1B5E20; color: #A5D6A7; padding: 0.6rem 1rem; 
            border-radius: 6px; font-weight: 700; text-align: right; margin-top: 0.5rem;">
            Total Demanda: {total_demanda:,} cajas
        </div>
        """, unsafe_allow_html=True)

    # -------------------------------------------------------
    # BALANCE OFERTA - DEMANDA
    # -------------------------------------------------------
    total_o = sum(st.session_state.ofertas[:n_alm])
    total_d = sum(st.session_state.demandas[:n_cli])
    _, tipo_balance, msg_balance = validar_balance(
        st.session_state.ofertas[:n_alm],
        st.session_state.demandas[:n_cli]
    )

    color_balance = {
        "balanceado": ("#E8F5E9", "#43A047", "#1B5E20", "✅"),
        "superavit":  ("#FFF3E0", "#FB8C00", "#E65100", "ℹ️"),
        "deficit":    ("#FFF3E0", "#FB8C00", "#E65100", "ℹ️")
    }
    bg, brd, txt, ico = color_balance.get(tipo_balance, ("#FFF8E1", "#F4B400", "#5D4037", "⚠️"))

    st.markdown(f"""
    <div style="background: {bg}; border: 1px solid {brd}; border-radius: 8px; 
        padding: 0.7rem 1.2rem; margin: 0.8rem 0;">
        <strong style="color: {txt};">{ico} Balance: {msg_balance}</strong>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # -------------------------------------------------------
    # MATRIZ DE COSTOS
    # -------------------------------------------------------
    st.markdown("""
    <div style="background: #FFF3E0; border: 1px solid #FFCC80; border-top: 4px solid #FB8C00; 
        border-radius: 8px; padding: 1rem 1.2rem; margin-bottom: 1rem;">
        <strong style="color: #263238;">💰 Matriz de Costos de Transporte</strong>
        <p style="color: #546E7A; font-size: 0.82rem; margin: 0.3rem 0 0 0;">
            Ingrese el costo unitario (Bs/caja) de transportar desde cada almacén hacia cada cliente
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Asegurar que la matriz tenga el tamaño correcto
    while len(st.session_state.costos) < n_alm:
        st.session_state.costos.append([5] * n_cli)
    for i in range(n_alm):
        while len(st.session_state.costos[i]) < n_cli:
            st.session_state.costos[i].append(5)

    # Encabezados de la tabla
    header_cols = st.columns([2] + [1] * n_cli)
    header_cols[0].markdown(
        "<div style='font-weight:700; color:#546E7A; font-size:0.82rem; padding:0.3rem 0;'>Almacén \\ Cliente</div>",
        unsafe_allow_html=True
    )
    for j in range(n_cli):
        nombre_cli = st.session_state.clientes[j] if j < len(st.session_state.clientes) else f"C{j+1}"
        header_cols[j+1].markdown(
            f"<div style='font-weight:700; color:#43A047; font-size:0.78rem; text-align:center; "
            f"padding:0.3rem 0;'>{nombre_cli[:12]}</div>",
            unsafe_allow_html=True
        )

    # Filas de costos
    for i in range(n_alm):
        row_cols = st.columns([2] + [1] * n_cli)
        nombre_alm = st.session_state.almacenes[i] if i < len(st.session_state.almacenes) else f"A{i+1}"
        row_cols[0].markdown(
            f"<div style='font-weight:600; color:#F4B400; font-size:0.85rem; "
            f"padding:0.4rem 0; white-space:nowrap; overflow:hidden;'>{nombre_alm[:18]}</div>",
            unsafe_allow_html=True
        )
        for j in range(n_cli):
            val_costo = st.session_state.costos[i][j] if (i < len(st.session_state.costos) and
                                                           j < len(st.session_state.costos[i])) else 5
            nuevo_costo = row_cols[j+1].number_input(
                f"c_{i}_{j}", value=float(val_costo),
                min_value=0.0, step=1.0,
                key=f"costo_{i}_{j}",
                label_visibility="collapsed"
            )
            st.session_state.costos[i][j] = float(nuevo_costo)

    # Vista previa del heatmap de costos
    st.markdown("---")
    st.markdown("#### 🔥 Vista Previa: Mapa de Calor de Costos")
    costos_vista = [st.session_state.costos[i][:n_cli] for i in range(n_alm)]
    alm_vista = st.session_state.almacenes[:n_alm]
    cli_vista = st.session_state.clientes[:n_cli]
    
    if alm_vista and cli_vista:
        fig_heat = crear_matriz_calor(alm_vista, cli_vista, costos_vista)
        st.plotly_chart(fig_heat, use_container_width=True)

    # Botón: guardar y validar
    st.markdown("---")
    col_btn, col_msg = st.columns([1, 2])
    with col_btn:
        if st.button("✅ Guardar y Validar Datos", type="primary", use_container_width=True):
            almacenes_act = st.session_state.almacenes[:n_alm]
            clientes_act = st.session_state.clientes[:n_cli]
            ofertas_act = st.session_state.ofertas[:n_alm]
            demandas_act = st.session_state.demandas[:n_cli]
            costos_act = [st.session_state.costos[i][:n_cli] for i in range(n_alm)]

            es_valido, errores = validar_datos_completos(
                almacenes_act, clientes_act, ofertas_act, demandas_act, costos_act
            )

            if es_valido:
                st.session_state.datos_validos = True
                st.session_state.resultado = None  # Resetear resultado anterior
                with col_msg:
                    st.success("✅ Datos validados correctamente. Puede proceder a la optimización.")
            else:
                st.session_state.datos_validos = False
                with col_msg:
                    for err in errores:
                        st.error(f"❌ {err}")


# ============================================================
# PÁGINA: OPTIMIZACIÓN
# ============================================================

def pagina_optimizacion():
    """Construcción del modelo y ejecución del solver."""
    st.markdown("""
    <div class="system-header">
        <div style="font-size: 2rem;">⚙️</div>
        <div>
            <h1>Optimización del Modelo de Transporte</h1>
            <p>Construcción y resolución mediante Programación Lineal con Método Simplex (PuLP)</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    n_alm = st.session_state.n_almacenes
    n_cli = st.session_state.n_clientes
    almacenes = st.session_state.almacenes[:n_alm]
    clientes = st.session_state.clientes[:n_cli]
    ofertas = st.session_state.ofertas[:n_alm]
    demandas = st.session_state.demandas[:n_cli]
    costos = [st.session_state.costos[i][:n_cli] for i in range(n_alm)]

    # -------------------------------------------------------
    # MODELO MATEMÁTICO ACTUAL
    # -------------------------------------------------------
    col_mod, col_act = st.columns([3, 2], gap="large")

    with col_mod:
        st.markdown("### 📐 Modelo Matemático Construido")
        st.markdown("""
        <div class="info-box">
            El modelo se construye automáticamente con los datos ingresados. 
            Verifique que las variables y restricciones correspondan a su problema.
        </div>
        """, unsafe_allow_html=True)

        # Función objetivo
        modelo_txt = construir_modelo_texto(almacenes, clientes, ofertas, demandas, costos)

        st.markdown('<div class="math-label">Función Objetivo — Minimizar Costo Total</div>',
                    unsafe_allow_html=True)
        fo_display = "Min Z = " + " + ".join(
            [f"{costos[i][j]}·x{i+1}{j+1}" for i in range(n_alm) for j in range(n_cli)]
        )
        st.markdown(f'<div class="math-block">{fo_display}</div>', unsafe_allow_html=True)

        # Restricciones de oferta
        st.markdown('<div class="math-label">Restricciones de Oferta (≤ Oᵢ)</div>',
                    unsafe_allow_html=True)
        texto_oferta = "\n".join(modelo_txt["restricciones_oferta"])
        st.markdown(f'<div class="math-block">{texto_oferta}</div>', unsafe_allow_html=True)

        # Restricciones de demanda
        st.markdown('<div class="math-label">Restricciones de Demanda (≥ Dⱼ)</div>',
                    unsafe_allow_html=True)
        texto_demanda = "\n".join(modelo_txt["restricciones_demanda"])
        st.markdown(f'<div class="math-block">{texto_demanda}</div>', unsafe_allow_html=True)

        # No negatividad
        st.markdown('<div class="math-label">Condición de No Negatividad</div>',
                    unsafe_allow_html=True)
        st.markdown(f'<div class="math-block">{modelo_txt["no_negatividad"]}</div>',
                    unsafe_allow_html=True)

    with col_act:
        st.markdown("### 📋 Resumen del Problema")

        # Tabla de almacenes
        df_alm = pd.DataFrame({
            "Almacén": almacenes,
            "Oferta (cajas)": ofertas
        })
        st.markdown("**Almacenes**")
        st.dataframe(df_alm, use_container_width=True, hide_index=True)

        # Tabla de clientes
        df_cli = pd.DataFrame({
            "Cliente": clientes,
            "Demanda (cajas)": demandas
        })
        st.markdown("**Clientes**")
        st.dataframe(df_cli, use_container_width=True, hide_index=True)

        # Estadísticas
        st.markdown(f"""
        <div style="background: #263238; color: #FFFFFF; padding: 1rem; border-radius: 8px; margin-top: 0.5rem;">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem;">
                <div>
                    <div style="color: #90A4AE; font-size: 0.75rem;">Variables</div>
                    <div style="color: #F4B400; font-weight: 700; font-size: 1.2rem;">{n_alm * n_cli}</div>
                </div>
                <div>
                    <div style="color: #90A4AE; font-size: 0.75rem;">Restricciones</div>
                    <div style="color: #FB8C00; font-weight: 700; font-size: 1.2rem;">{n_alm + n_cli}</div>
                </div>
                <div>
                    <div style="color: #90A4AE; font-size: 0.75rem;">Oferta Total</div>
                    <div style="color: #43A047; font-weight: 700;">{sum(ofertas):,} cajas</div>
                </div>
                <div>
                    <div style="color: #90A4AE; font-size: 0.75rem;">Demanda Total</div>
                    <div style="color: #43A047; font-weight: 700;">{sum(demandas):,} cajas</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # -------------------------------------------------------
    # BOTÓN DE OPTIMIZACIÓN
    # -------------------------------------------------------
    st.markdown("### 🚀 Ejecutar Optimización")
    col_btn, col_info = st.columns([1, 2])

    with col_btn:
        st.markdown('<div class="main-action-btn">', unsafe_allow_html=True)
        ejecutar = st.button(
            "⚡ Calcular Distribución Óptima",
            type="primary",
            use_container_width=True,
            help="Resuelve el modelo de transporte usando el Método Simplex"
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with col_info:
        st.markdown("""
        <div class="info-box naranja">
            <strong>ℹ️ Proceso de Optimización:</strong><br>
            1. Construye el modelo de PL con variables, función objetivo y restricciones<br>
            2. Aplica el Método Simplex mediante PuLP (CBC Solver)<br>
            3. Garantiza la solución globalmente óptima<br>
            4. Valida automáticamente el balance oferta-demanda
        </div>
        """, unsafe_allow_html=True)

    if ejecutar:
        # Validar datos antes de optimizar
        es_valido, errores = validar_datos_completos(
            almacenes, clientes, ofertas, demandas, costos
        )

        if not es_valido:
            st.markdown("""
            <div class="status-error">
                <h4>❌ Error de Validación</h4>
            """, unsafe_allow_html=True)
            for err in errores:
                st.error(err)
            st.markdown("</div>", unsafe_allow_html=True)
            return

        # Ejecutar resolución
        with st.spinner("⚙️ Resolviendo modelo de Programación Lineal..."):
            resultado = resolver_transporte(
                almacenes, clientes, ofertas, demandas, costos
            )
            st.session_state.resultado = resultado
            st.session_state.datos_validos = True

        if resultado.es_optimo:
            st.markdown(f"""
            <div class="status-optimal">
                <h4>✅ Solución Óptima Encontrada</h4>
                <p>{resultado.mensaje} — Costo total mínimo: <strong>Bs {resultado.costo_total:,.2f}</strong></p>
            </div>
            """, unsafe_allow_html=True)
            st.info("💡 Diríjase a la sección **Resultados** para ver el análisis completo.")
        else:
            st.markdown(f"""
            <div class="status-error">
                <h4>❌ No se encontró solución óptima</h4>
                <p>{resultado.mensaje}</p>
            </div>
            """, unsafe_allow_html=True)


# ============================================================
# PÁGINA: RESULTADOS
# ============================================================

def pagina_resultados():
    """Muestra todos los resultados de la optimización."""
    st.markdown("""
    <div class="system-header">
        <div style="font-size: 2rem;">📈</div>
        <div>
            <h1>Resultados de la Optimización</h1>
            <p>Plan de distribución óptimo y análisis de la solución</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    resultado = st.session_state.resultado

    # Sin resultados
    if resultado is None:
        st.markdown("""
        <div class="info-box naranja">
            <strong>⚠️ Sin resultados disponibles.</strong><br>
            Primero ingrese los datos y ejecute la optimización en la sección <em>Optimización</em>.
        </div>
        """, unsafe_allow_html=True)
        if st.button("→ Ir a Optimización"):
            st.session_state.pagina = "Optimización"
            st.rerun()
        return

    if not resultado.es_optimo:
        st.markdown(f"""
        <div class="status-error">
            <h4>❌ Sin solución óptima</h4>
            <p>{resultado.mensaje}</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # -------------------------------------------------------
    # ESTADO DE LA SOLUCIÓN
    # -------------------------------------------------------
    st.markdown("""
    <div class="status-optimal">
        <h4>✅ Solución Óptima Encontrada — Método Simplex (PuLP)</h4>
        <p>El modelo de Programación Lineal fue resuelto exitosamente. 
        La solución garantiza el mínimo costo de transporte cumpliendo todas las restricciones.</p>
    </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------
    # KPIs PRINCIPALES
    # -------------------------------------------------------
    kpis = calcular_kpis(resultado)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="kpi-card-hero">
            <div class="kpi-label">💰 Costo Total Mínimo</div>
            <div class="kpi-value">Bs {kpis['costo_total']:,.2f}</div>
            <div class="kpi-sub">Solución globalmente óptima</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card naranja">
            <div class="kpi-label">📦 Total Distribuido</div>
            <div class="kpi-value">{kpis['total_enviado']:,.0f}</div>
            <div class="kpi-sub">cajas de huevos</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card verde">
            <div class="kpi-label">🛣️ Rutas Activas</div>
            <div class="kpi-value">{kpis['n_rutas']}</div>
            <div class="kpi-sub">de {st.session_state.n_almacenes * st.session_state.n_clientes} posibles</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="kpi-card oscuro">
            <div class="kpi-label">📊 Costo Promedio</div>
            <div class="kpi-value">Bs {kpis['costo_promedio']:.2f}</div>
            <div class="kpi-sub">por caja transportada</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------------------------------
    # PLAN DE DISTRIBUCIÓN
    # -------------------------------------------------------
    st.markdown("### 📋 Plan de Distribución Óptimo")
    st.markdown("""
    <p style="color: #546E7A; font-size: 0.9rem; margin-bottom: 1rem;">
        Rutas de transporte con flujo positivo — cantidad de cajas a enviar por cada ruta.
    </p>
    """, unsafe_allow_html=True)

    if not resultado.plan_distribucion.empty:
        df_plan = resultado.plan_distribucion.copy()

        # Formatear columnas
        df_mostrar = df_plan.rename(columns={
            "Cantidad Enviada (cajas)": "Cantidad (cajas)",
            "Costo Unitario (Bs)": "C. Unitario (Bs)",
            "Costo Total Ruta (Bs)": "Costo Ruta (Bs)"
        })

        st.dataframe(
            df_mostrar,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Almacén": st.column_config.TextColumn("🏭 Almacén", width="medium"),
                "Cliente": st.column_config.TextColumn("🛒 Cliente", width="medium"),
                "Cantidad (cajas)": st.column_config.NumberColumn("📦 Cantidad (cajas)", format="%,.0f"),
                "C. Unitario (Bs)": st.column_config.NumberColumn("💵 C. Unitario (Bs)", format="%.2f"),
                "Costo Ruta (Bs)": st.column_config.NumberColumn("💰 Costo Ruta (Bs)", format="%,.2f")
            }
        )

        # Total
        st.markdown(f"""
        <div style="text-align: right; padding: 0.5rem 1rem; background: #263238; 
            color: #F4B400; border-radius: 6px; font-weight: 700; margin-top: 0.3rem;">
            COSTO TOTAL MÍNIMO: Bs {resultado.costo_total:,.2f}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # -------------------------------------------------------
    # OFERTA UTILIZADA Y DEMANDA ATENDIDA
    # -------------------------------------------------------
    col_of, col_dem = st.columns(2, gap="large")

    with col_of:
        st.markdown("### 🏭 Oferta Utilizada por Almacén")
        if not resultado.oferta_utilizada.empty:
            st.dataframe(
                resultado.oferta_utilizada,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Almacén": st.column_config.TextColumn("Almacén"),
                    "Oferta Total (cajas)": st.column_config.NumberColumn("Oferta Total", format="%,.0f"),
                    "Cantidad Enviada (cajas)": st.column_config.NumberColumn("Enviado", format="%,.0f"),
                    "Stock Restante (cajas)": st.column_config.NumberColumn("Stock Rest.", format="%,.0f"),
                    "Utilización (%)": st.column_config.ProgressColumn(
                        "Utilización (%)", min_value=0, max_value=100, format="%.1f%%"
                    )
                }
            )

    with col_dem:
        st.markdown("### 🛒 Demanda Atendida por Cliente")
        if not resultado.demanda_atendida.empty:
            st.dataframe(
                resultado.demanda_atendida,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Cliente": st.column_config.TextColumn("Cliente"),
                    "Demanda (cajas)": st.column_config.NumberColumn("Demanda", format="%,.0f"),
                    "Cantidad Recibida (cajas)": st.column_config.NumberColumn("Recibido", format="%,.0f"),
                    "Estado": st.column_config.TextColumn("Estado"),
                    "Cobertura (%)": st.column_config.ProgressColumn(
                        "Cobertura (%)", min_value=0, max_value=100, format="%.1f%%"
                    )
                }
            )

    st.markdown("---")

    # -------------------------------------------------------
    # VISUALIZACIONES
    # -------------------------------------------------------
    st.markdown("### 📊 Visualizaciones del Plan Óptimo")

    # Gráfico 1 y 2 en fila
    col_g1, col_g2 = st.columns(2, gap="large")

    with col_g1:
        st.markdown("#### Cantidad Enviada por Cliente")
        fig1 = grafico_cantidad_por_cliente(resultado.plan_distribucion)
        st.plotly_chart(fig1, use_container_width=True)

    with col_g2:
        st.markdown("#### Distribución por Almacén")
        fig2 = grafico_cantidad_por_almacen(resultado.oferta_utilizada)
        st.plotly_chart(fig2, use_container_width=True)

    # Gráfico 3 y 4 en fila
    col_g3, col_g4 = st.columns(2, gap="large")

    with col_g3:
        st.markdown("#### Comparación Oferta vs Demanda")
        fig3 = grafico_oferta_vs_demanda(resultado.oferta_utilizada, resultado.demanda_atendida)
        st.plotly_chart(fig3, use_container_width=True)

    with col_g4:
        st.markdown("#### Participación por Almacén")
        fig4 = grafico_utilizacion_almacenes(resultado.oferta_utilizada)
        st.plotly_chart(fig4, use_container_width=True)

    # -------------------------------------------------------
    # VARIABLES DE DECISIÓN (DETALLE TÉCNICO)
    # -------------------------------------------------------
    st.markdown("---")
    st.markdown("### 🔢 Variables de Decisión — Detalle Técnico")

    with st.expander("Ver todas las variables xᵢⱼ del modelo resuelto", expanded=False):
        if resultado.variables:
            vars_data = []
            for nombre_var, valor in resultado.variables.items():
                vars_data.append({
                    "Variable": nombre_var,
                    "Valor (cajas)": valor,
                    "Estado": "Activa" if valor > 0.001 else "Inactiva (= 0)"
                })

            df_vars = pd.DataFrame(vars_data)
            st.dataframe(
                df_vars,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Variable": st.column_config.TextColumn("Variable xᵢⱼ"),
                    "Valor (cajas)": st.column_config.NumberColumn("Valor óptimo", format="%,.2f"),
                    "Estado": st.column_config.TextColumn("Estado")
                }
            )

    # Nota metodológica
    st.markdown("""
    <div class="info-box verde" style="margin-top: 1rem;">
        <strong>📌 Nota Metodológica:</strong> La solución fue obtenida mediante el 
        <em>Método Simplex</em> implementado en el solver CBC de PuLP. 
        El algoritmo garantiza que no existe ninguna otra asignación de transporte con menor costo 
        que cumpla las restricciones de oferta y demanda establecidas.
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# ENRUTAMIENTO PRINCIPAL
# ============================================================

def main():
    """Función principal — renderiza sidebar y página activa."""
    renderizar_sidebar()

    pagina = st.session_state.pagina

    if pagina == "Inicio":
        pagina_inicio()
    elif pagina == "Datos":
        pagina_datos()
    elif pagina == "Optimización":
        pagina_optimizacion()
    elif pagina == "Resultados":
        pagina_resultados()


if __name__ == "__main__":
    main()
