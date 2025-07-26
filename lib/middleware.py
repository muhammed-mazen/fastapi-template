import json
import os.path
import time
from pathlib import Path
from typing import Any, Callable

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import Request, Response, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from pyinstrument import Profiler
from pyinstrument.renderers.html import HTMLRenderer
from pyinstrument.renderers.speedscope import SpeedscopeRenderer
from redis import asyncio as aioredis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware

import logging
from core.config import get_config

config = get_config()


class RequestResponseLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware in charge of logging the HTTP request and response

    Taken and adapted from https://medium.com/@dhavalsavalia/
    fastapi-logging-middleware-logging-requests-and-responses-with-ease-and-style-201b9aa4001a

    """

    def __init__(self, app: FastAPI) -> None:
        super().__init__(app)
        self.logger = logging.getLogger(__name__)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        logging_dict: dict[str, Any] = {}

        await request.body()
        response, response_dict = await self._log_response(call_next, request)
        request_dict = await self._log_request(request)
        logging_dict["request"] = request_dict
        logging_dict["response"] = response_dict
        logging_dict["correlation_id"] = request.headers["X-Request-ID"]

        self.logger.info(json.dumps(logging_dict))
        return response

    async def _log_request(self, request: Request) -> dict[str, Any]:
        """Logs request part
         Arguments:
        - request: Request

        """

        path = request.url.path
        if request.query_params:
            path += f"?{request.query_params}"

        request_logging = {
            "method": request.method,
            "path": path,
            "ip": request.client.host if request.client is not None else None,
        }

        try:
            body = await request.json()
        except Exception:
            body = None
        else:
            request_logging["body"] = body

        return request_logging

    async def _log_response(
            self, call_next: Callable, request: Request
    ) -> tuple[Response, dict[str, Any]]:
        """Logs response part

        Arguments:
        - call_next: Callable (To execute the actual path function and get response back)
        - request: Request
        - request_id: str (uuid)
        Returns:
        - response: Response
        - response_logging: str
        """

        start_time = time.perf_counter()
        response = await self._execute_request(call_next, request)
        finish_time = time.perf_counter()
        execution_time = finish_time - start_time

        overall_status = "successful" if response.status_code < 400 else "failed"

        response_logging = {
            "status": overall_status,
            "status_code": response.status_code,
            "time_taken": f"{execution_time:0.4f}s",
        }
        return response, response_logging

    async def _execute_request(self, call_next: Callable, request: Request) -> Response:
        """Executes the actual path function using call_next.

        Arguments:
        - call_next: Callable (To execute the actual path function
                     and get response back)
        - request: Request
        - request_id: str (uuid)
        Returns:
        - response: Response
        """
        try:
            response: Response = await call_next(request)

        except Exception as e:
            self.logger.exception({"path": request.url.path, "method": request.method, "reason": e})
            raise e

        else:
            return response


def register_cors_middleware(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.FRONTEND_CORS_ORIGIN,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def register_profiling_middleware(app: FastAPI):
    if config.PROFILING_ENABLED is True:

        @app.middleware("http")
        async def profile_request(request: Request, call_next):
            """Profile the current request

            Updated to store profiles in subdirectories and keep only the last 10 responses.
            """
            profile_type_to_ext = {"html": "html", "speedscope": "speedscope.json"}
            profile_type_to_renderer = {
                "html": HTMLRenderer,
                "speedscope": SpeedscopeRenderer,
            }

            if request.query_params.get("profile", False):
                profile_type = request.query_params.get("profile_format", "speedscope")
                with Profiler(interval=0.001, async_mode="enabled") as profiler:
                    response = await call_next(request)

                # Determine directory and file paths
                request_path = request.url.path.strip("/").replace("/", "_")
                base_profile_dir = Path("profile") / request_path
                base_profile_dir.mkdir(parents=True, exist_ok=True)

                # Get list of existing profiles and ensure only the last 10 are kept
                profiles = sorted(base_profile_dir.iterdir(), key=os.path.getmtime)
                if len(profiles) >= 10:
                    for old_profile in profiles[:-9]:
                        old_profile.unlink()

                # Write the current profile to a new file
                index = len(profiles) + 1
                extension = profile_type_to_ext[profile_type]
                renderer = profile_type_to_renderer[profile_type]()
                profile_file = base_profile_dir / f"profile_{index}.{extension}"
                with profile_file.open("w") as out:
                    out.write(profiler.output(renderer=renderer))

                return response

            return await call_next(request)


def register_request_response_logging_middleware(app: FastAPI):
    if config.LOG_REQUEST_RESPONSE:
        app.add_middleware(RequestResponseLoggingMiddleware)


def register_correlation_id_middleware(app: FastAPI):
    app.add_middleware(CorrelationIdMiddleware)


def register_gzip_middleware(app: FastAPI):
    app.add_middleware(GZipMiddleware, minimum_size=1000)


def register_redis():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")



def register_middlewares(app: FastAPI):
    register_cors_middleware(app)
    register_correlation_id_middleware(app)
    register_request_response_logging_middleware(app)
    register_profiling_middleware(app)
    register_gzip_middleware(app)
    register_redis()
