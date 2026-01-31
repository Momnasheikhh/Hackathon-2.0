
import pandas as pd
import numpy as np
import os
import joblib
import traceback
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# Config
BASE_PATH = "c:/Users/hp/Downloads/archive/Training"
OUTPUT_PATH = "c:/Users/hp/Downloads/archive/Training/AQI_Project/models"
os.makedirs(OUTPUT_PATH, exist_ok=True)

files = {
    "Islamabad": "islamabad_complete_data.xlsx",
    "Karachi": "karachi_complete_data.xlsx",
    "Lahore": "lahore_complete_data.xlsx",
    "Peshawar": "peshawar_complete_data.csv",
    "Quetta": "quetta_complete_data.csv"
}

def load_data():
    dfs = []
    for city, filename in files.items():
        path = os.path.join(BASE_PATH, filename)
        print(f"Loading {city} from {filename}...")
        
        try:
            if filename.endswith(".xlsx"):
                # Excel usually parses dates automatically, but let's be careful
                df = pd.read_excel(path)
            else:
                df = pd.read_csv(path)
            
            # Standardize columns: replace '.' with '_' and lowercase
            df.columns = [c.replace('.', '_').lower() for c in df.columns]
            
            # Ensure 'datetime' column exists
            if 'datetime' not in df.columns:
                print(f"WARNING: 'datetime' column missing in {city}")
                continue
                
            df['city'] = city
            dfs.append(df)
            print(f"Loaded {city}: {df.shape}")
        except Exception as e:
            print(f"Failed to load {city}: {e}")
            traceback.print_exc()
            
    if not dfs:
        raise ValueError("No data loaded!")
        
    full_df = pd.concat(dfs, ignore_index=True)
    return full_df

def preprocess(df):
    print("Preprocessing...")
    # Convert datetime with error handling
    # Using coerce to handle bad dates, dayfirst=True for DD/MM/YYYY
    df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce', dayfirst=True)
    
    # Drop rows with invalid dates
    if df['datetime'].isnull().sum() > 0:
        print(f"Dropping {df['datetime'].isnull().sum()} rows with invalid dates")
        df = df.dropna(subset=['datetime'])
        
    df = df.sort_values(by=['city', 'datetime'])
    
    # Feature Engineering
    df['hour'] = df['datetime'].dt.hour
    df['day'] = df['datetime'].dt.day
    df['month'] = df['datetime'].dt.month
    df['dayofweek'] = df['datetime'].dt.dayofweek
    
    # Simple Lag Features (Previous hour)
    # Ensure column exists before lagging
    target_col = 'components_pm2_5'
    if target_col not in df.columns:
        # Try to find it
        alternatives = ['components_pm2_5', 'pm2_5']
        for alt in alternatives:
            if alt in df.columns:
                target_col = alt
                break
    
    if target_col in df.columns:
        print(f"Creating lags for {target_col}")
        df['pm2_5_lag1'] = df.groupby('city')[target_col].shift(1)
        df['pm2_5_lag24'] = df.groupby('city')[target_col].shift(24)
    else:
        print("Warning: PM2.5 column not found for lagging")
    
    # Drop rows with NaNs (first 24 rows per city)
    df = df.dropna()
    
    return df

def train():
    try:
        df = load_data()
    except Exception as e:
        print(f"Fatal error loading data: {e}")
        return

    print("Columns:", df.columns)
    
    df = preprocess(df)
    
    # Target: main_aqi
    if 'main_aqi' not in df.columns:
        print("Error: 'main_aqi' column not found!")
        return
        
    unique_aqi = df['main_aqi'].unique()
    print(f"Unique AQI values: {unique_aqi}")
    
    # If main_aqi is mostly integers 1-5, treat as categorical
    # But clean it first - ensure it's numeric
    df['main_aqi'] = pd.to_numeric(df['main_aqi'], errors='coerce')
    df = df.dropna(subset=['main_aqi'])
    
    unique_aqi = sorted(df['main_aqi'].unique())
    print(f"Cleaned AQI values: {unique_aqi}")
    
    is_categorical = len(unique_aqi) <= 10 # Assuming 1-5 scale
    
    features = ['components_pm2_5', 'components_pm10', 'components_no2', 
                'temperature_2m', 'relative_humidity_2m', 'wind_speed_10m',
                'hour', 'month', 'pm2_5_lag1'] 
    
    # intersection of available columns
    features = [f for f in features if f in df.columns]
    
    X = df[features]
    y = df['main_aqi']
    
    print(f"Training on {X.shape[0]} samples with features: {features}")
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    if is_categorical:
        print("Training Classifier...")
        y_train = y_train.astype(int)
        y_test = y_test.astype(int)
        model = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        print("Accuracy:", accuracy_score(y_test, y_pred))
        print(classification_report(y_test, y_pred))
    else:
        print("Training Regressor...")
        model = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        print("Score:", model.score(X_test, y_test))
        
    # Save
    print("Saving model and artifacts...")
    joblib.dump(model, os.path.join(OUTPUT_PATH, "aqi_model.pkl"))
    joblib.dump(features, os.path.join(OUTPUT_PATH, "model_features.pkl"))
    
    # Save city list for app
    cities = df['city'].unique().tolist()
    joblib.dump(cities, os.path.join(OUTPUT_PATH, "cities.pkl"))
    
    # Save data for all cities (last 50 rows each)
    sample_df = df.groupby('city').tail(50)
    sample_df.to_csv(os.path.join(OUTPUT_PATH, "sample_data.csv"), index=False)
    
    print("Training Complete!")

if __name__ == "__main__":
    train()
