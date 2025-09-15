import os
import requests
import psycopg2
from datetime import datetime

# --- Configuration ---
# API keys and database credentials are not hard-coded for security.
# They are loaded from environment variables.
# This is a best practice, especially for public repositories.
ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY')
SUPABASE_DB_URL = os.environ.get('SUPABASE_DB_URL')

# List of symbols to fetch data for
SYMBOLS = ['BTC-USD', 'ETH-USD', 'SPY', 'EUR-USD'] 

# --- Main Function ---
def fetch_and_save_data(symbol):
    """
    Fetches intraday stock data from Alpha Vantage API and saves it to a PostgreSQL database.
    
    Args:
        symbol (str): The stock symbol (e.g., 'BTC-USD').
    """
    print(f"Fetching data for {symbol}...")
    
    # Construct the API request URL
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=5min&apikey={ALPHA_VANTAGE_API_KEY}'
    
    # Send the request to the API
    response = requests.get(url)
    data = response.json()

    # Error handling for the API response
    try:
        if 'Time Series (5min)' not in data:
            print(f"Error: Could not retrieve time series data for {symbol}. Check API key and symbol.")
            return

        time_series = data['Time Series (5min)']
        
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(SUPABASE_DB_URL)
        cur = conn.cursor()

        # Iterate over each timestamp in the API response
        for timestamp_str, values in time_series.items():
            # Data parsing and formatting
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            open_price = float(values['1. open'])
            close_price = float(values['4. close'])
            volume = int(values['5. volume'])

            # Insert the data into the 'stock_prices' table
            cur.execute(
                "INSERT INTO stock_prices (timestamp, symbol, open_price, close_price, volume) VALUES (%s, %s, %s, %s, %s)",
                (timestamp, symbol, open_price, close_price, volume)
            )

        # Commit the transaction to save changes to the database
        conn.commit()
        print(f"Data for {symbol} saved successfully!")

    except Exception as e:
        # Generic error handling for database connection or data processing issues
        print(f"Error processing data for {symbol}: {e}")

    finally:
        # Ensure the database connection is closed, even if an error occurs
        if 'conn' in locals():
            cur.close()
            conn.close()

# --- Entry Point ---
# This block runs when the script is executed directly
if __name__ == "__main__":
    for symbol in SYMBOLS:
        fetch_and_save_data(symbol)