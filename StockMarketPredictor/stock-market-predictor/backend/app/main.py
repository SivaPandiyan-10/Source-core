from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import stocks, predictions

app = FastAPI(title="Stock Market Predictor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
app.include_router(predictions.router, prefix="/predictions", tags=["predictions"])

@app.get("/")
def root():
    return {"message": "Stock Market Predictor API"}
