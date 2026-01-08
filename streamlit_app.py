import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client
import json
import time

# ───── 1. DESIGN & PAGE CONFIG ─────
st.set_page_config(page_title="Nyeri Weather AI", layout="wide", page_icon="🌤️")
st.cache_data.clear()

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .hero-card { padding: 30px; border-radius: 25px; text-align: center; margin-bottom: 20px; border: 1px solid rgba(255, 255, 255, 0.1); }
    
    .card-metric { 
        padding: 10px; 
        border-radius: 15px; 
        text-align: center; 
        height: 130px; 
        display: flex; 
        flex-direction: column; 
        justify-content: center;
        background: rgba(255,255,255,0.02);
    }
    .card-metric span { font-size: 20px; margin-bottom: 5px; } /* Emoji size */
    .card-metric small { font-size: 9px; font-weight: 700; color: #777; text-transform: uppercase; margin-bottom: 2px; }
    .card-metric h2 { font-size: 18px; margin: 0; font-weight: 800; color: #FFF; }
    .footer { text-align: center; padding: 20px; color: #444; font-size: 11px; }
    </style>
""", unsafe_allow_html=True)

# ───── 2. CONNECTIONS ─────
SUPABASE_URL = "https://ffbkgocjztagavphjbsq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZmYmtnb2NqenRhZ2F2cGhqYnNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA2NzA5NjcsImV4cCI6MjA3NjI0Njk2N30.sudxLkD1r8ARMEKjVMiyQqTg1KkKR7gSrWA-CKjVKb4"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ───── 3. SMART DATA FETCH (SKIP ZEROES) ─────
def fetch_active_data():
    try:
        # Filtering for rows where temperature > 0 to ignore ESP8266/DHT glitches
        res = supabase.table("weather_data").select("*").gt("temperature", 0).order("timestamp", desc=True).limit(1).execute()
        return res.data[0] if res.data else None
    except: return None

raw_data = fetch_active_data()

# ───── 4. LOGIC & CLEANING ─────
if not raw_data:
    st.info("📡 Filtering station glitches... Please wait.")
    time.sleep(5); st.rerun()

def sanitize(val, default=0.0):
    try: return float(val) if val is not None else default
    except: return default

f_raw = raw_data.get("forecast_weeks")
forecast = [sanitize(x) for x in (json.loads(f_raw.replace("'", '"')) if isinstance(f_raw, str) else (f_raw or [0]*8))]
total_rain = sanitize(raw_data.get("total_8week_rain")) or sum(forecast)

ai_label = str(raw_data.get("season_label", "Syncing"))
ai_advice = str(raw_data.get("crop_suggestions") or "")
emoji, color, bg_alpha = ("🌧️", "#00E676", "rgba(0, 230, 118, 0.05)") if "Rainy" in ai_label else ("☀️", "#FF5252", "rgba(255, 82, 82, 0.05)")

# ───── 5. UI DISPLAY ─────
st.markdown(f"<h1 style='text-align: center; font-size: 45px; font-weight: 900; color: #00D4FF;'>NYERI WEATHER AI</h1>", unsafe_allow_html=True)

st.markdown(f"""
    <div class="hero-card" style="background-color: {bg_alpha}; border-top: 8px solid {color};">
        <span style="font-size: 40px;">{emoji}</span>
        <h2 style="font-size: 35px; font-weight: 900; margin: 5px 0;">{ai_label.upper()}</h2>
        <p style="font-size: 16px; font-weight: 600; color: {color};">{ai_advice}</p>
    </div>
""", unsafe_allow_html=True)

c1, c2 = st.columns([2, 1])
with c1:
    fig = go.Figure(go.Scatter(x=[f"Wk {i+1}" for i in range(8)], y=forecast, fill='tozeroy', line=dict(color='#00D4FF', width=3)))
    fig.update_layout(height=250, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)
with c2:
    gauge = go.Figure(go.Indicator(mode="gauge+number", value=total_rain, gauge={'bar':{'color':color}, 'axis':{'range':[0,600]}}))
    gauge.update_layout(height=250, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(gauge, use_container_width=True)

# BOTTOM BOXES (Emojis Restored + Smaller Fonts)
m1, m2, m3, m4, m5 = st.columns(5)
with m1: st.markdown(f"<div class='card-metric' style='border: 1px solid #FF6F00;'><span>🌡️</span><small>Temp</small><h2>{sanitize(raw_data.get('temperature'))}°C</h2></div>", unsafe_allow_html=True)
with m2: st.markdown(f"<div class='card-metric' style='border: 1px solid #0091EA;'><span>💧</span><small>Humidity</small><h2>{sanitize(raw_data.get('humidity'))}%</h2></div>", unsafe_allow_html=True)
with m3: st.markdown(f"<div class='card-metric' style='border: 1px solid #00C853;'><span>🌬️</span><small>Wind</small><h2>{sanitize(raw_data.get('wind_speed'))}m/s</h2></div>", unsafe_allow_html=True)
with m4: st.markdown(f"<div class='card-metric' style='border: 1px solid #FFD600;'><span>☀️</span><small>Solar</small><h2>{sanitize(raw_data.get('solar_radiation'))}W/m²</h2></div>", unsafe_allow_html=True)
with m5: st.markdown(f"<div class='card-metric' style='border: 1px solid #AB47BC;'><span>🌧️</span><small>Rain</small><h2>{sanitize(raw_data.get('precipitation'))}mm</h2></div>", unsafe_allow_html=True)

st.sidebar.write(f"✅ Syncing ID: {raw_data.get('id')}")

time.sleep(10)
st.rerun()
