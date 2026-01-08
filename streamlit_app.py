import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client

# ───── 1. SETUP ─────
st.set_page_config(page_title="Nyeri Rain AI", layout="wide")

# Modern Styling
st.markdown("""
    <style>
    .status-card { padding: 30px; border-radius: 20px; text-align: center; border: 1px solid rgba(128,128,128,0.2); margin-bottom: 20px; }
    .metric-card { background: rgba(0, 150, 255, 0.05); padding: 20px; border-radius: 15px; text-align: center; }
    .footer { text-align: center; padding: 40px; color: #888; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

# ───── 2. DATA ─────
SUPABASE_URL = "https://ffbkgocjztagavphjbsq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZmYmtnb2NqenRhZ2F2cGhqYnNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA2NzA5NjcsImV4cCI6MjA3NjI0Njk2N30.sudxLkD1r8ARMEKjVMiyQqTg1KkKR7gSrWA-CKjVKb4" 
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=10)
def fetch_now():
    try:
        res = supabase.table("weather_data").select("*").order("timestamp", desc=True).limit(1).execute()
        return pd.DataFrame(res.data)
    except: return pd.DataFrame()

df = fetch_now()

if df.empty:
    st.info("🛰️ Initializing Satellite Link... Waiting for first sensor data.")
    st.stop()

latest = df.iloc[0]

# --- CLEAN DATA (Fixes the TypeError) ---
ai_label = str(latest.get("season_label") or "STATION ONLINE")
ai_advice = str(latest.get("crop_suggestions") or "Analyzing trends...")
raw_f = latest.get("forecast_weeks")
forecast = [float(x) for x in raw_f] if isinstance(raw_f, list) else [0.0]*8
total_rain = float(latest.get("total_8week_rain") or sum(forecast))

theme_color = "#00E676" if "Rainy" in ai_label else "#FFD740"

# ───── 3. UI ─────
st.markdown(f"<div class='status-card' style='border-top: 10px solid {theme_color};'> <h1 style='font-size: 45px;'>{ai_label.upper()}</h1> <p style='font-size: 20px; color: {theme_color};'>{ai_advice}</p> </div>", unsafe_allow_html=True)

c_chart, c_gauge = st.columns([2, 1])

with c_chart:
    fig = go.Figure(go.Scatter(x=[f"W{i+1}" for i in range(8)], y=forecast, fill='tozeroy', line_color='#0091EA'))
    fig.update_layout(title="8-Week Pulse", template=None, height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

with c_gauge:
    gauge = go.Figure(go.Indicator(mode="gauge+number", value=total_rain, title={'text': "Total (mm)"}, gauge={'bar': {'color': theme_color}, 'axis': {'range': [0, 600]}}))
    gauge.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(gauge, use_container_width=True)

st.markdown("### 📡 Station Sensors")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Temp", f"{latest['temperature']}°C")
m2.metric("Humidity", f"{latest['humidity']}%")
m3.metric("Wind", f"{latest.get('wind_speed', 0)} m/s")
m4.metric("Solar", f"{latest.get('solar_radiation', 0)} W/m²")

st.markdown("<div class='footer'>MADE FOR NYERI FARMERS WITH LOVE ❤️</div>", unsafe_allow_html=True)
