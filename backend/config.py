"""
配置管理模块

集中管理所有环境变量、应用配置和常量。
"""

import os
import logging
from typing import List, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


# ==========================================
# 应用配置
# ==========================================

class Settings:
    """应用配置类"""

    # 应用信息
    APP_NAME: str = "Otium API"
    APP_VERSION: str = "1.0.0"

    # 服务器配置
    HOST: str = os.environ.get("HOST", "0.0.0.0")
    PORT: int = int(os.environ.get("PORT", "8000"))

    # CORS配置
    CORS_ORIGINS: List[str] = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:8000,https://your-netlify-app.netlify.app"
    ).split(",")

    # 环境配置
    ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "development")
    DEBUG: bool = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")

    # JWT配置
    SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY") or os.environ.get(
        "SECRET_KEY",
        "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92"
    )
    ALGORITHM: str = os.environ.get("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    ADMIN_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ADMIN_TOKEN_EXPIRE_MINUTES", "1440"))

    # API密钥配置
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    GPTZERO_API_KEY: str = os.environ.get("GPTZERO_API_KEY", "")

    # 用户管理配置
    ADMIN_USERNAME: str = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.environ.get("ADMIN_PASSWORD", "admin123")

    # 文件路径配置
    USAGE_DB_PATH: str = os.environ.get("USAGE_DB_PATH", "usage_data.json")
    DATA_DIR: str = os.environ.get("DATA_DIR", "./data")

    # 数据库配置
    DATABASE_TYPE: str = os.environ.get("DATABASE_TYPE", "sqlite")
    DATABASE_PATH: str = os.environ.get("DATABASE_PATH", "./data/otium.db")
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "")

    # 密码哈希配置
    PASSWORD_HASH_ALGORITHM: str = os.environ.get("PASSWORD_HASH_ALGORITHM", "sha256")

    # 速率限制配置
    RATE_LIMIT_PER_MINUTE: int = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "5"))
    DAILY_TEXT_LIMIT: int = int(os.environ.get("DAILY_TEXT_LIMIT", "1000"))
    DAILY_TRANSLATION_LIMIT: int = int(os.environ.get("DAILY_TRANSLATION_LIMIT", "10"))
    DAILY_AI_DETECTION_LIMIT: int = int(os.environ.get("DAILY_AI_DETECTION_LIMIT", "10"))

    # 日志配置
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO").upper()
    LOG_FILE: Optional[str] = os.environ.get("LOG_FILE")
    LOG_TO_CONSOLE: bool = os.environ.get("LOG_TO_CONSOLE", "True").lower() in ("true", "1", "yes")

    # 功能开关
    ENABLE_AI_DETECTION: bool = os.environ.get("ENABLE_AI_DETECTION", "True").lower() in ("true", "1", "yes")
    ENABLE_TEXT_REFINEMENT: bool = os.environ.get("ENABLE_TEXT_REFINEMENT", "True").lower() in ("true", "1", "yes")
    ENABLE_TRANSLATION_DIRECTIVES: bool = os.environ.get("ENABLE_TRANSLATION_DIRECTIVES", "True").lower() in ("true", "1", "yes")

    # 邮件服务配置
    SMTP_HOST: str = os.environ.get("SMTP_HOST", "smtp.sendgrid.net")
    SMTP_PORT: int = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.environ.get("SMTP_USERNAME", "apikey")
    SMTP_PASSWORD: str = os.environ.get("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.environ.get("SMTP_FROM", "noreply@example.com")
    SMTP_TLS: bool = os.environ.get("SMTP_TLS", "true").lower() in ("true", "1", "yes")
    SMTP_SSL: bool = os.environ.get("SMTP_SSL", "false").lower() in ("true", "1", "yes")

    # 验证码和令牌配置
    VERIFICATION_CODE_TTL: int = int(os.environ.get("VERIFICATION_CODE_TTL", "600"))  # 10分钟
    RESET_TOKEN_TTL: int = int(os.environ.get("RESET_TOKEN_TTL", "86400"))  # 24小时
    MAX_VERIFICATION_ATTEMPTS: int = int(os.environ.get("MAX_VERIFICATION_ATTEMPTS", "3"))
    EMAIL_VERIFICATION_REQUIRED: bool = os.environ.get("EMAIL_VERIFICATION_REQUIRED", "true").lower() in ("true", "1", "yes")

    # 前端URL配置（用于重置密码链接）
    FRONTEND_BASE_URL: str = os.environ.get("FRONTEND_BASE_URL", "http://localhost:3000")

    # Render平台检测
    IS_RENDER: bool = os.environ.get("RENDER", "").lower() == "true"

    def __init__(self):
        """初始化配置"""
        # 在Render平台上自动调整配置
        if self.IS_RENDER:
            self._adjust_for_render()

        # 检查安全配置
        self._check_security()

    def _adjust_for_render(self):
        """为Render平台调整配置"""
        self.ENVIRONMENT = "production"
        self.DEBUG = False
        # Render会自动设置PORT变量

    def _check_security(self):
        """检查安全配置"""
        # 检查默认密钥
        DEFAULT_SECRET_KEY = "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92"
        if self.SECRET_KEY == DEFAULT_SECRET_KEY:
            logging.warning(
                "⚠️ SECRET_KEY 使用默认值！在生产环境中请设置 JWT_SECRET_KEY 环境变量。"
            )

        # 检查API密钥
        if not self.GEMINI_API_KEY:
            logging.warning("⚠️ GEMINI_API_KEY 未设置，Gemini相关功能将不可用")

        if not self.GPTZERO_API_KEY:
            logging.warning("⚠️ GPTZERO_API_KEY 未设置，AI检测功能将不可用")

        # 检查管理员密码
        if self.ADMIN_PASSWORD == "admin123":
            logging.warning("⚠️ 管理员密码使用默认值，请在生产环境中修改")

        # 检查数据库配置
        if self.DATABASE_TYPE == "postgresql" and not self.DATABASE_URL:
            logging.warning("⚠️ 使用PostgreSQL但未设置DATABASE_URL环境变量")

        # 检查邮件配置
        if not self.SMTP_PASSWORD:
            logging.warning("⚠️ SMTP_PASSWORD 未设置，邮件发送功能将不可用")
        if self.SMTP_FROM == "noreply@example.com":
            logging.warning("⚠️ SMTP_FROM 使用默认值，请设置为有效的发件人邮箱")


# 全局配置实例
settings = Settings()


# ==========================================
# 日志配置
# ==========================================

def setup_logging():
    """设置日志配置"""
    log_level_str = settings.LOG_LEVEL
    log_level = getattr(logging, log_level_str, logging.INFO)

    # 配置日志处理器
    handlers = []

    # 控制台处理器
    if settings.LOG_TO_CONSOLE:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        handlers.append(console_handler)

    # 文件处理器
    if settings.LOG_FILE:
        file_handler = logging.FileHandler(settings.LOG_FILE)
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)

    # 基础配置
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers if handlers else None
    )

    logging.info(f"日志级别设置为: {log_level_str} ({log_level})")
    logging.info(f"应用环境: {settings.ENVIRONMENT}")
    logging.info(f"调试模式: {settings.DEBUG}")


# ==========================================
# 辅助函数
# ==========================================

def is_expired(expiry_date_str: str) -> bool:
    """检查日期是否已过期"""
    from datetime import datetime

    try:
        # 尝试标准格式
        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d')
        return expiry_date.date() < datetime.now().date()
    except ValueError:
        try:
            # 尝试其他常见格式
            for fmt in ['%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y', '%m-%d-%Y', '%m/%d/%Y']:
                try:
                    expiry_date = datetime.strptime(expiry_date_str, fmt)
                    return expiry_date.date() < datetime.now().date()
                except ValueError:
                    continue
            # 所有格式都失败了
            logging.error(f"无法识别的日期格式: {expiry_date_str}")
            return False  # 如果无法解析，默认为未过期
        except Exception as e:
            logging.error(f"日期处理错误: {expiry_date_str}, 错误: {e}")
            return False  # 如果出现其他错误，默认为未过期
    except Exception as e:
        logging.error(f"日期处理异常: {expiry_date_str}, 错误: {e}")
        return False  # 如果出现其他异常，默认为未过期


# ==========================================
# 常量定义
# ==========================================

# 快捷批注命令
SHORTCUT_ANNOTATIONS = {
    "gc": "grammar correction",
    "sc": "spelling correction",
    "fc": "formal conversion",
    "ic": "informal conversion",
    "ac": "academic conversion",
    "br": "british conversion",
    "us": "american conversion",
    "ex": "expand text",
    "sh": "shorten text",
    "sy": "synonym replacement",
    "sim": "simplify text",
    "for": "formalize text",
    "inf": "informalize text",
    "para": "paraphrase text",
    "sum": "summarize text",
    "tone": "adjust tone",
    "coh": "improve coherence",
    "flu": "improve fluency"
}

# API端点常量
API_PREFIX = "/api"

# 默认用户配置
DEFAULT_USER_CONFIG = {
    "max_translations": 100,
    "used_translations": 0,
    "expiry_date": "2099-12-31"
}

# 文本处理操作类型
TEXT_OPERATIONS = {
    "error_check": "错误检查",
    "translate_us": "美式英语翻译",
    "translate_uk": "英式英语翻译"
}

# 版本类型
VERSION_TYPES = ["professional", "standard", "basic"]