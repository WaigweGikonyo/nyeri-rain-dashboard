import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ───── 1. PAGE CONFIG (Adaptable Theme) ─────
st.set_page_config(page_title="Nyeri Rain AI", layout="wide", page_icon="🌱")

# ───── 2. CONNECTIONS ─────
SUPABASE_URL = "https://ffbkgocjztagavphjbsq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZmYmtnb2NqenRhZ2F2cGhqYnNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA2NzA5NjcsImV4cCI6MjA3NjI0Njk2N30.sudxLkD1r8ARMEKjVMiyQqTg1KkKR7gSrWA-CKjVKb4" 
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Email Config
SENDER_EMAIL = "gikonyowaigwe@gmail.com"
SENDER_PASSWORD = "fsox aavj llad gvvp"
RECEIVERS = ["kinuthiajohnson941@gmail.com", "nganga.irvine19@students.dkut.ac.ke"]

# ───── 3. FUNCTIONS ─────
def send_alert_email(status, rain_total, advice):
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = ", ".join(RECEIVERS)
        msg["Subject"] = f"🌱 NYERI RAIN AI: {status}"
        
        body = f"""
        NYERI RAIN AI UPDATE
        ------------------------------
        Status: {status}
        8-Week Total: {rain_total:.1f} mm
        
        Recommendation:
        {advice}
        
        Check Live Dashboard: https://nyeri-rain-dashboard.streamlit.app
        """
        msg.attach(MIMEText(body, "plain"))
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        st.sidebar.error(f"Email failed: {e}")

@st.cache_data(ttl=60)
def fetch_data():
    res = supabase.table("weather_data").select("*").order("timestamp", desc=True).limit(1).execute()
    return pd.DataFrame(res.data)

# ───── 4. DATA PROCESSING ─────
df = fetch_data()

if df.empty:
    st.info("🛰️ Connecting to DeKUT Weather Station... Please wait.")
    st.stop()

latest = df.iloc[0]
forecast = latest.get("forecast_weeks") or [0.0]*8
total_rain = sum(forecast)
rainy_weeks = sum(1 for x in forecast if x > 30)

# ───── 5. DECISION ENGINE ─────
if total_rain > 350 and rainy_weeks >= 4:
    decision, color = "YES! PANDA SASA", "#28a745" # Green
    advice = "Consistent rains expected. Ideal for Maize (H6213) and Potatoes."
elif total_rain > 200:
    decision, color = "JARIBU TU (CAUTION)", "#ffc107" # Amber
    advice = "Rains are erratic. Use fast-maturing seeds (e.g., Beans/Shangi)."
else:
    decision, color = "HAPANA (SUBIRI)", "#dc3545" # Red
    advice = "Dry spell detected. Irrigation required for Tetu crops."

# ───── 6. EMAIL LOGIC (State Tracking) ─────
if "last_status" not in st.session_state:
    st.session_state.last_status = None

if st.session_state.last_status != decision:
    send_alert_email(decision, total_rain, advice)
    st.session_state.last_status = decision

# ───── 7. UI LAYOUT (Adaptable Colors) ─────
st.title("🚜 Nyeri Rain AI")
st.write(f"**Last Sync:** {latest['timestamp']}")

# Summary Card
st.markdown(f"""
    <div style="background-color: {color}; padding: 20px; border-radius: 10px; color: white; text-align: center;">
        <h1 style="margin:0;">{decision}</h1>
        <p style="font-size: 1.2rem;">{advice}</p>
    </div>
""", unsafe_allow_html=True)

st.write("---")

# Metrics
c1, c2, c3 = st.columns(3)
c1.metric("8-Week Forecast", f"{total_rain:.1f} mm")
c2.metric("Rainy Week Count", f"{rainy_weeks} weeks")
c3.metric("Station Temp", f"{latest['temperature']}°C")

# Visuals (Using 'None' for template lets it adapt to Phone settings)
fig = go.Figure(data=[go.Bar(x=[f"Wk {i+1}" for i in range(8)], y=forecast, marker_color='#007bff')])
fig.update_layout(
    title="Rainfall Pulse",
    template=None, 
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
)
st.plotly_chart(fig, use_container_width=True)

# Sensor Grid
st.subheader("Micro-Climate Data")
colA, colB, colC = st.columns(3)
colA.metric("Humidity", f"{latest['humidity']}%")
colB.metric("Wind Speed", f"{latest.get('wind_speed', 0)} m/s")
colC.metric("Solar Radiation", f"{latest.get('solar_radiation', 0)} W/m²")
