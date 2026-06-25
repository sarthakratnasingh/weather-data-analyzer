"""
fetch_data.py
--------------
Downloads 10 years of daily historical weather data (max/min/mean temperature
and precipitation) for New Delhi, India using the free Open-Meteo Historical
Weather API (no API key required).

API docs: https://open-meteo.com/en/docs/historical-weather-api

Usage:
    python src/fetch_data.py
"""

import datetime as dt
from pathlib import Path

import requests
import pandas as pd

# --- Configuration -----------------------------------------------------

# New Delhi, India coordinates
LATITUDE = 28.6139
LONGITUDE = 77.2090
TIMEZONE = "Asia/Kolkata"

# Last 10 full years of data
END_DATE = dt.date.today() - dt.timedelta(days=2)  # API has a short reporting lag
START_DATE = END_DATE.replace(year=END_DATE.year - 10)

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "new_delhi_weather_raw.csv"

API_URL = "https://archive-api.open-meteo.com/v1/archive"

DAILY_VARS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
    "rain_sum",
]


def fetch_weather_data(start_date: dt.date, end_date: dt.date) -> pd.DataFrame:
    """Fetch daily weather data from Open-Meteo in date-range chunks.

    The archive API can be queried for very long ranges in one call, but we
    chunk by year to keep individual requests small and easy to retry if one
    fails partway through.
    """
    all_frames = []
    current_start = start_date

    while current_start <= end_date:
        # Chunk into 1-year windows
        current_end = min(
            dt.date(current_start.year, 12, 31), end_date
        )

        print(f"Fetching {current_start} to {current_end}...")

        params = {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "start_date": current_start.isoformat(),
            "end_date": current_end.isoformat(),
            "daily": ",".join(DAILY_VARS),
            "timezone": TIMEZONE,
        }

        response = requests.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()

        daily = payload["daily"]
        frame = pd.DataFrame(daily)
        all_frames.append(frame)

        # Move to the next chunk
        current_start = dt.date(current_end.year + 1, 1, 1)

    full_df = pd.concat(all_frames, ignore_index=True)
    full_df = full_df.rename(
        columns={
            "time": "date",
            "temperature_2m_max": "temp_max_c",
            "temperature_2m_min": "temp_min_c",
            "temperature_2m_mean": "temp_mean_c",
            "precipitation_sum": "precipitation_mm",
            "rain_sum": "rain_mm",
        }
    )
    return full_df


def main():
    print(f"Fetching New Delhi weather data from {START_DATE} to {END_DATE}")
    df = fetch_weather_data(START_DATE, END_DATE)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved {len(df)} rows to {OUTPUT_PATH}")
    print(df.head())


if __name__ == "__main__":
    main()
