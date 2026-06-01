# 🥚 Sistema de Optimización de Distribución de Huevos

**Materia:** Investigación Operativa — Ingeniería de Sistemas  
**Modelo:** Problema de Transporte con Programación Lineal  
**Solver:** Método Simplex mediante PuLP (CBC)

---

## 📋 Descripción

Sistema web desarrollado con **Streamlit** que determina la **distribución óptima de cajas de huevos** desde almacenes ubicados en La Paz y El Alto hacia distintos clientes, minimizando el costo total de transporte.

Aplica el **Modelo de Transporte** como caso especial de **Programación Lineal**, resuelto mediante el **Método Simplex** implementado en la librería PuLP.

---

## 🏗️ Estructura del Proyecto

```
/project
├── app.py            # Aplicación principal Streamlit (UI + enrutamiento)
├── transporte.py     # Motor de optimización con PuLP (modelo PL)
├── utils.py          # Validaciones, formateo y gráficos Plotly
├── styles.css        # Estilos CSS del dashboard
├── requirements.txt  # Dependencias Python
└── README.md         # Este archivo
```

---

## 📐 Modelo Matemático

### Variables de Decisión
```
xᵢⱼ = Cantidad de cajas a enviar desde almacén i hacia cliente j
```

### Función Objetivo
```
Min Z = Σᵢ Σⱼ cᵢⱼ · xᵢⱼ
```

### Restricciones
```
Oferta:      Σⱼ xᵢⱼ ≤ Oᵢ    para todo i  (no exceder oferta de almacén)
Demanda:     Σᵢ xᵢⱼ ≥ Dⱼ    para todo j  (satisfacer demanda de cliente)
No negativ.: xᵢⱼ ≥ 0         para todo i,j
```

---

## 🖥️ Menú Principal

| Sección         | Descripción |
|-----------------|-------------|
| 🏠 **Inicio**    | Presentación del sistema, modelo matemático y flujo de trabajo |
| 📊 **Datos**     | Ingreso de almacenes, clientes, ofertas, demandas y matriz de costos |
| ⚙️ **Optimización** | Visualización del modelo construido y ejecución del solver |
| 📈 **Resultados** | Plan óptimo, KPIs, tablas de análisis y gráficos interactivos |

---

## 🚀 Instalación y Ejecución

### 1. Clonar o descargar el proyecto
```bash
cd egg_distribution_system
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Ejecutar la aplicación
```bash
streamlit run app.py
```

### 4. Abrir en el navegador
```
http://localhost:8501
```

---

## 📊 Datos de Ejemplo Incluidos

El sistema viene precargado con un problema de ejemplo real:

| Almacén               | Oferta |
|-----------------------|--------|
| Almacén Central Miraflores | 300 cajas |
| Almacén Norte El Alto | 250 cajas |
| Almacén Sur Viacha    | 200 cajas |

| Cliente               | Demanda |
|-----------------------|---------|
| Mercado Rodríguez     | 180 cajas |
| Supermercado Ketal    | 220 cajas |
| Tiendas Barrio Obrero | 150 cajas |
| Distribuidora El Alto | 160 cajas |

**Matriz de Costos (Bs/caja):**
```
               Merc.Rodr.  Ketal  Bar.Obr.  Distrib.El Alto
Alm.Central       8         12      6           15
Alm.Norte        10          9     13            7
Alm.Sur          14         11      8           10
```

---

## 🛠️ Tecnologías

| Tecnología  | Versión  | Uso |
|-------------|----------|-----|
| Python      | ≥ 3.10   | Lenguaje base |
| Streamlit   | ≥ 1.32   | Interfaz web |
| PuLP        | ≥ 2.7    | Solver LP / Simplex |
| Pandas      | ≥ 2.0    | Gestión de datos |
| NumPy       | ≥ 1.24   | Cálculos numéricos |
| Plotly      | ≥ 5.18   | Visualizaciones interactivas |

---

## 🎨 Paleta de Colores

| Color       | Hex       | Uso |
|-------------|-----------|-----|
| Amarillo    | `#F4B400` | Elementos primarios, sidebar |
| Naranja     | `#FB8C00` | Botón principal, alertas |
| Verde       | `#43A047` | Éxito, demanda |
| Gris Oscuro | `#263238` | Sidebar, fondo tarjetas |
| Gris Claro  | `#F5F5F5` | Fondos secundarios |
| Blanco      | `#FFFFFF` | Fondo principal |

---

## 📌 Características del Sistema

- ✅ Datos gestionados completamente en el sistema (sin base de datos)
- ✅ Validación automática de datos antes de optimizar
- ✅ Modelo balanceado automáticamente (superávit / déficit)
- ✅ KPIs destacados con tarjetas visuales
- ✅ 4 gráficos interactivos con Plotly
- ✅ Mapa de calor de la matriz de costos
- ✅ Tabla de variables de decisión del modelo
- ✅ Diseño responsive y profesional

---

## 📚 Referencias Teóricas

- Taha, H. A. — *Investigación de Operaciones* (10ma Ed.)
- Hillier & Lieberman — *Introducción a la Investigación de Operaciones*
- PuLP Documentation — https://coin-or.github.io/pulp/

---

*Desarrollado para la materia de Investigación Operativa — Ingeniería de Sistemas*
