# MHacks 2025 - Rental AI (FE/BE Split)
By: Ahaan Shah, Raymond Lin, Patrick Lu, Forest Qin

## Project Overview
Rent AI makes renting easy by combining Fetch.ai agents, Gemini, and AgentMail. It automatically analyzes rental property data to match user preferences, then acts as a personal real estate assistant to handle communication with landlords—scheduling viewings, requesting details, and guiding users through rental platforms. Our goal is to make finding and securing housing faster, smarter, and stress-free.
- backend/: FastAPI app
- frontend/: React + Vite app

## Backend Setup
1. cd backend
2. python3 -m venv .venv && source .venv/bin/activate
3. pip install -r requirements.txt
4. uvicorn app.main:app --reload

Health: http://127.0.0.1:8000/health

## Frontend Setup
1. cd frontend
2. cp .env.example .env
3. npm install
4. npm run dev

Dev server: http://localhost:5173

The frontend reads `VITE_API_BASE` from `.env` and calls `/health` on the backend.
