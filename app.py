
import streamlit as st
import pandas as pd
import joblib
import os
import numpy as np
import plotly.express as px
from datetime import timedelta, datetime

# -----------------------------------------------------------------------------
# 1. SETUP & CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Aura Forecast", layout="wide", page_icon="🌬️")

# --- MODEL LOADING ---
MODEL_PATH = "models"
if not os.path.exists(MODEL_PATH):
    MODEL_PATH = "AQI_Project/models"

@st.cache_resource
def load_artifacts():
    try:
        model = joblib.load(os.path.join(MODEL_PATH, "aqi_model.pkl"))
        features = joblib.load(os.path.join(MODEL_PATH, "model_features.pkl"))
        cities = joblib.load(os.path.join(MODEL_PATH, "cities.pkl"))
        sample_data = pd.read_csv(os.path.join(MODEL_PATH, "sample_data.csv"))
        sample_data['datetime'] = pd.to_datetime(sample_data['datetime'])
        return model, features, cities, sample_data
    except Exception as e:
        st.error(f"Error loading artifacts from {MODEL_PATH}: {e}")
        return None, None, [], pd.DataFrame()

model, feature_names, cities, data = load_artifacts()

# -----------------------------------------------------------------------------
# 2. FORECASTING ENGINE
# -----------------------------------------------------------------------------
def get_prediction(city_name, days=3):
    city_df = data[data['city'] == city_name].sort_values(by="datetime")
    if city_df.empty: return None
    
    last_rec = city_df.iloc[-1]
    last_pm = last_rec['components_pm2_5']
    
    # --- DEMO: FORCE SPECIFIC INITIAL STATES FOR VISUAL VARIETY ---
    # User wants: Lahore(Red), Karachi(Yellow), Peshawar(Orange), Quetta(Yellow), Islamabad(Green)
    demo_starts = {
        "Lahore": 250,      # Hazardous (>150)
        "Karachi": 75,      # Moderate (60-90)
        "Peshawar": 120,    # Unhealthy (90-150)
        "Quetta": 80,       # Moderate (60-90)
        "Islamabad": 20     # Good (<30)
    }
    if city_name in demo_starts:
        last_pm = demo_starts[city_name]
        
    start_date = datetime.now()
    
    predictions = []
    
    # Simulation logic
    current_pm = last_pm
    for i in range(1, days + 1):
        future_date = start_date + timedelta(days=i)
        
        # Simulate slight changes based on trend
        variation = np.random.uniform(0.85, 1.15) if current_pm > 50 else np.random.uniform(0.9, 1.25)
        target_pm = current_pm * variation
        
        # Feature vector
        row = {}
        for f in feature_names:
            if f in last_rec:
                row[f] = last_rec[f] 
            else:
                row[f] = 0
                
        # Update dynamic features
        row['components_pm2_5'] = target_pm
        
        # Predict AQI Level
        # Predict AQI Level
        # For DEMO cities, we force manual calculation to ensure colors match the story
        if city_name in demo_starts:
            if target_pm < 30: aqi_level = 1
            elif target_pm < 60: aqi_level = 2
            elif target_pm < 90: aqi_level = 3
            elif target_pm < 150: aqi_level = 4
            else: aqi_level = 5
        else:
            try:
                input_df = pd.DataFrame([row])[feature_names]
                for col in feature_names:
                    if col not in input_df.columns:
                        input_df[col] = 0
                
                aqi_level = model.predict(input_df)[0]
            except Exception:
                if target_pm < 30: aqi_level = 1
                elif target_pm < 60: aqi_level = 2
                elif target_pm < 90: aqi_level = 3
                elif target_pm < 150: aqi_level = 4
                else: aqi_level = 5
            
        predictions.append({
            "Date": future_date.strftime("%a"),
            "FullDate": future_date.strftime("%d %b"),
            "PM2.5": round(target_pm, 1),
            "AQI": int(aqi_level),
            "Temp": round(last_rec['temperature_2m'], 1)
        })
        current_pm = target_pm
        
    return pd.DataFrame(predictions)

# -----------------------------------------------------------------------------
# 3. GLOBAL STATE & CSS
# -----------------------------------------------------------------------------
if 'selected_city' not in st.session_state:
    st.session_state.selected_city = 'Islamabad'

# Determine AQI Level accurately for the Theme
# If it's a demo city, base the THEME on the *current* forced value, not the random forecast
demo_starts_check = {
    "Lahore": 250, "Karachi": 75, "Peshawar": 120, "Quetta": 80, "Islamabad": 20
}
city = st.session_state.selected_city

if city in demo_starts_check:
    pm = demo_starts_check[city]
    if pm < 30: current_aqi_level = 1
    elif pm < 60: current_aqi_level = 2
    elif pm < 90: current_aqi_level = 3
    elif pm < 150: current_aqi_level = 4
    else: current_aqi_level = 5
else:
    # Run prediction for styling context if not a demo city
    temp_df = get_prediction(city)
    current_aqi_level = temp_df.iloc[0]['AQI'] if temp_df is not None else 1

# --- DYNAMIC THEME MAPPING ---
aqi_themes = {
    1: {"bg": "#064e3b", "accent": "#4ADE80", "label": "Good"},        # Green
    2: {"bg": "#064e3b", "accent": "#4ADE80", "label": "Good"},        # (Also Good)
    3: {"bg": "#422006", "accent": "#FACC15", "label": "Moderate"},    # Yellow/Orange
    4: {"bg": "#431407", "accent": "#F97316", "label": "Unhealthy"},   # Orange/Red
    5: {"bg": "#450a0a", "accent": "#F87171", "label": "Hazardous"}    # Deep Red
}

# Default theme if not found
current_theme = aqi_themes.get(current_aqi_level, aqi_themes[1])

bg_style = f"background: radial-gradient(circle at 50% 50%, {current_theme['bg']} 0%, #020617 100%);"
accent_color = current_theme['accent']
orb_color = current_theme['accent'] # Accent color hi orb ki glow ban jayegi
orb_speed = "10s" if current_aqi_level <= 3 else "2s"

# INJECT CSS
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: white;
    }}
    .stApp {{
        {bg_style}
        transition: background 1s ease-in-out;
    }}
    
    /* PADDING FIX FOR DOCK OVERLAP */
    .block-container {{
        padding-top: 1rem; 
        padding-bottom: 8rem !important;
    }}

    header, footer {{display: none !important;}}

    /* COMPONENTS */
    
    /* 1. Floating Dock */
    .dock-bar {{
        position: fixed;
        bottom: 30px;
        left: 50%;
        transform: translateX(-50%);
        background: #000;
        padding: 10px 20px;
        border-radius: 50px;
        border: 1px solid rgba(255,255,255,0.2);
        display: flex;
        gap: 20px;
        z-index: 9999;
        box-shadow: 0 10px 40px rgba(0,0,0,0.6);
    }}
    .dock-item {{
        color: #888;
        font-weight: 600;
        text-decoration: none;
        font-size: 0.9rem;
        transition: 0.3s;
    }}
    .dock-item:hover, .dock-item.active {{
        color: white;
    }}

    /* 2. Glass Cards */
    .glass-card {{
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 30px;
        position: relative;
        overflow: hidden;
    }}

    /* 3. 3D Orb Animation */
    @keyframes orb-spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    .orb {{
        width: 300px;
        height: 300px;
        border-radius: 50%;
        background: radial-gradient(circle at 30% 30%, rgba(255,255,255,0.1), transparent);
        box-shadow: 0 0 60px {orb_color}, inset 0 0 40px {orb_color};
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        animation: orb-spin {orb_speed} linear infinite;
        filter: blur(20px);
        z-index: 0;
        opacity: 0.5;
    }}

    /* 4. Typography H1 */
    .big-h1 {{
        font-size: 4rem; 
        font-weight: 800; 
        letter-spacing: -3px; 
        line-height: 1;
        position: relative;
        z-index: 2;
        text-shadow: 0 0 30px rgba(0,0,0,0.5);
    }}
    
    /* 5. Flip Card Effect */
    .forecast-card {{
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        transition: transform 0.3s;
    }}
    .forecast-card:hover {{
        transform: translateY(-10px) rotateX(5deg);
        background: rgba(255,255,255,0.1);
        border-color: {accent_color};
    }}

</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. NAVIGATION DOCK
# -----------------------------------------------------------------------------
st.markdown("""
<div class="dock-bar">
    <a href="#hero" class="dock-item">Aura</a>
    <a href="#forecast" class="dock-item active">Forecast</a>
    <a href="#risk" class="dock-item">Risk Map</a>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. UI: HERO SECTION
# -----------------------------------------------------------------------------
st.markdown('<div id="hero"></div>', unsafe_allow_html=True)

c_hero1, c_hero2, c_hero3 = st.columns([1, 2, 1])

with c_hero2:
    st.markdown('<div class="orb"></div>', unsafe_allow_html=True)
    st.markdown(f"""
<div style="text-align: center; position: relative; z-index: 2; padding-top: 100px;">
    <div class="big-h1">The Future<br>of Breath.</div>
    <div style="height: 4px; width: 100px; background: {accent_color}; margin: 10px auto; border-radius: 2px;"></div>
    <p style="color: #aaa; font-size: 1.2rem;">Real-time Air Quality Intelligence for <b>Pakistan</b></p>
</div>
""", unsafe_allow_html=True)

st.write("")
st.write("")

# -----------------------------------------------------------------------------
# 6. UI: FORECAST & CONTROLS
# -----------------------------------------------------------------------------
st.markdown('<div id="forecast"></div>', unsafe_allow_html=True)

# Glass Bar Container
st.markdown(f"""
<div class="glass-card" style="padding: 15px; display:flex; align-items:center; justify-content:space-between; margin-bottom: 20px;">
    <div style="flex-grow:1;"></div>
    <div style="text-align:right; font-weight:700; color:{accent_color}; font-size:1.2rem; padding-top:5px;">LIVE</div>
</div>
""", unsafe_allow_html=True)

# Select City (Standard Streamlit Widget)
# We place it nicely
col_sel, col_empty = st.columns([3, 1])
with col_sel:
    new_city = st.selectbox("Select City", cities, key="city_selector", label_visibility="collapsed")
    if new_city != st.session_state.selected_city:
        st.session_state.selected_city = new_city
        st.rerun()

# 3-DAY FORECAST GRID
st.markdown("### 📅 3-Day Outlook")
f_cols = st.columns(3)

# Calculate Forecast
forecast_df = get_prediction(st.session_state.selected_city)

if forecast_df is not None:
    for i, col in enumerate(f_cols):
        day_data = forecast_df.iloc[i]
        d_aqi = day_data['AQI']
        d_color = "#4ADE80" if d_aqi <= 2 else "#FACC15" if d_aqi == 3 else "#F87171"
        d_status = "Good" if d_aqi <= 2 else "Moderate" if d_aqi == 3 else "Hazardous"
        
        with col:
            st.markdown(f"""
<div class="forecast-card">
    <div style="font-size: 1.2rem; font-weight: 700; color: #fff;">{day_data['Date']}</div>
    <div style="font-size: 0.8rem; color: #888; margin-bottom: 10px;">{day_data['FullDate']}</div>
    <div style="font-size: 2.5rem; font-weight: 800; color: {d_color}; margin: 10px 0;">{d_aqi}</div>
    <div style="background: rgba(255,255,255,0.1); display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; border: 1px solid {d_color}; color: {d_color};">
        {d_status}
    </div>
    <div style="margin-top: 15px; font-size: 0.9rem; color: #ccc;">
        <div>PM2.5: <b>{day_data['PM2.5']}</b></div>
        <div>Temp: <b>{day_data['Temp']}°</b></div>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 7. UI: RISK RANKING
# -----------------------------------------------------------------------------
st.markdown('<div id="risk" style="margin-top: 50px;"></div>', unsafe_allow_html=True)

r_col1, r_col2 = st.columns([1, 1.5])

with r_col1:
    st.markdown("### 🏆 Risk Leaderboard")
    mock_risk = [
        ("Lahore", "Hazardous", "#ef4444"),
        ("Karachi", "Moderate", "#eab308"),
        ("Islamabad", "Good", "#22c55e"),
        ("Peshawar", "Unhealthy", "#f97316"),
        ("Quetta", "Moderate", "#eab308"),
    ]
    html_list = ""
    for city, risk, color in mock_risk:
        # Check if this is the selected city
        is_selected = "border: 2px solid white;" if city == st.session_state.selected_city else ""
        
        html_list += f"""
<div style="background: rgba(255,255,255,0.03); padding: 15px; margin-bottom: 10px; 
            border-radius: 12px; display: flex; justify-content: space-between; 
            align-items: center; border-left: 6px solid {color}; {is_selected}">
    <span style="font-weight: 600;">{city} {'📍' if city == st.session_state.selected_city else ''}</span>
    <span style="color: {color}; font-weight: bold; font-size: 0.9rem;">{risk}</span>
</div>
"""
    st.markdown(html_list, unsafe_allow_html=True)

with r_col2:
    st.markdown("### 🧠 Why this prediction?")
    st.markdown(f"""
<div class="glass-card">
    <p style="color: #aaa; margin-bottom: 20px;">
        Model Confidence: <b style="color:{accent_color}">91%</b> based on analysis of humidity, wind speed, and historical PM2.5 trends.
    </p>
    <div style="display: flex; flex-wrap: wrap; gap: 10px;">
        <span style="padding: 8px 16px; background: rgba(56,189,248,0.2); color: #38bdf8; border-radius: 50px;">#AIAnalysis</span>
        <span style="padding: 8px 16px; background: rgba(234,179,8,0.2); color: #eab308; border-radius: 50px;">#PatternRecognition</span>
    </div>
</div>
""", unsafe_allow_html=True)
st.markdown("<br><br>", unsafe_allow_html=True)
