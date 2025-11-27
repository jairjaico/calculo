import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import math

# ==============================
# CONFIGURACIÓN INICIAL
# ==============================
st.set_page_config(
    page_title="Analizador Universal",
    layout="wide",
    page_icon="📊" 
)

# --- CSS PARA OCULTAR MENÚ Y HEADER ---
hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    .stAppDeployButton {display:none;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """
st.markdown(hide_menu_style, unsafe_allow_html=True)

# ==============================
# 0. TÍTULO CON REDIRECCIÓN
# ==============================
st.markdown("""
    <a href="https://wondrous-sawine-993b24.netlify.app/" target="_self" style="text-decoration: none; color: inherit;">
        <h1 style="margin-top: 0; padding-top: 0;">📊 Analizador Estadístico: Archivo o Manual</h1>
    </a>
    """, unsafe_allow_html=True)

st.caption("👆 Haz clic en el título para volver a la página de inicio.")
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

if opcion_fuente == "📂 Subir Archivo Excel/CSV":
    archivo = st.file_uploader("Sube tu archivo aquí:", type=["xlsx", "csv"])
    if archivo:
        # --- LECTURA ROBUSTA DE CSV/EXCEL ---
        try:
            if archivo.name.endswith(".csv"):
                # Intento 1: Autodetección inteligente
                try:
                    df_temp = pd.read_csv(archivo, sep=None, engine='python')
                except:
                    # Intento 2: Forzar punto y coma (común en español)
                    archivo.seek(0)
                    df_temp = pd.read_csv(archivo, sep=';')
            else:
                df_temp = pd.read_excel(archivo)
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")
            st.stop()
            
        columna_seleccionada = st.selectbox("Selecciona la columna a analizar:", df_temp.columns)
        
        if columna_seleccionada:
            # --- LIMPIEZA DE DATOS ---
            # 1. Convertimos a string
            serie_sucia = df_temp[columna_seleccionada].astype(str)
            # 2. Reemplazamos coma por punto (12,5 -> 12.5)
            serie_sucia = serie_sucia.str.replace(',', '.')
            # 3. Convertimos a números, los errores se vuelven NaN
            datos_limpios = pd.to_numeric(serie_sucia, errors='coerce')
            
            # 4. Creamos el DataFrame final eliminando vacíos
            df = pd.DataFrame(datos_limpios).dropna()
            nombre_columna_analisis = columna_seleccionada
            df.columns = [nombre_columna_analisis]
            
            # Verificación de seguridad
            if df.empty:
                st.warning("⚠️ La columna seleccionada no contiene números válidos después de limpiar. Intenta con otra columna.")
                df = None

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

    st.markdown("---")
    st.subheader("1. Configuración del Análisis")
    
    col_conf1, col_conf2 = st.columns(2)
    with col_conf1:
        tipo_seleccion = st.radio(
            "Selecciona el tipo de cálculo:",
            ["Datos No Agrupados (Simple)", "Datos Agrupados (Intervalos)"],
            index=1 
        )
    
    if tipo_seleccion == "Datos Agrupados (Intervalos)":
        modo_analisis = "Intervalos"
    else:
        modo_analisis = "Simple"

    with col_conf2:
        st.info(f"**Muestra válida (n):** {n}")
        st.info(f"**Modo:** {modo_analisis}")

    # ==============================
    # 3. TABLA DE FRECUENCIA
    # ==============================
    tabla_calculo = [] 
    amplitud_res = 0 
    
    if modo_analisis == "Intervalos":
        if n > 0:
            val_sturges = 1 + 3.322 * np.log10(n)
            k_sturges = int(val_sturges) if val_sturges > 0 else 5
        else:
            k_sturges = 5 

        st.caption(f"Intervalos sugeridos (Regla de Sturges): {k_sturges}")
        
        num_intervalos = st.slider("Número de intervalos (k):", 2, 30, k_sturges)

        # Generación de histograma segura
        try:
            frecuencias, bordes = np.histogram(datos, bins=num_intervalos)
        except Exception as e:
            st.error(f"Error calculando intervalos: {e}. Revisa tus datos.")
            st.stop()
        
        amplitud_res = bordes[1] - bordes[0]

        # Construcción de la tabla
        for i in range(len(frecuencias)):
            li, ls = bordes[i], bordes[i + 1]
            marca = (li + ls) / 2
            fi = frecuencias[i]
            
            if i == len(frecuencias) - 1:
                str_intervalo = f"[ {li:.2f} ; {ls:.2f} ]"
            else:
                str_intervalo = f"[ {li:.2f} ; {ls:.2f} >"
            
            tabla_calculo.append({
                "Intervalo": str_intervalo,
                "Li": li,
                "Ls": ls,
                "Marca Clase (xi)": marca,
                "fi": fi
            })

        tabla = pd.DataFrame(tabla_calculo)
        
        cols = ["Intervalo", "Marca Clase (xi)", "fi"]
        tabla_view = tabla[cols].copy() 
        col_grafico = "Marca Clase (xi)"

    else:
        # Modo Simple
        tabla = datos.value_counts().reset_index()
        tabla.columns = ["Dato (xi)", "fi"]
        tabla = tabla.sort_values(by="Dato (xi)")
        col_grafico = "Dato (xi)"
        tabla_view = tabla.copy()

    # Cálculos acumulados
    tabla["fi"] = tabla["fi"].astype(int)
    total = tabla["fi"].sum()
    tabla["hi"] = tabla["fi"] / total
    tabla["Fi"] = tabla["fi"].cumsum()
    tabla["Hi"] = tabla["hi"].cumsum()
    
    tabla_view["fi"] = tabla["fi"]
    tabla_view["hi"] = tabla["hi"]
    tabla_view["Fi"] = tabla["Fi"]
    tabla_view["Hi"] = tabla["Hi"]
    tabla_view["hi%"] = (tabla["hi"] * 100).round(2).astype(str) + "%"
    tabla_view["Hi%"] = (tabla["Hi"] * 100).round(2).astype(str) + "%"

    st.subheader("2. Tabla de Distribución de Frecuencias")
    st.dataframe(tabla_view, use_container_width=True, hide_index=True)

    # ==============================
    # 4. CÁLCULOS MATEMÁTICOS
    # ==============================
    st.subheader("3. Gráficos y Estadísticos")
    
    media_res = 0
    mediana_res = 0
    moda_res = 0
    rango_res = 0
    std_res = 0
    min_res = datos.min()
    max_res = datos.max()

    if es_numerico:
        if modo_analisis == "Intervalos":
            # --- FÓRMULAS PARA DATOS AGRUPADOS ---
            
            # 1. MEDIA PONDERADA
            tabla["xi_fi"] = tabla["Marca Clase (xi)"] * tabla["fi"]
            media_res = tabla["xi_fi"].sum() / n
            
            # 2. MEDIANA (Interpolación)
            posicion_mediana = n / 2
            intervalo_mediana_df = tabla[tabla["Fi"] >= posicion_mediana]
            
            if not intervalo_mediana_df.empty:
                intervalo_mediana = intervalo_mediana_df.iloc[0]
                Li_med = intervalo_mediana["Li"]
                fi_med = intervalo_mediana["fi"]
                idx_med = intervalo_mediana_df.index[0]
                Fi_ant = tabla.iloc[idx_med - 1]["Fi"] if idx_med > 0 else 0
                
                if fi_med > 0:
                    mediana_res = Li_med + ((posicion_mediana - Fi_ant) / fi_med) * amplitud_res
                else:
                    mediana_res = Li_med
            else:
                mediana_res = 0
            
            # 3. MODA (Interpolación)
            idx_moda = tabla["fi"].idxmax()
            row_moda = tabla.loc[idx_moda]
            fi_modal = row_moda["fi"]
            Li_mod = row_moda["Li"]
            
            fi_ant_mod = tabla.loc[idx_moda - 1]["fi"] if idx_moda > 0 else 0
            fi_sig_mod = tabla.loc[idx_moda + 1]["fi"] if idx_moda < len(tabla) - 1 else 0
            
            d1 = fi_modal - fi_ant_mod
            d2 = fi_modal - fi_sig_mod
            
            if (d1 + d2) == 0:
                moda_res = row_moda["Marca Clase (xi)"]
            else:
                moda_res = Li_mod + (d1 / (d1 + d2)) * amplitud_res

            # 4. RANGO
            rango_res = max_res - min_res

            # 5. DESVIACIÓN ESTÁNDAR AGRUPADA
            tabla["distancia_cuadrada"] = tabla["fi"] * ((tabla["Marca Clase (xi)"] - media_res) ** 2)
            if n > 1:
                varianza = tabla["distancia_cuadrada"].sum() / (n - 1)
                std_res = math.sqrt(varianza)
            else:
                std_res = 0

        else:
            # --- FÓRMULAS DATOS SIMPLES ---
            media_res = datos.mean()
            mediana_res = datos.median()
            try:
                moda_res = datos.mode()[0]
            except:
                moda_res = 0
            rango_res = datos.max() - datos.min()
            std_res = datos.std()

    col_medidas, col_graficos = st.columns([1, 3])

    # --- MOSTRAR MEDIDAS ---
    with col_medidas:
        st.write("📌 **Medidas Estadísticas**")
        
        if modo_analisis == "Intervalos":
            st.success("Cálculo: Datos Agrupados")
        else:
            st.warning("Cálculo: Datos No Agrupados")
            
        try:
            if es_numerico:
                st.metric("Media", f"{media_res:.4f}")
                st.metric("Mediana", f"{mediana_res:.4f}")
                st.metric("Moda", f"{moda_res:.4f}")
                
                if modo_analisis == "Intervalos":
                    st.metric("Amplitud (A)", f"{amplitud_res:.4f}")
                
                st.metric("Rango", f"{rango_res:.4f}")
                st.metric("Desviación Estándar", f"{std_res:.4f}")
                
                st.markdown("---")
                st.metric("Mínimo", f"{min_res}")
                st.metric("Máximo", f"{max_res}")
            else:
                try:
                    st.metric("Moda", str(datos.mode()[0]))
                except:
                    st.warning("No hay moda clara")
        except Exception as e:
            st.warning(f"Error en cálculo: {e}")

    # --- GRÁFICOS ---
    with col_graficos:
        tab_bar, tab_pie, tab_ojiva = st.tabs(["📊 Barras / Histograma", "🥧 Circular", "📈 Ojiva"])

        with tab_bar:
            fig1 = go.Figure()
            fig1.add_trace(go.Bar(
                x=tabla_view[col_grafico],
                y=tabla_view["fi"],
                text=tabla_view["fi"],
                textposition="outside",
                marker_color="#1f77b4",
                name="Frecuencia"
            ))

            if modo_analisis == "Intervalos":
                fig1.add_trace(go.Scatter(
                    x=tabla_view[col_grafico],
                    y=tabla_view["fi"],
                    mode="lines+markers",
                    line=dict(color="red"),
                    name="Polígono"
                ))
                fig1.update_layout(title=f"Histograma (Amplitud ≈ {amplitud_res:.2f})", height=500)
            else:
                fig1.update_layout(title="Gráfico de Barras", height=500)
            
            st.plotly_chart(fig1, use_container_width=True)

        with tab_pie:
            fig2 = go.Figure(data=[go.Pie(
                labels=tabla_view[col_grafico],
                values=tabla_view["fi"],
                hole=0.3
            )])
            fig2.update_layout(title="Distribución porcentual")
            st.plotly_chart(fig2, use_container_width=True)

        with tab_ojiva:
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=tabla_view[col_grafico],
                y=tabla_view["Fi"],
                mode="lines+markers",
                fill="tozeroy",
                name="Ojiva"
            ))
            fig3.update_layout(title="Ojiva (Frecuencia Acumulada)")
            st.plotly_chart(fig3, use_container_width=True)

else:
    st.info("👆 Esperando datos para procesar.")

st.markdown("""
---
## 📘 Notas
- **Soporte CSV:** El sistema ahora detecta automáticamente si tu archivo usa comas (`,`) o punto y coma (`;`).
- **Limpieza:** Se corrigen automáticamente los decimales (ej: `12,5` a `12.5`).
""")
