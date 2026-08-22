import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routers import auth, profile, world, simulation, whatif, game, missions, daily_challenge

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NEXUS API",
    description="AI-powered personalized simulation platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(world.router)
app.include_router(simulation.router)
app.include_router(whatif.router)
app.include_router(game.router)
app.include_router(missions.router)
app.include_router(daily_challenge.router)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def root():
    """Serves the single-file frontend directly - same origin as the API."""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/health")
def health():
    return {"status": "NEXUS API running", "docs": "/docs"}
