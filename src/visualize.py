"""
visualize.py
------------
Generates all charts for the New Delhi weather analysis project and saves
them as PNG files in outputs/figures/.

Charts produced:
  1. Yearly average temperature trend (line, with trend line)
  2. Monthly temperature climatology (avg max/mean/min by month)
  3. Monthly rainfall totals (bar chart, all years combined)
  4. Year x Month temperature heatmap
  5. Yearly total rainfall (bar chart, highlighting monsoon variability)
  6. Temperature vs rainfall scatter (daily)

Usage:
    python src/visualize.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

PROCESSED_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "new_delhi_weather_clean.csv"
FIG_DIR = Path(__file__).resolve().parent.parent / "outputs" / "figures"

MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# --- Color palette (semantic, not decorative) --------------------------
COLOR_MAX = "#d9480f"      # deep burnt orange - max temp
COLOR_MEAN = "#f08c00"     # amber - mean temp
COLOR_MIN = "#1971c2"      # steel blue - min temp
COLOR_RAIN = "#1864ab"     # rain blue
COLOR_TREND = "#495057"    # neutral grey for trend lines
BG_COLOR = "#fbfaf7"
GRID_COLOR = "#e0ddd5"

plt.rcParams.update({
    "figure.facecolor": BG_COLOR,
    "axes.facecolor": BG_COLOR,
    "axes.edgecolor": "#33312e",
    "axes.labelcolor": "#1a1a1a",
    "text.color": "#1a1a1a",
    "xtick.color": "#33312e",
    "ytick.color": "#33312e",
    "axes.grid": True,
    "grid.color": GRID_COLOR,
    "grid.linewidth": 0.8,
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def load_data() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_PATH, parse_dates=["date"])
    df["month_name"] = pd.Categorical(df["month_name"], categories=MONTH_ORDER, ordered=True)
    return df


def plot_yearly_temp_trend(df: pd.DataFrame):
    yearly = df.groupby("year")["temp_mean_c"].mean()
    years = yearly.index.values
    temps = yearly.values

    slope, intercept = np.polyfit(years, temps, 1)
    trend_line = slope * years + intercept

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(years, temps, marker="o", color=COLOR_MEAN, linewidth=2.2, markersize=6, label="Yearly avg temp")
    ax.plot(years, trend_line, linestyle="--", color=COLOR_TREND, linewidth=1.6,
            label=f"Trend: {slope:+.3f} \u00b0C/year")

    ax.set_title("New Delhi: Yearly Average Temperature (2016-2025)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Avg Temperature (\u00b0C)")
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "01_yearly_temperature_trend.png", dpi=150)
    plt.close(fig)


def plot_monthly_climatology(df: pd.DataFrame):
    monthly = df.groupby("month_name", observed=True).agg(
        avg_max=("temp_max_c", "mean"),
        avg_mean=("temp_mean_c", "mean"),
        avg_min=("temp_min_c", "mean"),
    ).reindex(MONTH_ORDER)

    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(MONTH_ORDER))

    ax.plot(x, monthly["avg_max"], marker="o", color=COLOR_MAX, label="Avg Max Temp", linewidth=2)
    ax.plot(x, monthly["avg_mean"], marker="o", color=COLOR_MEAN, label="Avg Mean Temp", linewidth=2)
    ax.plot(x, monthly["avg_min"], marker="o", color=COLOR_MIN, label="Avg Min Temp", linewidth=2)
    ax.fill_between(x, monthly["avg_min"], monthly["avg_max"], color=COLOR_MEAN, alpha=0.08)

    ax.set_xticks(x)
    ax.set_xticklabels(MONTH_ORDER)
    ax.set_title("New Delhi: Monthly Temperature Climatology (2016-2025 avg)")
    ax.set_ylabel("Temperature (\u00b0C)")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "02_monthly_temperature_climatology.png", dpi=150)
    plt.close(fig)


def plot_monthly_rainfall(df: pd.DataFrame):
    monthly_rain = df.groupby("month_name", observed=True)["precipitation_mm"].sum().reindex(MONTH_ORDER)
    n_years = df["year"].nunique()
    monthly_avg_rain = monthly_rain / n_years

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(MONTH_ORDER, monthly_avg_rain.values, color=COLOR_RAIN, alpha=0.85, width=0.65)

    # Highlight monsoon months (rain onset late May/June through September)
    monsoon_idx = [MONTH_ORDER.index(m) for m in ["Jun", "Jul", "Aug", "Sep"]]
    for i in monsoon_idx:
        bars[i].set_color("#0b4f8a")

    ax.set_title("New Delhi: Average Monthly Rainfall (2016-2025)")
    ax.set_ylabel("Avg Rainfall (mm)")
    ax.text(0.02, 0.95, "Darker bars = monsoon months (Jun-Sep)", transform=ax.transAxes,
            fontsize=9, color="#495057", va="top")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "03_monthly_rainfall.png", dpi=150)
    plt.close(fig)


def plot_temp_heatmap(df: pd.DataFrame):
    pivot = df.pivot_table(values="temp_mean_c", index="year", columns="month_name",
                            aggfunc="mean", observed=True)
    pivot = pivot.reindex(columns=MONTH_ORDER)

    fig, ax = plt.subplots(figsize=(9, 6))
    im = ax.imshow(pivot.values, cmap="YlOrRd", aspect="auto")

    ax.set_xticks(np.arange(len(MONTH_ORDER)))
    ax.set_xticklabels(MONTH_ORDER)
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_title("New Delhi: Mean Temperature Heatmap (Year x Month)")

    # Annotate cells with values
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            val = pivot.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.1f}", ha="center", va="center",
                        fontsize=8, color="#1a1a1a" if val < 30 else "white")

    cbar = fig.colorbar(im, ax=ax, label="Mean Temp (\u00b0C)")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "04_temperature_heatmap.png", dpi=150)
    plt.close(fig)


def plot_yearly_rainfall(df: pd.DataFrame):
    yearly_rain = df.groupby("year")["precipitation_mm"].sum()
    avg_rain = yearly_rain.mean()

    fig, ax = plt.subplots(figsize=(9, 5))
    colors = [COLOR_RAIN if v >= avg_rain else "#a5d8ff" for v in yearly_rain.values]
    ax.bar(yearly_rain.index.astype(str), yearly_rain.values, color=colors, width=0.6)
    ax.axhline(avg_rain, linestyle="--", color=COLOR_TREND, linewidth=1.5,
               label=f"10-yr avg: {avg_rain:.0f} mm")

    ax.set_title("New Delhi: Total Annual Rainfall (2016-2025)")
    ax.set_ylabel("Total Rainfall (mm)")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "05_yearly_rainfall.png", dpi=150)
    plt.close(fig)


def plot_temp_rain_scatter(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(8, 6))
    scatter = ax.scatter(df["temp_mean_c"], df["precipitation_mm"],
                          c=df["month"], cmap="twilight_shifted", alpha=0.5, s=14)

    ax.set_title("New Delhi: Daily Temperature vs Rainfall")
    ax.set_xlabel("Mean Temperature (\u00b0C)")
    ax.set_ylabel("Precipitation (mm)")

    corr = df["temp_mean_c"].corr(df["precipitation_mm"])
    ax.text(0.02, 0.95, f"Correlation: {corr:.2f}", transform=ax.transAxes,
            fontsize=10, color="#1a1a1a", va="top",
            bbox=dict(boxstyle="round", facecolor=BG_COLOR, edgecolor=GRID_COLOR))

    cbar = fig.colorbar(scatter, ax=ax, label="Month")
    cbar.set_ticks(range(1, 13))
    fig.tight_layout()
    fig.savefig(FIG_DIR / "06_temp_vs_rainfall_scatter.png", dpi=150)
    plt.close(fig)


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    df = load_data()

    print("Generating charts...")
    plot_yearly_temp_trend(df)
    print("  1/6 Yearly temperature trend")
    plot_monthly_climatology(df)
    print("  2/6 Monthly temperature climatology")
    plot_monthly_rainfall(df)
    print("  3/6 Monthly rainfall")
    plot_temp_heatmap(df)
    print("  4/6 Temperature heatmap")
    plot_yearly_rainfall(df)
    print("  5/6 Yearly rainfall")
    plot_temp_rain_scatter(df)
    print("  6/6 Temp vs rainfall scatter")

    print(f"\nAll charts saved to {FIG_DIR}")


if __name__ == "__main__":
    main()
