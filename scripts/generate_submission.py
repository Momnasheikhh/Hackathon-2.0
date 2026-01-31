
import pandas as pd
import joblib
import os
import numpy as np

MODEL_PATH = "models"
OUTPUT_FILE = "prediction_submission.csv"

def generate_submission():
    print("Loading models...")
    try:
        model = joblib.load(os.path.join(MODEL_PATH, "aqi_model.pkl"))
        features = joblib.load(os.path.join(MODEL_PATH, "model_features.pkl"))
        # Load the last part of data to get the starting point
        # It's better to load the full valid dataset from memory or reload
        # For this script, let's just reload the sample data which contains the tails
        data = pd.read_csv(os.path.join(MODEL_PATH, "sample_data.csv"))
    except Exception as e:
        print(f"Error loading artifacts: {e}")
        return

    submission_rows = []
    
    cities = data['city'].unique()
    print(f"Generating forecast for cities: {cities}")
    
    for city in cities:
        city_data = data[data['city'] == city].sort_values(by='datetime')
        if city_data.empty:
            continue
            
        last_record = city_data.iloc[-1]
        last_date = pd.to_datetime(last_record['datetime'])
        last_pm25 = last_record['components_pm2_5'] if 'components_pm2_5' in last_record else 0
        
        # Forecast next 3 days
        future_dates = pd.date_range(start=last_date, periods=4, freq='D')[1:]
        
        for date in future_dates:
            # Construct feature vector
            row_features = {}
            for feat in features:
                if feat in last_record:
                    # Logic: Persist weather, Perturb specific variables slightly
                    base_val = last_record[feat]
                    if feat == 'hour': base_val = 12 # Predict for noon
                    if feat == 'month': base_val = date.month
                    if 'pm2_5' in feat:
                         # Decay/Random walk for PM2.5
                        row_features[feat] = last_pm25 * np.random.uniform(0.95, 1.05)
                    else:
                        row_features[feat] = base_val
            
            # Predict
            X_df = pd.DataFrame([row_features], columns=features).fillna(0)
            pred_aqi = model.predict(X_df)[0]
            
            # Update last_pm25 for recursive forecasting
            if 'components_pm2_5' in X_df.columns:
                 last_pm25 = X_df['components_pm2_5'].values[0]
            
            submission_rows.append({
                "City": city,
                "Date": date.strftime("%Y-%m-%d"),
                "Predicted_AQI_Category": int(pred_aqi),
                "Forecast_Day": f"{(date - last_date).days} days ahead"
            })
            
    submission_df = pd.DataFrame(submission_rows)
    submission_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Submission saved to {OUTPUT_FILE}")
    print(submission_df)

if __name__ == "__main__":
    generate_submission()
