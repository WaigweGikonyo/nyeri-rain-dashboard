import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# ───── CONFIG ─────
st.set_page_config(page_title="Nyeri Rain AI", layout="centered")

SUPABASE_URL = "https://ffbkgocjztagavphjbsq.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZmYmtnb2NqenRhZ2F2cGhqYnNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA2NzA5NjcsImV4cCI6MjA3NjI0Njk2N30.sudxLkD1r8ARMEKjVMiyQqTg1KkKR7gSrWA-CKjVKb4"

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# ───── FETCH DATA ─────
@st.cache_data(ttl=300)  # refresh every 5 min
def get_data():
    res = supabase.table("weather_data").select("*").order("timestamp", desc=True).limit(50).execute()
    return pd.DataFrame(res.data)

df = get_data()
if df.empty:
    st.error("No data yet – run your sensor script!")
    st.stop()

latest = df.iloc[0]
forecast = latest["forecast_weeks"] or [0]*8
total_rain = sum(forecast)

# ───── SEXY DASHBOARD ─────
st.markdown(f"""
<style>
    .big-font {{font-size:50px !important; font-weight:bold; text-align:center;}}
    .medium-font {{font-size:28px !important; text-align:center;}}
    .rain {{color: #00D4FF;}}
    .dry {{color: #FFB800;}}
    .plant {{color: #00FF00;}}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 style='text-align:center;'>🌧️ Dedan Kimathi Rain AI</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center;'>Live for Nyeri Farmers • November 2025</h3>", unsafe_allow_html=True)

# Current Advice – HUGE
advice = latest["crop_suggestions"] or "Waiting for data..."
color = "rain" if "Mvua" in advice else "dry" if "HAKUNA" in advice else "plant"
st.markdown(f"<p class='big-font {color}'>{advice}</p>", unsafe_allow_html=True)

# Key metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Next 8 Weeks", f"{total_rain:.0f} mm", delta=f"{total_rain-250:+.0f} vs 250mm")
with col2:
    st.metric("Season", latest.get("season_label", "Unknown"))
with col3:
    st.metric("Plant Now?", "YES" if latest.get("suitable_for_planting") else "NO", 
              delta="Go!" if latest.get("suitable_for_planting") else "Wait")

# 8-week forecast – animated bars
weeks = [f"W{i+1}" for i in range(8)]
fig = go.Figure(data=[go.Bar(x=weeks, y=forecast, marker_color="#00D4FF")])
fig.update_layout(title="8-Week Rainfall Forecast", template="plotly_dark", height=400)
st.plotly_chart(fig, use_container_width=True)

# Live weather
st.subheader("Current Weather")
col4, col5, col6 = st.columns(3)
col4.metric("Temperature", f"{latest['temperature']:.1f}°C")
col5.metric("Humidity", f"{latest['humidity']:.0f}%")
col6.metric("Wind", f"{latest['wind_speed']:.1f} m/s")

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%d %b %Y • %I:%M %p')} EAT | Model: {latest.get('model_version','v5.1')}")
