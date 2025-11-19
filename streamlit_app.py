import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import plotly.graph_objects as go
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ───── CONFIG & AUTO REFRESH ─────
st.set_page_config(page_title="Nyeri Rain AI", layout="centered")
time.sleep(1)
st.markdown("<script>setTimeout(() => window.location.reload(), 60000);</script>", unsafe_allow_html=True)

# ───── SUPABASE CONNECTION ─────
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])

# ───── FETCH LATEST DATA ─────
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
good_weeks = sum(1 for r in forecast if r >= 50)
if total_rain >= 400 and good_weeks >= 4:
    planting_advice = "YES! Panda Sasa!"
    advice_color = "#00FF41"
    emoji_main = "Panda Sasa! Panda Sasa!"
elif total_rain >= 300:
    planting_advice = "Maybe – Jaribu Tu"
    advice_color = "#FFB800"
    emoji_main = "Thinking"
else:
    planting_advice = "NO – Subiri Kidogo"
    advice_color = "#FF3B30"
    emoji_main = "Hourglass"

# ───── CROP SUGGESTION FROM SUPABASE ─────
crop_suggestion = latest.get("crop_suggestions", "Panda H520 na KAT B9 sasa hivi!").strip()
main_headline = crop_suggestion.split("\n")[0].strip() or "PANDA H520 NA KAT B9"

# ───── EMAIL ALERT WHEN ADVICE CHANGES ─────
if "last_advice" not in st.session_state:
    st.session_state.last_advice = None

if planting_advice != st.session_state.last_advice:
    body = f"""
NYERI RAIN AI – NEW UPDATE! 

{planting_advice}
Expected rain (next 8 weeks): {total_rain:.0f} mm

{crop_suggestion}

Live dashboard → {st.secrets['APP_URL']}
    """.strip()

    msg = MIMEMultipart()
    msg["From"] = st.secrets["sender_email"]
    msg["To"] = st.secrets["receiver_email"]
    msg["Subject"] = f"NYERI RAIN ALERT • {planting_advice}"

    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(st.secrets["sender_email"], st.secrets["sender_password"])
        server.sendmail(st.secrets["sender_email"], st.secrets["receiver_email"], msg.as_string())
        server.quit()
    except:
        pass
    st.session_state.last_advice = planting_advice

# ───── BEAUTIFUL EMOJI-RICH DESIGN ─────
st.markdown("""
<style>
    .big {font-size:82px !important; font-weight:bold; text-align:center; margin:20px 0;}
    .med {font-size:40px !important; text-align:center; margin:15px 0;}
    .crop {font-size:34px !important; text-align:center; margin:30px 0; line-height:1.6; color:#00FFA3;}
</style>
""", unsafe_allow_html=True)

# Header with emojis
current_month = datetime.now().strftime("%B %Y")
st.markdown("<h1 style='text-align:center; margin-bottom:0;'>Dedan Kimathi Rain AI</h1>", unsafe_allow_html=True)
st.markdown(f"<h3 style='text-align:center; margin:8px 0 40px 0; color:#00D4FF;'>Live for Nyeri Farmers • {current_month}</h3>", unsafe_allow_html=True)

# Dynamic headline from Supabase
st.markdown(f"<h1 style='text-align:center; color:#00D4FF; margin:30px 0;'>{main_headline.upper()}</h1>", unsafe_allow_html=True)

# Main YES/NO with big emojis
st.markdown(f"<p class='big' style='color:{advice_color}'>{planting_advice}</p>", unsafe_allow_html=True)
st.markdown(f"<p class='med'>{emoji_main} {total_rain:.0f} mm (next 8 weeks)</p>", unsafe_allow_html=True)

# Full crop suggestion with corn emoji
if crop_suggestion:
    st.markdown(f"<div class='crop'>Corn {crop_suggestion}</div>", unsafe_allow_html=True)

# Metrics with emojis
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Next 8 Weeks", f"{total_rain:.0f} mm", f"{total_rain-250:+.0f} vs 250mm")
with col2:
    season = "Rainy Season" if total_rain >= 350 else "Dry Spell"
    st.metric("Season", f"{season} {'Heavy Rain' if total_rain >= 500 else 'Light Rain' if total_rain >= 300 else 'Drought'}")
with col3:
    short = crop_suggestion[:50] + "..." if len(crop_suggestion)>50 else crop_suggestion
    st.metric("Plant Now?", planting_advice.split()[0], short)

# Beautiful 8-week chart
weeks = [f"Week {i+1}" for i in range(8)]
fig = go.Figure(go.Bar(
    x=weeks, y=forecast,
    marker_color="#00D4FF",
    text=[f"{v}mm" for v in forecast],
    textposition="outside"
))
fig.update_layout(title="8-Week Rainfall Forecast", template="plotly_dark", height=480)
st.plotly_chart(fig, use_container_width=True)

# Current weather with fun emojis
st.subheader("Current Weather Conditions")
c1, c2, c3, c4 = st.columns(4)
solar = latest.get("solar_radiation") or latest.get("solar") or 0

c1.metric("Temperature", f"{latest['temperature']:.1f}°C", "Hot" if latest['temperature'] > 28 else "Cool")
c2.metric("Humidity", f"{latest['humidity']:.0f}%", "High" if latest['humidity'] > 70 else "Normal")
c3.metric("Wind", f"{latest['wind_speed']:.1f} m/s", "Strong" if latest['wind_speed'] > 5 else "Calm")
c4.metric("Solar", f"{solar:.0f} W/m²", "Jua Kali!" if solar > 700 else "Cloudy")

if solar > 800:
    st.markdown("<h2 style='text-align:center; margin:30px 0;'>JUA KALI SANA!</h2>", unsafe_allow_html=True)

# Footer with love
st.markdown("---")
st.caption(f"Last update: {datetime.now().strftime('%d %b %Y • %I:%M %p')} EAT • Auto-refresh every minute")
st.markdown("<p style='text-align:center; color:#888; font-size:18px;'>Built with love for Nyeri Farmers • DeKUT Weather AI</p>", unsafe_allow_html=True)
