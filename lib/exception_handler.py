from typing import Any, Self

from fastapi import HTTPException, Request, Response, FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import ResponseValidationError
from fastapi.responses import ORJSONResponse as JSONResponse
from starlette import status
from core.config import get_config

config = get_config()


class CacheHit(HTTPException):
    """Exception raised when a requested resource's ETag matches the If-None-Match request header"""


class RepositoryException(Exception): ...


class Forbidden(HTTPException):
    """Exception raises when a user is forbidden to access or modify a given resource"""

    def __init__(self, detail: Any = None, headers: dict[str, str] | None = None):
        super().__init__(detail=detail, headers=headers, status_code=status.HTTP_403_FORBIDDEN)


class ModelNotFound(RepositoryException):
    @classmethod
    def from_model_name(cls, model_name: str) -> Self:
        return cls(f"{model_name} not found")


class DuplicateModel(RepositoryException): ...


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(ModelNotFound)
    def raise_404_exception_on_model_not_found(_: Request, exc: Exception):
        """Return a 404 response when handling a ModelNotFound exception"""
        return JSONResponse(content={"detail": str(exc)}, status_code=status.HTTP_404_NOT_FOUND)

    @app.exception_handler(DuplicateModel)
    def raise_400_exception_on_duplicate_model(_: Request, exc: Exception):
        """Return a 400 response when handling a DuplicateModel exception"""
        return JSONResponse(content={"detail": str(exc)}, status_code=status.HTTP_400_BAD_REQUEST)

    @app.exception_handler(CacheHit)
    def cachehit_exception_handler(_: Request, exc: CacheHit):
        """Generate a correct 304 response when handling a CacheHit exception"""
        return Response("", status_code=exc.status_code, headers=exc.headers)

    @app.exception_handler(Forbidden)
    def forbidden_exception_handler(_: Request, exc: Forbidden):
        return JSONResponse(
            content={"detail": str(exc)},
            status_code=exc.status_code,
            headers=exc.headers,
        )

    if config.LOG_REQUEST_RESPONSE:
        @app.exception_handler(ResponseValidationError)
        async def validation_exception_handler(_: Request, exc: ResponseValidationError):
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=jsonable_encoder({"detail": exc.errors()}),
            )
