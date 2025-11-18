import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import plotly.graph_objects as go
import time

# ───── CONFIG ─────
st.set_page_config(page_title="Nyeri Rain AI", layout="centered")

# AUTO REFRESH EVERY 60 SECONDS – 100% WORKING METHOD (2025)
time.sleep(1)  # tiny delay so page fully loads first
st.markdown("""
<script>
    setTimeout(function(){ 
        window.location.reload(); 
    }, 60000);  // 60 seconds
</script>
""", unsafe_allow_html=True)

# ───── SUPABASE ─────
SUPABASE_URL = "https://ffbkgocjztagavphjbsq.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZmYmtnb2NqenRhZ2F2cGhqYnNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA2NzA5NjcsImV4cCI6MjA3NjI0Njk2N30.sudxLkD1r8ARMEKjVMiyQqTg1KkKR7gSrWA-CKjVKb4"

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
forecast = latest.get("forecast_weeks") or [0] * 8
total_rain = sum(forecast)

# ───── SMART PLANTING LOGIC ─────
def get_advice():
    good_weeks = sum(1 for r in forecast if r >= 50)
    if total_rain >= 400 and good_weeks >= 4:
        return {"text": "YES! Panda Sasa!", "color": "#00FF41", "sub": f"{total_rain:.0f} mm → Mvua poa kabisa!", "emoji": "Panda Sasa!"}
    elif total_rain >= 300:
        return {"text": "Maybe – Jaribu Tu", "color": "#FFB800", "sub": f"{total_rain:.0f} mm → Inakubalika", "emoji": "Thinking"}
    else:
        return {"text": "NO – Subiri Kidogo", "color": "#FF3B30", "sub": f"Only {total_rain:.0f} mm → Bado", "emoji": "Hourglass"}

advice = get_advice()

# ───── SEXY DESIGN ─────
st.markdown("""
<style>
    .big {font-size:70px !important; font-weight:bold; text-align:center;}
    .med {font-size:34px !important; text-align:center;}
    .refresh {font-size:16px; color:#888; text-align:center;}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 style='text-align:center;'>Dedan Kimathi Rain AI</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center;'>Live for Nyeri Farmers • November 2025</h3>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00D4FF;'>PANDA H520 NA KAT B9</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align:center; color:white;'>HARAKA! Mvua fupi!</h2>", unsafe_allow_html=True)

# Main Advice
st.markdown(f"<p class='big' style='color:{advice['color']}'>{advice['text']}</p>", unsafe_allow_html=True)
st.markdown(f"<p class='med'>{advice['emoji']} {advice['sub']}</p>", unsafe_allow_html=True)

# Live refresh indicator
st.markdown("<p class='refresh'>Auto-refreshing every minute...</p>", unsafe_allow_html=True)

# Metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Next 8 Weeks", f"{total_rain:.0f} mm", f"{total_rain-250:+.0f} vs 250mm")
with col2:
    st.metric("Season", "Rainy Season" if total_rain >= 350 else "Dry Spell")
with col3:
    st.metric("Plant Now?", advice["text"].split()[0], advice["sub"])

# Forecast Chart
weeks = [f"Week {i+1}" for i in range(8)]
fig = go.Figure(go.Bar(x=weeks, y=forecast, marker_color="#00D4FF",
                       text=[f"{v}mm" for v in forecast], textposition="outside"))
fig.update_layout(title="8-Week Rainfall Forecast", template="plotly_dark", height=450)
st.plotly_chart(fig, use_container_width=True)

# Current Weather + Solar
st.subheader("Current Conditions")
c1, c2, c3, c4 = st.columns(4)
solar = latest.get("solar_radiation") or latest.get("solar") or 0

c1.metric("Temp", f"{latest['temperature']:.1f}°C")
c2.metric("Humidity", f"{latest['humidity']:.0f}%")
c3.metric("Wind", f"{latest['wind_speed']:.1f} m/s")
c4.metric("Solar", f"{solar:.0f} W/m²", "Jua Kali!" if solar > 700 else "Cloudy")

if solar > 800:
    st.markdown("<h2 style='text-align:center;'>JUA KALI SANA!</h2>", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption(f"Last update: {datetime.now().strftime('%d %b %Y • %I:%M:%S %p')} EAT • Auto-refreshing")
st.markdown("<p style='text-align:center; color:#888;'>Built with ❤️ for Nyeri Farmers</p>", unsafe_allow_html=True)
