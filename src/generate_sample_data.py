"""
generate_sample_data.py
------------------------
NOT part of the final project deliverable.

This script generates a *synthetic but climatologically realistic* dataset
for New Delhi, used only so the analysis/visualization pipeline can be built
and tested inside this sandbox (which can't reach the live Open-Meteo API
due to network restrictions).

When you run fetch_data.py on your own machine, it will produce a real CSV
in the exact same format, and the rest of the pipeline will work unchanged.
"""

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "new_delhi_weather_raw.csv"

np.random.seed(42)

START_DATE = dt.date(2016, 1, 1)
END_DATE = dt.date(2025, 12, 31)

dates = pd.date_range(START_DATE, END_DATE, freq="D")
n = len(dates)
day_of_year = dates.dayofyear.values
years = dates.year.values

# --- Temperature model -------------------------------------------------
# Calibrated to real New Delhi climatology (approx. long-term monthly
# average mean temperatures in Celsius):
#   Jan: 14, Feb: 17, Mar: 23, Apr: 29, May: 33.5, Jun: 33.5,
#   Jul: 30.5, Aug: 29.5, Sep: 28.5, Oct: 25, Nov: 19, Dec: 15
monthly_mean_targets = {
    1: 14.0, 2: 17.0, 3: 23.0, 4: 29.0, 5: 33.5, 6: 33.5,
    7: 30.5, 8: 29.5, 9: 28.5, 10: 25.0, 11: 19.0, 12: 15.0,
}

months = dates.month.values
days_in_month = dates.day.values
month_length = dates.days_in_month.values

# Smoothly interpolate between this month's target and next month's target
# based on how far through the month we are, so the seasonal curve doesn't
# have sharp jumps at month boundaries.
next_month = (months % 12) + 1
frac_through_month = (days_in_month - 1) / month_length

current_targets = np.array([monthly_mean_targets[m] for m in months])
next_targets = np.array([monthly_mean_targets[m] for m in next_month])
mean_temp_base = current_targets + (next_targets - current_targets) * frac_through_month

# Slight warming trend over the decade (~0.04 C/year, consistent with broader warming trends)
year_trend = (years - years.min()) * 0.04

# Daily random noise
noise = np.random.normal(0, 1.8, n)

temp_mean = mean_temp_base + year_trend + noise
# Diurnal range is wider in dry winter months, narrower in humid monsoon months
monsoon_mask = (months >= 7) & (months <= 9)
diurnal_range = 9 - 3 * monsoon_mask.astype(float)  # ~9C swing normally, ~6C in monsoon
temp_max = temp_mean + diurnal_range / 2 + np.random.normal(0, 0.8, n)
temp_min = temp_mean - diurnal_range / 2 + np.random.normal(0, 0.8, n)
# Clip to realistic physical bounds for Delhi
temp_min = np.clip(temp_min, 2, None)
temp_max = np.clip(temp_max, None, 49)

# --- Precipitation model -----------------------------------------------
# Monsoon (Jun-Sep, roughly day 152-273) carries ~80% of annual rainfall.
# Outside monsoon: occasional light winter rain, mostly dry.

rain = np.zeros(n)
for i, doy in enumerate(day_of_year):
    if 152 <= doy <= 273:  # monsoon season
        # High probability of rain, higher intensity
        if np.random.random() < 0.45:
            rain[i] = np.random.gamma(shape=2.0, scale=12.0)
    elif 1 <= doy <= 31 or doy >= 335:  # winter light rain
        if np.random.random() < 0.08:
            rain[i] = np.random.gamma(shape=1.2, scale=4.0)
    else:
        if np.random.random() < 0.04:
            rain[i] = np.random.gamma(shape=1.0, scale=3.0)

rain = np.round(rain, 1)

# Introduce a small amount of realistic missing data (~1.5% of rows)
missing_mask = np.random.random(n) < 0.015

df = pd.DataFrame(
    {
        "date": dates.strftime("%Y-%m-%d"),
        "temp_max_c": np.round(temp_max, 1),
        "temp_min_c": np.round(temp_min, 1),
        "temp_mean_c": np.round(temp_mean, 1),
        "precipitation_mm": rain,
        "rain_mm": rain,
    }
)

# Apply missing data to a few columns to simulate real-world gaps
df.loc[missing_mask, ["temp_max_c", "temp_min_c", "temp_mean_c"]] = np.nan
missing_rain_mask = np.random.random(n) < 0.01
df.loc[missing_rain_mask, ["precipitation_mm", "rain_mm"]] = np.nan

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT_PATH, index=False)
print(f"Sample dataset written to {OUTPUT_PATH} ({len(df)} rows)")
print(df.head())
print(df.describe())
