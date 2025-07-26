from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import UJSONResponse

from db.session import init_db
from lib.exception_handler import register_exception_handlers
from lib.logging import setup_logging
from lib.middleware import register_middlewares
from lib.prometheus import register_prometheus
from routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Task Manager",
        description="An API for the Task Manager",
        version="0.1.0",
        lifespan=lifespan,
        root_path="/backend",
        default_response_class=UJSONResponse
    )

    setup_logging(app)
    register_middlewares(app)
    register_exception_handlers(app)
    register_prometheus(app)
    app.include_router(api_router)

    return app
