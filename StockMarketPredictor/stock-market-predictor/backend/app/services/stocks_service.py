from app.models.models import Stock
from app.utils.db import get_db
from sqlalchemy.orm import Session

def get_all_stocks():
    db: Session = get_db()
    return db.query(Stock).all()

def get_stock_by_symbol(symbol: str):
    db: Session = get_db()
    return db.query(Stock).filter(Stock.symbol == symbol).first()
