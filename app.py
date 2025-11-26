import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Analizador Universal", layout="wide")
st.title("📊 Analizador Estadístico: Archivo o Manual")
st.markdown("---")

# ==============================
# 1. INPUT DE DATOS
# ==============================
opcion_fuente = st.radio(
    "¿Cómo quieres ingresar los datos?",
    ["📂 Subir Archivo Excel/CSV", "✍️ Escribir Datos Manualmente"],
    horizontal=True,
)

df = None
nombre_columna_analisis = "Datos"

# ------------------------------------------
# A) SUBIR ARCHIVO
# ------------------------------------------
if opcion_fuente == "📂 Subir Archivo Excel/CSV":
    archivo = st.file_uploader("Sube tu archivo aquí:", type=["xlsx", "csv"])

    if archivo:
        if archivo.name.endswith(".csv"):
            df_temp = pd.read_csv(archivo)
        else:
            df_temp = pd.read_excel(archivo)

        columna_seleccionada = st.selectbox("Selecciona la columna a analizar:", df_temp.columns)
        if columna_seleccionada:
            df = df_temp[[columna_seleccionada]].dropna()
            nombre_columna_analisis = columna_seleccionada
            df.columns = [nombre_columna_analisis]

# ------------------------------------------
# B) DATOS MANUALES
# ------------------------------------------
else:
    st.info("Ingresa tus datos separados por comas, espacios o saltos de línea.")
    datos_texto = st.text_area("Escribe tus datos aquí:", height=150)

    if datos_texto:
        texto_limpio = datos_texto.replace(",", " ").replace("\n", " ")
        lista_datos = [x.strip() for x in texto_limpio.split(" ") if x.strip()]

        if len(lista_datos) > 0:
            try:
                lista_datos = [float(x) for x in lista_datos]
            except:
                pass

            df = pd.DataFrame(lista_datos, columns=["Datos Manuales"])
            nombre_columna_analisis = "Datos Manuales"

# ==============================
# 2. ANÁLISIS
# ==============================
if df is not None and not df.empty:
    datos = df[nombre_columna_analisis]
    n = len(datos)

    es_numerico = pd.api.types.is_numeric_dtype(datos)
    valores_unicos = datos.nunique()

    # DETECCIÓN AUTOMÁTICA DEL TIPO
    if es_numerico:
        if valores_unicos < 15:
            tipo_var = "Cuantitativa Discreta (Corto Recorrido)"
            modo_analisis = "Simple"
        else:
            tipo_var = "Cuantitativa Continua (Largo Recorrido)"
            modo_analisis = "Intervalos"
    else:
        tipo_var = "Cualitativa"
        modo_analisis = "Simple"

    st.markdown("---")
    st.subheader("1. Resumen Detectado")

    c1, c2, c3 = st.columns(3)
    c1.info(f"**Muestra (n):** {n}")
    c2.info(f"**Variable:** {nombre_columna_analisis}")
    c3.info(f"**Tipo:** {tipo_var}")

    # ==============================
    # 3. TABLA DE FRECUENCIA
    # ==============================
    if modo_analisis == "Intervalos":
        k_sturges = int(1 + 3.322 * np.log10(n))
        st.caption(f"Intervalos sugeridos (Sturges): {k_sturges}")

        num_intervalos = st.slider("Número de intervalos:", 2, 20, k_sturges)

        frecuencias, bordes = np.histogram(datos, bins=num_intervalos)

        tabla_data = []
        for i in range(len(frecuencias)):
            li, ls = bordes[i], bordes[i + 1]
            marca = (li + ls) / 2
            fi = frecuencias[i]
            tabla_data.append({
                "Intervalo": f"[ {li:.2f} ; {ls:.2f} >",
                "Marca Clase (xi)": marca,
                "fi": fi
            })

        tabla = pd.DataFrame(tabla_data)
        col_grafico = "Marca Clase (xi)"

    else:
        tabla = datos.value_counts().reset_index()
        tabla.columns = ["Dato (xi)", "fi"]
        tabla = tabla.sort_values(by="Dato (xi)")
        col_grafico = "Dato (xi)"

    tabla["fi"] = tabla["fi"].astype(int)
    total = tabla["fi"].sum()
    tabla["hi"] = tabla["fi"] / total
    tabla["Fi"] = tabla["fi"].cumsum()
    tabla["Hi"] = tabla["hi"].cumsum()
    tabla["hi%"] = (tabla["hi"] * 100).round(2).astype(str) + "%"
    tabla["Hi%"] = (tabla["Hi"] * 100).round(2).astype(str) + "%"

    st.subheader("2. Tabla de Distribución de Frecuencias")
    st.dataframe(tabla, use_container_width=True)

    # ==============================
    # 4. GRÁFICOS Y MEDIDAS
    # ==============================
    st.subheader("3. Gráficos y Estadísticos")

    col_medidas, col_graficos = st.columns([1, 3])

    # --- MEDIDAS ---
    with col_medidas:
        st.write("📌 **Medidas Estadísticas**")
        try:
            st.metric("Moda", str(datos.mode()[0]))
            if es_numerico:
                st.metric("Media", f"{datos.mean():.2f}")
                st.metric("Mediana", f"{datos.median():.2f}")
                st.metric("Mínimo", f"{datos.min()}")
                st.metric("Máximo", f"{datos.max()}")
        except:
            st.warning("No se pudieron calcular medidas.")

    # --- GRÁFICOS ---
    with col_graficos:
        tab_bar, tab_pie, tab_ojiva = st.tabs(["📊 Barras / Histograma", "🥧 Circular", "📈 Ojiva"])

        # BARRAS / HISTOGRAMA
        with tab_bar:
            fig1 = go.Figure()

            fig1.add_trace(go.Bar(
                x=tabla[col_grafico],
                y=tabla["fi"],
                text=tabla["fi"],
                textposition="outside",
                marker_color="#1f77b4"
            ))

            if modo_analisis == "Intervalos":
                fig1.add_trace(go.Scatter(
                    x=tabla[col_grafico],
                    y=tabla["fi"],
                    mode="lines+markers",
                    line=dict(color="red"),
                    name="Polígono"
                ))

            fig1.update_layout(title="Frecuencias", height=500)
            st.plotly_chart(fig1, use_container_width=True)

        # PIE
        with tab_pie:
            fig2 = go.Figure(data=[go.Pie(
                labels=tabla[col_grafico],
                values=tabla["fi"],
                hole=0.3
            )])
            fig2.update_layout(title="Distribución porcentual")
            st.plotly_chart(fig2, use_container_width=True)

        # OJIVA
        with tab_ojiva:
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=tabla[col_grafico],
                y=tabla["Fi"],
                mode="lines+markers",
                fill="tozeroy",
                name="Ojiva"
            ))
            fig3.update_layout(title="Ojiva (Frecuencia Acumulada)")
            st.plotly_chart(fig3, use_container_width=True)

else:
    st.info("👆 Esperando datos para procesar.")

# =======================================================
# 🔵 SECCIÓN INFORMATIVA — AGREGADA TAL COMO PEDISTE
# =======================================================
st.markdown("""
---
## 📘 Información Estadística

### 📌 ¿Qué es una Tabla de Frecuencia?
Una tabla de frecuencia organiza los datos mostrando cuántas veces aparece cada valor.  
Permite identificar patrones, repeticiones y la distribución general de la información.

---

### 📌 Media
La media es el **promedio** de los datos. Indica el valor representativo central del conjunto numérico.

### 📌 Mediana
La mediana es el valor que divide los datos ordenados en dos partes iguales.  
Es útil cuando existen valores extremos que distorsionan el promedio.

### 📌 Moda
La moda es el valor que **más se repite** en un conjunto de datos.  
Puede haber una moda, varias o ninguna.

---

### 📌 ¿Por qué es útil analizar datos?
El análisis estadístico permite:

- Comprender tendencias  
- Detectar errores  
- Analizar fenómenos  
- Comparar grupos  
- Tomar decisiones basadas en datos reales  

---

### 📌 Aplicaciones comunes
- Investigación académica  
- Estudios de mercado  
- Control de calidad  
- Educación  
- Ciencia de Datos  
""")
