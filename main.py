import os
import requests
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import logging

logging.basicConfig(
    filename='pipeline.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()
API_KEY = os.getenv('WEATHER_API_KEY')
CITIES = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']
DB_CONNECTION = "sqlite:///weather_data.db"


def extract(cities):
    """Fetches raw JSON data from OpenWeatherMap API."""
    raw_data = []
    base_url = "http://api.openweathermap.org/data/2.5/weather"

    for city in cities:
        try:
            response = requests.get(
                base_url, params={'q': city, 'appid': API_KEY, 'units': 'metric'})
            response.raise_for_status()
            raw_data.append(response.json())
        except Exception as e:
            logging.error(f"Failed to extract {city}: {e}")

    return raw_data


def transform(raw_data_list):
    """Refines raw JSON into a flat Pandas DataFrame."""
    transformed = []
    for entry in raw_data_list:
        transformed.append({
            "city": entry.get("name"),
            "temp": entry.get("main", {}).get("temp"),
            "humidity": entry.get("main", {}).get("humidity"),
            "description": entry.get("weather", [{}])[0].get("description"),
            "timestamp": datetime.fromtimestamp(entry.get("dt")),
            "processed_at": datetime.now()
        })
    return pd.DataFrame(transformed)


def load(df):
    """Persists the cleaned data into a SQL database."""
    engine = create_engine(DB_CONNECTION)
    df.to_sql('weather_reports', con=engine, if_exists='append', index=False)


def run_pipeline():
    try:
        logging.info("Starting ETL Pipeline...")
        data = extract(CITIES)
        df = transform(data)
        load(df)
        logging.info(f"Pipeline finished. {len(df)} rows processed.")
    except Exception as e:
        logging.error(f"Pipeline crashed: {str(e)}")


if __name__ == "__main__":
    run_pipeline()

    engine = create_engine(DB_CONNECTION)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM weather_reports"))
        for row in result.fetchall():
            print(row)
