from fastapi import FastAPI
from .database import init_db
from .routes import players

app = FastAPI(title="Chess PGN Analyzer API")


@app.on_event("startup")
async def on_startup():
    await init_db()


app.include_router(players.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Welcome to Chess PGN Analyzer API"}
