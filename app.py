import streamlit as st
import pandas as pd
import psycopg2
import os

# --- Configuración de la conexión a Supabase ---
SUPABASE_DB_URL = os.environ.get('SUPABASE_DB_URL')

# ... (El resto del código para get_data_from_supabase() y la conexión es el mismo)

def get_data_from_supabase():
    # ... (código existente)
    conn = None
    try:
        conn = psycopg2.connect(SUPABASE_DB_URL)
        query = "SELECT timestamp, symbol, close_price FROM stock_prices ORDER BY timestamp ASC"
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Error al conectar a la base de datos: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


# --- Título y descripción del dashboard ---
st.title("Financial Markets Dashboard")
st.write("Datos de mercados financieros actualizados diariamente.")


# --- Obtener datos ---
data = get_data_from_supabase()

if not data.empty:
    # --- Agregar un filtro de símbolos ---
    symbols = data['symbol'].unique()
    selected_symbol = st.selectbox("Selecciona un Símbolo", symbols)
    
    # Filtrar datos
    filtered_data = data[data['symbol'] == selected_symbol].copy()
    filtered_data['timestamp'] = pd.to_datetime(filtered_data['timestamp'])
    filtered_data.set_index('timestamp', inplace=True)
    
    # --- CÁLCULO DE KPIs ---
    
    # 1. Rendimiento Diario (Daily Returns)
    filtered_data['daily_returns'] = filtered_data['close_price'].pct_change()
    
    # 2. Volatilidad Anualizada (Annualized Volatility)
    annualized_volatility = filtered_data['daily_returns'].std() * (252**0.5)
    
    # --- MOSTRAR KPIs ---
    st.subheader(f"KPIs para {selected_symbol}")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Rendimiento del último día", value=f"{filtered_data['daily_returns'].iloc[-1]:.2%}")
    with col2:
        st.metric(label="Volatilidad Anualizada", value=f"{annualized_volatility:.2f}")

    # --- MOSTRAR GRÁFICOS ---
    st.subheader("Gráfico de Precios de Cierre")
    st.line_chart(filtered_data['close_price'])
    
    st.subheader("Gráfico de Rendimientos Diarios")
    st.line_chart(filtered_data['daily_returns'])
    
else:
    st.warning("No hay datos para mostrar. Revisa tu conexión a la base de datos.")