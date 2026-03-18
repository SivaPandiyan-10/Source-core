from fastapi import APIRouter, HTTPException
from app.services.stocks_service import get_all_stocks, get_stock_by_symbol

router = APIRouter()

@router.get("")
def get_stocks():
    return get_all_stocks()

@router.get("/{symbol}")
def get_stock(symbol: str):
    stock = get_stock_by_symbol(symbol)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return stock
