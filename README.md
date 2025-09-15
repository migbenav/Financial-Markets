# Financial-Markets Data Pipeline

![Workflow Status](https://github.com/migbenav/Financial-Markets/actions/workflows/main.yml/badge.svg)

A project to automate the collection of financial market data (stocks, cryptocurrencies, currencies) and store it in a PostgreSQL database using Supabase.

---

## 🚀 Features

-   **Daily Automation:** Uses GitHub Actions to run a Python script that updates the database data daily.
-   **Data Diversity:** Gathers data from different markets, including cryptocurrencies (BTC, ETH), and currencies (EUR, JPY, GBP).
-   **Cloud Storage:** Data is securely stored in a Supabase database.

---

## 🛠️ How It Works

The core of this project is a data pipeline that runs automatically.

1.  **Extraction:** A Python script (`get_data.py`) connects to the **Alpha Vantage** API to get the latest market data.
2.  **Loading:** The data is inserted into a table (`stock_prices`) in the **Supabase** database.
3.  **Automation:** **GitHub Actions** ensures this process runs on a schedule, keeping the database up to date.

---

## ⚙️ Configuration

To run this project, you need to set up the following environment variables:

1.  **ALPHA_VANTAGE_API_KEY:** Your Alpha Vantage API key.
2.  **SUPABASE_DB_URL:** Your Supabase database connection string.

These variables should be added as "Secrets" in your GitHub repository for the automation to work.

---

## 📄 License

This project is licensed under the MIT License.