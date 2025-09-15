import os
import requests
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY')
SUPABASE_DB_URL = os.environ.get('SUPABASE_DB_URL')

# List of symbols to fetch data for
SYMBOLS = {
    #'stocks': ['MSFT', 'GOOGL', 'AMZN', 'SPY'],
    'stocks': ['SPY'],
    'crypto': ['BTC', 'ETH'],
    'forex': ['EUR', 'JPY', 'GBP']
}

# --- Helper Function to build API URL ---
def get_api_url(asset_type, symbol):
    """
    Constructs the correct Alpha Vantage API URL based on the asset type for data.
    """
    base_url = "https://www.alphavantage.co/query?"
    
    if asset_type == 'stocks':
        return f'{base_url}function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&outputsize=compact&apikey={ALPHA_VANTAGE_API_KEY}'
    elif asset_type == 'crypto':
        return f'{base_url}function=DIGITAL_CURRENCY_DAILY&symbol={symbol}&market=USD&apikey={ALPHA_VANTAGE_API_KEY}'
    elif asset_type == 'forex':
        return f'{base_url}function=FX_DAILY&from_symbol={symbol}&to_symbol=USD&apikey={ALPHA_VANTAGE_API_KEY}'
    else:
        raise ValueError("Invalid asset type provided.")

# --- Main Function ---
def fetch_and_save_data():
    """
    Fetches intraday data for all symbols and saves it to the database.
    """
    conn = None
    try:
        conn = psycopg2.connect(SUPABASE_DB_URL)
        cur = conn.cursor()


        for asset_type, symbols in SYMBOLS.items():
            for symbol in symbols:
                print(f"Fetching {asset_type} data for {symbol}...")
                
                url = get_api_url(asset_type, symbol)
                response = requests.get(url)
                
                # --- Aquí se añade la pausa de 1 segundo ---
                time.sleep(1)

                if response.status_code != 200:
                    print(f"Error for {symbol}. Status Code: {response.status_code}")
                    continue
                
                data = response.json()
                
                if asset_type == 'stocks':
                    time_series_key = 'Time Series (Daily)'
                    open_key, close_key, volume_key = '1. open', '4. close', '6. volume'
                elif asset_type == 'crypto':
                    time_series_key = 'Time Series (Digital Currency Daily)'
                    open_key, close_key, volume_key = '1. open', '4. close', '5. volume'
                elif asset_type == 'forex':
                    time_series_key = 'Time Series FX (Daily)'
                    open_key, close_key = '1. open', '4. close'
                    
                if time_series_key not in data:
                    print(f"Error: Could not retrieve data for {symbol}. Check API response.")
                    continue

                time_series = data[time_series_key]
                
                for timestamp_str, values in time_series.items():
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d')
                    open_price = float(values[open_key])
                    close_price = float(values[close_key])

                    # Define volume based on asset type
                    if asset_type != 'forex':
                        volume = float(values[volume_key])
                    else:
                        volume = 0

                    current_time = datetime.now()

                    cur.execute(
                        "INSERT INTO stock_prices (timestamp, symbol, open_price, close_price, volume, load_timestamp) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (timestamp, symbol) DO NOTHING",
                        (timestamp, symbol, open_price, close_price, volume, current_time)
                    )
                
                print(f"Daily data for {symbol} saved successfully!")
                conn.commit()

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    fetch_and_save_data()