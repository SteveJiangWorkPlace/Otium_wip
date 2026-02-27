"""
配置管理模块

集中管理所有环境变量、应用配置和常量。
"""

import logging
import os

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


# ==========================================
# 应用配置
# ==========================================


class Settings:
    """应用配置类"""

    def __init__(self):
        """初始化配置"""
        # 应用信息
        self.APP_NAME: str = "Otium API"
        self.APP_VERSION: str = "1.0.0"

        # 服务器配置
        self.HOST: str = os.environ.get("HOST", "0.0.0.0")
        self.PORT: int = int(os.environ.get("PORT", "8000"))

        # CORS配置 - 更健壮地解析环境变量
        self.CORS_ORIGINS: list[str] = self._parse_cors_origins()

        # 环境配置
        self.ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "development")
        self.DEBUG: bool = os.environ.get("DEBUG", "True").lower() in (
            "true",
            "1",
            "yes",
        )

        # JWT配置
        self.SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY") or os.environ.get(
            "SECRET_KEY",
            "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92",
        )
        self.ALGORITHM: str = os.environ.get("ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
            os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )
        self.ADMIN_TOKEN_EXPIRE_MINUTES: int = int(
            os.environ.get("ADMIN_TOKEN_EXPIRE_MINUTES", "1440")
        )

        # API密钥配置
        self.GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
        self.GPTZERO_API_KEY: str = os.environ.get("GPTZERO_API_KEY", "")
        self.MANUS_API_KEY: str = os.environ.get("MANUS_API_KEY", "")

        # 响应大小限制配置
        self.MAX_RESPONSE_SIZE_BYTES: int = int(os.environ.get("MAX_RESPONSE_SIZE_BYTES", "1048576"))  # 默认1MB
        self.CHUNK_SIZE_BYTES: int = int(os.environ.get("CHUNK_SIZE_BYTES", "65536"))  # 默认64KB

        # 用户管理配置
        self.ADMIN_USERNAME: str = os.environ.get("ADMIN_USERNAME", "admin")
        self.ADMIN_PASSWORD: str = os.environ.get("ADMIN_PASSWORD", "admin123")

        # 文件路径配置
        self.USAGE_DB_PATH: str = os.environ.get("USAGE_DB_PATH", "usage_data.json")
        self.DATA_DIR: str = os.environ.get("DATA_DIR", "./data")

        # 数据库配置
        self.DATABASE_TYPE: str = os.environ.get("DATABASE_TYPE", "sqlite")
        self.DATABASE_PATH: str = os.environ.get("DATABASE_PATH", "./data/otium.db")
        self.DATABASE_URL: str = os.environ.get("DATABASE_URL", "")

        # 密码哈希配置
        self.PASSWORD_HASH_ALGORITHM: str = os.environ.get("PASSWORD_HASH_ALGORITHM", "sha256")

        # 速率限制配置
        self.RATE_LIMIT_PER_MINUTE: int = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "5"))
        self.DAILY_TRANSLATION_LIMIT: int = int(os.environ.get("DAILY_TRANSLATION_LIMIT", "3"))
        self.DAILY_AI_DETECTION_LIMIT: int = int(os.environ.get("DAILY_AI_DETECTION_LIMIT", "3"))

        # 日志配置
        self.LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO").upper()
        self.LOG_FILE: str | None = os.environ.get("LOG_FILE")
        self.LOG_TO_CONSOLE: bool = os.environ.get("LOG_TO_CONSOLE", "True").lower() in (
            "true",
            "1",
            "yes",
        )

        # 功能开关
        self.ENABLE_AI_DETECTION: bool = os.environ.get("ENABLE_AI_DETECTION", "True").lower() in (
            "true",
            "1",
            "yes",
        )
        self.ENABLE_TEXT_REFINEMENT: bool = os.environ.get(
            "ENABLE_TEXT_REFINEMENT", "True"
        ).lower() in (
            "true",
            "1",
            "yes",
        )
        self.ENABLE_TRANSLATION_DIRECTIVES: bool = os.environ.get(
            "ENABLE_TRANSLATION_DIRECTIVES", "True"
        ).lower() in ("true", "1", "yes")

        # 邮件服务配置
        self.EMAIL_PROVIDER: str = "resend"  # 本项目仅支持 Resend API

        # Resend API配置（当EMAIL_PROVIDER=resend时使用）
        self.RESEND_API_KEY: str = os.environ.get("RESEND_API_KEY", "")
        self.RESEND_FROM: str = os.environ.get("RESEND_FROM", "onboarding@resend.dev")

        # 验证码和令牌配置
        self.VERIFICATION_CODE_TTL: int = int(
            os.environ.get("VERIFICATION_CODE_TTL", "600")
        )  # 10分钟
        self.RESET_TOKEN_TTL: int = int(os.environ.get("RESET_TOKEN_TTL", "86400"))  # 24小时
        self.MAX_VERIFICATION_ATTEMPTS: int = int(os.environ.get("MAX_VERIFICATION_ATTEMPTS", "3"))
        self.EMAIL_VERIFICATION_REQUIRED: bool = os.environ.get(
            "EMAIL_VERIFICATION_REQUIRED", "true"
        ).lower() in ("true", "1", "yes")

        # 前端URL配置（用于重置密码链接）
        self.FRONTEND_BASE_URL: str = os.environ.get("FRONTEND_BASE_URL", "http://localhost:3000")

        # Render平台检测
        self.IS_RENDER: bool = os.environ.get("RENDER", "").lower() == "true"

        # 在Render平台上自动调整配置
        if self.IS_RENDER:
            self._adjust_for_render()

        # 检查安全配置
        self._check_security()

    def _parse_cors_origins(self) -> list[str]:
        """解析CORS来源环境变量"""
        cors_origins_env = os.environ.get("CORS_ORIGINS", "")
        origins_list: list[str] = []

        if cors_origins_env:
            # 支持逗号分隔的列表，同时清理每个项目
            import re

            # 使用正则表达式分割逗号，同时处理可能的空格
            origins = re.split(r"\s*,\s*", cors_origins_env)
            for origin in origins:
                origin = origin.strip()
                # 去除可能的引号
                if origin.startswith('"') and origin.endswith('"'):
                    origin = origin[1:-1]
                elif origin.startswith("'") and origin.endswith("'"):
                    origin = origin[1:-1]
                if origin:  # 非空字符串
                    origins_list.append(origin)
            logging.info(f"CORS_ORIGINS从环境变量解析: {origins_list}")

        # 如果CORS_ORIGINS为空或未设置，使用默认值
        if not origins_list:
            default_origins = [
                "http://localhost:3000",
                "http://localhost:8000",
                "https://otiumtrans.netlify.app",
            ]
            origins_list = default_origins
            logging.info(f"CORS_ORIGINS使用默认值: {origins_list}")

        return origins_list

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
                "[警告] SECRET_KEY 使用默认值！在生产环境中请设置 JWT_SECRET_KEY 环境变量。"
            )

        # 检查API密钥
        if not self.GEMINI_API_KEY:
            logging.warning("[警告] GEMINI_API_KEY 未设置，Gemini相关功能将不可用")

        if not self.GPTZERO_API_KEY:
            logging.warning("[警告] GPTZERO_API_KEY 未设置，AI检测功能将不可用")

        if not self.MANUS_API_KEY:
            logging.warning("[警告] MANUS_API_KEY 未设置，文献调研功能将不可用")

        # 检查管理员密码
        if self.ADMIN_PASSWORD == "admin123":
            logging.warning("[警告] 管理员密码使用默认值，请在生产环境中修改")

        # 检查数据库配置
        if self.DATABASE_TYPE == "postgresql" and not self.DATABASE_URL:
            logging.warning("[警告] 使用PostgreSQL但未设置DATABASE_URL环境变量")

        # 检查邮件配置（仅支持 Resend API）
        if not self.RESEND_API_KEY:
            logging.warning("[警告] RESEND_API_KEY 未设置，邮件发送功能将不可用")
        if self.RESEND_FROM == "onboarding@resend.dev":
            logging.warning("[警告] RESEND_FROM 使用默认值，请设置为已验证的发件人邮箱")


# 全局配置实例
settings = Settings()


# ==========================================
# 日志配置
# ==========================================


def setup_logging():
    """设置应用日志配置

    根据配置文件设置日志级别和处理器，支持控制台和文件输出。
    日志级别从settings.LOG_LEVEL读取，支持标准日志级别字符串。

    Returns:
        None: 函数直接配置logging模块，无返回值

    Raises:
        ValueError: 当日志级别字符串无效时可能抛出

    Examples:
        >>> setup_logging()
        [INFO] 日志级别设置为: INFO (20)
        [INFO] 应用环境: development
        [INFO] 调试模式: False

    Notes:
        - 日志级别字符串需为logging模块支持的级别（DEBUG、INFO、WARNING、ERROR、CRITICAL）
        - 当LOG_TO_CONSOLE为True时启用控制台输出
        - 当LOG_FILE不为空时启用文件输出，文件编码为UTF-8
    """
    log_level_str = settings.LOG_LEVEL
    log_level = getattr(logging, log_level_str, logging.INFO)

    # 配置日志处理器
    handlers = []

    # 控制台处理器
    if settings.LOG_TO_CONSOLE:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(console_formatter)
        handlers.append(console_handler)

    # 文件处理器
    if settings.LOG_FILE:
        file_handler = logging.FileHandler(settings.LOG_FILE, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)

    # 基础配置
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=handlers if handlers else None,
    )

    logging.info(f"日志级别设置为: {log_level_str} ({log_level})")
    logging.info(f"应用环境: {settings.ENVIRONMENT}")
    logging.info(f"调试模式: {settings.DEBUG}")


# ==========================================
# 辅助函数
# ==========================================


def is_expired(expiry_date_str: str) -> bool:
    """检查给定日期字符串是否已过期

    解析日期字符串并与当前日期比较，支持多种常见日期格式。
    当无法解析日期格式时返回False（默认为未过期）。

    Args:
        expiry_date_str: 日期字符串，支持以下格式：
            - 标准格式: "YYYY-MM-DD"
            - 其他格式: "YYYY/MM/DD", "DD-MM-YYYY", "DD/MM/YYYY",
                      "MM-DD-YYYY", "MM/DD/YYYY"

    Returns:
        bool: True表示日期已过期，False表示未过期或无法解析

    Raises:
        无: 函数内部处理所有异常，不会向外抛出

    Examples:
        >>> is_expired("2026-02-27")
        False  # 如果今天是2026-02-27
        >>> is_expired("2024-12-31")
        True   # 过去日期
        >>> is_expired("invalid-date")
        False  # 无法解析，默认未过期

    Notes:
        - 使用datetime.strptime解析日期，性能开销小
        - 当解析失败时会尝试所有支持的格式
        - 所有异常都被捕获，避免服务中断
        - 解析失败时会记录错误日志
    """
    from datetime import datetime

    try:
        # 尝试标准格式
        expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d")
        return expiry_date.date() < datetime.now().date()
    except ValueError:
        try:
            # 尝试其他常见格式
            for fmt in ["%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%m-%d-%Y", "%m/%d/%Y"]:
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
    "flu": "improve fluency",
}

# API端点常量
API_PREFIX = "/api"

# 默认用户配置
DEFAULT_USER_CONFIG = {
    "max_translations": 100,
    "used_translations": 0,
    "expiry_date": "2099-12-31",
}

# 文本处理操作类型
TEXT_OPERATIONS = {
    "error_check": "错误检查",
    "translate_us": "美式英语翻译",
    "translate_uk": "英式英语翻译",
}

# 版本类型
VERSION_TYPES = ["professional", "standard", "basic"]
