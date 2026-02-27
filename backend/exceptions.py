"""
异常处理和错误响应模块

包含自定义异常类和统一的异常处理装饰器。
"""

import logging
from functools import wraps
from typing import Any

from fastapi import HTTPException, status

from schemas import ErrorResponse

# ==========================================
# 自定义异常类
# ==========================================


class APIError(Exception):
    """API错误基类"""

    pass


class GeminiAPIError(APIError):
    """Gemini API错误"""

    def __init__(self, message: str, error_type: str = "unknown"):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)


class GPTZeroAPIError(APIError):
    """GPTZero API错误"""

    pass


class RateLimitError(APIError):
    """速率限制错误"""

    pass


class ValidationError(APIError):
    """文本验证错误"""

    pass


class AuthenticationError(APIError):
    """认证错误"""

    pass


class AuthorizationError(APIError):
    """授权错误"""

    pass


class ResourceNotFoundError(APIError):
    """资源未找到错误"""

    pass


class DatabaseError(APIError):
    """数据库错误"""

    pass


# ==========================================
# 统一异常处理装饰器
# ==========================================


def api_error_handler(func):
    """统一异常处理装饰器

    处理不同类型的异常并返回统一的错误响应格式：
    - ValueError: 400 Bad Request
    - RateLimitError: 429 Too Many Requests
    - APIError 子类: 根据错误类型映射状态码
    - 其他异常: 500 Internal Server Error
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValueError as e:
            # 参数验证错误
            logging.error(f"参数验证错误: {repr(str(e))}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    error_code="VALIDATION_ERROR",
                    message=repr(str(e)) if str(e) else "参数验证失败",
                    details={"exception_type": "ValueError"},
                ).dict(),
            ) from e
        except RateLimitError as e:
            # 速率限制错误
            logging.error(f"速率限制错误: {repr(str(e))}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=ErrorResponse(
                    error_code="RATE_LIMIT_EXCEEDED",
                    message=repr(str(e)) if str(e) else "请求过于频繁，请稍后再试",
                    details={"exception_type": "RateLimitError"},
                ).dict(),
            ) from e
        except GeminiAPIError as e:
            # Gemini API 错误
            logging.error(f"Gemini API 错误: {repr(str(e))}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error_code="GEMINI_API_ERROR",
                    message=repr(str(e)) if str(e) else "Gemini API 处理失败",
                    details={
                        "exception_type": "GeminiAPIError",
                        "error_type": e.error_type,
                    },
                ).dict(),
            ) from e
        except GPTZeroAPIError as e:
            # GPTZero API 错误
            logging.error(f"GPTZero API 错误: {repr(str(e))}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error_code="GPTZERO_API_ERROR",
                    message=repr(str(e)) if str(e) else "GPTZero API 处理失败",
                    details={"exception_type": "GPTZeroAPIError"},
                ).dict(),
            ) from e
        except ValidationError as e:
            # 文本验证错误
            logging.error(f"文本验证错误: {repr(str(e))}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    error_code="TEXT_VALIDATION_ERROR",
                    message=repr(str(e)) if str(e) else "文本验证失败",
                    details={"exception_type": "ValidationError"},
                ).dict(),
            ) from e
        except AuthenticationError as e:
            # 认证错误
            logging.error(f"认证错误: {repr(str(e))}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponse(
                    error_code="AUTHENTICATION_ERROR",
                    message=repr(str(e)) if str(e) else "认证失败",
                    details={"exception_type": "AuthenticationError"},
                ).dict(),
            ) from e
        except AuthorizationError as e:
            # 授权错误
            logging.error(f"授权错误: {repr(str(e))}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorResponse(
                    error_code="AUTHORIZATION_ERROR",
                    message=repr(str(e)) if str(e) else "权限不足",
                    details={"exception_type": "AuthorizationError"},
                ).dict(),
            ) from e
        except ResourceNotFoundError as e:
            # 资源未找到错误
            logging.error(f"资源未找到错误: {repr(str(e))}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error_code="RESOURCE_NOT_FOUND",
                    message=repr(str(e)) if str(e) else "请求的资源不存在",
                    details={"exception_type": "ResourceNotFoundError"},
                ).dict(),
            ) from e
        except HTTPException:
            # 重新抛出已有的 HTTPException
            raise
        except Exception as e:
            # 其他未知错误
            logging.error(f"API处理异常: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error_code="INTERNAL_SERVER_ERROR",
                    message="服务器内部错误",
                    details={"exception_type": e.__class__.__name__},
                ).dict(),
            ) from e

    return wrapper


# ==========================================
# 错误响应工具函数
# ==========================================


def create_error_response(
    error_code: str,
    message: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    创建标准化的错误响应字典

    根据提供的错误信息构建统一的错误响应格式，确保所有API错误返回一致的
    数据结构。该函数将错误代码、消息、状态码和详细信息封装成标准格式。

    Args:
        error_code: 错误代码字符串，如 "VALIDATION_ERROR"、"RATE_LIMIT_EXCEEDED" 等
        message: 人类可读的错误描述信息
        status_code: HTTP状态码，默认500（服务器内部错误）
        details: 可选的额外错误详细信息字典，用于调试或提供上下文

    Returns:
        dict[str, Any]: 标准化的错误响应字典，包含以下字段：
            - error_code: 错误代码
            - message: 错误消息
            - details: 错误详情（如果提供了details参数）

    Raises:
        无: 函数内部不会抛出异常，确保总是返回有效的字典

    Examples:
        >>> create_error_response("VALIDATION_ERROR", "输入文本过长", 400)
        {"error_code": "VALIDATION_ERROR", "message": "输入文本过长", "details": {}}

        >>> create_error_response("API_ERROR", "服务暂时不可用", 503, {"retry_after": 60})
        {"error_code": "API_ERROR", "message": "服务暂时不可用", "details": {"retry_after": 60}}

    Notes:
        - 该函数不实际设置HTTP状态码，仅创建响应内容字典
        - 状态码参数主要用于记录和调试目的
        - 所有外部API错误都应使用此函数创建统一格式的响应
        - 前端应用依赖此格式进行错误处理和显示
    """
    return ErrorResponse(error_code=error_code, message=message, details=details or {}).dict()


def handle_exception(
    exception: Exception, default_message: str = "服务器内部错误"
) -> HTTPException:
    """处理异常并返回HTTPException"""
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

    logging.error(f"{error_code}: {message}", exc_info=True)

    return HTTPException(
        status_code=status_code,
        detail=create_error_response(
            error_code=error_code,
            message=message,
            details={"exception_type": exception.__class__.__name__},
        ),
    )
