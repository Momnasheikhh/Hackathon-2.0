# 📄 AQI Project Technical Report: Aura Forecast

## 1. Executive Summary
**Project Title:** Aura Forecast - AI-Powered Air Quality Intelligence Dashboard
**Objective:** To develop a real-time, aesthetically immersive application that predicts and visualizes Air Quality Index (AQI) trends for major cities in Pakistan. The system aims to provide actionable health intelligence through an "Emotive UI" that visually communicates risk levels.

---

## 2. Technical Architecture

### 2.1 Technology Stack
*   **Programming Language:** Python 3.8+
*   **Web Framework:** Streamlit (chosen for rapid data app prototyping).
*   **Data Manipulation:** Pandas, NumPy.
*   **Machine Learning:** Scikit-Learn / XGBoost (via Joblib integration).
*   **Visualization:** Plotly (Charts) & Custom CSS/HTML (UI Design).

### 2.2 System Workflow
1.  **Data Ingestion:** The app loads pre-trained model artifacts (`aqi_model.pkl`) and historical city data (`sample_data.csv`) at startup.
2.  **User Interaction:** Users select a city from the "Floating Dock" or dropdown.
3.  **Inference Engine:** The selected city's current atmospheric data (PM2.5, Temperature) is fed into the ML model.
4.  **Forecasting Simulation:** The engine projects pollution trends for the next 72 hours using a stochastic process combined with ML predictions.
5.  **Dynamic Rendering:** The frontend updates the CSS variables (Background Gradients, Accent Colors) based on the predicted AQI Severity.

---

## 3. Machine Learning Methodology

### 3.1 Model Selection
The core intelligence is powered by a **Supervised Learning Regressor** (Random Forest / XGBoost ensemble). This approach was selected to handle non-linear relationships between weather parameters and pollution levels.

*   **Model Type:** Regression & Classification Hybrid.
*   **Deployment Format:** Serialized `.pkl` file (Pickle) for low-latency inference.

### 3.2 Feature Engineering
The model was trained on the following key environmental features:
*   **Primary Predictor:** `PM2.5` (Particulate Matter < 2.5 microns).
*   **Meteorological Features:**
    *   `Temperature_2m` (°C)
    *   `Relative_Humidity` (%)
    *   `Wind_Speed` (km/h)
*   **Temporal Features:** Hour of day, Day of week (to capture traffic/industrial patterns).

### 3.3 Training Process (Summary)
1.  **Data Cleaning:** Handling missing values and removing sensor outliers.
2.  **Normalization:** Scaling features to ensure uniform model weight distribution.
3.  **Training:** The model was trained to minimize Root Mean Squared Error (RMSE) for PM2.5 prediction.
4.  **Threshold Mapping:** Raw predictions are mapped to AQI Classes:
    *   *Good (0-50)*
    *   *Moderate (51-100)*
    *   *Unhealthy (101-150)*
    *   *Hazardous (>150)*

---

## 4. Application Development & Features

### 4.1 "Emotive UI" Implementation
A unique logic layer was developed to make the application "feel" alive.
*   **Logic:** `get_prediction()` determines the AQI Class.
*   **Reaction:** A global state manager injects CSS styles into the `st.markdown` layer.
    *   *Scenario A (Clear Air):* App applies `Radial Gradient (Emerald Green)` + `Slow Orb Animation (10s)`.
    *   *Scenario B (Hazardous):* App applies `Radial Gradient (Deep Red)` + `Fast Orb Animation (2s)`.

### 4.2 Dynamic Risk Leaderboard
A real-time ranking system that:
*   Aggregates risk levels across all monitored cities.
*   Uses a **Highlighter Logic** (`border: 2px solid white`) to visually distinguish the user's currently selected city from the rest of the list.

### 4.3 Simulation Mode (Demo)
To ensure consistent presentation during demonstrations, a deterministic override layer was added:
*   **Lahore** is locked to *Hazardous* parameters.
*   **Islamabad** is locked to *Good* parameters.
*   **Quetta/Karachi** are locked to *Moderate* parameters.
This ensures the audience sees the full spectrum of the app's capabilities without waiting for real-time weather changes.

---

## 5. Conclusion & Future Scope
The **Aura Forecast** successfully demonstrates how AI can be combined with high-end UI/UX principles to create compelling environmental tools.
*   **Current Status:** Fully Functional Prototype.
*   **Future Scope:** Integration with live hardware IoT sensors and API deployment for mobile apps.
