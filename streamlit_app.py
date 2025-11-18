import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import plotly.graph_objects as go
import time

# ───── AUTO REFRESH EVERY 60 SECONDS ─────
st.set_page_config(page_title="Nyeri Rain AI", layout="centered")

# Add this magic line → forces refresh every 60 seconds
st.rerun_scope = st.experimental_rerun
st.autorefresh(interval=60_000, key="datarefresh")  # 60,000 ms = 1 minute

# ───── SUPABASE CONNECTION ─────
SUPABASE_URL = "https://ffbkgocjztagavphjbsq.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInRlZiI6ImZmYmtnb2NqenRhZ2F2cGhqYnNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA2NzA5NjcsImV4cCI6MjA3NjI0Njk2N30.sudxLkD1r8ARMEKjVMiyQqTg1KkKR7gSrWA-CKjVKb4"

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# ───── FETCH LATEST DATA (cached for speed, but refreshed every run) ─────
@st.cache_data(ttl=55)  # cache for 55 seconds so it feels instant
def get_data():
    res = supabase.table("weather_data").select("*").order("timestamp", desc=True).limit(1).execute()
    return pd.DataFrame(res.data)

df = get_data()
if df.empty:
    st.error("No data yet – waiting for sensor...")
    st.stop()

latest = df.iloc[0]
forecast = latest["forecast_weeks"] or [0]*8
total_rain = sum(forecast)

# ───── SMART PLANTING ADVICE ─────
def get_planting_advice():
    total = total_rain
    good_weeks = sum(1 for x in forecast if x >= 50)
    
    if total >= 400 and good_weeks >= 4:
        return {"answer": "YES! Panda Sasa!", "color": "#00FF41", "subtext": f"Perfect rains → {total:.0f} mm", "emoji": "🌱🚀🌧️"}
    elif total >= 300:
        return {"answer": "Maybe – Jaribu Tu", "color": "#FFB800", "subtext": f"{total:.0f} mm – okay", "emoji": "🤔"}
    else:
        return {"answer": "NO – Subiri Kidogo", "color": "#FF3B30", "subtext": f"Only {total:.0f} mm", "emoji": "⏳"}

advice = get_planting_advice()

# ───── SEXY CSS + LIVE COUNTDOWN ─────
st.markdown("""
<style>
    .big-font {font-size:68px !important; font-weight:bold; text-align:center; margin:0;}
    .medium-font {font-size:32px !important; text-align:center; margin:10px;}
    .countdown {font-size:20px; color:#888; text-align:center;}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 style='text-align:center;'>🌧️ Dedan Kimathi Rain AI</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center;'>Live for Nyeri Farmers • November 2025</h3>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00D4FF;'>PANDA H520 NA KAT B9</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align:center; color:#FFFFFF;'>HARAKA! Mvua fupi! 💦</h2>", unsafe_allow_html=True)

# MAIN ADVICE
st.markdown(f"<p class='big-font' style='color:{advice['color']}'>{advice['answer']}</p>", unsafe_allow_html=True)
st.markdown(f"<p class='medium-font'>{advice['emoji']} {advice['subtext']}</p>", unsafe_allow_html=True)

# Live countdown timer
st.markdown(f"<p class='countdown'>Refreshing in {60 - (int(time.time()) % 60)} seconds...</p>", unsafe_allow_html=True)

# Key Metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Next 8 Weeks", f"{total_rain:.0f} mm", 
              delta=f"{total_rain-250:+.0f} vs 250mm")
with col2:
    season = "Rainy Season 🌧️" if total_rain >= 350 else "Dry Season ☀️"
    st.metric("Season", season)
with col3:
    st.metric("Plant Now?", advice["answer"].split("!")[0], delta=advice["subtext"])

# 8-Week Forecast
weeks = [f"Week {i+1}" for i in range(8)]
fig = go.Figure(data=[go.Bar(x=weeks, y=forecast, marker_color="#00D4FF",
                             text=[f"{v}mm" for v in forecast], textposition="outside")])
fig.update_layout(title="8-Week Rainfall Forecast", template="plotly_dark", height=450,
                  plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', yaxis_title="Rainfall (mm)")
st.plotly_chart(fig, use_container_width=True)

# Current Weather + Solar Radiation
st.subheader("🌤️ Current Conditions")
col_a, col_b, col_c, col_d = st.columns(4)
solar = latest.get('solar_radiation') or latest.get('solar') or 0

with col_a:
    st.metric("Temperature", f"{latest['temperature']:.1f}°C")
with col_b:
    st.metric("Humidity", f"{latest['humidity']:.0f}%")
with col_c:
    st.metric("Wind Speed", f"{latest['wind_speed']:.1f} m/s")
with col_d:
    st.metric("Solar Radiation", f"{solar:.0f} W/m²", 
              delta="Jua Kali!" if solar > 700 else "Cloudy")

if solar > 800:
    st.markdown("<h2 style='text-align:center;'>☀️☀️ JUA KALI SANA! ☀️☀️</h2>", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%d %b %Y • %I:%M %p')} • Auto-refreshes every minute")
st.markdown("<p style='text-align:center; color:#888;'>Built with ❤️ for Nyeri Farmers</p>", unsafe_allow_html=True)
