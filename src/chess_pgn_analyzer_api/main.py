from fastapi import FastAPI
from contextlib import asynccontextmanager
from .database import init_db
from .routes import players


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: run database initialization
    await init_db()
    yield
    # Shutdown: add any cleanup code here if needed


app = FastAPI(title="Chess PGN Analyzer API", lifespan=lifespan)

app.include_router(players.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Welcome to Chess PGN Analyzer API"}

