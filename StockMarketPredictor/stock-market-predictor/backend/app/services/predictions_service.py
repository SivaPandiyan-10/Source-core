from app.models.models import Prediction, Stock
from app.utils.db import get_db
from sqlalchemy.orm import Session
from sqlalchemy import desc

def get_top_predictions(limit: int = 20):
    db: Session = get_db()
    return db.query(Prediction, Stock).join(Stock, Prediction.stock_id == Stock.id).order_by(desc(Prediction.probability_up)).limit(limit).all()

def get_all_predictions():
    db: Session = get_db()
    return db.query(Prediction, Stock).join(Stock, Prediction.stock_id == Stock.id).all()

def get_prediction_by_symbol(symbol: str):
    db: Session = get_db()
    return db.query(Prediction, Stock).join(Stock, Prediction.stock_id == Stock.id).filter(Stock.symbol == symbol).first()
