import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import plotly.graph_objects as go
import time

# ───── PAGE CONFIG ─────
st.set_page_config(page_title="Dedan Kimathi Rain AI", layout="centered")

# Auto-refresh every 60 seconds
st.markdown("<meta http-equiv='refresh' content='60'>", unsafe_allow_html=True)

# ───── SUPABASE ─────
SUPABASE_URL = "https://ffbkgocjztagavphjbsq.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZmYmtnb2NqenRhZ2F2cGhqYnNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA2NzA5NjcsImV4cCI6MjA3NjI0Njk2N30.sudxLkD1r8ARMEKjVMiyQqTg1KkKR7gSrWA-CKjVKb4"
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# ───── FETCH LATEST DATA ─────
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

# ───── PLANTING LOGIC (NO EMOJIS) ─────
good_weeks = sum(1 for r in forecast if r >= 50)
if total_rain >= 400 and good_weeks >= 4:
    planting_advice = "YES! Panda Sasa!"
    advice_color = "#00C853"
elif total_rain >= 300:
    planting_advice = "Maybe – Jaribu Tu"
    advice_color = "#FF9800"
else:
    planting_advice = "NO – Subiri Kidogo"
    advice_color = "#D32F2F"

# ───── 100% FROM SUPABASE (NO HARD-CODED TEXT) ─────
crop_suggestion = latest.get("crop_suggestions", "").strip()
main_headline = crop_suggestion.split("\n", 1)[0].strip() if crop_suggestion else "Waiting for today’s advice..."

# ───── CLEAN LIGHT THEME DESIGN (EXACTLY LIKE YOUR PHOTO) ─────
st.markdown("""
<style>
    .big-headline {font-size:  font-size: 52px; font-weight: bold; text-align: center; color: #00ACC1; margin: 30px 0 10px 0;}
    .rain-total {font-size: 64px; font-weight: bold; text-align: center; color: #212121; margin: 20px 0;}
    .delta {font-size: 24px; text-align: center; color: #00C853;}
    .advice {font-size: 80px; font-weight: bold; text-align: center; margin: 40px 0 20px 0;}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 style='text-align:center; color:#212121; margin-bottom:5px;'>Dedan Kimathi Rain AI</h1>", unsafe_allow_html=True)
st.markdown(f"<h3 style='text-align:center; color:#666;'>Live for Nyeri Farmers • {datetime.now().strftime('%B %Y')}</h3>", unsafe_allow_html=True)

# Main crop headline from Supabase
st.markdown(f"<div class='big-headline'>{main_headline.upper()}</div>", unsafe_allow_html=True)

# Rain total
st.markdown(f"<div class='rain-total'>{total_rain:.0f} mm</div>", unsafe_allow_html=True)
st.markdown(f"<div class='delta'>+{total_rain-250:.0f} vs 250mm target</div>", unsafe_allow_html=True)

# Season
st.markdown("<h2 style='text-align:center; color:#212121; margin:40px 0 10px 0;'>Rainy Season</h2>", unsafe_allow_html=True)

# Plant Now?
st.markdown(f"<div class='advice' style='color:{advice_color};'>{planting_advice.split('!')[0] if '!' in planting_advice else planting_advice}</div>", unsafe_allow_html=True)
if "YES" in planting_advice:
    st.markdown("<p style='text-align:center; font-size:28px; color:#00C853; margin-top:-20px;'>Panda Sasa!</p>", unsafe_allow_html=True)
elif "NO" in planting_advice:
    st.markdown("<p style='text-align:center; font-size:28px; color:#D32F2F; margin-top:-20px;'>Wait a little</p>", unsafe_allow_html=True)

# 8-Week Chart
weeks = [f"W{i+1}" for i in range(8)]
fig = go.Figure(data=[go.Bar(
    x=weeks,
    y=forecast,
    marker_color='#00ACC1',
    text=[f"{v}mm" for v in forecast],
    textposition='outside'
)])
fig.update_layout(
    title="Next 8 Weeks",
    template="simple_white",
    height=400,
    margin=dict(l=40, r=40, t=60, b=40),
    yaxis=dict(showgrid=False, range=[0, max(forecast)*1.3])
)
st.plotly_chart(fig, use_container_width=True)

# Current Weather
st.markdown("### Current Weather")
col1, col2, col3 = st.columns(3)
solar = latest.get("solar_radiation") or latest.get("solar") or 0

col1.metric("Temperature", f"{latest['temperature']:.1f}°C", "Temperature")
col2.metric("", f"{latest['humidity']:.0f}%", "Humidity")
col3.metric("", f"{latest['wind_speed']:.1f} m/s", "Wind")

st.metric("Solar", f"{solar:.0f} W/m²", "Sunny" if solar > 600 else "Cloudy")

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%d %B %Y • %I:%M %p')} EAT | Model: v5.1-nyeri-live")
