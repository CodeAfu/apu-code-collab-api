
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.database.core import init_db
from src.exceptions import APIException
from src.user.controller import user_router
from src.auth.controller import auth_router
from src.github.controller import github_router

openapi_tags = [
    {
        "name": "Users",
        "description": "User operations",
    },
    {
        "name": "Auth",
        "description": "Authentication operations",
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

async def api_exception_handler(request: Request, exc: APIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.error,
            "message": exc.message
        }
    )

def add_exception_handlers(app: FastAPI):
    app.add_exception_handler(APIException, api_exception_handler)

def add_routes(app: FastAPI):
    app.include_router(user_router, tags=["Users"])
    app.include_router(auth_router, tags=["Authentication"])
    app.include_router(github_router, tags=["GitHub"])

def configure_api(app: FastAPI):
    add_routes(app)
    add_exception_handlers(app)