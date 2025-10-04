from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from fastapi import FastAPI

from src.routes.user_route import user_router
from src.utils.db import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    
load_dotenv()
port = os.getenv("PORT")
debug = os.getenv("PYTHON_ENV") == "development"

app = FastAPI(debug=debug, lifespan=lifespan)

app.include_router(user_router)

@app.get("/")
async def health_check():
    return {
        "status": 400,
        "message": "API is running",
    }
