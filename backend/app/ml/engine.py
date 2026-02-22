import joblib
import os
import pandas as pd
from typing import Dict, Any, Optional
from app.config import settings

class ModelManager:
    """Institutional model loader with regime-specific routing."""
    
    def __init__(self):
        self.model_dir = os.path.join(os.path.dirname(__file__), "models")
        self.models = {}
        self.load_models()
        
    def load_models(self):
        """Pre-loads all available regime models into memory."""
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
            return

        try:
            available_files = os.listdir(self.model_dir)
            for f in available_files:
                if f.endswith(".joblib"):
                    # Filename format: xgb_trending_v1.0.joblib
                    parts = f.split("_")
                    if len(parts) > 1:
                        regime = parts[1].upper()
                        self.models[regime] = joblib.load(os.path.join(self.model_dir, f))
                        print(f"[ModelManager] Loaded {regime} model: {f}")
        except Exception as e:
            print(f"[ModelManager] Error loading models: {e}")

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        regime = str(features.get("regime", "GLOBAL")).upper()
        
        # Determine which model to use
        model_key = "GLOBAL"
        if "TRENDING" in regime: model_key = "TRENDING"
        elif "RANGING" in regime: model_key = "RANGING"
        
        model = self.models.get(model_key) or self.models.get("GLOBAL")
        
        if model:
            try:
                # Prepare features for XGBoost
                # Create a single-row DataFrame
                input_df = pd.DataFrame([features])
                
                # Drop non-feature columns
                drop_cols = ['symbol', 'regime', 'direction', 'signal_id']
                X = input_df.drop(columns=[c for c in drop_cols if c in input_df.columns])
                
                # Predict probability of class 1 (SUCCESS)
                prob = float(model.predict_proba(X)[0][1])
                version = f"XGB-{model_key}-v1.0"
                
                return {
                    "prob": round(prob, 4),
                    "confidence": 0.90 if prob > 0.7 or prob < 0.3 else 0.75,
                    "version": version
                }
            except Exception as e:
                print(f"[ModelManager] Inference error: {e}. Falling back to heuristics.")

        # Fallback Heuristics (Original Phase 2 Logic)
        prob_multiplier = 1.05 if "TRENDING" in regime else (0.95 if "RANGING" in regime else 1.0)
        score = features.get("score", 50)
        success_prob = min(0.98, (score / 100.0) * prob_multiplier)
        
        return {
            "prob": round(success_prob, 4),
            "confidence": 0.88 if "TRENDING" in regime else 0.75,
            "version": "Heuristic-Fallback-v1.0"
        }

model_manager = ModelManager()
