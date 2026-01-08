import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client
from datetime import datetime

# ───── 1. PAGE SETUP ─────
st.set_page_config(page_title="Nyeri Rain AI", layout="wide", page_icon="🌱")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .status-card { padding: 40px; border-radius: 24px; text-align: center; margin-bottom: 30px; border: 1px solid rgba(128,128,128,0.2); }
    .metric-card { background: rgba(0, 150, 255, 0.05); padding: 25px; border-radius: 20px; border: 1px solid rgba(0, 150, 255, 0.1); text-align: center; }
    .footer { text-align: center; padding: 60px 0 30px 0; color: #999; font-weight: 600; font-size: 13px; }
    </style>
""", unsafe_allow_html=True)

# ───── 2. DATA FETCH ─────
SUPABASE_URL = "https://ffbkgocjztagavphjbsq.supabase.co"
SUPABASE_KEY = "YOUR_ANON_KEY" 
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
    st.info("🛰️ Initializing Satellite Link... Please refresh.")
    st.stop()

latest = df.iloc[0]

# --- Extract & Clean Data ---
ai_label = latest.get("season_label", "Analyzing...")
ai_advice = latest.get("crop_suggestions", "Gathering data...")
raw_forecast = latest.get("forecast_weeks") or [0.0]*8
# Ensure forecast is a list of floats (Fixes potential data type errors)
forecast = [float(x) for x in raw_forecast]
total_rain = float(latest.get("total_8week_rain", sum(forecast)))

# Theme Color
theme_color = "#00E676" if "Rainy" in ai_label else "#FFD740" if "Transition" in ai_label or "MPITO" in ai_advice else "#FF5252"

# ───── 3. VISUAL DISPLAY ─────

st.markdown(f"<p style='text-align:center; color:#888;'>STATION SYNC: {latest['timestamp']}</p>", unsafe_allow_html=True)

st.markdown(f"""
    <div class="status-card" style="border-top: 10px solid {theme_color}; background-color: {theme_color}10;">
        <h1 style="font-size: 50px; font-weight: 900; margin:0;">{ai_label.upper()}</h1>
        <p style="font-size: 22px; color: {theme_color}; font-weight: 700; margin-top:10px;">{ai_advice}</p>
    </div>
""", unsafe_allow_html=True)

col_chart, col_gauge = st.columns([2, 1])

with col_chart:
    # FIXED PLOTLY CHART
    fig_pulse = go.Figure()
    fig_pulse.add_trace(go.Scatter(
        x=[f"Week {i+1}" for i in range(8)], 
        y=forecast, 
        fill='tozeroy', 
        line=dict(color='#0091EA', width=4),
        mode='lines+markers',
        marker=dict(
            size=12, 
            line=dict(color="white", width=2), # FIXED: Changed bordercolor to line
            color='#0091EA'
        )
    ))
    fig_pulse.update_layout(
        title="<b>8-WEEK PRECIPITATION PULSE</b>",
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(gridcolor='rgba(128,128,128,0.1)', title="Rainfall (mm)"),
        xaxis=dict(gridcolor='rgba(128,128,128,0.1)')
    )
    st.plotly_chart(fig_pulse, use_container_width=True)

with col_gauge:
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = total_rain,
        title = {'text': "Total Predicted (mm)", 'font': {'size': 18}},
        number = {'font': {'color': theme_color}},
        gauge = {
            'axis': {'range': [0, 600]},
            'bar': {'color': theme_color},
            'bgcolor': "rgba(128,128,128,0.1)",
        }
    ))
    fig_gauge.update_layout(height=380, paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_gauge, use_container_width=True)

# Sensor Metrics
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

st.markdown("<div class='footer'>MADE FOR NYERI FARMERS WITH LOVE ❤️</div>", unsafe_allow_html=True)
