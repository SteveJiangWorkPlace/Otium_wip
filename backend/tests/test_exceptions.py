"""
异常处理模块测试

测试exceptions.py中的自定义异常类和异常处理装饰器。
"""

from unittest.mock import patch

import pytest
from fastapi import HTTPException, status

from exceptions import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    GeminiAPIError,
    GPTZeroAPIError,
    RateLimitError,
    ResourceNotFoundError,
    ValidationError,
    api_error_handler,
    create_error_response,
    handle_exception,
)


class TestCustomExceptions:
    """测试自定义异常类"""

    def test_api_error_base_class(self):
        """测试APIError基类"""
        error = APIError("测试错误")
        assert str(error) == "测试错误"
        assert isinstance(error, Exception)

    def test_gemini_api_error(self):
        """测试GeminiAPIError"""
        error = GeminiAPIError("Gemini API错误", "timeout")
        assert str(error) == "Gemini API错误"
        assert error.error_type == "timeout"
        assert isinstance(error, APIError)

    def test_gptzero_api_error(self):
        """测试GPTZeroAPIError"""
        error = GPTZeroAPIError("GPTZero API错误")
        assert str(error) == "GPTZero API错误"
        assert isinstance(error, APIError)

    def test_rate_limit_error(self):
        """测试RateLimitError"""
        error = RateLimitError("速率限制错误")
        assert str(error) == "速率限制错误"
        assert isinstance(error, APIError)

    def test_validation_error(self):
        """测试ValidationError"""
        error = ValidationError("验证错误")
        assert str(error) == "验证错误"
        assert isinstance(error, APIError)

    def test_authentication_error(self):
        """测试AuthenticationError"""
        error = AuthenticationError("认证错误")
        assert str(error) == "认证错误"
        assert isinstance(error, APIError)

    def test_authorization_error(self):
        """测试AuthorizationError"""
        error = AuthorizationError("授权错误")
        assert str(error) == "授权错误"
        assert isinstance(error, APIError)

    def test_resource_not_found_error(self):
        """测试ResourceNotFoundError"""
        error = ResourceNotFoundError("资源未找到")
        assert str(error) == "资源未找到"
        assert isinstance(error, APIError)

    def test_database_error(self):
        """测试DatabaseError"""
        error = DatabaseError("数据库错误")
        assert str(error) == "数据库错误"
        assert isinstance(error, APIError)


class TestErrorResponseFunctions:
    """测试错误响应工具函数"""

    def test_create_error_response(self):
        """测试create_error_response函数"""
        response = create_error_response(
            error_code="TEST_ERROR",
            message="测试错误",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"field": "username"},
        )

        assert isinstance(response, dict)
        assert response["success"] is False
        assert response["error_code"] == "TEST_ERROR"
        assert response["message"] == "测试错误"
        assert response["details"] == {"field": "username"}

    def test_create_error_response_without_details(self):
        """测试create_error_response函数（无details）"""
        response = create_error_response(
            error_code="TEST_ERROR",
            message="测试错误",
        )

        assert isinstance(response, dict)
        assert response["success"] is False
        assert response["error_code"] == "TEST_ERROR"
        assert response["message"] == "测试错误"
        assert response["details"] == {}

    def test_handle_exception(self):
        """测试handle_exception函数"""
        exception = ValueError("测试验证错误")
        http_exception = handle_exception(exception)

        assert isinstance(http_exception, HTTPException)
        assert http_exception.status_code == status.HTTP_400_BAD_REQUEST
        assert http_exception.detail["error_code"] == "VALIDATION_ERROR"
        assert "测试验证错误" in http_exception.detail["message"]

    def test_handle_exception_with_default_message(self):
        """测试handle_exception函数（使用默认消息）"""
        exception = Exception("")
        http_exception = handle_exception(exception)

        assert isinstance(http_exception, HTTPException)
        assert http_exception.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert http_exception.detail["error_code"] == "INTERNAL_SERVER_ERROR"
        assert http_exception.detail["message"] == "服务器内部错误"

    @pytest.mark.parametrize(
        "exception_class,expected_error_code,expected_status",
        [
            (ValueError, "VALIDATION_ERROR", status.HTTP_400_BAD_REQUEST),
            (RateLimitError, "RATE_LIMIT_EXCEEDED", status.HTTP_429_TOO_MANY_REQUESTS),
            (GeminiAPIError, "GEMINI_API_ERROR", status.HTTP_500_INTERNAL_SERVER_ERROR),
            (
                GPTZeroAPIError,
                "GPTZERO_API_ERROR",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            ),
            (ValidationError, "TEXT_VALIDATION_ERROR", status.HTTP_400_BAD_REQUEST),
            (AuthenticationError, "AUTHENTICATION_ERROR", status.HTTP_401_UNAUTHORIZED),
            (AuthorizationError, "AUTHORIZATION_ERROR", status.HTTP_403_FORBIDDEN),
            (ResourceNotFoundError, "RESOURCE_NOT_FOUND", status.HTTP_404_NOT_FOUND),
        ],
    )
    def test_handle_exception_various_types(
        self, exception_class, expected_error_code, expected_status
    ):
        """测试handle_exception处理各种异常类型"""
        exception = exception_class("测试错误")
        http_exception = handle_exception(exception)

        assert isinstance(http_exception, HTTPException)
        assert http_exception.status_code == expected_status
        assert http_exception.detail["error_code"] == expected_error_code


class TestApiErrorHandler:
    """测试api_error_handler装饰器"""

    async def async_function_that_raises(self, exception):
        """一个会抛出指定异常的异步函数"""
        raise exception("测试错误")

    @pytest.mark.asyncio
    @patch("exceptions.logging")
    async def test_api_error_handler_value_error(self, mock_logging):
        """测试装饰器处理ValueError"""

        # 创建装饰后的函数
        @api_error_handler
        async def test_func():
            raise ValueError("参数验证错误")

        # 验证抛出正确的HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await test_func()

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail["error_code"] == "VALIDATION_ERROR"
        assert "参数验证错误" in exc_info.value.detail["message"]
        # 验证日志被调用
        mock_logging.error.assert_called()

    @pytest.mark.asyncio
    @patch("exceptions.logging")
    async def test_api_error_handler_rate_limit_error(self, mock_logging):
        """测试装饰器处理RateLimitError"""

        @api_error_handler
        async def test_func():
            raise RateLimitError("速率限制")

        with pytest.raises(HTTPException) as exc_info:
            await test_func()

        assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert exc_info.value.detail["error_code"] == "RATE_LIMIT_EXCEEDED"
        mock_logging.error.assert_called()

    @pytest.mark.asyncio
    @patch("exceptions.logging")
    async def test_api_error_handler_gemini_api_error(self, mock_logging):
        """测试装饰器处理GeminiAPIError"""

        @api_error_handler
        async def test_func():
            raise GeminiAPIError("Gemini错误", "timeout")

        with pytest.raises(HTTPException) as exc_info:
            await test_func()

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail["error_code"] == "GEMINI_API_ERROR"
        assert exc_info.value.detail["details"]["error_type"] == "timeout"
        mock_logging.error.assert_called()

    @pytest.mark.asyncio
    @patch("exceptions.logging")
    async def test_api_error_handler_authentication_error(self, mock_logging):
        """测试装饰器处理AuthenticationError"""

        @api_error_handler
        async def test_func():
            raise AuthenticationError("认证失败")

        with pytest.raises(HTTPException) as exc_info:
            await test_func()

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail["error_code"] == "AUTHENTICATION_ERROR"
        mock_logging.error.assert_called()

    @pytest.mark.asyncio
    @patch("exceptions.logging")
    async def test_api_error_handler_http_exception_re_raise(self, mock_logging):
        """测试装饰器重新抛出HTTPException"""
        existing_http_exception = HTTPException(
            status_code=status.HTTP_418_IM_A_TEAPOT, detail={"message": "我是茶壶"}
        )

        @api_error_handler
        async def test_func():
            raise existing_http_exception

        with pytest.raises(HTTPException) as exc_info:
            await test_func()

        # 应该重新抛出相同的HTTPException
        assert exc_info.value.status_code == status.HTTP_418_IM_A_TEAPOT
        assert exc_info.value.detail["message"] == "我是茶壶"
        # 不应记录错误日志（HTTPException不被视为异常）
        mock_logging.error.assert_not_called()

    @pytest.mark.asyncio
    @patch("exceptions.logging")
    async def test_api_error_handler_generic_exception(self, mock_logging):
        """测试装饰器处理通用异常"""

        @api_error_handler
        async def test_func():
            raise RuntimeError("运行时错误")

        with pytest.raises(HTTPException) as exc_info:
            await test_func()

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail["error_code"] == "INTERNAL_SERVER_ERROR"
        mock_logging.error.assert_called()

    @pytest.mark.asyncio
    @patch("exceptions.logging")
    async def test_api_error_handler_successful_execution(self, mock_logging):
        """测试装饰器正常执行（无异常）"""

        @api_error_handler
        async def test_func():
            return {"message": "成功"}

        result = await test_func()
        assert result == {"message": "成功"}
        mock_logging.error.assert_not_called()

    def test_api_error_handler_preserves_function_metadata(self):
        """测试装饰器保留函数元数据"""

        @api_error_handler
        async def original_func(arg1, arg2=None):
            """原始函数文档"""
            return arg1 + (arg2 or "")

        # 检查函数名和文档
        assert original_func.__name__ == "original_func"
        assert original_func.__doc__ == "原始函数文档"

        # 检查函数签名和参数
        import inspect

        sig = inspect.signature(original_func)
        params = list(sig.parameters.keys())
        assert params == ["arg1", "arg2"]

    @pytest.mark.asyncio
    @patch("exceptions.logging")
    async def test_api_error_handler_empty_value_error_message(self, mock_logging):
        """测试装饰器处理空消息的ValueError"""

        @api_error_handler
        async def test_func():
            raise ValueError("")

        with pytest.raises(HTTPException) as exc_info:
            await test_func()

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail["error_code"] == "VALIDATION_ERROR"
        assert exc_info.value.detail["message"] == "参数验证失败"  # 默认消息
        mock_logging.error.assert_called()
