import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client
import json
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ───── 1. DESIGN & PAGE CONFIG ─────
st.set_page_config(page_title="Nyeri Weather AI", layout="wide", page_icon="🌤️")
st.cache_data.clear()

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* Fixed visibility for Hero Card */
    .hero-card { 
        padding: 30px; 
        border-radius: 25px; 
        text-align: center; 
        margin-bottom: 20px; 
        border: 1px solid rgba(255, 255, 255, 0.1);
        background-color: #1E1E1E; /* Force dark background so white text shows */
        color: white;
    }
    
    .card-metric { 
        padding: 10px; border-radius: 15px; text-align: center; height: 130px; 
        display: flex; flex-direction: column; justify-content: center;
        background: rgba(128, 128, 128, 0.1); /* Neutral tint for both modes */
        border: 1px solid rgba(128, 128, 128, 0.2);
    }
    
    .card-metric span { font-size: 20px; margin-bottom: 5px; }
    .card-metric small { font-size: 9px; font-weight: 700; color: #888; text-transform: uppercase; margin-bottom: 2px; }
    
    /* Dynamic Metric Text Color */
    .card-metric h2 { font-size: 18px; margin: 0; font-weight: 800; }
    
    .footer { text-align: center; padding: 20px; color: #888; font-size: 11px; }
    </style>
""", unsafe_allow_html=True)

# ───── 2. CONNECTIONS ─────
SUPABASE_URL = "https://ffbkgocjztagavphjbsq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZmYmtnb2NqenRhZ2F2cGhqYnNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA2NzA5NjcsImV4cCI6MjA3NjI0Njk2N30.sudxLkD1r8ARMEKjVMiyQqTg1KkKR7gSrWA-CKjVKb4"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# EMAIL SETTINGS
SENDER_EMAIL = "gikonyowaigwe@gmail.com"
SENDER_PASSWORD = "fsox aavj llad gvvp" 
RECEIVERS = ["kinuthiajohnson941@gmail.com", "nganga.irvine19@students.dkut.ac.ke", "gikonyo.joy21@students.dkut.ac.ke"]

def send_weather_email(label, advice, rain_total, emoji):
    try:
        msg = MIMEMultipart()
        msg["From"] = f"Nyeri Weather AI <{SENDER_EMAIL}>"
        msg["To"] = ", ".join(RECEIVERS)
        msg["Subject"] = f"⚠️ Weather Shift: {label}"
        
        body = f"""
        📍 NYERI WEATHER AI - STATUS CHANGE DETECTED
        -------------------------------------------
        New Season Status: {label} {emoji}
        Predicted 8-Week Total: {rain_total:.2f}mm
        
        AGRICULTURAL ADVICE:
        {advice}
        
        This is an automated alert based on live station data.
        """
        msg.attach(MIMEText(body, "plain"))
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception:
        return False

# ───── 3. DATA FETCHING ─────
def fetch_active_data():
    try:
        res = supabase.table("weather_data").select("*").gt("temperature", 0).order("timestamp", desc=True).limit(1).execute()
        return res.data[0] if res.data else None
    except: return None

raw_data = fetch_active_data()

# ───── 4. LOGIC & DATA CLEANING ─────
if not raw_data:
    st.info("📡 Station Syncing... Filtering out sensor glitches.")
    time.sleep(5); st.rerun()

def sanitize(val, default=0.0):
    try: return float(val) if val is not None else default
    except: return default

f_raw = raw_data.get("forecast_weeks")
forecast = [sanitize(x) for x in (json.loads(f_raw.replace("'", '"')) if isinstance(f_raw, str) else (f_raw or [0]*8))]
total_rain = sanitize(raw_data.get("total_8week_rain")) or sum(forecast)

ai_label = str(raw_data.get("season_label", "Station Online"))
ai_advice = str(raw_data.get("crop_suggestions") or "Monitoring conditions...")
emoji, color, bg_alpha = ("🌧️", "#00E676", "rgba(0, 230, 118, 0.15)") if "Rainy" in ai_label else ("☀️", "#FF5252", "rgba(255, 82, 82, 0.15)")

# ───── 5. SMART EMAIL TRIGGER ─────
if "last_season" not in st.session_state:
    st.session_state.last_season = ai_label
if "last_advice" not in st.session_state:
    st.session_state.last_advice = ai_advice

if (ai_label != st.session_state.last_season or ai_advice != st.session_state.last_advice) and len(ai_advice) > 5:
    if send_weather_email(ai_label, ai_advice, total_rain, emoji):
        st.sidebar.success(f"📧 Alert Sent: {ai_label}")
        st.session_state.last_season = ai_label
        st.session_state.last_advice = ai_advice

# ───── 6. UI DISPLAY ─────
st.markdown(f"<h1 style='text-align: center; font-size: 45px; font-weight: 900; color: #00D4FF; margin-bottom: 0;'>NYERI WEATHER AI</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #888; font-size: 12px;'>LAST SYNC: {raw_data.get('timestamp')}</p>", unsafe_allow_html=True)

# Hero Section (Fixed for Light Mode)
st.markdown(f"""
    <div class="hero-card" style="border-top: 8px solid {color}; background-color: #1A1A1A;">
        <span style="font-size: 40px;">{emoji}</span>
        <h2 style="font-size: 35px; font-weight: 900; margin: 5px 0; color: white;">{ai_label.upper()}</h2>
        <p style="font-size: 16px; font-weight: 600; color: {color};">{ai_advice}</p>
    </div>
""", unsafe_allow_html=True)

c1, c2 = st.columns([2, 1])

with c1:
    # --- BAR GRAPH ---
    fig = go.Figure(go.Bar(x=[f"Wk {i+1}" for i in range(8)], y=forecast, marker_color='#00D4FF', opacity=0.8))
    fig.update_layout(
        title={'text': "<b>WEEKLY RAINFALL PREDICTION</b>", 'y':0.95, 'x':0.5, 'xanchor': 'center'},
        xaxis_title="Forecast Week", yaxis_title="Rainfall (mm)",
        height=300, margin=dict(l=50, r=20, t=60, b=50), 
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        # Removed hardcoded 'white' font so it follows system theme
    )
    st.plotly_chart(fig, use_container_width=True)

with c2:
    # --- GAUGE ---
    gauge = go.Figure(go.Indicator(
        mode="gauge+number", value=total_rain, 
        title={'text': "<b>8-WEEK TOTAL (MM)</b>", 'font': {'size': 16}},
        gauge={'bar':{'color':color}, 'axis':{'range':[0,600]}}
    ))
    gauge.update_layout(height=300, margin=dict(l=30, r=30, t=50, b=20), paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(gauge, use_container_width=True)

# Live Station Boxes
st.markdown("<h4 style='text-align: center; font-weight: 800; margin-top: 20px;'>📍 LIVE STATION FEED</h4>", unsafe_allow_html=True)
m1, m2, m3, m4, m5 = st.columns(5)
with m1: st.markdown(f"<div class='card-metric' style='border: 1px solid #FF6F00;'><span>🌡️</span><small>Temp</small><h2>{sanitize(raw_data.get('temperature'))}°C</h2></div>", unsafe_allow_html=True)
with m2: st.markdown(f"<div class='card-metric' style='border: 1px solid #0091EA;'><span>💧</span><small>Humidity</small><h2>{sanitize(raw_data.get('humidity'))}%</h2></div>", unsafe_allow_html=True)
with m3: st.markdown(f"<div class='card-metric' style='border: 1px solid #00C853;'><span>🌬️</span><small>Wind</small><h2>{sanitize(raw_data.get('wind_speed'))}m/s</h2></div>", unsafe_allow_html=True)
with m4: st.markdown(f"<div class='card-metric' style='border: 1px solid #FFD600;'><span>☀️</span><small>Solar</small><h2>{sanitize(raw_data.get('solar_radiation'))}W/m²</h2></div>", unsafe_allow_html=True)
with m5: st.markdown(f"<div class='card-metric' style='border: 1px solid #AB47BC;'><span>🌧️</span><small>Rain</small><h2>{sanitize(raw_data.get('precipitation'))}mm</h2></div>", unsafe_allow_html=True)

st.markdown("<div class='footer'>NYERI FARMING INTELLIGENCE UNIT ❤️</div>", unsafe_allow_html=True)
st.sidebar.write(f"✅ Monitoring ID: {raw_data.get('id')}")

# ───── 7. REFRESH LOOP ─────
time.sleep(10)
st.rerun()
