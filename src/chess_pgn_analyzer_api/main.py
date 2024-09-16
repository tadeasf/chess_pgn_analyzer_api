from fastapi import FastAPI
from .routes import players, games, moves

app = FastAPI(title="Chess PGN Analyzer API")

app.include_router(players.router, prefix="/api/v1")
app.include_router(games.router, prefix="/api/v1")
app.include_router(moves.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Welcome to Chess PGN Analyzer API"}
