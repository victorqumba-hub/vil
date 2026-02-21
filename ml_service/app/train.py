import os
import json
import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
from sqlalchemy import create_all, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config - Use sync engine for training scripts
DATABASE_URL = "postgresql://vil:vilpass@localhost:5432/vildb"
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)

def fetch_training_data():
    """Fetches combined signal and outcome data from the DB."""
    logger.info("Fetching training data from PostgreSQL...")
    engine = create_engine(DATABASE_URL)
    
    query = """
        SELECT 
            s.id as signal_id,
            s.score as base_score,
            s.regime,
            s.direction,
            ds.features_json,
            ds.target_reached,
            ds.stop_hit,
            ds.r_multiple
        FROM signals s
        JOIN ml_signal_dataset ds ON s.id = ds.signal_id
        WHERE ds.target_reached IS NOT NULL OR ds.stop_hit IS NOT NULL
        ORDER BY s.timestamp DESC
    """
    
    df = pd.read_sql(query, engine)
    logger.info(f"Fetched {len(df)} samples with outcomes.")
    return df

def preprocess_data(df):
    """Processes features_json and encodes categorical variables."""
    if df.empty:
        return None, None
    
    # Expand features_json
    features_list = []
    for idx, row in df.iterrows():
        try:
            feat = json.loads(row['features_json'])
            # Ensure target is present
            feat['target'] = row['target_reached']
            features_list.append(feat)
        except Exception as e:
            logger.error(f"Error parsing features for signal {row['signal_id']}: {e}")
            continue
            
    pdf = pd.DataFrame(features_list)
    
    # Basic Feature Engineering
    # Convert regime and direction to categorical codes
    pdf['regime_cat'] = pdf['regime'].astype('category').cat.codes
    pdf['direction_cat'] = pdf['direction'].astype('category').cat.codes
    
    # Drop non-feature columns
    target = pdf['target']
    drop_cols = ['target', 'symbol', 'regime', 'direction']
    X = pdf.drop(columns=[c for c in drop_cols if c in pdf.columns])
    
    return X, target

def train_regime_model(regime_name, X, y):
    """Trains a specific model for a market regime."""
    logger.info(f"Training model for regime: {regime_name} ({len(X)} samples)")
    
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.05,
        random_state=42,
        use_label_encoder=False,
        eval_metric='logloss'
    )
    
    model.fit(X, y)
    
    model_path = os.path.join(MODEL_DIR, f"xgb_{regime_name.lower()}_v1.0.joblib")
    joblib.dump(model, model_path)
    logger.info(f"Model saved to {model_path}")
    return model

def main():
    df = fetch_training_data()
    if len(df) < 5:
        logger.warning("Not enough data to train models. Using dummy data for initialization.")
        # Create dummy data if DB is empty to satisfy the script
        dummy_data = {
            'score': np.random.uniform(40, 95, 20),
            'structure_score': np.random.uniform(20, 100, 20),
            'volatility_score': np.random.uniform(0, 100, 20),
            'liquidity_score': np.random.uniform(0, 100, 20),
            'event_score': np.random.uniform(0, 100, 20),
            'adx': np.random.uniform(10, 50, 20),
            'rsi': np.random.uniform(20, 80, 20),
            'atr_percentile': np.random.uniform(0, 1, 20),
            'relative_volume': np.random.uniform(0.5, 3.0, 20),
            'hour_of_day': np.random.randint(0, 24, 20),
            'day_of_week': np.random.randint(0, 5, 20),
            'target': np.random.randint(0, 2, 20)
        }
        X = pd.DataFrame(dummy_data).drop(columns=['target'])
        y = pd.Series(dummy_data['target'])
        
        train_regime_model("trending", X, y)
        train_regime_model("ranging", X, y)
        train_regime_model("global", X, y)
    else:
        # Realistic implementation: split by regime
        X, y = preprocess_data(df)
        # For now, train one global model if data is sparse, or regime-specific if possible
        train_regime_model("global", X, y)
        
        if 'regime' in df.columns:
            for reg in df['regime'].unique():
                reg_mask = df['regime'] == reg
                X_reg, y_reg = preprocess_data(df[reg_mask])
                if len(X_reg) >= 5:
                    train_regime_model(str(reg), X_reg, y_reg)

if __name__ == "__main__":
    main()
