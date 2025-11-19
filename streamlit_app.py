import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import plotly.graph_objects as go
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ───── CONFIG ─────
st.set_page_config(page_title="Nyeri Rain AI", layout="centered")
st.markdown("<meta http-equiv='refresh' content='60'>", unsafe_allow_html=True)

SUPABASE_URL = "https://ffbkgocjztagavphjbsq.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInRlZiI6ImZmYmtnb2NqenRhZ2F2cGhqYnNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA2NzA5NjcsImV4cCI6MjA3NjI0Njk2N30.sudxLkD1r8ARMEKjVMiyQqTg1KkKR7gSrWA-CKjVKb4"
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

DASHBOARD_URL = "https://nyeri-rain-dashboard-6nvsflctxyimknz7sactb3.streamlit.app"

# ───── EMAIL CONFIG ─────
SENDER_EMAIL = "gikonyowaigwe@gmail.com"
SENDER_PASSWORD = "fsox aavj llad gvvp"
RECEIVERS = ["kinuthiajohnson941@gmail.com", "nganga.irvine19@students.dkut.ac.ke"]

def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = ", ".join(RECEIVERS)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVERS, msg.as_string())
        server.quit()
    except:
        pass

# ───── FETCH DATA ─────
@st.cache_data(ttl=55)
def get_data():
    try:
        res = supabase.table("weather_data").select("*").order("timestamp", desc=True).limit(1).execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

df = get_data()

# BEAUTIFUL "WAITING" MESSAGE — NO UGLY RED BAR!
if df.empty:
    st.markdown("""
    <div style='text-align:center; margin-top:100px;'>
        <h1 style='color:#00D4FF; font-size:56px;'>Nyeri Rain AI</h1>
        <h3 style='color:#AAAAAA;'>Live for Nyeri Farmers</h3>
        <div style='margin:80px 0;'>
            <h2 style='color:#00FF88; font-size:48px;'>Waiting for Sensor...</h2>
            <p style='color:#888; font-size:28px;'>Data will appear automatically when the weather station sends the next update</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()  # Stops execution but looks beautiful

latest = df.iloc[0]
forecast = latest.get("forecast_weeks") or [0]*8
total_rain = sum(forecast)

# ───── PLANTING ADVICE ─────
good_weeks = sum(1 for r in forecast if r >= 50)
if total_rain >= 400 and good_weeks >= 4:
    answer = "YES! Panda Sasa!"
    color = "#00FF41"
    subtext = f"Perfect rains ahead → {total_rain:.0f} mm"
elif total_rain >= 300:
    answer = "Maybe – Jaribu Tu"
    color = "#FFB800"
    subtext = f"{total_rain:.0f} mm – okay for some crops"
else:
    answer = "NO – Subiri Kidogo"
    color = "#FF3B30"
    subtext = f"Only {total_rain:.0f} mm – mvua bado kidogo"

# FROM SUPABASE
crop_full = str(latest.get("crop_suggestions", "No crop recommendation yet")).strip()
main_crop_line = crop_full.split("\n", 1)[0].strip() if "\n" in crop_full else crop_full

# ───── EMAIL (FIXED — NEVER BLANK) ─────
today = datetime.now().date()
if "last_answer" not in st.session_state:
    st.session_state.last_answer = None
    st.session_state.last_email_date = None

changed = answer != st.session_state.last_answer
monday = today.weekday() == 0

if changed or (monday and st.session_state.last_email_date != today):
    email_body = f"""
NYERI RAIN AI UPDATE • {datetime.now().strftime('%d %b %Y')}

{answer}

{subtext}

Today’s recommendation:
{crop_full}

Live Dashboard → {DASHBOARD_URL}

Sent: {datetime.now().strftime('%I:%M %p')} EAT
Built with love for Nyeri Farmers • DeKUT Weather AI
    """.strip()

    send_email(f"NYERI RAIN AI • {answer}", email_body)
    st.session_state.last_answer = answer
    if monday:
        st.session_state.last_email_date = today

# ───── GORGEOUS DASHBOARD (your favorite style) ─────
st.markdown("""
<style>
    .big-font   {font-size:72px !important; font-weight:900; text-align:center; margin:10px 0;}
    .medium-font {font-size:34px !important; text-align:center; margin:15px 0 50px 0;}
    .subtitle    {font-size:28px !important; text-align:center; color:#AAAAAA; margin-bottom:40px;}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center;'>Dedan Kimathi Rain AI</h1>", unsafe_allow_html=True)
st.markdown(f"<h3 class='subtitle'>Live for Nyeri Farmers • {datetime.now().strftime('%B %Y')}</h3>", unsafe_allow_html=True)
st.markdown(f"<h1 style='text-align:center; color:#00D4FF;'>{main_crop_line.upper()}</h1>", unsafe_allow_html=True)

st.markdown(f"<p class='big-font' style='color:{color}'>{answer}</p>", unsafe_allow_html=True)
st.markdown(f"<p class='medium-font' style='color:white;'>{subtext}</p>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Next 8 Weeks", f"{total_rain:.0f} mm", delta=f"{total_rain-250:+.0f} vs 250mm")
with col2:
    st.metric("Season", "Rainy Season" if total_rain >= 350 else "Dry Season")
with col3:
    st.metric("Plant Now?", answer.split("!")[0], delta=subtext)

weeks = [f"Week {i+1}" for i in range(8)]
fig = go.Figure(go.Bar(x=weeks, y=forecast, marker_color="#00D4FF",
                       text=[f"{v}mm" for v in forecast], textposition="outside"))
fig.update_layout(title="8-Week Rainfall Forecast", template="plotly_dark",
                  height=460, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                  font=dict(color="white"))
st.plotly_chart(fig, use_container_width=True)

st.subheader("Current Conditions in Nyeri")
c1, c2, c3, c4 = st.columns(4)
solar = latest.get('solar_radiation') or latest.get('solar') or 0
c1.metric("Temperature", f"{latest['temperature']:.1f}°C")
c2.metric("Humidity", f"{latest['humidity']:.0f}%")
c3.metric("Wind Speed", f"{latest['wind_speed']:.1f} m/s")
c4.metric("Solar Radiation", f"{solar:.0f} W/m²", "Sunny!" if solar > 600 else "Cloudy")

if solar > 800:
    st.markdown("<h2 style='text-align:center; color:#FFD700;'>JUA KALI SANA!</h2>", unsafe_allow_html=True)
elif solar > 400:
    st.markdown("<h3 style='text-align:center; color:#FFEB3B;'>Jua Poa</h3>", unsafe_allow_html=True)

st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%d %b %Y • %I:%M %p')} • Powered by Dedan Kimathi University Weather Station")
st.markdown("<p style='text-align:center; color:#888;'>Built with love for Nyeri Farmers</p>", unsafe_allow_html=True)
