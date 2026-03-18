import pandas as pd
import joblib
from feature_engineering import generate_features
from utils import get_latest_data

MODEL_PATH = "model/latest_xgb_model.joblib"

def predict():
    df = get_latest_data()
    X, _ = generate_features(df)
    model = joblib.load(MODEL_PATH)
    proba = model.predict_proba(X)
    return proba

if __name__ == "__main__":
    print(predict())
