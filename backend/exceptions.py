"""
Exception handling and error response helpers.

Contains custom exception classes and a unified exception handling decorator.
"""

import logging
from functools import wraps
from typing import Any

from fastapi import HTTPException, status

from schemas import ErrorResponse

# ==========================================
# Custom exception classes
# ==========================================


class APIError(Exception):
    """Base API error."""

    pass


class GeminiAPIError(APIError):
    """Gemini API error."""

    def __init__(self, message: str, error_type: str = "unknown"):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)


class GPTZeroAPIError(APIError):
    """GPTZero API error."""

    pass


class RateLimitError(APIError):
    """Rate limit error."""

    pass


class ValidationError(APIError):
    """Text validation error."""

    pass


class AuthenticationError(APIError):
    """Authentication error."""

    pass


class AuthorizationError(APIError):
    """Authorization error."""

    pass


class ResourceNotFoundError(APIError):
    """Resource not found error."""

    pass


class DatabaseError(APIError):
    """Database error."""

    pass


# ==========================================
# Unified exception handler decorator
# ==========================================


def api_error_handler(func):
    """Unified exception handling decorator."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValueError as e:
            logging.error("Parameter validation error: %r", str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    error_code="VALIDATION_ERROR",
                    message=repr(str(e)) if str(e) else "参数验证失败",
                    details={"exception_type": "ValueError"},
                ).model_dump(),
            ) from e
        except RateLimitError as e:
            logging.error("Rate limit error: %r", str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=ErrorResponse(
                    error_code="RATE_LIMIT_EXCEEDED",
                    message=repr(str(e)) if str(e) else "请求过于频繁，请稍后再试",
                    details={"exception_type": "RateLimitError"},
                ).model_dump(),
            ) from e
        except GeminiAPIError as e:
            logging.error("Gemini API error: %r", str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error_code="GEMINI_API_ERROR",
                    message=repr(str(e)) if str(e) else "Gemini API 处理失败",
                    details={
                        "exception_type": "GeminiAPIError",
                        "error_type": e.error_type,
                    },
                ).model_dump(),
            ) from e
        except GPTZeroAPIError as e:
            logging.error("GPTZero API error: %r", str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error_code="GPTZERO_API_ERROR",
                    message=repr(str(e)) if str(e) else "GPTZero API 处理失败",
                    details={"exception_type": "GPTZeroAPIError"},
                ).model_dump(),
            ) from e
        except ValidationError as e:
            logging.error("Text validation error: %r", str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    error_code="TEXT_VALIDATION_ERROR",
                    message=repr(str(e)) if str(e) else "文本验证失败",
                    details={"exception_type": "ValidationError"},
                ).model_dump(),
            ) from e
        except AuthenticationError as e:
            logging.error("Authentication error: %r", str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponse(
                    error_code="AUTHENTICATION_ERROR",
                    message=repr(str(e)) if str(e) else "认证失败",
                    details={"exception_type": "AuthenticationError"},
                ).model_dump(),
            ) from e
        except AuthorizationError as e:
            logging.error("Authorization error: %r", str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorResponse(
                    error_code="AUTHORIZATION_ERROR",
                    message=repr(str(e)) if str(e) else "权限不足",
                    details={"exception_type": "AuthorizationError"},
                ).model_dump(),
            ) from e
        except ResourceNotFoundError as e:
            logging.error("Resource not found error: %r", str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error_code="RESOURCE_NOT_FOUND",
                    message=repr(str(e)) if str(e) else "请求的资源不存在",
                    details={"exception_type": "ResourceNotFoundError"},
                ).model_dump(),
            ) from e
        except HTTPException:
            raise
        except Exception as e:
            logging.error("Unhandled API exception: %s", str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error_code="INTERNAL_SERVER_ERROR",
                    message="服务器内部错误",
                    details={"exception_type": e.__class__.__name__},
                ).model_dump(),
            ) from e

    return wrapper


# ==========================================
# Error response helper functions
# ==========================================


def create_error_response(
    error_code: str,
    message: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a normalized error response payload."""
    return ErrorResponse(
        error_code=error_code, message=message, details=details or {}
    ).model_dump()


def handle_exception(
    exception: Exception, default_message: str = "服务器内部错误"
) -> HTTPException:
    """Handle an exception and return an HTTPException."""
    error_code = "INTERNAL_SERVER_ERROR"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    if isinstance(exception, ValueError):
        error_code = "VALIDATION_ERROR"
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exception, RateLimitError):
        error_code = "RATE_LIMIT_EXCEEDED"
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
    elif isinstance(exception, GeminiAPIError):
        error_code = "GEMINI_API_ERROR"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    elif isinstance(exception, GPTZeroAPIError):
        error_code = "GPTZERO_API_ERROR"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    elif isinstance(exception, ValidationError):
        error_code = "TEXT_VALIDATION_ERROR"
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exception, AuthenticationError):
        error_code = "AUTHENTICATION_ERROR"
        status_code = status.HTTP_401_UNAUTHORIZED
    elif isinstance(exception, AuthorizationError):
        error_code = "AUTHORIZATION_ERROR"
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(exception, ResourceNotFoundError):
        error_code = "RESOURCE_NOT_FOUND"
        status_code = status.HTTP_404_NOT_FOUND

    message = str(exception) if str(exception) else default_message

    logging.error("%s: %s", error_code, message, exc_info=True)

    return HTTPException(
        status_code=status_code,
        detail=create_error_response(
            error_code=error_code,
            message=message,
            details={"exception_type": exception.__class__.__name__},
        ),
    )
