import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import plotly.graph_objects as go

# ───── CONFIG ─────
st.set_page_config(page_title="Nyeri Rain AI", layout="centered")

# AUTO REFRESH EVERY 60 SECONDS (THIS IS THE CORRECT 2025 WAY)
st.autorefresh(interval=60, key="auto")

# ───── SUPABASE ─────
SUPABASE_URL = "https://ffbkgocjztagavphjbsq.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInRlZiI6ImZmYmtnb2NqenRhZ2F2cGhqYnNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA2NzA5NjcsImV4cCI6MjA3NjI0Njk2N30.sudxLkD1r8ARMEKjVMiyQqTg1KkKR7gSrWA-CKjVKb4"

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# ───── FETCH DATA ─────
@st.cache_data(ttl=55)
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

# ───── PLANTING ADVICE ─────
def get_planting_advice():
    good_weeks = sum(1 for x in forecast if x >= 50)
    if total_rain >= 400 and good_weeks >= 4:
        return {"answer": "YES! Panda Sasa!", "color": "#00FF41", "subtext": f"{total_rain:.0f} mm → Perfect!", "emoji": "Panda Sasa!"}
    elif total_rain >= 300:
        return {"answer": "Maybe – Jaribu Tu", "color": "#FFB800", "subtext": f"{total_rain:.0f} mm", "emoji": "Thinking"}
    else:
        return {"answer": "NO – Subiri Kidogo", "color": "#FF3B30", "subtext": f"Only {total_rain:.0f} mm", "emoji": "Hourglass"}

advice = get_planting_advice()

# ───── SEXY CSS ─────
st.markdown("""
<style>
    .big-font {font-size:68px !important; font-weight:bold; text-align:center;}
    .medium-font {font-size:32px !important; text-align:center;}
</style>
""", unsafe_allow_html=True)

# ───── DASHBOARD CONTENT ─────
st.markdown("<h1 style='text-align:center;'>Dedan Kimathi Rain AI</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center;'>Live for Nyeri Farmers • November 2025</h3>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00D4FF;'>PANDA H520 NA KAT B9</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align:center; color:#FFFFFF;'>HARAKA! Mvua fupi!</h2>", unsafe_allow_html=True)

st.markdown(f"<p class='big-font' style='color:{advice['color']}'>{advice['answer']}</p>", unsafe_allow_html=True)
st.markdown(f"<p class='medium-font'>{advice['emoji']} {advice['subtext']}</p>", unsafe_allow_html=True)

# Metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Next 8 Weeks", f"{total_rain:.0f} mm", f"{total_rain-250:+.0f} vs 250mm")
with col2:
    st.metric("Season", "Rainy Season" if total_rain >= 350 else "Dry Season")
with col3:
    st.metric("Plant Now?", advice["answer"].split("!")[0], advice["subtext"])

# Chart
weeks = [f"Week {i+1}" for i in range(8)]
fig = go.Figure(go.Bar(x=weeks, y=forecast, marker_color="#00D4FF", text=[f"{v}mm" for v in forecast], textposition="outside"))
fig.update_layout(title="8-Week Rainfall Forecast", template="plotly_dark", height=450)
st.plotly_chart(fig, use_container_width=True)

# Current conditions + Solar
st.subheader("Current Conditions")
cols = st.columns(4)
solar = latest.get('solar_radiation') or latest.get('solar') or 0

cols[0].metric("Temp", f"{latest['temperature']:.1f}°C")
cols[1].metric("Humidity", f"{latest['humidity']:.0f}%")
cols[2].metric("Wind", f"{latest['wind_speed']:.1f} m/s")
cols[3].metric("Solar", f"{solar:.0f} W/m²", "Jua Kali!" if solar > 700 else "Cloudy")

# Footer
st.caption(f"Auto-refreshing every minute • Last update: {datetime.now().strftime('%H:%M:%S')}")
