## Architecture (FE/BE Split)

- backend/: FastAPI service
  - `app/main.py`: entrypoint, CORS, health endpoint
  - Add routers under `app/api/` as you grow (search, recommend, confirm)
- frontend/: React + Vite
  - `src/lib/api.ts`: API client using `VITE_API_BASE`
  - `src/App.tsx`: shows backend health as a smoke test

Keep it simple; split into more services only when needed.
