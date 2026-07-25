"""Stable public API errors and request correlation."""

import logging
from collections.abc import Awaitable, Callable, Mapping
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

RequestHandler = Callable[[Request], Awaitable[Response]]
logger = logging.getLogger(__name__)


class ErrorBody(BaseModel):
    """Stable error fields returned to API clients."""

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    details: dict[str, Any] | None = None
    request_id: str


class ErrorResponse(BaseModel):
    """Top-level public API error envelope."""

    model_config = ConfigDict(extra="forbid")

    error: ErrorBody


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Assign an untrusted-input-independent request correlation identifier."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestHandler,
    ) -> Response:
        request_id = str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


def _request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", uuid4()))


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    request_id = _request_id(request)
    payload = ErrorResponse(
        error=ErrorBody(
            code=code,
            message=message,
            details=details,
            request_id=request_id,
        )
    )
    response = JSONResponse(
        status_code=status_code,
        content=payload.model_dump(mode="json"),
        headers=headers,
    )
    response.headers["X-Request-ID"] = request_id
    return response


def _http_error_code(status_code: int) -> str:
    return {
        status.HTTP_400_BAD_REQUEST: "bad_request",
        status.HTTP_401_UNAUTHORIZED: "authentication_required",
        status.HTTP_403_FORBIDDEN: "operation_forbidden",
        status.HTTP_404_NOT_FOUND: "resource_not_found",
        status.HTTP_409_CONFLICT: "state_conflict",
        status.HTTP_422_UNPROCESSABLE_CONTENT: "validation_failed",
        status.HTTP_429_TOO_MANY_REQUESTS: "rate_limit_exceeded",
        status.HTTP_503_SERVICE_UNAVAILABLE: "service_unavailable",
    }.get(status_code, "request_failed")


async def handle_http_exception(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Map framework HTTP exceptions to the public error contract."""
    if not isinstance(exception, HTTPException):
        raise exception

    message = (
        exception.detail
        if isinstance(exception.detail, str)
        else "The request could not be completed."
    )
    return _error_response(
        request,
        status_code=exception.status_code,
        code=_http_error_code(exception.status_code),
        message=message,
        headers=exception.headers,
    )


async def handle_validation_exception(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Return validation locations and types without echoing request values."""
    if not isinstance(exception, RequestValidationError):
        raise exception

    details = {
        "violations": [
            {
                "location": [str(part) for part in error["loc"]],
                "type": error["type"],
            }
            for error in exception.errors()
        ]
    }
    return _error_response(
        request,
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="validation_failed",
        message="The request failed validation.",
        details=details,
    )


async def handle_unexpected_exception(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Log an unexpected failure without request secrets and return a safe error."""
    logger.exception(
        "Unhandled request failure",
        exc_info=exception,
        extra={
            "event": "unhandled_request_failure",
            "request_id": _request_id(request),
            "method": request.method,
            "path": request.url.path,
        },
    )
    return _error_response(
        request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="internal_error",
        message="An unexpected error occurred.",
    )


def configure_error_handling(application: FastAPI) -> None:
    """Install request IDs and stable public exception handlers."""
    application.add_middleware(RequestIdMiddleware)
    application.add_exception_handler(HTTPException, handle_http_exception)
    application.add_exception_handler(
        RequestValidationError,
        handle_validation_exception,
    )
    application.add_exception_handler(Exception, handle_unexpected_exception)
