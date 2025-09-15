import streamlit as st
import pandas as pd
import psycopg2
import os

# --- Database connection configuration ---
SUPABASE_DB_URL = os.environ.get('SUPABASE_DB_URL')

def get_data_from_supabase():
    """
    Connects to the database and retrieves data from the 'stock_prices' table.
    """
    conn = None
    try:
        conn = psycopg2.connect(SUPABASE_DB_URL)
        query = "SELECT timestamp, symbol, close_price FROM stock_prices ORDER BY timestamp ASC"
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Error connecting to the database: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

# --- Dashboard title and description ---
st.title("Financial Markets Dashboard")
st.write("Financial market data updated daily.")

# --- Get data and perform analysis ---
data = get_data_from_supabase()

if not data.empty:
    symbols = data['symbol'].unique()
    selected_symbol = st.selectbox("Select a Symbol", symbols)
    
    filtered_data = data[data['symbol'] == selected_symbol].copy()
    filtered_data['timestamp'] = pd.to_datetime(filtered_data['timestamp'])
    filtered_data.set_index('timestamp', inplace=True)
    
    # Calculate key performance indicators (KPIs)
    filtered_data['daily_returns'] = filtered_data['close_price'].pct_change()
    annualized_volatility = filtered_data['daily_returns'].std() * (252**0.5)
    
    # --- Display KPIs ---
    st.subheader(f"KPIs for {selected_symbol}")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Last Day's Return", value=f"{filtered_data['daily_returns'].iloc[-1]:.2%}")
    with col2:
        st.metric(label="Annualized Volatility", value=f"{annualized_volatility:.2f}")

    # --- Display charts ---
    st.subheader("Closing Price Chart")
    st.line_chart(filtered_data['close_price'])
    
    st.subheader("Daily Returns Chart")
    st.line_chart(filtered_data['daily_returns'])
    
else:
    st.warning("No data to display. Check your database connection.")