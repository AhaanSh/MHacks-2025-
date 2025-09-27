from fastapi import FastAPI
from loguru import logger

app = FastAPI(title="MHacks Rental AI")



@app.get("/health")
async def health():
    return {"status": "ok"}
from fastapi.middleware.cors import CORSMiddleware\n\napp.add_middleware(\n    CORSMiddleware,\n    allow_origins=["http://localhost:5173"],\n    allow_credentials=True,\n    allow_methods=["*"],\n    allow_headers=["*"],\n)\n