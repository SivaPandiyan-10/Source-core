# Code Flow

## Backend (FastAPI)
- `main.py`: App entry, router registration
- `api/`: API endpoints for stocks and predictions
- `services/`: Business logic for stocks and predictions
- `models/`: SQLAlchemy models
- `utils/`: DB connection, data fetch, Redis update

## AI Engine
- `train_model.py`: Loads data, trains XGBoost, saves model
- `feature_engineering.py`: Computes technical indicators
- `predict.py`: Loads model, generates predictions
- `utils.py`: Data access helpers

## Scheduler
- `jobs.py`: APScheduler jobs for daily pipeline

## Frontend (Angular)
- `pages/`: Dashboard, All Stocks, Stock Details
- `app.module.ts`: Module setup
- `app-routing.module.ts`: Routing
- `app.component.ts`: Layout, navigation

---
