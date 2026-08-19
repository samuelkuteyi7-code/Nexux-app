from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import profile, world, simulation, whatif

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NEXUS API",
    description="AI-powered personalized simulation platform - MVP backend",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile.router)
app.include_router(world.router)
app.include_router(simulation.router)
app.include_router(whatif.router)


@app.get("/")
def root():
    return {"status": "NEXUS API running", "docs": "/docs"}
