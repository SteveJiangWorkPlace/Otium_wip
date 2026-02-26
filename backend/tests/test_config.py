"""
配置模块测试

测试config.py中的Settings类和辅助函数。
"""

import os
from unittest.mock import patch

import pytest

from config import Settings, is_expired, setup_logging


class TestSettings:
    """测试Settings类"""

    def test_default_values(self):
        """测试默认值"""
        settings = Settings()

        # 应用信息
        assert settings.APP_NAME == "Otium API"
        assert settings.APP_VERSION == "1.0.0"

        # 服务器配置
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8000

        # 环境配置
        assert settings.ENVIRONMENT in ["development", "testing", "production"]
        assert isinstance(settings.DEBUG, bool)

    def test_environment_variables(self):
        """测试环境变量覆盖"""
        with patch.dict(
            os.environ,
            {
                "PORT": "9000",
                "DEBUG": "false",
                "ENVIRONMENT": "production",
                "SECRET_KEY": "test_secret_key",
            },
        ):
            settings = Settings()

            assert settings.PORT == 9000
            assert settings.DEBUG is False
            assert settings.ENVIRONMENT == "production"
            assert settings.SECRET_KEY == "test_secret_key"

    def test_cors_origins_parsing(self):
        """测试CORS来源解析"""
        # 测试逗号分隔的列表
        with patch.dict(
            os.environ,
            {
                "CORS_ORIGINS": "http://localhost:3000,http://localhost:8000,https://example.com",
            },
        ):
            settings = Settings()
            assert "http://localhost:3000" in settings.CORS_ORIGINS
            assert "http://localhost:8000" in settings.CORS_ORIGINS
            assert "https://example.com" in settings.CORS_ORIGINS

        # 测试带空格和引号的列表
        with patch.dict(
            os.environ,
            {
                "CORS_ORIGINS": " \"http://test.com\", 'http://test2.com', http://test3.com ",
            },
        ):
            settings = Settings()
            assert "http://test.com" in settings.CORS_ORIGINS
            assert "http://test2.com" in settings.CORS_ORIGINS
            assert "http://test3.com" in settings.CORS_ORIGINS

        # 测试空环境变量（使用默认值）
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert len(settings.CORS_ORIGINS) > 0
            assert "http://localhost:3000" in settings.CORS_ORIGINS

    def test_api_keys_validation(self):
        """测试API密钥验证"""
        # 测试所有API密钥都设置的情况
        with patch.dict(
            os.environ,
            {
                "GEMINI_API_KEY": "test_gemini_key",
                "GPTZERO_API_KEY": "test_gptzero_key",
                "MANUS_API_KEY": "test_manus_key",
                "RESEND_API_KEY": "test_resend_key",
            },
        ):
            Settings()
            # 不应有警告（需要在日志中验证）

        # 测试API密钥缺失的情况
        with patch.dict(os.environ, {}, clear=True):
            Settings()
            # 应有警告（需要在日志中验证）

    def test_render_platform_detection(self):
        """测试Render平台检测"""
        # 测试非Render环境
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.IS_RENDER is False

        # 测试Render环境
        with patch.dict(os.environ, {"RENDER": "true"}):
            settings = Settings()
            assert settings.IS_RENDER is True
            assert settings.ENVIRONMENT == "production"
            assert settings.DEBUG is False

    def test_security_warnings(self, caplog):
        """测试安全警告"""
        with patch.dict(
            os.environ,
            {
                "SECRET_KEY": "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92",  # 默认密钥
                "ADMIN_PASSWORD": "admin123",  # 默认密码
                "RESEND_FROM": "onboarding@resend.dev",  # 默认发件人
            },
        ):
            Settings()
            # 检查警告日志
            warning_messages = [
                record.message for record in caplog.records if record.levelname == "WARNING"
            ]
            assert any("SECRET_KEY 使用默认值" in msg for msg in warning_messages)
            assert any("管理员密码使用默认值" in msg for msg in warning_messages)
            assert any("RESEND_FROM 使用默认值" in msg for msg in warning_messages)

    def test_database_configuration(self):
        """测试数据库配置"""
        # 测试SQLite默认配置
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.DATABASE_TYPE == "sqlite"
            assert settings.DATABASE_PATH == "./data/otium.db"
            assert settings.DATABASE_URL == ""

        # 测试PostgreSQL配置
        with patch.dict(
            os.environ,
            {
                "DATABASE_TYPE": "postgresql",
                "DATABASE_URL": "postgresql://user:pass@localhost/db",
            },
        ):
            settings = Settings()
            assert settings.DATABASE_TYPE == "postgresql"
            assert settings.DATABASE_URL == "postgresql://user:pass@localhost/db"


class TestHelperFunctions:
    """测试辅助函数"""

    @pytest.mark.parametrize(
        "date_str, expected",
        [
            ("2023-12-31", True),  # 过去日期
            ("2099-12-31", False),  # 未来日期
            ("2026-02-25", False),  # 今天（测试当天）
        ],
    )
    def test_is_expired(self, date_str, expected):
        """测试日期过期检查"""
        result = is_expired(date_str)
        assert result == expected

    def test_is_expired_invalid_format(self, caplog):
        """测试无效日期格式"""
        result = is_expired("invalid-date")
        assert result is False  # 默认返回False
        # 应记录错误
        error_messages = [
            record.message for record in caplog.records if record.levelname == "ERROR"
        ]
        assert any("无法识别的日期格式" in msg for msg in error_messages)

    def test_setup_logging(self):
        """测试日志设置"""
        # 测试正常设置
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG", "LOG_TO_CONSOLE": "true"}):
            setup_logging()
            # 验证日志级别已设置（通过日志输出验证）

        # 测试文件日志
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmpfile:
            log_file = tmpfile.name

        try:
            with patch.dict(os.environ, {"LOG_FILE": log_file}):
                setup_logging()
                # 验证日志文件已创建
                assert os.path.exists(log_file)
        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)


class TestConstants:
    """测试常量定义"""

    def test_shortcut_annotations(self):
        """测试快捷批注命令"""
        from config import SHORTCUT_ANNOTATIONS

        assert isinstance(SHORTCUT_ANNOTATIONS, dict)
        assert len(SHORTCUT_ANNOTATIONS) > 0

        # 检查一些常见命令
        assert "gc" in SHORTCUT_ANNOTATIONS
        assert "sc" in SHORTCUT_ANNOTATIONS
        assert "fc" in SHORTCUT_ANNOTATIONS
        assert "para" in SHORTCUT_ANNOTATIONS

        # 检查值类型
        for key, value in SHORTCUT_ANNOTATIONS.items():
            assert isinstance(key, str)
            assert isinstance(value, str)

    def test_api_constants(self):
        """测试API常量"""
        from config import API_PREFIX, DEFAULT_USER_CONFIG, TEXT_OPERATIONS, VERSION_TYPES

        assert API_PREFIX == "/api"
        assert isinstance(DEFAULT_USER_CONFIG, dict)
        assert isinstance(TEXT_OPERATIONS, dict)
        assert isinstance(VERSION_TYPES, list)

        # 检查文本操作类型
        assert "error_check" in TEXT_OPERATIONS
        assert "translate_us" in TEXT_OPERATIONS
        assert "translate_uk" in TEXT_OPERATIONS

        # 检查版本类型
        assert "professional" in VERSION_TYPES
        assert "standard" in VERSION_TYPES
        assert "basic" in VERSION_TYPES
