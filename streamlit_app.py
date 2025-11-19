import time
import requests
import serial
import joblib
import numpy as np
import tensorflow as tf
from datetime import datetime
from supabase import create_client, Client

# ==================== CONFIG ====================
SUPABASE_URL = "https://ffbkgocjztagavphjbsq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZmYmtnb2NqenRhZ2F2cGhqYnNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA2NzA5NjcsImV4cCI6MjA3NjI0Njk2N30.sudxLkD1r8ARMEKjVMiyQqTg1KkKR7gSrWA-CKjVKb4"

LAT, LON = -0.445, 36.860  # Nyeri exact

MODEL_PATH = r"C:\Users\user\OneDrive\Desktop\Final Project\nyeri_model_dedan_v5\rain_model_dedan_v5.keras"
SCALER_PATH = r"C:\Users\user\OneDrive\Desktop\Final Project\nyeri_model_dedan_v5\scaler.pkl"

# ==================== SUPABASE & MODEL ====================
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
print("Loading Dedan Kimathi Rain AI v5.1-nyeri-live...")
model = tf.keras.models.load_model(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)
print("Model loaded – ready for Nyeri farmers!")

# ==================== ESP8266 + DHT22 (COM4) ====================
try:
    ser = serial.Serial("COM4", 115200, timeout=15)
    time.sleep(2)
    ser.flushInput()
    print("ESP8266 + DHT22 connected on COM4 → LIVE TEMPERATURE & HUMIDITY")
except Exception as e:
    print("ESP8266 NOT DETECTED! Check cable & COM port")
    print(e)
    exit()

# ==================== OPEN-METEO (Solar, Wind, Precip only) ====================
def get_api_weather():
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={LAT}&longitude={LON}&current=shortwave_radiation,wind_speed_10m,precipitation&timezone=Africa/Nairobi"
    )
    try:
        data = requests.get(url, timeout=10).json()["current"]
        return {
            "solar": float(data["shortwave_radiation"]),
            "wind": float(data["wind_speed_10m"]),
            "precip": float(data["precipitation"])
        }
    except:
        print("Open-Meteo down → using safe values")
        return {"solar": 180.0, "wind": 6.0, "precip": 0.0}

# ==================== READ DHT22 FROM ESP8266 ====================
def read_dht22():
    try:
        if ser.in_waiting > 0:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if "," in line:
                parts = line.split(",")
                if len(parts) >= 2:
                    temp = float(parts[0])
                    hum = float(parts[1])
                    if 10 <= temp <= 45 and 20 <= hum <= 100:
                        return round(temp, 2), round(hum, 1)
    except:
        pass
    return None, None

# ==================== PREDICTION (FIXED HISTORY – NO NULLS) ====================
def predict_8weeks(temp, rh, wind, solar, precip):
    week = datetime.now().isocalendar()[1]
    
    history = []
    for i in range(12):
        past_week = (week - (12 - i) + 52) % 52
        sin_w = np.sin(2 * np.pi * past_week / 52)
        cos_w = np.cos(2 * np.pi * past_week / 52)
        
        # Realistic Nyeri climate pattern
        base_temp = 19 + 4 * np.sin(2 * np.pi * (past_week - 8) / 52)
        base_rh = 78
        base_wind = 5.5
        base_solar = 200
        base_precip = 25 if past_week in range(10,22) or past_week in range(42,50) else 8  # Long & short rains

        history.append([
            base_temp, base_rh, base_wind, base_solar, base_precip,
            past_week, sin_w, cos_w,
            datetime.now().month, base_precip, 0.0
        ])
    
    # Inject CURRENT real sensor + API data
    history[-1][:5] = [temp, rh, wind, solar, precip]
    
    X = scaler.transform(history)
    X = X.reshape(1, 12, -1)
    pred = model.predict(X, verbose=0)[0]
    pred = np.maximum(pred, 0).round(2)
    return pred.tolist()

# ==================== CROP ADVICE ====================
def get_advice(forecast):
    total = sum(forecast)
    good_weeks = sum(1 for x in forecast if x >= 50)
    month = datetime.now().month

    if total >= 500 and good_weeks >= 5:
        return "MVUA NZURI SANA!\nPANDA H6213, ROSE COCO NA MAHINDI SASA!"
    elif total >= 400 and good_weeks >= 4:
        return "PANDA H520 NA KAT B9 HARAKA!\nMvua fupi lakini ya kutosha"
    elif total >= 300:
        return "PANDA H624 AU MALAIKA\nMvua ya wastani – bado poa"
    else:
        return "Subiri kidogo – mvua inakuja hivi karibuni"

# ==================== MAIN LOOP (5 MINUTES) ====================
print("\nDEKUT RAIN AI v5.1 → LIVE WITH DHT22 SENSOR")
print("="*80)

while True:
    try:
        print(f"\n[{datetime.now().strftime('%d %b %Y • %H:%M')}] Reading DHT22...")

        temp, rh = read_dht22()
        if temp is None or rh is None:
            print("No data from DHT22 → skipping this cycle")
            time.sleep(60)
            continue

        api = get_api_weather()

        print(f"Temperature: {temp}°C | Humidity: {rh}% (DHT22)")
        print(f"Solar: {api['solar']:.0f} W/m² | Wind: {api['wind']:.1f} m/s | Precip: {api['precip']:.1f} mm")

        forecast = predict_8weeks(temp, rh, api["wind"], api["solar"], api["precip"])
        total_rain = sum(forecast)
        advice = get_advice(forecast)

        record = {
            "timestamp": datetime.now().isoformat(),
            "temperature": temp,
            "humidity": rh,
            "precipitation": round(api["precip"], 2),
            "solar_radiation": round(api["solar"], 1),
            "wind_speed": round(api["wind"], 2),
            "forecast_weeks": forecast,
            "crop_suggestions": advice,
            "model_version": "v5.1-nyeri-dht22-live"
        }

        supabase.table("weather_data").insert(record).execute()
        print(f"UPDATE SENT → {advice}")
        print(f"8-Week Total: {total_rain:.0f} mm → {forecast}\n")

        time.sleep(300)  # Every 5 minutes

    except KeyboardInterrupt:
        print("\nStopped. Asante sana!")
        ser.close()
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(60)
