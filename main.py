import os
import requests
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
import logging

logging.basicConfig(
    filename="pipeline.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Optional: only load .env locally if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

API_KEY = os.getenv("WEATHER_API_KEY")
CITIES = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]

# ✅ Make this match what GitHub Actions commits
DB_CONNECTION = "sqlite:///weather.db"


def extract(cities):
    raw_data = []
    base_url = "https://api.openweathermap.org/data/2.5/weather"

    if not API_KEY:
        raise RuntimeError("WEATHER_API_KEY is missing (set it in GitHub Secrets or .env)")

    for city in cities:
        try:
            response = requests.get(
                base_url,
                params={"q": city, "appid": API_KEY, "units": "metric"},
                timeout=20,
            )
            response.raise_for_status()
            raw_data.append(response.json())
        except Exception as e:
            logging.error(f"Failed to extract {city}: {e}")

    return raw_data


def transform(raw_data_list):
    transformed = []
    for entry in raw_data_list:
        # skip invalid entries
        if not isinstance(entry, dict) or "main" not in entry:
            continue

        transformed.append({
            "city": entry.get("name"),
            "temp": entry.get("main", {}).get("temp"),
            "humidity": entry.get("main", {}).get("humidity"),
            "description": entry.get("weather", [{}])[0].get("description"),
            "timestamp": datetime.fromtimestamp(entry.get("dt")) if entry.get("dt") else None,
            "processed_at": datetime.now()
        })

    return pd.DataFrame(transformed)


def load(df):
    if df.empty:
        logging.warning("No rows to load (data extraction may have failed).")
        return

    engine = create_engine(DB_CONNECTION)
    df.to_sql("weather_reports", con=engine, if_exists="append", index=False)


def run_pipeline():
    logging.info("Starting ETL Pipeline...")
    data = extract(CITIES)
    df = transform(data)
    load(df)
    logging.info(f"Pipeline finished. {len(df)} rows processed.")


if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as e:
        logging.exception(f"Pipeline crashed: {e}")
        raise

    # ✅ Only read if the table exists
    engine = create_engine(DB_CONNECTION)
    with engine.connect() as conn:
        exists = conn.execute(text("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='weather_reports'
        """)).fetchone()

        if not exists:
            print("Table weather_reports does not exist yet.")
        else:
            result = conn.execute(text("SELECT * FROM weather_reports ORDER BY processed_at DESC LIMIT 10"))
            for row in result.fetchall():
                print(row)
