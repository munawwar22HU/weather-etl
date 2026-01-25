import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px

# ============================================================
# Config
# ============================================================
st.set_page_config(
    page_title="Weather ETL Dashboard",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Small helper to keep visuals consistent
st.markdown(
    """
    <style>
      .block-container { padding-top: 2rem; }
      [data-testid="stMetricValue"] { font-size: 1.6rem; }
      [data-testid="stMetricLabel"] { opacity: 0.85; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# Database
# ============================================================
engine = create_engine("sqlite:///weather.db")


def table_exists() -> bool:
    """Return True if weather_reports exists in the SQLite DB."""
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='table' AND name='weather_reports'
                """
            )
        ).fetchone()
        return row is not None



def load_data() -> pd.DataFrame:
    """Load weather reports and parse types safely."""
    df = pd.read_sql("SELECT * FROM weather_reports ORDER BY timestamp DESC", engine)

    # Parse types (robust to nulls / strings)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    if "processed_at" in df.columns:
        df["processed_at"] = pd.to_datetime(df["processed_at"], errors="coerce")

    for col in ["temp", "humidity"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


# ============================================================
# Header
# ============================================================
st.title("🌍 Weather ETL Dashboard")
st.caption("ETL → SQLite → Streamlit dashboard for quick monitoring and city-level trends.")

if not table_exists():
    st.error("Table `weather_reports` not found. Run the ETL once to create/populate it.")
    st.stop()

df = load_data()
if df.empty:
    st.warning("No data found in `weather_reports` yet. Run the ETL pipeline to insert rows.")
    st.stop()

# ============================================================
# Sidebar Filters
# ============================================================
st.sidebar.header("Filters")

cities = sorted(df["city"].dropna().unique().tolist())
selected_cities = st.sidebar.multiselect("Cities", cities, default=cities)

filtered = df[df["city"].isin(selected_cities)] if selected_cities else df

# Date range toggle (keeps it simple)
use_date = st.sidebar.toggle("Filter by date range", value=False)

if use_date and filtered["timestamp"].notna().any():
    min_d = filtered["timestamp"].min().date()
    max_d = filtered["timestamp"].max().date()
    start_d, end_d = st.sidebar.date_input(
        "Date range",
        value=(min_d, max_d),
        min_value=min_d,
        max_value=max_d,
    )
    start_dt = pd.to_datetime(start_d)
    end_dt = pd.to_datetime(end_d) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    filtered = filtered[(filtered["timestamp"] >= start_dt) & (filtered["timestamp"] <= end_dt)]

show_raw = st.sidebar.toggle("Show raw data", value=False)

# ============================================================
# KPI Row
# ============================================================
latest_ts = filtered["timestamp"].max()
latest_str = latest_ts.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(latest_ts) else "—"

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Records", f"{len(filtered):,}")
k2.metric("Cities Tracked", f"{filtered['city'].nunique():,}")

avg_temp = filtered["temp"].mean() if filtered["temp"].notna().any() else None
k3.metric("Average Temp", "—" if avg_temp is None else f"{avg_temp:.1f} °C")

k4.metric("Latest Timestamp", latest_str)

st.divider()

# ============================================================
# Latest Snapshot Table (1 row per city)
# ============================================================
st.subheader("Latest Snapshot by City")
st.caption("Most recent reading for each selected city.")

latest = (
    filtered.dropna(subset=["timestamp"])
    .sort_values("timestamp", ascending=False)
    .groupby("city", as_index=False)
    .head(1)
    .sort_values("city")
)

# Rename for cleaner presentation (keeps DB schema unchanged)
display_latest = latest.copy()
rename_map = {
    "city": "City",
    "temp": "Temp (°C)",
    "humidity": "Humidity (%)",
    "description": "Conditions",
    "timestamp": "Timestamp",
}
display_latest = display_latest.rename(columns={k: v for k, v in rename_map.items() if k in display_latest.columns})

table_cols = [c for c in ["City", "Temp (°C)", "Humidity (%)", "Conditions", "Timestamp"] if c in display_latest.columns]
st.dataframe(display_latest[table_cols], use_container_width=True, hide_index=True)

st.divider()

# ============================================================
# Trend Chart
# ============================================================
st.subheader("Temperature Trends")
st.caption("Temperature over time for the selected cities.")

plot_df = filtered.dropna(subset=["timestamp", "temp"]).copy()

if plot_df.empty:
    st.info("Not enough temperature data to plot yet.")
else:
    fig = px.line(
        plot_df,
        x="timestamp",
        y="temp",
        color="city",
        markers=True,
        labels={
            "timestamp": "Time",
            "temp": "Temperature (°C)",
            "city": "City",
        },
    )

    # Make chart styling more consistent and readable
    fig.update_layout(
        legend_title_text="City",
        hovermode="x unified",
        margin=dict(l=10, r=10, t=10, b=10),
    )

    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# Raw Data (optional)
# ============================================================
if show_raw:
    st.subheader("Raw Data (Filtered)")
    st.caption("This is the exact data pulled from SQLite after filters are applied.")
    st.dataframe(filtered, use_container_width=True, hide_index=True)
