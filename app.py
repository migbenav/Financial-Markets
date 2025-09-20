import streamlit as st
import pandas as pd
import psycopg2
import os
import numpy as np
import altair as alt

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
    if len(filtered_data) > 1:
        filtered_data['daily_returns'] = filtered_data['close_price'].pct_change()
    else:
        filtered_data['daily_returns'] = 0

    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Overview", "Advanced Charts", "Correlations"])

    # --- Tab 1: Overview (KPIs and basic chart) ---
    with tab1:
        st.header("Overview")
        
        # Display KPIs
        st.subheader("Key Performance Indicators (KPIs)")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if len(filtered_data) > 1:
                st.metric(label="Last Day's Return", value=f"{filtered_data['daily_returns'].iloc[-1]:.2%}")
            else:
                st.metric(label="Last Day's Return", value="N/A")
        with col2:
            if len(filtered_data) > 252:
                annualized_volatility = filtered_data['daily_returns'].std() * (252**0.5)
                st.metric(label="Annualized Volatility", value=f"{annualized_volatility:.2f}")
            else:
                st.metric(label="Annualized Volatility", value="N/A")
        with col3:
            if len(filtered_data) > 21:
                monthly_growth = (filtered_data['close_price'].iloc[-1] - filtered_data['close_price'].iloc[-21]) / filtered_data['close_price'].iloc[-21]
                st.metric(label="Monthly Growth", value=f"{monthly_growth:.2%}")
            else:
                st.metric(label="Monthly Growth", value="N/A")

        col4, col5, col6 = st.columns(3)
        with col4:
            if len(filtered_data) > 252:
                yearly_growth = (filtered_data['close_price'].iloc[-1] - filtered_data['close_price'].iloc[-252]) / filtered_data['close_price'].iloc[-252]
                st.metric(label="Yearly Growth", value=f"{yearly_growth:.2%}")
            else:
                st.metric(label="Yearly Growth", value="N/A")
        with col5:
            if len(filtered_data) > 252:
                average_annual_return = filtered_data['daily_returns'].mean() * 252
                st.metric(label="Avg Annual Return", value=f"{average_annual_return:.2%}")
            else:
                st.metric(label="Avg Annual Return", value="N/A")
        with col6:
            if len(filtered_data) > 252:
                high_52_week = filtered_data['close_price'].rolling(window=252).max().iloc[-1]
                st.metric(label="52-Week High", value=f"${high_52_week:,.2f}")
            else:
                st.metric(label="52-Week High", value="N/A")

        col7, col8, col9 = st.columns(3)
        with col7:
            if len(filtered_data) > 252:
                low_52_week = filtered_data['close_price'].rolling(window=252).min().iloc[-1]
                st.metric(label="52-Week Low", value=f"${low_52_week:,.2f}")
            else:
                st.metric(label="52-Week Low", value="N/A")
        with col8:
            if len(filtered_data) > 30:
                thirty_day_return = (filtered_data['close_price'].iloc[-1] - filtered_data['close_price'].iloc[-30]) / filtered_data['close_price'].iloc[-30]
                st.metric(label="30-Day Return", value=f"{thirty_day_return:.2%}")
            else:
                st.metric(label="30-Day Return", value="N/A")
        with col9:
            # Check if the 'volume' column exists and is not entirely null
            if 'volume' in filtered_data.columns and not filtered_data['volume'].isnull().all():
                # Ensure the average volume is not zero before calculating the ratio
                avg_volume = filtered_data['volume'].rolling(window=20).mean().iloc[-1]
                if avg_volume is not None and avg_volume != 0:
                    price_volume_ratio = filtered_data['close_price'].iloc[-1] / avg_volume
                    st.metric(label="Price/Volume Ratio", value=f"{price_volume_ratio:,.2f}")
                else:
                    st.metric(label="Price/Volume Ratio", value="N/A")
            else:
                st.metric(label="Price/Volume Ratio", value="N/A")

        # Basic Price Chart with Zoom and Formatting
        st.subheader("Basic Price Chart")
        
        chart = alt.Chart(filtered_data.reset_index()).mark_line().encode(
            x=alt.X('timestamp', axis=alt.Axis(title='Date')),
            y=alt.Y('close_price', axis=alt.Axis(title='Closing Price', format=',.2f')),
            tooltip=[
                alt.Tooltip('timestamp', title='Date'),
                alt.Tooltip('close_price', title='Price', format=',.2f')
            ]
        ).interactive()
        
        st.altair_chart(chart, use_container_width=True)

    # --- Tab 2: Advanced Charts ---
    with tab2:
        st.header("Advanced Historical Charts")

        # Resampling options
        resample_option = st.radio(
            "Select a timeframe:",
            ("Daily", "Weekly", "Monthly"),
            horizontal=True
        )

        resampled_data = filtered_data.copy()
        if resample_option == "Weekly":
            resampled_data = filtered_data['close_price'].resample('W').last().to_frame()
        elif resample_option == "Monthly":
            resampled_data = filtered_data['close_price'].resample('M').last().to_frame()
        
        chart_type = st.radio(
            "Select chart type:",
            ("Line", "Bar"),
            horizontal=True
        )

        st.subheader(f"Closing Prices - {resample_option}")
        if chart_type == "Line":
            st.line_chart(resampled_data['close_price'])
        else:
            st.bar_chart(resampled_data['close_price'])

        window_size = st.slider("Moving Average Window (days):", 10, 200, 50)
        # Se crea una copia del DataFrame para evitar un error de asignación
        df_ma = resampled_data.copy()
        df_ma['Moving Average'] = df_ma['close_price'].rolling(window=window_size).mean()

        st.subheader("Closing Price with Moving Average")
        st.line_chart(df_ma[['close_price', 'Moving Average']])
    
    # --- Tab 3: Correlation Analysis ---
    with tab3:
        st.header("Correlation Analysis")

        st.write("Select two symbols to analyze their correlation.")
        
        corr_symbols = symbols.tolist()
        if selected_symbol in corr_symbols:
            corr_symbols.remove(selected_symbol)
        
        col_corr1, col_corr2 = st.columns(2)
        with col_corr1:
            symbol1 = st.selectbox("Symbol 1", symbols)
        with col_corr2:
            symbol2 = st.selectbox("Symbol 2", corr_symbols)
        
        if symbol1 and symbol2 and symbol1 != symbol2:
            data_symbol1 = data[data['symbol'] == symbol1].set_index('timestamp')['close_price']
            data_symbol2 = data[data['symbol'] == symbol2].set_index('timestamp')['close_price']
            
            combined_data = pd.concat([data_symbol1, data_symbol2], axis=1).dropna()
            combined_data.columns = [symbol1, symbol2]
            
            returns = combined_data.pct_change().dropna()
            
            if len(returns) > 1:
                correlation = returns.corr().iloc[0, 1]
                st.subheader(f"Correlation between {symbol1} and {symbol2}")
                st.metric(label="Correlation Coefficient", value=f"{correlation:.2f}")

                st.subheader("Daily Returns Scatter Plot")
                st.scatter_chart(returns)

                st.write("A correlation close to 1 means the assets move in the same direction. Close to -1 means they move in opposite directions. Close to 0 means no linear relationship.")
            else:
                st.warning("Not enough common historical data to calculate correlation.")
        else:
            st.warning("Please select two different symbols to calculate correlation.")

else:
    st.warning("No data to display. Check your database connection.")