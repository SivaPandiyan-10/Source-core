from fastapi import APIRouter, HTTPException
from app.services.predictions_service import get_top_predictions, get_all_predictions, get_prediction_by_symbol

router = APIRouter()

@router.get("/top")
def top_predictions():
    return get_top_predictions()

@router.get("/all")
def all_predictions():
    return get_all_predictions()

@router.get("/{symbol}")
def prediction_by_symbol(symbol: str):
    prediction = get_prediction_by_symbol(symbol)
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return prediction
