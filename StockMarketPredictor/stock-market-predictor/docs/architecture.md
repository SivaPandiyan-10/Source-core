# Architecture

## Overview

The Stock Market Predictor Platform is a microservices-based system with the following components:

- **Backend (FastAPI)**: Serves REST API for stocks and predictions.
- **AI Engine (Python/XGBoost)**: Handles feature engineering, model training, and prediction.
- **Scheduler (APScheduler)**: Orchestrates daily data pipeline jobs.
- **Frontend (Angular)**: User dashboard for viewing predictions and stock data.
- **Database (PostgreSQL/TimescaleDB)**: Stores stocks, prices, and predictions.
- **Redis**: Caches predictions for fast UI access.

## Service Responsibilities

- **Backend**: API endpoints, DB access, business logic.
- **AI Engine**: Data science, ML model training, batch prediction.
- **Scheduler**: Triggers daily ETL, training, and prediction jobs.
- **Frontend**: UI, charts, tables, user navigation.
- **Database**: Persistent storage, time-series queries.
- **Redis**: Low-latency cache for predictions.

## Data Flow

1. Scheduler triggers data fetch → feature engineering → model training → prediction → DB/Redis update.
2. Frontend queries backend API for stocks/predictions (served from DB/Redis).

---
