# Setup Guide

## Prerequisites
- Docker & Docker Compose
- Node.js (for local frontend dev)

## Quick Start

1. Clone the repository:
   ```sh
   git clone <repo-url>
   cd stock-market-predictor
   ```
2. Build and run all services:
   ```sh
   cd deployment
   docker-compose up --build
   ```
3. Access the platform:
   - Frontend: http://localhost:4200
   - Backend API: http://localhost:8000

## Local Development

- **Backend**: `cd backend && uvicorn app.main:app --reload`
- **AI Engine**: `cd ai-engine && python train_model.py`
- **Scheduler**: `cd scheduler && python jobs.py`
- **Frontend**: `cd frontend/angular-dashboard && npm install && npm start`

## Database
- Connect to PostgreSQL at `localhost:5432`, user: `postgres`, password: `postgres`, db: `stockdb`
- Run `database/schema.sql` to initialize tables.

## Environment Variables
- See `docker-compose.yml` for all service environment variables.

---
