"""
数据模型测试

测试schemas.py中的所有Pydantic模型。
"""

import pytest
from pydantic import ValidationError

from schemas import (
    AddUserRequest,
    AdminLoginRequest,
    AIChatMessage,
    AIChatRequest,
    AIChatResponse,
    AIDetectionRequest,
    AIDetectionResponse,
    CheckEmailResponse,
    CheckTextRequest,
    CheckTextResponse,
    CheckUsernameRequest,
    CheckUsernameResponse,
    ErrorResponse,
    LoginRequest,
    PasswordResetRequest,
    PasswordResetResponse,
    RefineTextRequest,
    RefineTextResponse,
    RegisterRequest,
    ResetPasswordRequest,
    SendVerificationRequest,
    StreamRefineTextChunk,
    StreamRefineTextRequest,
    StreamTranslationChunk,
    StreamTranslationRequest,
    SuccessResponse,
    TranslationDirective,
    UpdateUserRequest,
    UsageStats,
    UserInfo,
    UserInfoWithEmail,
    VerificationResponse,
    VerifyEmailRequest,
)


class TestRequestModels:
    """测试请求模型"""

    def test_login_request(self):
        """测试登录请求模型"""
        # 有效数据
        data = {"username": "testuser", "password": "password123"}
        request = LoginRequest(**data)
        assert request.username == "testuser"
        assert request.password == "password123"

        # 缺少必填字段
        with pytest.raises(ValidationError):
            LoginRequest(username="testuser")  # 缺少password

        # 字段类型错误
        with pytest.raises(ValidationError):
            LoginRequest(username=123, password="password123")  # username应为字符串

    def test_check_text_request(self):
        """测试文本检查请求模型"""
        # 有效数据
        data = {
            "text": "这是一个测试文本。",
            "operation": "error_check",
            "version": "professional",
        }
        request = CheckTextRequest(**data)
        assert request.text == "这是一个测试文本。"
        assert request.operation == "error_check"
        assert request.version == "professional"

        # 默认值
        data = {"text": "测试", "operation": "translate_us"}
        request = CheckTextRequest(**data)
        assert request.version == "professional"  # 默认值

        # 缺少必填字段
        with pytest.raises(ValidationError):
            CheckTextRequest(operation="error_check")  # 缺少text

    def test_refine_text_request(self):
        """测试文本润色请求模型"""
        # 有效数据
        data = {"text": "This is a test text.", "directives": ["improve grammar"]}
        request = RefineTextRequest(**data)
        assert request.text == "This is a test text."
        assert request.directives == ["improve grammar"]

        # 默认值
        data = {"text": "Test"}
        request = RefineTextRequest(**data)
        assert request.directives == []  # 默认空列表

    def test_ai_detection_request(self):
        """测试AI检测请求模型"""
        data = {"text": "这是一段需要检测的文本。"}
        request = AIDetectionRequest(**data)
        assert request.text == "这是一段需要检测的文本。"

        # 缺少必填字段
        with pytest.raises(ValidationError):
            AIDetectionRequest()

    def test_admin_login_request(self):
        """测试管理员登录请求模型"""
        data = {"password": "admin123"}
        request = AdminLoginRequest(**data)
        assert request.password == "admin123"

        # 缺少必填字段
        with pytest.raises(ValidationError):
            AdminLoginRequest()

    def test_update_user_request(self):
        """测试更新用户请求模型"""
        data = {"username": "testuser"}
        request = UpdateUserRequest(**data)
        assert request.username == "testuser"
        assert request.daily_translation_limit is None
        assert request.daily_ai_detection_limit is None
        assert request.password is None

        # 所有字段
        data = {
            "username": "testuser",
            "daily_translation_limit": 10,
            "daily_ai_detection_limit": 5,
            "password": "newpassword123",
        }
        request = UpdateUserRequest(**data)
        assert request.daily_translation_limit == 10
        assert request.daily_ai_detection_limit == 5
        assert request.password == "newpassword123"

    def test_add_user_request(self):
        """测试添加用户请求模型"""
        data = {"username": "newuser", "password": "password123"}
        request = AddUserRequest(**data)
        assert request.username == "newuser"
        assert request.password == "password123"
        assert request.daily_translation_limit == 3  # 默认值
        assert request.daily_ai_detection_limit == 3  # 默认值

        # 自定义限制
        data = {
            "username": "newuser",
            "password": "password123",
            "daily_translation_limit": 10,
            "daily_ai_detection_limit": 5,
        }
        request = AddUserRequest(**data)
        assert request.daily_translation_limit == 10
        assert request.daily_ai_detection_limit == 5

    def test_verification_requests(self):
        """测试验证相关请求模型"""
        # 发送验证码请求
        data = {"email": "test@example.com"}
        request = SendVerificationRequest(**data)
        assert request.email == "test@example.com"

        # 验证邮箱请求
        data = {"email": "test@example.com", "code": "123456"}
        request = VerifyEmailRequest(**data)
        assert request.email == "test@example.com"
        assert request.code == "123456"

        # 注册请求
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "verification_token": "token123",
        }
        request = RegisterRequest(**data)
        assert request.username == "testuser"
        assert request.email == "test@example.com"
        assert request.password == "password123"
        assert request.verification_token == "token123"

    def test_password_reset_requests(self):
        """测试密码重置请求模型"""
        # 密码重置请求
        data = {"email": "test@example.com"}
        request = PasswordResetRequest(**data)
        assert request.email == "test@example.com"

        # 重置密码请求
        data = {"token": "reset_token_123", "new_password": "newpassword123"}
        request = ResetPasswordRequest(**data)
        assert request.token == "reset_token_123"
        assert request.new_password == "newpassword123"

    def test_check_username_request(self):
        """测试检查用户名请求模型"""
        data = {"username": "testuser"}
        request = CheckUsernameRequest(**data)
        assert request.username == "testuser"


class TestResponseModels:
    """测试响应模型"""

    def test_user_info_models(self):
        """测试用户信息模型"""
        # UserInfo
        data = {
            "username": "testuser",
            "daily_translation_limit": 10,
            "daily_ai_detection_limit": 5,
            "daily_translation_used": 2,
            "daily_ai_detection_used": 1,
            "is_admin": False,
            "is_active": True,
        }
        user_info = UserInfo(**data)
        assert user_info.username == "testuser"
        assert user_info.daily_translation_limit == 10
        assert user_info.daily_ai_detection_used == 1
        assert user_info.is_admin is False

        # UserInfoWithEmail
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "email_verified": True,
            "daily_translation_limit": 10,
            "daily_ai_detection_limit": 5,
            "daily_translation_used": 2,
            "daily_ai_detection_used": 1,
            "is_admin": False,
            "is_active": True,
        }
        user_info = UserInfoWithEmail(**data)
        assert user_info.email == "test@example.com"
        assert user_info.email_verified is True
        assert user_info.created_at is None  # 默认值

    def test_verification_response(self):
        """测试验证响应模型"""
        data = {"success": True, "message": "验证码已发送"}
        response = VerificationResponse(**data)
        assert response.success is True
        assert response.message == "验证码已发送"
        assert response.verification_token is None

        # 带令牌的响应
        data = {
            "success": True,
            "message": "邮箱验证成功",
            "verification_token": "token_123",
        }
        response = VerificationResponse(**data)
        assert response.verification_token == "token_123"

    def test_check_response_models(self):
        """测试检查响应模型"""
        # 检查用户名响应
        data = {"available": True, "message": "用户名可用"}
        response = CheckUsernameResponse(**data)
        assert response.available is True
        assert response.message == "用户名可用"

        # 检查邮箱响应
        data = {"available": False, "message": "邮箱已被注册"}
        response = CheckEmailResponse(**data)
        assert response.available is False

    def test_password_reset_response(self):
        """测试密码重置响应模型"""
        data = {"success": True, "message": "重置邮件已发送"}
        response = PasswordResetResponse(**data)
        assert response.success is True
        assert response.username is None

        # 带用户名的响应
        data = {"success": True, "message": "密码重置成功", "username": "testuser"}
        response = PasswordResetResponse(**data)
        assert response.username == "testuser"

    def test_error_response(self):
        """测试错误响应模型"""
        data = {"error_code": "AUTH_FAILED", "message": "认证失败"}
        response = ErrorResponse(**data)
        assert response.success is False  # 默认值
        assert response.error_code == "AUTH_FAILED"
        assert response.message == "认证失败"
        assert response.details is None

        # 带详细信息的错误响应
        data = {
            "error_code": "VALIDATION_ERROR",
            "message": "验证失败",
            "details": {"field": "username", "error": "不能为空"},
        }
        response = ErrorResponse(**data)
        assert response.details == {"field": "username", "error": "不能为空"}

    def test_success_response(self):
        """测试成功响应模型"""
        data = {"message": "操作成功"}
        response = SuccessResponse(**data)
        assert response.success is True  # 默认值
        assert response.message == "操作成功"
        assert response.data is None

        # 带数据的成功响应
        data = {
            "message": "用户信息",
            "data": {"username": "testuser", "email": "test@example.com"},
        }
        response = SuccessResponse(**data)
        assert response.data == {"username": "testuser", "email": "test@example.com"}

    def test_text_processing_responses(self):
        """测试文本处理响应模型"""
        # 文本检查响应
        data = {
            "original_text": "原始文本",
            "processed_text": "处理后的文本",
            "annotations": [{"type": "grammar", "message": "语法错误"}],
        }
        response = CheckTextResponse(**data)
        assert response.original_text == "原始文本"
        assert len(response.annotations) == 1

        # 文本润色响应
        data = {
            "original_text": "Original text",
            "refined_text": "Refined text",
            "changes": [{"type": "grammar", "description": "Improved grammar"}],
        }
        response = RefineTextResponse(**data)
        assert response.original_text == "Original text"
        assert response.refined_text == "Refined text"

        # AI检测响应
        data = {
            "text": "检测文本",
            "ai_probability": 0.75,
            "is_ai_generated": True,
            "details": {"confidence": 0.8, "model": "GPT-4"},
        }
        response = AIDetectionResponse(**data)
        assert response.text == "检测文本"
        assert response.ai_probability == 0.75
        assert response.is_ai_generated is True
        assert response.details == {"confidence": 0.8, "model": "GPT-4"}

    def test_usage_stats_and_directive(self):
        """测试使用统计和指令模型"""
        # 使用统计
        data = {
            "total_users": 100,
            "active_users": 50,
            "total_translations": 1000,
            "recent_translations": [{"user": "testuser", "count": 10}],
        }
        stats = UsageStats(**data)
        assert stats.total_users == 100
        assert len(stats.recent_translations) == 1

        # 翻译指令
        data = {
            "id": "directive_1",
            "name": "学术风格",
            "description": "学术论文翻译风格",
            "content": "请使用学术风格翻译",
            "is_active": True,
        }
        directive = TranslationDirective(**data)
        assert directive.id == "directive_1"
        assert directive.name == "学术风格"
        assert directive.is_active is True
        assert directive.created_at is None  # 默认值


class TestAIChatModels:
    """测试AI聊天模型"""

    def test_ai_chat_message(self):
        """测试AI聊天消息模型"""
        data = {"role": "user", "content": "你好"}
        message = AIChatMessage(**data)
        assert message.role == "user"
        assert message.content == "你好"

        # 无效角色
        with pytest.raises(ValidationError):
            AIChatMessage(role="invalid", content="消息")

    def test_ai_chat_request(self):
        """测试AI聊天请求模型"""
        messages = [{"role": "user", "content": "你好"}]
        data = {"messages": messages}
        request = AIChatRequest(**data)
        assert len(request.messages) == 1
        assert request.messages[0].role == "user"
        assert request.session_id is None

        # 带会话ID
        data = {"messages": messages, "session_id": "session_123"}
        request = AIChatRequest(**data)
        assert request.session_id == "session_123"

    def test_ai_chat_response(self):
        """测试AI聊天响应模型"""
        data = {
            "success": True,
            "text": "你好，我是AI助手",
            "model_used": "gemini-flash",
        }
        response = AIChatResponse(**data)
        assert response.success is True
        assert response.text == "你好，我是AI助手"
        assert response.model_used == "gemini-flash"
        assert response.error is None
        assert response.session_id is None

        # 带错误的响应
        data = {"success": False, "text": "", "model_used": "", "error": "API错误"}
        response = AIChatResponse(**data)
        assert response.success is False
        assert response.error == "API错误"


class TestStreamModels:
    """测试流式模型"""

    def test_stream_translation_models(self):
        """测试流式翻译模型"""
        # 请求
        data = {
            "text": "测试文本",
            "operation": "translate_us",
            "version": "professional",
        }
        request = StreamTranslationRequest(**data)
        assert request.text == "测试文本"
        assert request.operation == "translate_us"

        # 数据块
        data = {"type": "chunk", "text": "部分翻译", "chunk_index": 0}
        chunk = StreamTranslationChunk(**data)
        assert chunk.type == "chunk"
        assert chunk.text == "部分翻译"
        assert chunk.chunk_index == 0
        assert chunk.error is None

        # 错误块
        data = {"type": "error", "error": "翻译失败", "error_type": "api_error"}
        chunk = StreamTranslationChunk(**data)
        assert chunk.type == "error"
        assert chunk.error == "翻译失败"

    def test_stream_refine_models(self):
        """测试流式文本修改模型"""
        # 请求
        data = {"text": "Test text", "directives": ["improve grammar"]}
        request = StreamRefineTextRequest(**data)
        assert request.text == "Test text"
        assert request.directives == ["improve grammar"]

        # 数据块
        data = {"type": "sentence", "text": "Improved sentence", "index": 0, "total": 5}
        chunk = StreamRefineTextChunk(**data)
        assert chunk.type == "sentence"
        assert chunk.index == 0
        assert chunk.total == 5


class TestModelValidationEdgeCases:
    """测试模型验证边界情况"""

    @pytest.mark.parametrize(
        "field,value,should_pass",
        [
            ("username", "a" * 100, True),  # 长用户名
            ("username", "", False),  # 空用户名
            ("password", "short", True),  # 短密码（允许，由业务逻辑验证）
            ("email", "invalid-email", True),  # 无效邮箱格式（允许，由业务逻辑验证）
            ("email", "valid@example.com", True),
            ("daily_translation_limit", -1, True),  # 负限制（允许，由业务逻辑验证）
            ("daily_translation_limit", 0, True),
            ("daily_translation_limit", 1000, True),
            ("ai_probability", 1.5, False),  # 超出范围的概率
            ("ai_probability", -0.1, False),
            ("ai_probability", 0.5, True),
            (
                "is_ai_generated",
                "true",
                True,
            ),  # 字符串"true"会被Pydantic自动转换为布尔值True
            ("is_ai_generated", True, True),
        ],
    )
    def test_field_validation(self, field, value, should_pass):
        """测试字段验证"""
        # 根据字段类型选择适当的模型
        if field in ["username", "password"]:
            model_class = LoginRequest
            data = {"username": "test", "password": "test"}
            data[field] = value
        elif field == "email":
            model_class = SendVerificationRequest
            data = {"email": value}
        elif field == "daily_translation_limit":
            model_class = AddUserRequest
            data = {"username": "test", "password": "test"}
            data[field] = value
        elif field in ["ai_probability", "is_ai_generated"]:
            model_class = AIDetectionResponse
            data = {
                "text": "test",
                "ai_probability": 0.5,
                "is_ai_generated": False,
                "details": {},
            }
            data[field] = value
        else:
            return

        try:
            instance = model_class(**data)
            if should_pass:
                # 特殊处理：is_ai_generated字段的字符串"true"会被转换为True
                if field == "is_ai_generated" and value == "true":
                    assert getattr(instance, field) is True
                else:
                    assert getattr(instance, field) == value
            else:
                pytest.fail(f"验证应失败但通过了: {field}={value}")
        except ValidationError:
            if should_pass:
                pytest.fail(f"验证应通过但失败了: {field}={value}")
