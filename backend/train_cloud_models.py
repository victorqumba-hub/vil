import os
import pandas as pd
import numpy as np
import joblib
import json
import psycopg2
from xgboost import XGBClassifier
from dotenv import load_dotenv
from urllib.parse import urlparse, unquote

load_dotenv()

PG_URL = os.getenv("DATABASE_URL", "").replace("+asyncpg", "")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "app", "ml", "models")

def train_models():
    print("--- STARTING PRODUCTION MODEL TRAINING ---")
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)

    # 1. Connect and Fetch Data
    print(f"Fetching data from Supabase...")
    try:
        # Use simple psycopg2 for blocking fetch
        conn = psycopg2.connect(PG_URL)
        query = "SELECT features_json, target_reached FROM ml_signal_dataset"
        df_raw = pd.read_sql(query, conn)
        conn.close()
    except Exception as e:
        print(f"  Error fetching data: {e}")
        return

    if df_raw.empty:
        print("  No data found in dataset.")
        return

    print(f"  Loaded {len(df_raw)} records.")

    # 2. Preprocess
    print("Preprocessing data...")
    feature_list = []
    targets = []
    
    for _, row in df_raw.iterrows():
        try:
            feats = json.loads(row['features_json'])
            # Extract common features
            feature_row = {
                'score': float(feats.get('score', 0)),
                'structure_score': float(feats.get('structure_score', 0)),
                'volatility_score': float(feats.get('volatility_score', 0)),
                'liquidity_score': float(feats.get('liquidity_score', 0)),
                'event_score': float(feats.get('event_score', 0)),
                'adx': float(feats.get('adx', 0)),
                'rsi': float(feats.get('rsi', 0)),
                'atr_percentile': float(feats.get('atr_percentile', 0)),
                'relative_volume': float(feats.get('relative_volume', 0)),
                'hour_of_day': int(feats.get('hour_of_day', 0)),
                'day_of_week': int(feats.get('day_of_week', 0)),
                'regime': feats.get('regime', 'GLOBAL')
            }
            feature_list.append(feature_row)
            targets.append(1 if row['target_reached'] == 1 else 0)
        except Exception as e:
            continue

    df = pd.DataFrame(feature_list)
    df['target'] = targets

    # 3. Train Regime-Specific Models
    regimes = ['GLOBAL', 'TRENDING', 'RANGING']
    
    for regime in regimes:
        print(f"Training {regime} model...")
        if regime == 'GLOBAL':
            regime_df = df
        else:
            regime_df = df[df['regime'].str.contains(regime, na=False)]
        
        if len(regime_df) < 50:
            print(f"  Insufficient data for {regime} ({len(regime_df)} rows). Using Global model base.")
            if regime == 'GLOBAL':
                continue # Should not happen if data exists
            else:
                regime_df = df

        X = regime_df.drop(columns=['target', 'regime'])
        y = regime_df['target']

        model = XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.05,
            objective='binary:logistic',
            random_state=42
        )
        
        model.fit(X, y)
        
        model_path = os.path.join(MODEL_DIR, f"xgb_{regime.lower()}_v1.0.joblib")
        joblib.dump(model, model_path)
        print(f"  Saved {regime} model to {model_path}")

    print("\n--- TRAINING COMPLETE ---")

if __name__ == "__main__":
    train_models()
