# MHacks 2025 - Rental AI (FE/BE Split)

A simple split:
- backend/: FastAPI app
- frontend/: React + Vite app

## Backend
1. cd backend
2. python3 -m venv .venv && source .venv/bin/activate
3. pip install -r requirements.txt
4. uvicorn app.main:app --reload

Health: http://127.0.0.1:8000/health

## Frontend
1. cd frontend
2. cp .env.example .env
3. npm install
4. npm run dev

Dev server: http://localhost:5173

The frontend reads `VITE_API_BASE` from `.env` and calls `/health` on the backend.
