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

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .hero-card { 
        padding: 30px; border-radius: 25px; text-align: center; margin-bottom: 20px; 
        border: 1px solid rgba(255, 255, 255, 0.1); background-color: #1A1A1A; color: white;
    }
    .card-metric { 
        padding: 15px; border-radius: 15px; text-align: center; 
        background: rgba(128, 128, 128, 0.05); border: 1px solid rgba(128, 128, 128, 0.2);
    }
    .card-metric span { font-size: 24px; display: block; margin-bottom: 5px; }
    .card-metric h2 { font-size: 20px; margin: 0; font-weight: 800; color: #00D4FF; }
    .card-metric small { color: #888; text-transform: uppercase; font-size: 10px; font-weight: 700; }
    .footer { text-align: center; padding: 20px; color: #888; font-size: 11px; }
    </style>
""", unsafe_allow_html=True)

# ───── 2. CONNECTIONS & EMAIL CONFIG ─────
SUPABASE_URL = "https://ffbkgocjztagavphjbsq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZmYmtnb2NqenRhZ2F2cGhqYnNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA2NzA5NjcsImV4cCI6MjA3NjI0Njk2N30.sudxLkD1r8ARMEKjVMiyQqTg1KkKR7gSrWA-CKjVKb4"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

SENDER_EMAIL = "gikonyowaigwe@gmail.com"
SENDER_PASSWORD = "fsox aavj llad gvvp" # Gmail App Password
RECEIVERS = ["kinuthiajohnson941@gmail.com", "nganga.irvine19@students.dkut.ac.ke", "gikonyo.joy21@students.dkut.ac.ke"]

def send_alert_email(label, advice, rain_total):
    try:
        msg = MIMEMultipart()
        msg["From"] = f"Nyeri Weather AI <{SENDER_EMAIL}>"
        msg["To"] = ", ".join(RECEIVERS)
        msg["Subject"] = f"⚠️ Weather Alert: {label}"
        body = f"📍 NYERI WEATHER AI - STATUS: {label}\nPredicted 8-Week Total: {rain_total:.2f}mm\n\nADVICE: {advice}"
        msg.attach(MIMEText(body, "plain"))
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except: return False

# ───── 3. DATA FETCHING ─────
def fetch_latest_data():
    try:
        res = supabase.table("weather_data").select("*").order("recorded_at", desc=True).limit(1).execute()
        return res.data[0] if res.data else None
    except: return None

raw_data = fetch_latest_data()

# ───── 4. SIDEBAR & TEST TOOLS ─────
with st.sidebar:
    st.header("🛠️ Admin Tools")
    if st.button("📧 Send Test Alert Now"):
        if send_alert_email("DEMO TEST", "Test advice from Streamlit", 0.0):
            st.success("Test Email Sent!")
        else:
            st.error("Failed to send email.")
    st.info("System will auto-email if the Season Level changes.")

# ───── 5. LOGIC & UI ─────
if not raw_data:
    st.warning("📡 Waiting for Station Data...")
    time.sleep(5); st.rerun()

advice = raw_data.get("crop_advice", "Monitoring...")
current_label = raw_data.get("season_label", "Normal")
total_rain = raw_data.get("total_8week_rain", 0)

# Email Trigger logic
if "last_notified" not in st.session_state:
    st.session_state.last_notified = current_label

if current_label != st.session_state.last_notified:
    send_alert_email(current_label, advice, total_rain)
    st.session_state.last_notified = current_label
    st.toast("📧 Season change detected. Email alerts dispatched!", icon="🚀")

# Graphs and Metrics
f_raw = raw_data.get("forecast_weeks", [0]*8)
forecast = f_raw if isinstance(f_raw, list) else json.loads(f_raw)
is_rainy = "RAIN" in advice.upper() or "MVUA" in advice.upper()
emoji, color = ("🌧️", "#00E676") if is_rainy else ("☀️", "#FFD600")

st.markdown(f"<h1 style='text-align: center; font-size: 42px; font-weight: 900; color: #00D4FF; margin-bottom: 0;'>🚀 NYERI RAIN AI</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #888; font-size: 12px;'>KIMATHI CAMPUS | LAST SYNC: {raw_data.get('recorded_at')}</p>", unsafe_allow_html=True)

st.markdown(f"""
    <div class="hero-card" style="border-top: 8px solid {color};">
        <span style="font-size: 50px;">{emoji}</span>
        <h2 style="font-size: 32px; font-weight: 900; margin: 10px 0;">{current_label}</h2>
        <p style="font-size: 18px; font-weight: 600; color: {color};">{advice.split(':')[-1] if ':' in advice else advice}</p>
    </div>
""", unsafe_allow_html=True)

c1, c2 = st.columns([2, 1])
with c1:
    fig = go.Figure(go.Bar(x=[f"Wk {i+1}" for i in range(8)], y=forecast, marker_color='#00D4FF'))
    fig.update_layout(title="<b>8-WEEK AI PREDICTION (MM)</b>", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300)
    st.plotly_chart(fig, use_container_width=True)
with c2:
    gauge = go.Figure(go.Indicator(mode="gauge+number", value=total_rain, title={'text': "<b>SEASON TOTAL</b>"}, gauge={'bar':{'color':color}, 'axis':{'range':[0,500]}}))
    gauge.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=300)
    st.plotly_chart(gauge, use_container_width=True)

m1, m2, m3, m4, m5 = st.columns(5)
m1.markdown(f"<div class='card-metric'><span>🌡️</span><small>Temp</small><h2>{raw_data.get('temperature')}°C</h2></div>", unsafe_allow_html=True)
m2.markdown(f"<div class='card-metric'><span>💧</span><small>Hum</small><h2>{raw_data.get('humidity')}%</h2></div>", unsafe_allow_html=True)
m3.markdown(f"<div class='card-metric'><span>🌬️</span><small>Wind</small><h2>{raw_data.get('wind')}m/s</h2></div>", unsafe_allow_html=True)
m4.markdown(f"<div class='card-metric'><span>☀️</span><small>Solar</small><h2>{raw_data.get('solar')}W</h2></div>", unsafe_allow_html=True)
m5.markdown(f"<div class='card-metric'><span>🌧️</span><small>Rain</small><h2>{raw_data.get('precip_api')}mm</h2></div>", unsafe_allow_html=True)

st.markdown("<div class='footer'>NYERI FARMING INTELLIGENCE UNIT ❤️</div>", unsafe_allow_html=True)
time.sleep(30); st.rerun()
