"""
analyze.py
----------
Runs the core statistical analysis on the cleaned New Delhi weather data:
- Yearly and monthly summary statistics
- Trend analysis (is it getting hotter? more/less rain?)
- Hottest/coldest/wettest records
- Correlation between temperature and rainfall

Usage:
    python src/analyze.py
"""

from pathlib import Path

import pandas as pd
import numpy as np

PROCESSED_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "new_delhi_weather_clean.csv"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "outputs" / "summary_stats.txt"

MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load_data() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_PATH, parse_dates=["date"])
    return df


def yearly_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = df.groupby("year").agg(
        avg_temp_c=("temp_mean_c", "mean"),
        max_temp_c=("temp_max_c", "max"),
        min_temp_c=("temp_min_c", "min"),
        total_rainfall_mm=("precipitation_mm", "sum"),
        rainy_days=("precipitation_mm", lambda x: (x > 1).sum()),
    ).round(2)
    return summary


def monthly_climatology(df: pd.DataFrame) -> pd.DataFrame:
    """Average pattern by calendar month, across all years."""
    monthly = df.groupby("month_name").agg(
        avg_temp_c=("temp_mean_c", "mean"),
        avg_max_temp_c=("temp_max_c", "mean"),
        avg_min_temp_c=("temp_min_c", "mean"),
        avg_rainfall_mm=("precipitation_mm", "mean"),
        total_rainfall_mm=("precipitation_mm", "sum"),
    ).round(2)
    monthly = monthly.reindex(MONTH_ORDER)
    return monthly


def temperature_trend(df: pd.DataFrame) -> dict:
    """Simple linear trend: degrees C change per year, via least-squares fit
    on yearly average temperature."""
    yearly_avg = df.groupby("year")["temp_mean_c"].mean()
    years = yearly_avg.index.values
    temps = yearly_avg.values

    slope, intercept = np.polyfit(years, temps, 1)
    total_years = years.max() - years.min()
    total_change = slope * total_years

    return {
        "slope_c_per_year": round(slope, 4),
        "total_change_over_period_c": round(total_change, 2),
        "period": f"{years.min()}-{years.max()}",
    }


def rainfall_trend(df: pd.DataFrame) -> dict:
    yearly_total = df.groupby("year")["precipitation_mm"].sum()
    years = yearly_total.index.values
    totals = yearly_total.values

    slope, intercept = np.polyfit(years, totals, 1)
    total_years = years.max() - years.min()
    total_change = slope * total_years

    return {
        "slope_mm_per_year": round(slope, 2),
        "total_change_over_period_mm": round(total_change, 1),
        "period": f"{years.min()}-{years.max()}",
    }


def extremes(df: pd.DataFrame) -> dict:
    hottest = df.loc[df["temp_max_c"].idxmax()]
    coldest = df.loc[df["temp_min_c"].idxmin()]
    wettest = df.loc[df["precipitation_mm"].idxmax()]

    return {
        "hottest_day": (hottest["date"].date(), hottest["temp_max_c"]),
        "coldest_day": (coldest["date"].date(), coldest["temp_min_c"]),
        "wettest_day": (wettest["date"].date(), wettest["precipitation_mm"]),
    }


def temp_rain_correlation(df: pd.DataFrame) -> float:
    """Correlation between daily mean temperature and daily rainfall."""
    return round(df["temp_mean_c"].corr(df["precipitation_mm"]), 3)


def monsoon_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Year-by-year monsoon (Jun-Sep) rainfall total, to check variability."""
    monsoon = df[df["season"] == "Monsoon"]
    yearly_monsoon = monsoon.groupby("year")["precipitation_mm"].sum().round(1)
    return yearly_monsoon


def main():
    df = load_data()

    print("=" * 60)
    print("NEW DELHI WEATHER ANALYSIS (2016-2025)")
    print("=" * 60)

    print("\n--- Yearly Summary ---")
    yearly = yearly_summary(df)
    print(yearly)

    print("\n--- Monthly Climatology (avg across all years) ---")
    monthly = monthly_climatology(df)
    print(monthly)

    print("\n--- Temperature Trend ---")
    temp_trend = temperature_trend(df)
    print(temp_trend)

    print("\n--- Rainfall Trend ---")
    rain_trend = rainfall_trend(df)
    print(rain_trend)

    print("\n--- Extremes ---")
    ext = extremes(df)
    for k, v in ext.items():
        print(f"{k}: {v}")

    print("\n--- Temp vs Rainfall Correlation ---")
    corr = temp_rain_correlation(df)
    print(f"Correlation coefficient: {corr}")

    print("\n--- Monsoon (Jun-Sep) Rainfall by Year ---")
    monsoon = monsoon_analysis(df)
    print(monsoon)

    # Save a text summary report
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        f.write("NEW DELHI WEATHER ANALYSIS SUMMARY\n")
        f.write("=" * 60 + "\n\n")
        f.write("YEARLY SUMMARY\n")
        f.write(yearly.to_string() + "\n\n")
        f.write("MONTHLY CLIMATOLOGY\n")
        f.write(monthly.to_string() + "\n\n")
        f.write(f"TEMPERATURE TREND: {temp_trend}\n\n")
        f.write(f"RAINFALL TREND: {rain_trend}\n\n")
        f.write("EXTREMES\n")
        for k, v in ext.items():
            f.write(f"{k}: {v}\n")
        f.write(f"\nTEMP-RAINFALL CORRELATION: {corr}\n\n")
        f.write("MONSOON (Jun-Sep) RAINFALL BY YEAR\n")
        f.write(monsoon.to_string() + "\n")

    print(f"\nFull summary written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
