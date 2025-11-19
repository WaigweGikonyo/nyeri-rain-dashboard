import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import plotly.graph_objects as go

# ───── PAGE CONFIG ─────
st.set_page_config(page_title="Dedan Kimathi Rain AI", layout="centered")

# Auto-refresh every minute
st.markdown('<meta http-equiv="refresh" content="60">', unsafe_allow_html=True)

# ───── SUPABASE ─────
supabase = create_client(
    "https://ffbkgocjztagavphjbsq.supabase.co",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZmYmtnb2NqenRhZ2F2cGhqYnNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA2NzA5NjcsImV4cCI6MjA3NjI0Njk2N30.sudxLkD1r8ARMEKjVMiyQqTg1KkKR7gSrWA-CKjVKb4"
)

@st.cache_data(ttl=55)
def get_data():
    try:
        res = supabase.table("weather_data").select("*").order("timestamp", desc=True).limit(1).execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

df = get_data()
if df.empty:
    st.error("No data yet – waiting for sensor...")
    st.stop()

latest = df.iloc[0]
forecast = latest.get("forecast_weeks") or [0]*8
total_rain = sum(forecast)

# Planting Logic
good_weeks = sum(1 for r in forecast if r >= 50)
if total_rain >= 400 and good_weeks >= 4:
    decision = "YES"
    decision_color = "#00C853"
    subtext = "Panda Sasa!"
elif total_rain >= 300:
    decision = "MAYBE"
    decision_color = "#FF9800"
    subtext = "Jaribu Tu"
else:
    decision = "NO"
    decision_color = "#D32F2F"
    subtext = "Subiri Kidogo"

# 100% from Supabase
crop_suggestion = latest.get("crop_suggestions", "").strip()
main_headline = crop_suggestion.split("\n", 1)[0].strip() if crop_suggestion else "Waiting for today’s advice..."

# ───── ABSOLUTELY GORGEOUS & PRACTICAL DESIGN ─────
st.markdown("""
<style>
    .title     {font-size: 52px !important; font-weight: 800; text-align: center; color: #1a1a1a; margin: 10px 0 0 0;}
    .subtitle  {font-size: 28px !important; text-align: center; color: #333333; margin: 0 0 50px 0;}
    .headline  {font-size: 58px !important; font-weight: 900; text-align: center; color: #00ACC1; margin: 30px 0 15px 0; line-height: 1.2;}
    .rain      {font-size: 96px !important; font-weight: 900; text-align: center; color: #000000; margin: 20px 0 5px 0;}
    .delta     {font-size: 34px !important; text-align: center; color: #00C853; margin: 0 0 50px 0;}
    .decision  {font-size: 140px !important; font-weight: 900; text-align: center; margin: 40px 0 10px 0; line-height: 1;}
    .subtext   {font-size: 42px !important; font-weight: bold; text-align: center; margin: -10px 0 60px 0;}
    .chart     {margin: 40px 0;}
    .weather   {font-size: 32px !important; margin: 20px 0 10px 0;}
    .footer    {text-align: center; color: #444444; font-size: 20px; margin-top: 60px;}
    .stMetric > div {font-size: 28px !important;}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="title">Dedan Kimathi Rain AI</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subtitle">Live for Nyeri Farmers • {datetime.now().strftime("%B %Y")}</div>', unsafe_allow_html=True)

# Main Supabase headline
st.markdown(f'<div class="headline">{main_headline.upper()}</div>', unsafe_allow_html=True)

# Total Rain
st.markdown(f'<div class="rain">{total_rain:.0f} mm</div>', unsafe_allow_html=True)
st.markdown(f'<div class="delta">+{total_rain-250:.0f} vs 250mm target</div>', unsafe_allow_html=True)

# Decision
st.markdown(f'<div class="decision" style="color:{decision_color};">{decision}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subtext" style="color:{decision_color};">{subtext}</div>', unsafe_allow_html=True)

# Beautiful 8-week chart
weeks = [f"W{i+1}" for i in range(8)]
fig = go.Figure(go.Bar(
    x=weeks,
    y=forecast,
    marker_color="#00ACC1",
    text=[f"{v}mm" for v in forecast],
    textposition="outside",
    textfont=dict(size=18, color="#000000")
))
fig.update_layout(
    title="Next 8 Weeks",
    title_font=dict(size=28, color="#000000"),
    template="simple_white",
    height=460,
    margin=dict(l=30, r=30, t=80, b=30),
    yaxis=dict(visible=False, range=[0, max(forecast)*1.35 if forecast else 100])
)
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# Current Weather – big & clear
st.markdown('<h2 class="weather">Current Weather</h2>', unsafe_allow_html=True)
solar = latest.get("solar_radiation") or latest.get("solar") or 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Temperature", f"{latest['temperature']:.1f}°C")
with col2:
    st.metric("Humidity", f"{latest['humidity']:.0f}%")
with col3:
    st.metric("Wind", f"{latest['wind_speed']:.1f} m/s")
with col4:
    st.metric("Solar", f"{solar:.0f} W/m²", "Sunny" if solar > 600 else "Cloudy")

# Footer
st.markdown("---")
st.markdown(f'<div class="footer">Last updated: {datetime.now().strftime("%d %B %Y • %I:%M %p")} EAT<br>Model: v5.1-nyeri-live</div>', unsafe_allow_html=True)
