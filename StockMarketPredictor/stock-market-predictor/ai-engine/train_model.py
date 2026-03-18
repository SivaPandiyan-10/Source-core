import pandas as pd
import xgboost as xgb
import joblib
from feature_engineering import generate_features
from utils import get_training_data

MODEL_PATH = "model/latest_xgb_model.joblib"

def train():
    df = get_training_data()
    X, y = generate_features(df)
    model = xgb.XGBClassifier(n_estimators=100, max_depth=5, n_jobs=-1)
    model.fit(X, y)
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    train()
