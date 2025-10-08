from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.models.api_exception import APIException
from src.routes.user_route import user_router
from src.utils.db import init_db

openapi_tags = [
    {
        "name": "Users",
        "description": "User operations",
    },
    {
        "name": "Health Checks",
        "description": "Application health checks",
    }
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    
load_dotenv()

port = os.getenv("PORT")
env = os.getenv("PYTHON_ENV")

app = FastAPI(
    openapi_tags=openapi_tags,
    debug=env == "development",
    lifespan=lifespan
)

app.include_router(user_router, prefix="/api/users", tags=["Users"])

@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.error,
            "message": exc.message
        }
    )


@app.get("/health", tags=["Health Checks"])
async def health_check():
    return {
        "message": "API is running",
    }
