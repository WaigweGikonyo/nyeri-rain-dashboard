import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client
import json
import time

# ───── 1. DESIGN & PAGE CONFIG ─────
st.set_page_config(page_title="Nyeri Weather AI", layout="wide", page_icon="🌤️")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .hero-card { padding: 50px; border-radius: 30px; text-align: center; margin-bottom: 40px; border: 1px solid rgba(255, 255, 255, 0.2); box-shadow: 0 20px 40px rgba(0,0,0,0.1); }
    .card-temp { background: linear-gradient(135deg, rgba(255,111,0,0.1), rgba(255,204,128,0.1)); border: 1px solid #FF6F00; padding: 20px; border-radius: 20px; text-align: center; height: 150px; }
    .card-hum { background: linear-gradient(135deg, rgba(0,145,234,0.1), rgba(129,212,250,0.1)); border: 1px solid #0091EA; padding: 20px; border-radius: 20px; text-align: center; height: 150px; }
    .card-wind { background: linear-gradient(135deg, rgba(0,200,83,0.1), rgba(185,246,202,0.1)); border: 1px solid #00C853; padding: 20px; border-radius: 20px; text-align: center; height: 150px; }
    .card-solar { background: linear-gradient(135deg, rgba(255,214,0,0.1), rgba(255,245,157,0.1)); border: 1px solid #FFD600; padding: 20px; border-radius: 20px; text-align: center; height: 150px; }
    .card-rain { background: linear-gradient(135deg, rgba(171,71,188,0.1), rgba(225,190,231,0.1)); border: 1px solid #AB47BC; padding: 20px; border-radius: 20px; text-align: center; height: 150px; }
    .footer { text-align: center; padding: 60px 0 30px 0; color: #888; font-weight: 700; letter-spacing: 2px; font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

# ───── 2. CONNECTIONS ─────
SUPABASE_URL = "https://ffbkgocjztagavphjbsq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZmYmtnb2NqenRhZ2F2cGhqYnNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA2NzA5NjcsImV4cCI6MjA3NjI0Njk2N30.sudxLkD1r8ARMEKjVMiyQqTg1KkKR7gSrWA-CKjVKb4"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ───── 3. DATA FETCHING (UNCACHED FOR LIVE SYNC) ─────
def fetch_active_data():
    try:
        # No caching here ensures we see what you see in the Supabase Dashboard
        res = supabase.table("weather_data").select("*").order("timestamp", desc=True).limit(1).execute()
        return res.data[0] if res.data else None
    except:
        return None

raw_data = fetch_active_data()

# Sidebar Sync Status
st.sidebar.title("🛠️ Station Debugger")
if raw_data:
    st.sidebar.success(f"Synced with Supabase ID: {raw_data.get('id')}")
    st.sidebar.write("**Latest Data Received:**")
    st.sidebar.json(raw_data)
else:
    st.error("🛰️ Station Offline. Check your AI Background Script.")
    st.stop()

# ───── 4. SANITIZER ─────
def sanitize(val, default=0.0):
    try: return float(val) if val is not None else default
    except: return default

# Forecast Parsing
f_raw = raw_data.get("forecast_weeks")
forecast = [0.0] * 8
try:
    if isinstance(f_raw, str):
        forecast = [float(x) for x in json.loads(f_raw.replace("'", '"'))]
    elif isinstance(f_raw, list):
        forecast = [float(x) for x in f_raw]
except: pass

ai_label = str(raw_data.get("season_label", "Updating"))
ai_advice = str(raw_data.get("crop_suggestions") or "")
if ai_advice.lower() in ["none", "null", "nan"]: ai_advice = ""

# Theme Logic
if "Rainy" in ai_label:
    emoji, color, bg_alpha = "🌧️", "#00E676", "rgba(0, 230, 118, 0.1)"
elif "Dry" in ai_label:
    emoji, color, bg_alpha = "☀️", "#FF5252", "rgba(255, 82, 82, 0.1)"
else:
    emoji, color, bg_alpha = "⛅", "#FFD740", "rgba(255, 215, 64, 0.1)"

# ───── 5. UI DISPLAY ─────
st.markdown(f"<h1 style='text-align: center; font-size: 85px; font-weight: 900; color: #00D4FF; margin-bottom: 0;'>NYERI WEATHER AI</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #888; font-weight: 600;'>STATION SYNCED: {raw_data.get('timestamp')}</p>", unsafe_allow_html=True)

# Hero Card
st.markdown(f"""
    <div class="hero-card" style="background-color: {bg_alpha}; border-top: 15px solid {color};">
        <span style="font-size: 80px;">{emoji}</span>
        <h1 style="font-size: 65px; font-weight: 900; margin: 10px 0;">{ai_label.upper()}</h1>
        <p style="font-size: 26px; font-weight: 700; color: {color};">{ai_advice}</p>
    </div>
""", unsafe_allow_html=True)

st.write("---")

col_graph, col_stats = st.columns([2, 1])
with col_graph:
    fig = go.Figure(go.Scatter(x=[f"Wk {i+1}" for i in range(8)], y=forecast, fill='tozeroy', line=dict(color='#00D4FF', width=5), mode='lines+markers'))
    fig.update_layout(title="<b>8-WEEK RAINFALL PULSE</b>", height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

with col_stats:
    total_rain = sanitize(raw_data.get("total_8week_rain"), default=sum(forecast))
    gauge = go.Figure(go.Indicator(mode="gauge+number", value=total_rain, title={'text': "Total Rain (mm)"}, gauge={'bar':{'color':color}, 'axis':{'range':[0,600]}}))
    gauge.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(gauge, use_container_width=True)

st.write("---")
st.markdown("<h3 style='text-align: center; font-weight: 800;'>📍 LIVE STATION FEED</h3>", unsafe_allow_html=True)

# colorful metric cards with emojis
m1, m2, m3, m4, m5 = st.columns(5)
with m1: st.markdown(f"<div class='card-temp'>🌡️<br><small>TEMP</small><br><h2>{sanitize(raw_data.get('temperature'))}°C</h2></div>", unsafe_allow_html=True)
with m2: st.markdown(f"<div class='card-hum'>💧<br><small>HUMIDITY</small><br><h2>{sanitize(raw_data.get('humidity'))}%</h2></div>", unsafe_allow_html=True)
with m3: st.markdown(f"<div class='card-wind'>🌬️<br><small>WIND</small><br><h2>{sanitize(raw_data.get('wind_speed'))} m/s</h2></div>", unsafe_allow_html=True)
with m4: st.markdown(f"<div class='card-solar'>☀️<br><small>SOLAR</small><br><h2>{sanitize(raw_data.get('solar_radiation'))} W/m²</h2></div>", unsafe_allow_html=True)
with m5: st.markdown(f"<div class='card-rain'>🌧️<br><small>RAIN</small><br><h2>{sanitize(raw_data.get('precipitation'))} mm</h2></div>", unsafe_allow_html=True)

st.markdown("<div class='footer'>MADE FOR NYERI FARMERS WITH LOVE ❤️</div>", unsafe_allow_html=True)

# refresh loop
time.sleep(10)
st.rerun()
