import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.database import Base, engine
from src.routers import api_router
import src.models


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Hospital CRM API",
    description="Внутрішня CRM-система для управління записами до лікаря",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(api_router)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def serve_admin_dashboard():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Hospital CRM API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}