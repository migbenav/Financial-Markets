import os
import requests
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY')
SUPABASE_DB_URL = os.environ.get('SUPABASE_DB_URL')

# List of symbols to fetch historical data for
SYMBOLS = {
    #'stocks': ['MSFT', 'GOOGL', 'AMZN', 'SPY'],
    'stocks': ['SPY'],
    'crypto': ['BTC', 'ETH'],  # Alpha Vantage uses 'BTC' instead of 'BTC-USD'
    'forex': ['EUR', 'JPY', 'GBP'] # For pairs, we use the base currency
}

# Start date for historical data (January 1, 2024)
START_DATE = datetime(2024, 1, 1)

# --- Helper Function to build API URL ---
def get_api_url(asset_type, symbol):
    """
    Constructs the correct Alpha Vantage API URL based on the asset type.
    """
    base_url = "https://www.alphavantage.co/query?"
    
    if asset_type == 'stocks':
        return f'{base_url}function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=full&apikey={ALPHA_VANTAGE_API_KEY}'
    elif asset_type == 'crypto':
        return f'{base_url}function=DIGITAL_CURRENCY_DAILY&symbol={symbol}&market=USD&apikey={ALPHA_VANTAGE_API_KEY}'
    elif asset_type == 'forex':
        return f'{base_url}function=FX_DAILY&from_symbol={symbol}&to_symbol=USD&apikey={ALPHA_VANTAGE_API_KEY}'
    else:
        raise ValueError("Invalid asset type provided.")

# --- Main Function ---
def fetch_and_save_historical_data():
    """
    Fetches historical data for all symbols and saves it to the database.
    """
    conn = None
    try:
        conn = psycopg2.connect(SUPABASE_DB_URL)
        cur = conn.cursor()

        # Iterate through each asset type
        for asset_type, symbols in SYMBOLS.items():
            for symbol in symbols:
                print(f"Fetching {asset_type} data for {symbol}...")
                
                url = get_api_url(asset_type, symbol)
                response = requests.get(url)

                # Checks if the request was successful (status code 200)
                if response.status_code != 200:
                    print(f"Error en la solicitud para {symbol}. Código de estado: {response.status_code}")
                    continue
                
                data = response.json()

                #print(f"DEBUG: Data for {symbol}: {data}")

                if asset_type == 'stocks':
                    time_series_key = 'Time Series (Daily)'
                    open_key, close_key, volume_key = '1. open', '4. close', '5. volume'
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
                
                for date_str, values in time_series.items():
                    current_date = datetime.strptime(date_str, '%Y-%m-%d')
                    
                    if current_date < START_DATE:
                        continue

                    open_price = float(values[open_key])
                    close_price = float(values[close_key])
                    volume = float(values[volume_key]) if asset_type != 'forex' else 0 # Forex doesn't have a volume key
                    current_time = datetime.now()

                    # Insert the data into the 'stock_prices' table
                    cur.execute(
                        "INSERT INTO stock_prices (timestamp, symbol, open_price, close_price, volume, load_timestamp) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (timestamp, symbol) DO NOTHING",
                        (current_date, symbol, open_price, close_price, volume, current_time)
                    )
                
                print(f"Historical data for {symbol} saved successfully!")
                conn.commit()

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    fetch_and_save_historical_data()