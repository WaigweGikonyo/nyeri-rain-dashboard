import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta
import plotly.graph_objects as go
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ───── CONFIG & AUTO REFRESH ─────
st.set_page_config(page_title="Nyeri Rain AI", layout="centered")
time.sleep(1)
st.markdown("<script>setTimeout(() => window.location.reload(), 60000);</script>", unsafe_allow_html=True)

# ───── SUPABASE ─────
SUPABASE_URL = "https://ffbkgocjztagavphjbsq.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZmYmtnb2NqenRhZ2F2cGhqYnNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA2NzA5NjcsImV4cCI6MjA3NjI0Njk2N30.sudxLkD1r8ARMEKjVMiyQqTg1KkKR7gSrWA-CKjVKb4"
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# ───── EMAIL CONFIG (CHANGE ONLY THESE) ─────
SENDER_EMAIL = "gikonyowaigwe@gmail.com"
SENDER_PASSWORD = "fsox aavj llad gvvp"  # your 16-digit app password
RECEIVER_EMAILS = ["kinuthiajohnson941@gmail.com", "nganga.irvine19@students.dkut.ac.ke"]

def send_email(subject, body):
    if "gikonyo" not in SENDER_EMAIL: return  # safety
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = ", ".join(RECEIVER_EMAILS)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAILS, msg.as_string())
        server.quit()
    except:
        pass  # silent fail in production

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

# ───── SMART ADVICE ─────
good_weeks = sum(1 for r in forecast if r >= 50)
if total_rain >= 400 and good_weeks >= 4:
    planting_advice = "YES! Panda Sasa!"
    advice_color = "#00FF41"
    emoji = "Tractor Tractor"
elif total_rain >= 300:
    planting_advice = "Maybe – Jaribu Tu"
    advice_color = "#FFB800"
    emoji = "Thinking"
else:
    planting_advice = "NO – Subiri Kidogo"
    advice_color = "#FF3B30"
    emoji = "Hourglass"

# ───── 100% FROM SUPABASE (NO HARD-CODED TEXT) ─────
crop_suggestion = latest.get("crop_suggestions", "").strip()
main_headline = crop_suggestion.split("\n", 1)[0].strip() if crop_suggestion else "Waiting for today’s advice..."

# ───── WEEKLY EMAIL + CHANGE ALERT ─────
today = datetime.now().date()
is_monday = today.weekday() == 0  # 0 = Monday

# Send weekly summary every Monday + when advice changes
if "last_advice" not in st.session_state:
    st.session_state.last_advice = None
    st.session_state.last_email_date = None

advice_changed = planting_advice != st.session_state.last_advice
should_send_weekly = is_monday and st.session_state.last_email_date != today

if advice_changed or should_send_weekly:
    email_body = f"""
NYERI RAIN AI {'WEEKLY' if should_send_weekly else 'URGENT'} UPDATE

{planting_advice}
Total rain next 8 weeks: {total_rain:.0f} mm

Recommendation:
{crop_suggestion or "No advice yet"}

Live Dashboard → https://your-app-name.streamlit.app
{'' if advice_changed else 'Weekly summary – every Monday'}

Sent: {datetime.now().strftime('%A, %d %B %Y at %I:%M %p')} EAT
    """.strip()

    send_email(f"NYERI RAIN AI • {planting_advice}", email_body)
    
    st.session_state.last_advice = planting_advice
    if should_send_weekly:
        st.session_state.last_email_date = today

# ───── BEAUTIFUL DESIGN WITH EMOJIS ─────
st.markdown("""
<style>
    .big {font-size:82px !important; font-weight:bold; text-align:center; margin:15px 0;}
    .med {font-size:40px !important; text-align:center; margin:10px 0;}
    .crop {font-size:34px !important; text-align:center; margin:35px 0 20px 0; line-height:1.6; color:#00FFA3;}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("# Dedan Kimathi Rain AI")
st.markdown(f"### Live for Nyeri Farmers • {datetime.now().strftime('%B %Y')}")

# 100% FROM SUPABASE – BIG & CLEAN
st.markdown(f"<h1 style='text-align:center; color:#00D4FF; margin:40px 0 20px 0;'>{main_headline.upper()}</h1>", unsafe_allow_html=True)

# Main Decision
st.markdown(f"<p class='big' style='color:{advice_color}'>{emoji}  {planting_advice}</p>", unsafe_allow_html=True)
st.markdown(f"<p class='med'>Rain {total_rain:.0f} mm in next 8 weeks</p>", unsafe_allow_html=True)

# Full crop advice
if crop_suggestion:
    st.markdown(f"<div class='crop'>{crop_suggestion}</div>", unsafe_allow_html=True)

# Metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Next 8 Weeks", f"{total_rain:.0f} mm", f"{total_rain-250:+.0f} vs 250mm")
with col2:
    st.metric("Season", "Rainy Season" if total_rain >= 350 else "Dry Spell")
with col3:
    short = crop_suggestion[:50] + "..." if crop_suggestion and len(crop_suggestion)>50 else (crop_suggestion or "Waiting...")
    st.metric("Plant Now?", planting_advice.split()[0], short)

# Chart
weeks = [f"Week {i+1}" for i in range(8)]
fig = go.Figure(go.Bar(x=weeks, y=forecast, marker_color="#00D4FF", text=[f"{v}mm" for v in forecast], textposition="outside"))
fig.update_layout(title="8-Week Rainfall Forecast", template="plotly_dark", height=450)
st.plotly_chart(fig, use_container_width=True)

# Weather
st.subheader("Current Weather Now")
c1, c2, c3, c4 = st.columns(4)
solar = latest.get("solar_radiation") or latest.get("solar") or 0
c1.metric("Temperature", f"{latest['temperature']:.1f}°C")
c2.metric("Humidity", f"{latest['humidity']:.0f}%")
c3.metric("Wind", f"{latest['wind_speed']:.1f} m/s")
c4.metric("Solar", f"{solar:.0f} W/m²", "Hot Sun" if solar > 700 else "Cloudy")
if solar > 800:
    st.markdown("### Hot Sun JUA KALI SANA! Hot Sun")

# Footer
st.markdown("---")
st.caption(f"Last update: {datetime.now().strftime('%d %b %Y • %I:%M %p')} EAT • Auto-refreshing")
st.markdown("<p style='text-align:center; color:#888; margin-top:20px;'>Built with love for Nyeri Farmers • DeKUT Weather AI</p>", unsafe_allow_html=True)
