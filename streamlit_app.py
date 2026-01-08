import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client
from datetime import datetime

# ───── 1. PAGE SETUP & ADAPTIVE STYLING ─────
st.set_page_config(page_title="Nyeri Rain AI", layout="wide", page_icon="🌱")

# High-end styling for Glassmorphism and clean typography
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .status-card {
        padding: 40px;
        border-radius: 24px;
        text-align: center;
        margin-bottom: 30px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        box-shadow: 0 15px 35px rgba(0,0,0,0.05);
    }
    .metric-card {
        background: rgba(0, 150, 255, 0.05);
        padding: 25px;
        border-radius: 20px;
        border: 1px solid rgba(0, 150, 255, 0.1);
        text-align: center;
    }
    .footer {
        text-align: center;
        padding: 60px 0 30px 0;
        color: #999;
        font-weight: 600;
        letter-spacing: 1.5px;
        font-size: 13px;
    }
    </style>
""", unsafe_allow_html=True)

# ───── 2. SECURE DATA FETCH ─────
SUPABASE_URL = "https://ffbkgocjztagavphjbsq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZmYmtnb2NqenRhZ2F2cGhqYnNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA2NzA5NjcsImV4cCI6MjA3NjI0Njk2N30.sudxLkD1r8ARMEKjVMiyQqTg1KkKR7gSrWA-CKjVKb4" # Use your project's Anon Key
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=30)
def get_latest_sync():
    try:
        res = supabase.table("weather_data").select("*").order("timestamp", desc=True).limit(1).execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

df = get_latest_sync()

if df.empty:
    st.info("🛰️ Initializing Satellite Link... Please refresh in a moment.")
    st.stop()

latest = df.iloc[0]

# --- Extract Data from Supabase ---
# These names MUST match your Supabase column names exactly
ai_label = latest.get("season_label", "Analyzing...")
ai_advice = latest.get("crop_suggestions", "Gathering soil data...")
forecast = latest.get("forecast_weeks") or [0.0]*8
total_rain = latest.get("total_8week_rain", sum(forecast))
rain_count = latest.get("rainy_weeks_count", 0)

# Dynamic Color Scheme based on AI Label
if "Rainy" in ai_label or "Panda" in ai_advice:
    theme_color = "#00E676" # Vibrant Green
elif "Dry" in ai_label:
    theme_color = "#FF5252" # Soft Red
else:
    theme_color = "#FFD740" # Amber

# ───── 3. VISUAL LAYOUT ─────

# Header Sync Info
st.markdown(f"<p style='text-align:center; color:#888; margin-bottom:0;'>DEKUT WEATHER STATION • {latest['timestamp']}</p>", unsafe_allow_html=True)

# Main Intelligence Card
st.markdown(f"""
    <div class="status-card" style="border-top: 10px solid {theme_color}; background-color: {theme_color}05;">
        <h1 style="font-size: 64px; font-weight: 900; margin:0; letter-spacing:-1px;">{ai_label.upper()}</h1>
        <p style="font-size: 26px; color: {theme_color}; font-weight: 700; margin-top:10px;">{ai_advice}</p>
    </div>
""", unsafe_allow_html=True)

# Graphics row: Forecast Area Chart & Consistency Gauge
col_chart, col_gauge = st.columns([2, 1])

with col_chart:
    # Beautiful Smooth Area Chart
    fig_pulse = go.Figure()
    fig_pulse.add_trace(go.Scatter(
        x=[f"Week {i+1}" for i in range(8)], 
        y=forecast, 
        fill='tozeroy', 
        line=dict(color='#0091EA', width=4),
        mode='lines+markers',
        marker=dict(size=10, bordercolor="white", borderwidth=2)
    ))
    fig_pulse.update_layout(
        title="<b>8-WEEK PRECIPITATION PULSE</b>",
        template=None, # Adaptable to phone settings
        margin=dict(l=10, r=10, t=50, b=10),
        height=420,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(gridcolor='rgba(128,128,128,0.1)', title="Rainfall (mm)")
    )
    st.plotly_chart(fig_pulse, use_container_width=True)

with col_gauge:
    # Volume Gauge
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = total_rain,
        title = {'text': "Total Predicted Rain", 'font': {'size': 18, 'weight': 'bold'}},
        number = {'suffix': "mm", 'font': {'color': theme_color}},
        gauge = {
            'axis': {'range': [0, 600]},
            'bar': {'color': theme_color},
            'bgcolor': "rgba(128,128,128,0.1)",
            'steps': [
                {'range': [0, 200], 'color': "rgba(255,0,0,0.05)"},
                {'range': [200, 400], 'color': "rgba(255,255,0,0.05)"},
                {'range': [400, 600], 'color': "rgba(0,255,0,0.05)"}
            ]
        }
    ))
    fig_gauge.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=80))
    st.plotly_chart(fig_gauge, use_container_width=True)

# Live Sensor Metrics (Glass Cards)
st.markdown("### 📡 Live Sensor Network")
m1, m2, m3, m4 = st.columns(4)

metrics = [
    ("Temperature", f"{latest['temperature']}°C", "🌡️"),
    ("Humidity", f"{latest['humidity']}%", "💧"),
    ("Wind Speed", f"{latest.get('wind_speed', 0)} m/s", "🌬️"),
    ("Solar Index", f"{latest.get('solar_radiation', 0)} W/m²", "☀️")
]

for col, (label, val, icon) in zip([m1, m2, m3, m4], metrics):
    col.markdown(f"""
        <div class="metric-card">
            <span style="font-size:24px;">{icon}</span><br>
            <small style="color:#888; font-weight:700;">{label.upper()}</small><br>
            <h2 style="margin:0; font-weight:900;">{val}</h2>
        </div>
    """, unsafe_allow_html=True)

# ───── 4. THE SIGNATURE ─────
st.markdown("<div class='footer'>MADE FOR NYERI FARMERS WITH LOVE ❤️</div>", unsafe_allow_html=True)
