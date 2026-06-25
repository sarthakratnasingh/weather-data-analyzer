"""
clean_data.py
--------------
Loads the raw weather CSV, handles missing values, parses dates, adds
derived time columns (year, month, season), and saves a cleaned version
ready for analysis.

Usage:
    python src/clean_data.py
"""

from pathlib import Path

import pandas as pd

RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "new_delhi_weather_raw.csv"
PROCESSED_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "new_delhi_weather_clean.csv"


def assign_season(month: int) -> str:
    """Map month number to a meteorological season label for North India."""
    if month in (12, 1, 2):
        return "Winter"
    elif month in (3, 4):
        return "Spring/Pre-monsoon"
    elif month == 5:
        return "Summer"
    elif month in (6, 7, 8, 9):
        return "Monsoon"
    else:  # 10, 11
        return "Post-monsoon/Autumn"


def load_and_clean(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    # Parse dates
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # Report missing values before cleaning
    missing_before = df.isna().sum()
    print("Missing values before cleaning:")
    print(missing_before[missing_before > 0])

    # Set date as index temporarily for time-aware interpolation
    df = df.set_index("date")

    temp_cols = ["temp_max_c", "temp_min_c", "temp_mean_c"]
    rain_cols = ["precipitation_mm", "rain_mm"]

    # Temperature: interpolate gaps (weather doesn't jump erratically day to day)
    df[temp_cols] = df[temp_cols].interpolate(method="time", limit=5)

    # Rainfall: missing almost always means "not recorded" -> safer to assume 0
    # rather than interpolate (rain is highly non-smooth day to day)
    df[rain_cols] = df[rain_cols].fillna(0)

    df = df.reset_index()

    # Drop any remaining rows with missing temperature (gaps too long to interpolate)
    remaining_missing = df[temp_cols].isna().sum().sum()
    if remaining_missing > 0:
        print(f"Dropping {remaining_missing} rows with unfillable temperature gaps")
        df = df.dropna(subset=temp_cols)

    # Derived columns for grouping/analysis
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%b")
    df["season"] = df["month"].apply(assign_season)

    # Sanity checks
    assert (df["temp_max_c"] >= df["temp_min_c"]).all(), "Found max < min temperature!"
    assert (df["precipitation_mm"] >= 0).all(), "Found negative rainfall!"

    print(f"\nFinal cleaned dataset: {len(df)} rows, {df['date'].min().date()} to {df['date'].max().date()}")

    return df


def main():
    df = load_and_clean(RAW_PATH)
    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED_PATH, index=False)
    print(f"Saved cleaned data to {PROCESSED_PATH}")


if __name__ == "__main__":
    main()
