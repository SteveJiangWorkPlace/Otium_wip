"""
Tests for config.py.
"""

import os
from datetime import datetime
from unittest.mock import patch

import pytest

from config import Settings, is_expired, setup_logging


class TestSettings:
    def test_default_values(self):
        settings = Settings()

        assert settings.APP_NAME == "Otium API"
        assert settings.APP_VERSION == "1.0.0"
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8000
        assert settings.ENVIRONMENT in ["development", "testing", "production"]
        assert isinstance(settings.DEBUG, bool)

    def test_environment_variables(self):
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

        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert len(settings.CORS_ORIGINS) > 0
            assert "http://localhost:3000" in settings.CORS_ORIGINS

    def test_api_keys_validation(self):
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

        with patch.dict(os.environ, {}, clear=True):
            Settings()

    def test_render_platform_detection(self):
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.IS_RENDER is False

        with patch.dict(os.environ, {"RENDER": "true"}):
            settings = Settings()
            assert settings.IS_RENDER is True
            assert settings.ENVIRONMENT == "production"
            assert settings.DEBUG is False

    def test_security_warnings(self, caplog):
        with patch.dict(
            os.environ,
            {
                "SECRET_KEY": "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92",
                "ADMIN_PASSWORD": "admin123",
                "RESEND_FROM": "onboarding@resend.dev",
            },
        ):
            Settings()
            warning_messages = [
                record.message for record in caplog.records if record.levelname == "WARNING"
            ]
            assert any("SECRET_KEY" in msg for msg in warning_messages)
            assert any("RESEND_FROM" in msg for msg in warning_messages)
            assert len(warning_messages) >= 3

    def test_database_configuration(self):
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.DATABASE_TYPE == "sqlite"
            assert settings.DATABASE_PATH == "./data/otium.db"
            assert settings.DATABASE_URL == ""

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
    @pytest.mark.parametrize(
        "date_str, expected",
        [
            ("2023-12-31", True),
            ("2099-12-31", False),
            (datetime.now().strftime("%Y-%m-%d"), False),
        ],
    )
    def test_is_expired(self, date_str, expected):
        result = is_expired(date_str)
        assert result == expected

    def test_is_expired_invalid_format(self, caplog):
        result = is_expired("invalid-date")
        assert result is False
        error_messages = [
            record.message for record in caplog.records if record.levelname == "ERROR"
        ]
        assert any("invalid-date" in msg for msg in error_messages)

    def test_setup_logging(self):
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG", "LOG_TO_CONSOLE": "true"}):
            setup_logging()

        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmpfile:
            log_file = tmpfile.name

        try:
            with patch.dict(os.environ, {"LOG_FILE": log_file}):
                setup_logging()
                assert os.path.exists(log_file)
        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)


class TestConstants:
    def test_shortcut_annotations(self):
        from config import SHORTCUT_ANNOTATIONS

        assert isinstance(SHORTCUT_ANNOTATIONS, dict)
        assert len(SHORTCUT_ANNOTATIONS) > 0
        assert "gc" in SHORTCUT_ANNOTATIONS
        assert "sc" in SHORTCUT_ANNOTATIONS
        assert "fc" in SHORTCUT_ANNOTATIONS
        assert "para" in SHORTCUT_ANNOTATIONS

        for key, value in SHORTCUT_ANNOTATIONS.items():
            assert isinstance(key, str)
            assert isinstance(value, str)

    def test_api_constants(self):
        from config import API_PREFIX, DEFAULT_USER_CONFIG, TEXT_OPERATIONS, VERSION_TYPES

        assert API_PREFIX == "/api"
        assert isinstance(DEFAULT_USER_CONFIG, dict)
        assert isinstance(TEXT_OPERATIONS, dict)
        assert isinstance(VERSION_TYPES, list)
        assert "error_check" in TEXT_OPERATIONS
        assert "translate_us" in TEXT_OPERATIONS
        assert "translate_uk" in TEXT_OPERATIONS
        assert "professional" in VERSION_TYPES
        assert "standard" in VERSION_TYPES
        assert "basic" in VERSION_TYPES
