import streamlit as st
import pandas as pd
import psycopg2
import os

# --- Database connection configuration ---
SUPABASE_DB_URL = os.environ.get('SUPABASE_DB_URL')

def get_data_from_supabase():
    """
    Connects to the database and retrieves all data from the 'stock_prices' table.
    """
    conn = None
    try:
        conn = psycopg2.connect(SUPABASE_DB_URL)
        query = "SELECT * FROM stock_prices ORDER BY timestamp ASC"
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
    # This check prevents an IndexError if there's not enough data
    if len(filtered_data) > 1:
        filtered_data['daily_returns'] = filtered_data['close_price'].pct_change()
    else:
        filtered_data['daily_returns'] = 0

    # --- DISPLAY KPIs ---
    st.subheader(f"KPIs for {selected_symbol}")
    
    # First row of KPIs
    col1, col2, col3 = st.columns(3)
    with col1:
        # Last Day's Return
        if len(filtered_data) > 1:
            st.metric(label="Last Day's Return", value=f"{filtered_data['daily_returns'].iloc[-1]:.2%}")
        else:
            st.metric(label="Last Day's Return", value="N/A")
    with col2:
        # Annualized Volatility
        if len(filtered_data) > 252:
            annualized_volatility = filtered_data['daily_returns'].std() * (252**0.5)
            st.metric(label="Annualized Volatility", value=f"{annualized_volatility:.2f}")
        else:
            st.metric(label="Annualized Volatility", value="N/A")
    with col3:
        # Month-over-Month Growth
        if len(filtered_data) > 21:
            monthly_growth = (filtered_data['close_price'].iloc[-1] - filtered_data['close_price'].iloc[-21]) / filtered_data['close_price'].iloc[-21]
            st.metric(label="Monthly Growth", value=f"{monthly_growth:.2%}")
        else:
            st.metric(label="Monthly Growth", value="N/A")

    # Second row of KPIs
    col4, col5, col6 = st.columns(3)
    with col4:
        # Year-over-Year Growth
        if len(filtered_data) > 252:
            yearly_growth = (filtered_data['close_price'].iloc[-1] - filtered_data['close_price'].iloc[-252]) / filtered_data['close_price'].iloc[-252]
            st.metric(label="Yearly Growth", value=f"{yearly_growth:.2%}")
        else:
            st.metric(label="Yearly Growth", value="N/A")
    with col5:
        # Average Annual Return
        if len(filtered_data) > 252:
            average_annual_return = filtered_data['daily_returns'].mean() * 252
            st.metric(label="Avg Annual Return", value=f"{average_annual_return:.2%}")
        else:
            st.metric(label="Avg Annual Return", value="N/A")
    with col6:
        # 52-Week High
        if len(filtered_data) > 252:
            high_52_week = filtered_data['close_price'].rolling(window=252).max().iloc[-1]
            st.metric(label="52-Week High", value=f"${high_52_week:.2f}")
        else:
            st.metric(label="52-Week High", value="N/A")

    # Third row of KPIs
    col7, col8, col9 = st.columns(3)
    with col7:
        # 52-Week Low
        if len(filtered_data) > 252:
            low_52_week = filtered_data['close_price'].rolling(window=252).min().iloc[-1]
            st.metric(label="52-Week Low", value=f"${low_52_week:.2f}")
        else:
            st.metric(label="52-Week Low", value="N/A")
    with col8:
        # 30-Day Return
        if len(filtered_data) > 30:
            thirty_day_return = (filtered_data['close_price'].iloc[-1] - filtered_data['close_price'].iloc[-30]) / filtered_data['close_price'].iloc[-30]
            st.metric(label="30-Day Return", value=f"{thirty_day_return:.2%}")
        else:
            st.metric(label="30-Day Return", value="N/A")
    with col9:
        # Price/Volume Ratio
        if 'volume' in filtered_data.columns and not pd.isna(filtered_data['volume']).all():
            avg_volume = filtered_data['volume'].rolling(window=20).mean().iloc[-1]
            price_volume_ratio = filtered_data['close_price'].iloc[-1] / avg_volume
            st.metric(label="Price/Volume Ratio", value=f"{price_volume_ratio:.2f}")
        else:
            st.metric(label="Price/Volume Ratio", value="N/A")

    # --- DISPLAY CHARTS ---
    st.subheader("Closing Price Chart")
    st.line_chart(filtered_data['close_price'])
    
    st.subheader("Daily Returns Chart")
    if len(filtered_data) > 1:
        st.line_chart(filtered_data['daily_returns'])
    else:
        st.warning("Not enough data to display Daily Returns.")
    
else:
    st.warning("No data to display. Check your database connection.")