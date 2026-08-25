import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración Ejecutiva del Dashboard
st.set_page_config(page_title="AgroData Chubut - Monitor Ovino", page_icon="🐑", layout="wide")

# 2. Ingesta y Limpieza de Datos (Caché activo para rendimiento logístico)
@st.cache_data
def cargar_y_limpiar_datos():
    url_csv = "https://docs.google.com/spreadsheets/d/1ILv6j6Iyvb2Hu5WNNuIZiF5Q4YT9RmZvcWH-x5KCTp0/export?format=csv"
    try:
        df = pd.read_csv(url_csv, on_bad_lines='skip')
        df.columns = df.columns.str.strip().str.lower()
        
        # Estandarización de variables geográficas (Meseta Central, VIRCh, Senguer-San Jorge)
        if 'departamento' in df.columns:
            df['departamento'] = df['departamento'].str.upper()
            
        df['total ovinos'] = pd.to_numeric(df['total ovinos'], errors='coerce').fillna(0)
        df['latitud'] = pd.to_numeric(df['latitud'], errors='coerce')
        df['longitud'] = pd.to_numeric(df['longitud'], errors='coerce')
        
        # Aislamiento de unidades productivas con coordenadas válidas
        df_geo = df.dropna(subset=['latitud', 'longitud'])
        return df, df_geo
    except Exception as e:
        st.error(f"Error de conexión con la base del RENSPA: {e}")
        return pd.DataFrame(), pd.DataFrame()

df, df_geo = cargar_y_limpiar_datos()

# 3. Interfaz Gráfica y Contexto Institucional
st.title("🐑 AgroData Chubut: Monitor Geoespacial Ovino")
st.markdown("Herramienta técnica para el análisis de distribución de majadas y evaluación de impacto logístico-climático en el territorio provincial.")

if not df.empty:
    # Panel de Filtrado Territorial
    st.sidebar.header("Parámetros Territoriales")
    lista_deptos = ["TODA LA PROVINCIA"] + sorted(list(df['departamento'].dropna().unique()))
    depto_seleccionado = st.sidebar.selectbox("Filtro por Departamento:", lista_deptos)
    
    if depto_seleccionado != "TODA LA PROVINCIA":
        df_filtrado = df[df['departamento'] == depto_seleccionado]
        df_geo_filtrado = df_geo[df_geo['departamento'] == depto_seleccionado]
    else:
        df_filtrado = df
        df_geo_filtrado = df_geo

    # KPIs Agronómicos y Productivos
    total_cabezas = df_filtrado['total ovinos'].sum()
    total_establecimientos = df_filtrado['establecimiento'].nunique() if 'establecimiento' in df_filtrado.columns else len(df_filtrado)
    promedio_carga = total_cabezas / total_establecimientos if total_establecimientos > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Stock Ovino Total", f"{int(total_cabezas):,}".replace(",", "."))
    col2.metric("Unidades Productivas (UP)", f"{total_establecimientos:,}".replace(",", "."))
    col3.metric("Carga Animal Promedio (Cabezas/UP)", f"{int(promedio_carga):,}".replace(",", "."))
    
    st.markdown("---")

    # Layout Analítico
    col_barras, col_mapa = st.columns((1, 1.2))

    with col_barras:
        st.subheader("Distribución Departamental")
        df_agrupado = df_filtrado.groupby('departamento')['total ovinos'].sum().reset_index().sort_values(by='total ovinos', ascending=True)
        fig_barras = px.bar(
            df_agrupado, x='total ovinos', y='departamento', orientation='h',
            color='total ovinos', color_continuous_scale='YlOrBr',
            labels={'total ovinos': 'Cabezas Declaradas', 'departamento': 'Jurisdicción'}
        )
        fig_barras.update_layout(showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_barras, use_container_width=True)

    with col_mapa:
        st.subheader("Geolocalización Logística")
        if not df_geo_filtrado.empty:
            fig_mapa = px.scatter_mapbox(
                df_geo_filtrado, lat="latitud", lon="longitud", size="total ovinos",
                color="total ovinos", hover_name="establecimiento" if 'establecimiento' in df_geo_filtrado.columns else None,
                hover_data=["juzgado de paz", "total ovinos"],
                color_continuous_scale=px.colors.sequential.YlOrBr, size_max=25,
                zoom=4.5 if depto_seleccionado == "TODA LA PROVINCIA" else 7,
                center={"lat": -43.8, "lon": -68.5} if depto_seleccionado == "TODA LA PROVINCIA" else None,
                mapbox_style="carto-positron"
            )
            fig_mapa.update_layout(margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig_mapa, use_container_width=True)
        else:
            st.warning("Sin datos de coordenadas para la comarca seleccionada.")
            
    st.sidebar.markdown("---")
    st.sidebar.info("Desarrollado para el análisis productivo de Chubut. Facilita la planificación logística ante emergencias (nevadas/sequías) y auditorías del Plan PROLANA.")
else:
    st.error("Error crítico: Ausencia de datos primarios.")