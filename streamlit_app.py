import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import plotly.graph_objects as go
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ───── PAGE CONFIG ─────
st.set_page_config(page_title="Nyeri Rain AI", layout="centered")
time.sleep(1)
st.markdown("<script>setTimeout(() => window.location.reload(), 60000);</script>", unsafe_allow_html=True)

# ───── SUPABASE ─────
SUPABASE_URL = "https://ffbkgocjztagavphjbsq.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZmYmtnb2NqenRhZ2F2cGhqYnNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA2NzA5NjcsImV4cCI6MjA3NjI0Njk2N30.sudxLkD1r8ARMEKjVMiyQqTg1KkKR7gSrWA-CKjVKb4"
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# ───── EMAIL CONFIG ─────
SENDER_EMAIL = "gikonyowaigwe@gmail.com"
SENDER_PASSWORD = "fsox aavj llad gvvp"
RECEIVER_EMAILS = ["kinuthiajohnson941@gmail.com", "nganga.irvine19@students.dkut.ac.ke"]

def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = ", ".join(RECEIVER_EMAILS)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAILS, msg.as_string())
        server.quit()
    except:
        pass

# ───── FIXED: PROPER SUPABASE QUERY (NO MORE APIError) ─────
@st.cache_data(ttl=55, show_spinner="Fetching latest weather data...")
def get_data():
    try:
        # CORRECT WAY: use .order("timestamp", desc=True)
        response = supabase.table("weather_data")\
            .select("*")\
            .order("timestamp", desc=True)\
            .limit(1)\
            .execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error("Could not fetch data from Supabase. Check your connection.")
        return pd.DataFrame()

df = get_data()
if df.empty:
    st.error("No weather data available yet.")
    st.stop()

latest = df.iloc[0]
forecast = latest.get("forecast_weeks") or [0] * 8
total_rain = sum(forecast)

# ───── PLANTING LOGIC ─────
good_weeks = sum(1 for r in forecast if r >= 50)
if total_rain >= 400 and good_weeks >= 4:
    planting_advice = "YES! Panda Sasa!"
    advice_color = "#00FF3B"
elif total_rain >= 300:
    planting_advice = "Maybe – Jaribu Tu"
    advice_color = "#FFB800"
else:
    planting_advice = "NO – Subiri Kidogo"
    advice_color = "#FF3B30"

# ───── 100% FROM SUPABASE ─────
crop_suggestion = latest.get("crop_suggestions", "").strip()
main_headline = crop_suggestion.split("\n", 1)[0].strip() if crop_suggestion else "Waiting for today’s planting advice..."

# ───── EMAIL ON CHANGE OR WEEKLY (Monday) ─────
today = datetime.now().date()
if "last_advice" not in st.session_state:
    st.session_state.last_advice = None
    st.session_state.last_email_date = None

advice_changed = planting_advice != st.session_state.last_advice
send_weekly = today.weekday() == 0 and st.session_state.last_email_date != today

if advice_changed or send_weekly:
    body = f"""
NYERI RAIN AI UPDATE

{planting_advice}
Total rain (8 weeks): {total_rain:.0f} mm

{crop_suggestion or "No recommendation yet"}

Live Dashboard → https://your-app-name.streamlit.app
    """.strip()
    send_email(f"NYERI RAIN AI • {planting_advice}", body)
    st.session_state.last_advice = planting_advice
    if send_weekly:
        st.session_state.last_email_date = today

# ───── BEAUTIFUL DESIGN ─────
st.markdown("""
<style>
    .big {font-size:90px !important; font-weight:900; text-align:center; margin:20px 0;}
    .headline {font-size:50px !important; text-align:center; color:#00D4FF; margin:30px 0;}
    .detail {font-size:36px !important; text-align:center; color:#00FFA3; margin:25px 0; line-height:1.6;}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; color:#00D4FF;'>Dedan Kimathi Rain AI</h1>", unsafe_allow_html=True)
st.markdown(f"<h3 style='text-align:center; color:#00FFA3;'>Live for Nyeri Farmers • {datetime.now().strftime('%B %Y')}</h3>", unsafe_allow_html=True)

st.markdown(f"<div class='headline'>{main_headline.upper()}</div>", unsafe_allow_html=True)

if "YES" in planting_advice:
    st.markdown(f"<div class='big' style='color:#00FF3B;'>YES! Panda Sasa!</div>", unsafe_allow_html=True)
elif "NO" in planting_advice:
    st.markdown(f"<div class='big' style='color:#FF3B30;'>NO – Subiri Kidogo</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='big' style='color:{advice_color};'>{planting_advice}</div>", unsafe_allow_html=True)

st.markdown(f"<div style='font-size:42px; text-align:center; color:white;'>Rain {total_rain:.0f} mm in next 8 weeks</div>", unsafe_allow_html=True)

if crop_suggestion:
    st.markdown(f"<div class='detail'>{crop_suggestion}</div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Next 8 Weeks", f"{total_rain:.0f} mm", f"{total_rain-250:+.0f} vs target")
with col2:
    st.metric("Season", "Rainy Season" if total_rain >= 350 else "Dry Spell")
with col3:
    short = crop_suggestion[:45] + "..." if crop_suggestion and len(crop_suggestion)>45 else (crop_suggestion or "No advice")
    st.metric("Plant Now?", planting_advice.split("!")[0], short)

# Chart
weeks = [f"Week {i+1}" for i in range(8)]
fig = go.Figure(go.Bar(x=weeks, y=forecast, marker_color="#00D4FF", text=[f"{v}mm" for v in forecast], textposition="outside"))
fig.update_layout(title="8-Week Rainfall Forecast", template="plotly_dark", height=500)
st.plotly_chart(fig, use_container_width=True)

# Current Weather
st.markdown("### Current Weather Now")
c1, c2, c3, c4 = st.columns(4)
solar = latest.get("solar_radiation") or latest.get("solar") or 0
c1.metric("Temperature", f"{latest['temperature']:.1f}°C")
c2.metric("Humidity", f"{latest['humidity']:.0f}%")
c3.metric("Wind", f"{latest['wind_speed']:.1f} m/s")
c4.metric("Solar", f"{solar:.0f} W/m²", "Hot Sun" if solar > 700 else "Cloudy")

if solar > 800:
    st.markdown("<h2 style='text-align:center;'>Hot Sun JUA KALI SANA! Hot Sun</h2>", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption(f"Last update: {datetime.now().strftime('%d %B %Y • %I:%M %p')} EAT")
st.markdown("<p style='text-align:center; color:#888; font-size:18px;'>Built with love for Nyeri Farmers • DeKUT Weather AI</p>", unsafe_allow_html=True)
