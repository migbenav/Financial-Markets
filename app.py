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
    
    # First row of KPIs
    col1, col2, col3 = st.columns(3)
    with col1:
        # Last Day's Return
        st.metric(label="Last Day's Return", value=f"{filtered_data['daily_returns'].iloc[-1]:.2%}")
    with col2:
        # Annualized Volatility
        annualized_volatility = filtered_data['daily_returns'].std() * (252**0.5)
        st.metric(label="Annualized Volatility", value=f"{annualized_volatility:.2f}")
    with col3:
        # Month-over-Month Growth
        monthly_growth = (filtered_data['close_price'].iloc[-1] - filtered_data['close_price'].iloc[-21]) / filtered_data['close_price'].iloc[-21]
        st.metric(label="Monthly Growth", value=f"{monthly_growth:.2%}")

    # Second row of KPIs
    col4, col5, col6 = st.columns(3)
    with col4:
        # Year-over-Year Growth
        yearly_growth = (filtered_data['close_price'].iloc[-1] - filtered_data['close_price'].iloc[-252]) / filtered_data['close_price'].iloc[-252]
        st.metric(label="Yearly Growth", value=f"{yearly_growth:.2%}")
    with col5:
        # Average Annual Return
        average_annual_return = filtered_data['daily_returns'].mean() * 252
        st.metric(label="Avg Annual Return", value=f"{average_annual_return:.2%}")
    with col6:
        # 52-Week High
        high_52_week = filtered_data['close_price'].rolling(window=252).max().iloc[-1]
        st.metric(label="52-Week High", value=f"${high_52_week:.2f}")

    # Third row of KPIs
    col7, col8, col9 = st.columns(3)
    with col7:
        # 52-Week Low
        low_52_week = filtered_data['close_price'].rolling(window=252).min().iloc[-1]
        st.metric(label="52-Week Low", value=f"${low_52_week:.2f}")
    with col8:
        # 30-Day Return
        thirty_day_return = (filtered_data['close_price'].iloc[-1] - filtered_data['close_price'].iloc[-30]) / filtered_data['close_price'].iloc[-30]
        st.metric(label="30-Day Return", value=f"{thirty_day_return:.2%}")
    with col9:
        # Price/Volume Ratio
        if 'volume' in filtered_data.columns and filtered_data['volume'].mean() > 0:
            avg_volume = filtered_data['volume'].rolling(window=20).mean().iloc[-1]
            price_volume_ratio = filtered_data['close_price'].iloc[-1] / avg_volume
            st.metric(label="Price/Volume Ratio", value=f"{price_volume_ratio:.2f}")
        else:
            st.metric(label="Price/Volume Ratio", value="N/A")

    # --- Display charts ---
    st.subheader("Closing Price Chart")
    st.line_chart(filtered_data['close_price'])
    
    st.subheader("Daily Returns Chart")
    st.line_chart(filtered_data['daily_returns'])
    
else:
    st.warning("No data to display. Check your database connection.") 