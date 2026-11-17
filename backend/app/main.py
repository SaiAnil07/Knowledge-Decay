from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.db.database import init_db
from backend.app.api.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database schema
    await init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Privacy-Preserving Software Documentation Consistency Analyzer",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow local frontend ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "operational",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR
    }
