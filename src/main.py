from fastapi import FastAPI
from src.database import Base, engine
import src.models  

app = FastAPI(
    title="Hospital CRM API",
    description="Внутрішня CRM-система для управління записами до лікаря",
    version="0.1.0"
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok", "stage": "Lab 4 - Base Code Structure"}