from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import users, families, analytics

app = FastAPI(
    title="Test Capacity Analytics API",
    version="0.1.0",
    description="Microservice to calculate testing capacity and cycle times."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api")
app.include_router(families.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "ok"}