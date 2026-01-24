import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px

# 1. Database Connection
engine = create_engine("sqlite:///weather.db")

def load_data():
    query = "SELECT * FROM weather_reports ORDER BY timestamp DESC"
    return pd.read_sql(query, engine)

# 2. Dashboard UI
st.set_page_config(page_title="Weather ETL Dashboard", layout="wide")
st.title("🌍 Real-Time Weather Analytics")

df = load_data()

# 3. Key Metrics (The Top Row)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Records", len(df))
with col2:
    st.metric("Avg Global Temp", f"{df['temp'].mean():.1f}°C")
with col3:
    st.metric("Cities Tracked", df['city'].nunique())

# 4. Interactive Charts
st.subheader("Temperature Trends Over Time")
fig = px.line(df, x="timestamp", y="temp", color="city", markers=True)
st.plotly_chart(fig, use_container_width=True)

# 5. Raw Data Preview
if st.checkbox("Show Raw Data"):
    st.write(df)