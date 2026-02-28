"""
文件名称：main.py
功能描述：FastAPI主应用文件，包含所有API路由定义和核心业务逻辑
创建时间：2026-02-27
作者：项目团队
版本：1.0.0
"""

import hashlib
import json
import logging
import os
import sys
import time
import warnings

from pydantic.warnings import ArbitraryTypeWarning

warnings.filterwarnings("ignore", category=ArbitraryTypeWarning)

# 设置控制台编码环境变量
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

# Windows控制台编码修复 - 确保UTF-8编码
if sys.platform == "win32":
    try:
        # 重新配置标准流使用UTF-8编码
        sys.stdout = open(
            sys.stdout.fileno(),
            mode="w",
            encoding="utf-8",
            errors="replace",
            buffering=1,
        )
        sys.stderr = open(
            sys.stderr.fileno(),
            mode="w",
            encoding="utf-8",
            errors="replace",
            buffering=1,
        )
    except Exception:
        pass  # 如果失败，继续使用默认编码

# 配置logging使用UTF-8编码并过滤非ASCII字符

logging.basicConfig(encoding="utf-8")
# 为所有处理器设置errors='replace'，避免编码错误
for handler in logging.getLogger().handlers:
    if hasattr(handler, "stream") and hasattr(handler.stream, "encoding"):
        # 确保处理器使用UTF-8编码
        pass


# 添加自定义过滤器，替换非ASCII字符
class ASCIIFilter(logging.Filter):
    """日志过滤器，确保日志输出只包含ASCII字符

    在Windows环境下，控制台编码可能不是UTF-8，这会导致非ASCII字符显示乱码。
    此过滤器将所有非ASCII字符替换为'?'，确保日志输出在Windows命令行中正常显示。
    """
    def filter(self, record):
        """过滤日志记录，替换非ASCII字符

        Args:
            record (logging.LogRecord): 日志记录对象

        Returns:
            bool: 总是返回True，表示记录应该被处理
        """
        if isinstance(record.msg, str):
            # 替换非ASCII字符为'?'
            record.msg = record.msg.encode("ascii", errors="replace").decode("ascii")
        elif isinstance(record.args, tuple):
            # 处理格式化参数中的字符串
            new_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    new_args.append(arg.encode("ascii", errors="replace").decode("ascii"))
                else:
                    new_args.append(arg)
            record.args = tuple(new_args)
        return True


# 将过滤器添加到根日志记录器
logging.getLogger().addFilter(ASCIIFilter())

# 已提前导入并配置ArbitraryTypeWarning警告过滤
from datetime import datetime  # noqa: E402

# 这些异常现在由 google.genai.errors 提供
from dotenv import load_dotenv  # noqa: E402
from fastapi import Depends, FastAPI, HTTPException, Request, status  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.middleware.gzip import GZipMiddleware  # noqa: E402
from fastapi.responses import StreamingResponse  # noqa: E402
from fastapi.security import (  # noqa: E402
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
)

# 导入类型用于类型提示
from jose import jwt  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

# 导入自定义模块
from api_services import (  # noqa: E402
    chat_with_gemini,
    chat_with_manus,
    check_gptzero,
    extract_annotations_with_context,
    generate_gemini_content_stream,
    generate_gemini_content_with_fallback,
    generate_safe_hash_for_cache,
)
from config import settings, setup_logging  # noqa: E402
from exceptions import api_error_handler  # noqa: E402
from models.database import get_db, get_session_local, init_database, User  # noqa: E402
from prompts import (  # noqa: E402
    SHORTCUT_ANNOTATIONS,
    build_academic_translate_prompt,
    build_english_refine_prompt,
    build_error_check_prompt,
    build_literature_research_prompt,
)
from schemas import (  # noqa: E402
    AddUserRequest,
    AdminLoginRequest,
    AIChatRequest,
    AIChatResponse,
    AIDetectionRequest,
    BackgroundTaskResponse,
    CheckEmailResponse,
    CheckTextRequest,
    CheckUsernameResponse,
    ErrorResponse,
    LoginRequest,
    PasswordResetRequest,
    PasswordResetResponse,
    RefineTextRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SendVerificationRequest,
    StreamRefineTextChunk,
    StreamRefineTextRequest,
    StreamTranslationChunk,
    StreamTranslationRequest,
    TaskPollRequest,
    TaskStatusResponse,
    UpdateUserRequest,
    VerificationResponse,
    VerifyEmailRequest,
)
from services.email_service import email_service  # noqa: E402
from services.verification_service import verification_service  # noqa: E402
from user_services.user_service import UserService  # noqa: E402
from utils import CacheManager, RateLimiter, TextValidator  # noqa: E402

# 后台任务服务
from background_task_service import get_background_task_service  # noqa: E402

# 加载环境变量
load_dotenv()


def run_migrations_if_needed():
    """运行数据库迁移（如果可用）"""
    logging.info("开始检查数据库迁移...")

    try:
        from alembic import command
        from alembic.config import Config

        # 获取alembic.ini路径
        alembic_ini_path = os.path.join(os.path.dirname(__file__), "alembic.ini")
        logging.info(f"检查alembic.ini路径: {alembic_ini_path}")
        if not os.path.exists(alembic_ini_path):
            logging.warning(f"alembic.ini未找到: {alembic_ini_path}")
            # 仍然尝试确保email列存在
            ensure_email_column_exists()
            return

        logging.info(f"alembic.ini文件存在，大小: {os.path.getsize(alembic_ini_path)} bytes")

        # 创建配置
        alembic_cfg = Config(alembic_ini_path)
        logging.info("Alembic配置创建成功")

        # 运行迁移到最新版本
        logging.info("运行数据库迁移...")
        command.upgrade(alembic_cfg, "head")
        logging.info("数据库迁移完成")
        return  # 迁移成功，不需要运行后备方案

    except ImportError as e:
        logging.warning(f"alembic未安装，跳过迁移: {e}")
        logging.info("运行email列检查后备方案...")
        ensure_email_column_exists()
    except Exception as e:
        logging.error(f"数据库迁移失败: {e}", exc_info=True)
        logging.warning("迁移失败，应用将继续启动")
        logging.info("运行email列检查后备方案...")
        ensure_email_column_exists()


def ensure_email_column_exists():
    """确保users表有email列（迁移失败时的后备方案）"""
    logging.info("开始检查users表email列...")
    try:
        from sqlalchemy import inspect, text

        from models.database import get_engine

        engine = get_engine()
        logging.info(f"获取数据库引擎: {engine.url}")
        inspector = inspect(engine)

        # 检查users表是否存在
        table_names = inspector.get_table_names()
        logging.info(f"数据库中的表: {table_names}")

        if "users" not in table_names:
            logging.warning("users表不存在，可能尚未创建")
            return

        # 检查users表是否存在email列
        columns = inspector.get_columns("users")
        column_names = [col["name"] for col in columns]
        logging.info(f"users表的列: {column_names}")

        if "email" in column_names:
            logging.info("email列已存在")
            return

        logging.warning("users表缺少email列，尝试添加...")

        # 根据数据库类型执行ALTER TABLE
        from config import settings

        logging.info(f"数据库类型: {settings.DATABASE_TYPE}")

        if settings.DATABASE_TYPE == "postgresql":
            # PostgreSQL
            logging.info("为PostgreSQL添加email列...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(255)"))
                conn.execute(
                    text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT false")
                )
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_email ON users(email)"))
                conn.commit()
                logging.info("PostgreSQL ALTER TABLE执行成功")
        else:
            # SQLite
            logging.info("为SQLite添加email列...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(255)"))
                conn.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0"))
                conn.execute(text("CREATE INDEX ix_users_email ON users(email)"))
                conn.commit()
                logging.info("SQLite ALTER TABLE执行成功")

        logging.info("成功添加email列和email_verified列")
    except Exception as e:
        logging.error(f"添加email列失败: {e}", exc_info=True)
        # 不抛出异常，应用继续运行


# 日志配置
setup_logging()

logger = logging.getLogger(__name__)


app = FastAPI(title="Just Trans API", version="1.0.0")

# 在应用初始化时添加环境变量检查日志
logging.info("应用启动，环境变量检查:")
logging.info(f"ADMIN_USERNAME 是否设置: {bool(os.environ.get('ADMIN_USERNAME'))}")
logging.info(f"ADMIN_PASSWORD 是否设置: {bool(os.environ.get('ADMIN_PASSWORD'))}")
logging.info(f"ADMIN_USERNAME 值: {os.environ.get('ADMIN_USERNAME', 'admin')}")
logging.info(f"ADMIN_PASSWORD 长度: {len(os.environ.get('ADMIN_PASSWORD', 'admin123'))}")

# CORS配置
logging.info(f"CORS环境变量CORS_ORIGINS: {os.environ.get('CORS_ORIGINS', '未设置')}")
logging.info(f"settings.CORS_ORIGINS值: {settings.CORS_ORIGINS}")

# 硬编码允许的源列表，确保前端URL被允许
hardcoded_origins = [
    "https://otiumtrans.netlify.app",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:3001",
    "http://localhost:8001",
]

# 合并settings.CORS_ORIGINS和硬编码源
all_allowed_origins = list(set(hardcoded_origins + settings.CORS_ORIGINS))
logging.info(f"合并后的允许源列表: {all_allowed_origins}")
logging.info(
    f"前端URL 'https://otiumtrans.netlify.app' 在允许源中: {'https://otiumtrans.netlify.app' in all_allowed_origins}"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=all_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加Gzip压缩中间件，减少响应体大小
app.add_middleware(GZipMiddleware, minimum_size=1000)  # 只压缩大于1000字节的响应


# 添加请求日志中间件，记录请求处理时间和状态
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # 记录请求开始
    logging.info(f"请求开始: {request.method} {request.url.path}")

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # 记录请求完成信息
        logging.info(
            f"请求完成: {request.method} {request.url.path} - "
            f"状态码: {response.status_code} - "
            f"处理时间: {process_time:.3f}秒"
        )

        # 如果处理时间超过5秒，记录警告
        if process_time > 5:
            logging.warning(
                f"请求处理时间过长: {process_time:.3f}秒 - "
                f"{request.method} {request.url.path}"
            )

        return response

    except Exception as e:
        process_time = time.time() - start_time
        logging.error(
            f"请求异常: {request.method} {request.url.path} - "
            f"异常: {type(e).__name__}: {str(e)} - "
            f"处理时间: {process_time:.3f}秒"
        )
        # 重新抛出异常，让应用错误处理器处理
        raise


# 添加UTF-8编码中间件，确保所有JSON响应使用UTF-8字符集
@app.middleware("http")
async def add_charset_to_json_response(request: Request, call_next):
    response = await call_next(request)
    content_type = response.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        # 确保字符集为UTF-8
        if "charset=" not in content_type:
            response.headers["content-type"] = "application/json; charset=utf-8"
    return response


security = HTTPBearer()

# ==========================================
# 数据模型
# ==========================================


# 定义 OAuth2 方案，指定获取 Token 的地址（虽然我们现在是手动验证，但定义是必须的）
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# JWT 配置
# 优先从JWT_SECRET_KEY环境变量读取，其次从SECRET_KEY读取，最后使用默认值（向后兼容）
SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or os.environ.get(
    "SECRET_KEY", "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92"
)
ALGORITHM = "HS256"

# 检查SECRET_KEY是否为默认值，如果是则记录警告
DEFAULT_SECRET_KEY = "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92"
if SECRET_KEY == DEFAULT_SECRET_KEY:
    logging.warning(
        "[警告] SECRET_KEY使用的是默认值！在生产环境中应设置JWT_SECRET_KEY或SECRET_KEY环境变量来增强安全性"
    )

# ==========================================
# 统一错误响应模型（已从schemas.py导入）
# ==========================================

# ErrorResponse类已从schemas.py导入

# ==========================================
# 全局实例
# ==========================================

# Initialize database schema
try:
    if settings.DATABASE_TYPE == "postgresql":
        # Production path: rely on Alembic only to avoid duplicate CREATE TABLE.
        logging.info("PostgreSQL detected, running Alembic migrations only")
        run_migrations_if_needed()
    else:
        # Local SQLite path: keep lightweight auto-create behavior.
        init_database()
        logging.info("SQLite schema initialized via create_all")
except Exception as e:
    logging.error(f"Database initialization failed: {e}")
    logging.warning("App will continue startup with limited database functionality")

# 用户服务（使用数据库存储）
try:
    user_service = UserService()
except Exception as e:
    logging.error(f"用户服务初始化失败: {e}")
    # 创建一个简单的用户服务回退
    from user_services.user_service import UserService

    user_service = UserService()
    logging.warning("使用回退用户服务，功能可能受限")
# 从环境变量读取速率限制配置，默认为每分钟5次
rate_limit_max_calls = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "5"))
rate_limiter = RateLimiter(max_calls=rate_limit_max_calls, time_window=60)
logging.info(f"速率限制配置: 每分钟{rate_limit_max_calls}次调用")
gemini_cache = CacheManager(ttl=3600, max_entries=100)
gptzero_cache = CacheManager(ttl=3600, max_entries=100)

# 配置 API Keys（优先使用环境变量，其次使用请求头中的用户输入）
# GEMINI_API_KEY 和 GPTZERO_API_KEY 现在通过环境变量或请求头动态获取
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# 注意：API密钥现在优先使用环境变量，如果环境变量未设置则使用请求头中的用户输入
logger.info("API密钥配置：优先使用环境变量，其次使用请求头中的用户输入")


# ==========================================
# 认证依赖
# ==========================================


# 1. 先在 get_current_user 函数外面定义这个"无敌类"
class UserObject(dict):
    """特殊的字典类，支持属性式访问

    继承自dict，同时允许通过属性语法访问字典键值。
    主要用于调试和测试场景，提供更友好的API。
    """
    def __getattr__(self, name):
        """通过属性语法获取字典值

        Args:
            name (str): 属性名，对应字典的键

        Returns:
            Any: 字典中对应键的值，如果键不存在则返回None
        """
        return self.get(name)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    # 2. 调试 Token 逻辑
    if token == "debug_token_123":
        # 返回这个既是字典又是对象的玩意儿
        return UserObject(username=ADMIN_USERNAME, role="admin")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无有效的令牌",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception

        # 从 JWT 获取角色，如果没有则默认为普通用户
        role = payload.get("role", "user")

        return UserObject(username=username, role=role)
    except Exception as e:
        logging.error(f"Token 验证失败: {str(e)}", exc_info=True)
        raise credentials_exception from e


# ==========================================
# API 路由
# ==========================================


@app.post("/api/login")
# @api_error_handler
async def login(data: LoginRequest):
    logging.info(f"登录尝试: 用户名 = {data.username}")

    # 首先检查是否是管理员（基于环境变量）
    if data.username == ADMIN_USERNAME and data.password == ADMIN_PASSWORD:
        logging.info("管理员登录成功")
        # 创建JWT令牌，包含角色信息
        token_data = {"sub": data.username, "role": "admin"}
        access_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        # 获取管理员用户信息
        user_info = user_service.get_user_info(data.username)
        if not user_info:
            # 创建默认的管理员用户信息
            user_info = {
                "username": data.username,
                "role": "admin",
                "expiry_date": "2099-12-31",
                "max_translations": 99999,  # 管理员有非常大的翻译次数限制
                "used_translations": 0,
                "remaining_translations": 99999,
                "is_admin": True,
                "is_active": True,
            }
        else:
            # 确保角色信息正确
            user_info["role"] = "admin"

        return {
            "success": True,
            "token": access_token,
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_info,
            "message": "",
        }

    # 如果不是管理员，检查是否是允许的普通用户
    allowed, message = user_service.authenticate_user(data.username, data.password)
    if allowed:
        logging.info(f"用户 {data.username} 登录成功")

        # 创建JWT令牌，普通用户角色
        token_data = {"sub": data.username, "role": "user"}
        access_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        # 获取完整的用户信息
        user_info = user_service.get_user_info(data.username)
        if not user_info:
            # 如果获取失败，创建基本用户信息
            user_info = {
                "username": data.username,
                "role": "user",
                "expiry_date": "2099-12-31",
                "max_translations": 100,
                "used_translations": 0,
                "remaining_translations": 100,
                "is_admin": False,
                "is_active": True,
            }
        else:
            # 添加角色信息到用户信息
            user_info["role"] = "user"

        return {
            "success": True,
            "token": access_token,
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_info,
            "message": "",
        }
    else:
        logging.error(f"登录失败: {message}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error_code="AUTHENTICATION_FAILED",
                message="用户名或密码错误",
                details={"username": data.username},
            ).dict(),
        )


# ==========================================
# 用户注册和密码重置API
# ==========================================


@app.post("/api/register/send-verification")
@api_error_handler
async def send_verification_code(request: SendVerificationRequest):
    """发送邮箱验证码

    用于注册流程中的邮箱验证
    """
    logger.info(f"发送验证码请求: {request.email}")

    # 检查邮箱格式
    if "@" not in request.email or "." not in request.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="INVALID_EMAIL",
                message="邮箱格式不正确",
                details={"email": request.email},
            ).dict(),
        )

    # 检查速率限制
    if verification_service.is_rate_limited(request.email, "verify"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=ErrorResponse(
                error_code="RATE_LIMIT_EXCEEDED",
                message="验证码发送过于频繁，请稍后再试",
                details={"email": request.email},
            ).dict(),
        )

    # 检查邮箱是否已被注册
    user_info = user_service.get_user_by_email(request.email)
    if user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="EMAIL_ALREADY_REGISTERED",
                message="该邮箱已被注册",
                details={"email": request.email},
            ).dict(),
        )

    # 生成验证码
    verification_code = verification_service.generate_code()

    # 存储验证码到缓存
    verification_service.store_verification_code(request.email, verification_code)

    # 发送邮件
    email_sent = email_service.send_verification_code(request.email, verification_code)

    if not email_sent:
        # 邮件发送失败，但仍然返回成功（不暴露内部错误）
        # 在实际生产环境中，可能需要记录错误并提供更详细的错误信息
        logger.error(f"验证码邮件发送失败: {request.email}")
        # 仍然返回成功，但提示用户检查邮箱或联系管理员
        return VerificationResponse(
            success=True, message="验证码已生成，如果未收到邮件请检查邮箱或联系管理员"
        )

    logger.info(f"验证码发送成功: {request.email}")
    return VerificationResponse(success=True, message="验证码已发送到您的邮箱，请查收")


@app.post("/api/register/verify-email")
@api_error_handler
async def verify_email_code(request: VerifyEmailRequest):
    """验证邮箱验证码

    验证成功后返回一个临时令牌，用于后续注册步骤
    """
    logger.info(f"验证邮箱验证码: {request.email}")

    # 验证验证码
    is_valid, error_message = verification_service.verify_code(request.email, request.code)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="INVALID_VERIFICATION_CODE",
                message=error_message,
                details={"email": request.email},
            ).dict(),
        )

    # 验证成功，生成临时令牌（用于后续注册）
    verification_token = verification_service.generate_alphanumeric_code(32)
    verification_service.store_verified_token(request.email, verification_token)

    logger.info(f"邮箱验证成功: {request.email}")
    return VerificationResponse(
        success=True, message="邮箱验证成功", verification_token=verification_token
    )


@app.get("/api/register/check-username")
@api_error_handler
async def check_username_available(username: str):
    """检查用户名是否可用

    用于注册时的实时用户名验证
    """
    logger.info(f"检查用户名可用性: {username}")

    is_available, message = user_service.check_username_available(username)

    return CheckUsernameResponse(available=is_available, message=message)


@app.post("/api/register")
@api_error_handler
async def register_user(request: RegisterRequest):
    """注册新用户

    需要提供已验证邮箱的临时令牌
    """
    logger.info(f"注册请求: 用户名={request.username}, 邮箱={request.email}")

    # 验证临时令牌（确保邮箱已验证）
    is_valid, token_email = verification_service.verify_verified_token(request.verification_token)

    if not is_valid or token_email != request.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="INVALID_VERIFICATION_TOKEN",
                message="邮箱验证已过期或无效，请重新验证邮箱",
                details={"email": request.email},
            ).dict(),
        )

    # 验证用户名可用性
    is_available, username_message = user_service.check_username_available(request.username)
    if not is_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="USERNAME_UNAVAILABLE",
                message=username_message,
                details={"username": request.username},
            ).dict(),
        )

    # 验证邮箱可用性
    email_available, email_message = user_service.check_email_available(request.email)
    if not email_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="EMAIL_UNAVAILABLE",
                message=email_message,
                details={"email": request.email},
            ).dict(),
        )

    # 注册用户（邮箱已验证）
    success, error_message = user_service.register_user(
        username=request.username,
        email=request.email,
        password=request.password,
        email_verified=True,  # 邮箱已验证
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="REGISTRATION_FAILED",
                message=error_message,
                details={"username": request.username, "email": request.email},
            ).dict(),
        )

    # 发送欢迎邮件（异步或后台任务）
    try:
        email_service.send_welcome_email(request.email, request.username)
    except Exception as e:
        logger.error(f"发送欢迎邮件失败: {e}")
        # 不中断注册流程，仅记录错误

    # 使用注册的用户自动登录
    allowed, auth_message = user_service.authenticate_user(request.username, request.password)
    if not allowed:
        # 注册成功但自动登录失败，返回成功但需要用户手动登录
        logger.warning(f"注册成功但自动登录失败: {request.username}, {auth_message}")
        return VerificationResponse(success=True, message="注册成功，请使用用户名和密码登录")

    # 创建JWT令牌
    token_data = {"sub": request.username, "role": "user"}
    access_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    # 获取用户信息
    user_info = user_service.get_user_info(request.username)
    if user_info:
        user_info["role"] = "user"

    logger.info(f"用户注册成功并自动登录: {request.username}")
    return {
        "success": True,
        "token": access_token,
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_info,
        "message": "注册成功",
    }


@app.post("/api/password/reset-request")
@api_error_handler
async def request_password_reset(request: PasswordResetRequest):
    """请求密码重置（发送重置链接）"""
    logger.info(f"密码重置请求: {request.email}")

    # 验证邮箱格式
    if "@" not in request.email or "." not in request.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="INVALID_EMAIL",
                message="邮箱格式不正确",
                details={"email": request.email},
            ).dict(),
        )

    # 检查邮箱是否存在
    success, error_message, username = user_service.request_password_reset(request.email)

    if not success:
        # 即使邮箱不存在，也返回成功（防止邮箱枚举攻击）
        logger.info(f"密码重置请求处理: {request.email} - {error_message}")
        return PasswordResetResponse(
            success=True, message="如果邮箱已注册，重置链接将发送到您的邮箱"
        )

    # 生成重置令牌
    reset_token = verification_service.generate_alphanumeric_code(32)
    verification_service.store_reset_token(request.email, reset_token)

    # 发送重置邮件
    email_sent = email_service.send_password_reset_link(request.email, reset_token)

    if not email_sent:
        logger.error(f"密码重置邮件发送失败: {request.email}")
        # 仍然返回成功，不暴露内部错误
        return PasswordResetResponse(
            success=True,
            message="重置请求已处理，如果未收到邮件请检查邮箱或联系管理员",
            username=username,
        )

    logger.info(f"密码重置邮件发送成功: {request.email}")
    return PasswordResetResponse(
        success=True, message="密码重置链接已发送到您的邮箱，请查收", username=username
    )


@app.post("/api/password/reset")
@api_error_handler
async def reset_password(request: ResetPasswordRequest):
    """重置密码（使用重置令牌）"""
    logger.info("重置密码请求")

    # 验证重置令牌
    email = verification_service.consume_reset_token(request.token)

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="INVALID_RESET_TOKEN",
                message="重置链接已过期或无效，请重新申请",
                details={},
            ).dict(),
        )

    # 获取用户名
    user_info = user_service.get_user_by_email(email)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="USER_NOT_FOUND",
                message="用户不存在",
                details={"email": email},
            ).dict(),
        )

    username = user_info["username"]

    # 重置密码
    success, error_message = user_service.reset_password(username, request.new_password)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="PASSWORD_RESET_FAILED",
                message=error_message,
                details={"username": username},
            ).dict(),
        )

    logger.info(f"密码重置成功: {username}")
    return PasswordResetResponse(
        success=True, message="密码重置成功，请使用新密码登录", username=username
    )


@app.get("/api/register/check-email")
@api_error_handler
async def check_email_available(email: str):
    """检查邮箱是否可用

    用于注册时的实时邮箱验证
    """
    logger.info(f"检查邮箱可用性: {email}")

    # 验证邮箱格式
    if "@" not in email or "." not in email:
        return CheckEmailResponse(available=False, message="邮箱格式不正确")

    email_available, message = user_service.check_email_available(email)

    return CheckEmailResponse(available=email_available, message=message)


@app.get("/api/user/info")
@api_error_handler
async def get_user_info(user: UserObject = Depends(get_current_user)):
    """获取用户信息"""
    username = user.username if hasattr(user, "username") else str(user)
    user_info = user_service.get_user_info(username)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error_code="USER_NOT_FOUND",
                message="用户不存在",
                details={"username": username},
            ).dict(),
        )
    return user_info


@app.post("/api/text/check")
@api_error_handler
async def check_text(
    http_request: Request,
    request: CheckTextRequest,
    user: UserObject = Depends(get_current_user),
):
    """文本检查（纠错或翻译）"""

    # 提取用户名
    username = user.username if hasattr(user, "username") else str(user)

    # 速率限制检查
    allowed, wait_time = rate_limiter.is_allowed(username)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=ErrorResponse(
                error_code="RATE_LIMIT_EXCEEDED",
                message=f"请求过于频繁，请等待 {wait_time} 秒",
                details={"wait_time": wait_time, "username": username},
            ).dict(),
        )

    # 文本验证
    is_valid, message = TextValidator.validate_for_gemini(request.text)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="TEXT_VALIDATION_ERROR",
                message=message,
                details={"text_length": len(request.text)},
            ).dict(),
        )

    # 生成缓存键
    cache_key = generate_safe_hash_for_cache(request.text, f"{request.operation}_{request.version}")

    # 检查缓存
    cached_result = gemini_cache.get(cache_key)
    if cached_result:
        logging.info(f"使用缓存结果: {cache_key}")
        return cached_result

    # 根据操作类型构建prompt
    if request.operation == "error_check":
        prompt = build_error_check_prompt(request.text)
    elif request.operation == "translate_us":
        prompt = build_academic_translate_prompt(
            request.text, "US", request.version or "professional"
        )
    elif request.operation == "translate_uk":
        prompt = build_academic_translate_prompt(
            request.text, "UK", request.version or "professional"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="UNSUPPORTED_OPERATION",
                message="不支持的操作类型",
                details={"operation": request.operation},
            ).dict(),
        )

    # 获取API密钥（优先从环境变量获取，其次从请求头获取）
    gemini_api_key = None
    source = "环境变量"

    # 从环境变量获取Gemini API密钥
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    logging.info(f"check_text函数: 从环境变量获取GEMINI_API_KEY: {gemini_api_key is not None}")
    if not gemini_api_key:
        # 从请求头获取
        gemini_api_key = http_request.headers.get("X-Gemini-Api-Key")
        source = "请求头"
        logging.info(f"check_text函数: 从请求头获取X-Gemini-Api-Key: {gemini_api_key is not None}")

    # 调试日志：记录API密钥信息
    if gemini_api_key:
        key_prefix = (
            gemini_api_key[:8] if len(gemini_api_key) > 8 else gemini_api_key[: len(gemini_api_key)]
        )
        logging.info(f"从{source}获取到Gemini API密钥，前缀: {key_prefix}...")
    else:
        logging.warning(f"Gemini API密钥未提供：{source}中未找到")

    # 检查API密钥是否存在
    if not gemini_api_key:
        logging.warning("Gemini API密钥未提供：环境变量和请求头中都未找到")
        # 记录所有请求头用于调试
        all_headers = dict(http_request.headers)
        logging.info(f"所有请求头: {all_headers}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="GEMINI_API_KEY_MISSING",
                message="需要提供Gemini API密钥（可通过环境变量GEMINI_API_KEY或侧边栏输入设置）",
                details={"service": "Gemini"},
            ).dict(),
        )

    # 调用 Gemini API，文本相关功能使用 gemini-2.5-flash 作为主模型
    result = generate_gemini_content_with_fallback(
        prompt,
        api_key=gemini_api_key,
        primary_model="gemini-2.5-flash",
        fallback_model="gemini-2.5-pro",
    )

    if not result["success"]:
        error_message = result.get("error", "处理失败")
        error_type = result.get("error_type", "unknown")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error_code="GEMINI_API_ERROR",
                message=error_message,
                details={"error_type": error_type},
            ).dict(),
        )

    response_data = {
        "success": True,
        "text": result["text"],
        "model_used": result.get("model_used", "unknown"),
    }

    # 如果是翻译操作，记录翻译次数
    if request.operation in ["translate_us", "translate_uk"]:
        try:
            remaining = user_service.record_usage(
                username,
                operation_type=request.operation,
                text_length=len(request.text),
            )
            response_data["remaining_translations"] = remaining
        except ValueError as e:
            # 用户不存在或其他验证错误
            logging.error(f"记录翻译次数失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    error_code="USER_VALIDATION_ERROR",
                    message=str(e),
                    details={"username": username, "exception_type": "ValueError"},
                ).dict(),
            ) from e
        except RuntimeError as e:
            # 数据保存失败
            logging.error(f"保存翻译记录失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error_code="DATA_SAVE_ERROR",
                    message="系统错误：无法保存翻译记录",
                    details={
                        "original_error": str(e),
                        "exception_type": "RuntimeError",
                    },
                ).dict(),
            ) from e
        except Exception as e:
            # 其他未知错误
            logging.error(f"记录翻译次数时发生未知错误: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error_code="INTERNAL_SERVER_ERROR",
                    message="系统内部错误",
                    details={
                        "original_error": str(e),
                        "exception_type": e.__class__.__name__,
                    },
                ).dict(),
            ) from e

    # 缓存结果
    gemini_cache.set(cache_key, response_data)

    return response_data


@app.post("/api/text/translate-stream")
@api_error_handler
async def translate_stream(
    http_request: Request,
    request: StreamTranslationRequest,
    user: UserObject = Depends(get_current_user),
):
    """流式翻译端点

    使用 Server-Sent Events (SSE) 返回流式翻译结果
    """
    # 提取用户名
    username = user.username if hasattr(user, "username") else str(user)

    # 速率限制检查
    allowed, wait_time = rate_limiter.is_allowed(username)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=ErrorResponse(
                error_code="RATE_LIMIT_EXCEEDED",
                message=f"请求过于频繁，请等待 {wait_time} 秒",
                details={"wait_time": wait_time, "username": username},
            ).dict(),
        )

    # 文本验证
    is_valid, message = TextValidator.validate_for_gemini(request.text)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="TEXT_VALIDATION_ERROR",
                message=message,
                details={"text_length": len(request.text)},
            ).dict(),
        )

    # 检查操作类型
    if request.operation not in ["translate_us", "translate_uk"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="UNSUPPORTED_OPERATION",
                message="流式翻译仅支持 translate_us 和 translate_uk 操作",
                details={"operation": request.operation},
            ).dict(),
        )

    # 生成缓存键（流式翻译不适用缓存，但保留逻辑用于统计）
    generate_safe_hash_for_cache(request.text, f"{request.operation}_{request.version}")

    # 根据操作类型构建prompt
    style = "US" if request.operation == "translate_us" else "UK"
    prompt = build_academic_translate_prompt(request.text, style, request.version or "professional")

    # 获取API密钥（优先从环境变量获取，其次从请求头获取）
    gemini_api_key = None

    # 从环境变量获取Gemini API密钥
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    logging.info(
        f"translate_stream函数: 从环境变量获取GEMINI_API_KEY: {gemini_api_key is not None}"
    )
    if not gemini_api_key:
        # 从请求头获取
        gemini_api_key = http_request.headers.get("X-Gemini-Api-Key")
        logging.info(
            f"translate_stream函数: 从请求头获取X-Gemini-Api-Key: {gemini_api_key is not None}"
        )

    # 检查API密钥是否存在
    if not gemini_api_key:
        logging.warning("Gemini API密钥未提供：环境变量和请求头中都未找到")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="GEMINI_API_KEY_MISSING",
                message="需要提供Gemini API密钥（可通过环境变量GEMINI_API_KEY或侧边栏输入设置）",
                details={"service": "Gemini"},
            ).dict(),
        )

    async def stream_generator():
        """流式生成器，产生SSE格式的数据"""
        try:
            # 调用流式翻译服务，使用 gemini-2.5-flash 作为主模型
            stream = generate_gemini_content_stream(
                prompt=prompt,
                api_key=gemini_api_key,
                primary_model="gemini-2.5-flash",
                fallback_model="gemini-2.5-pro",
            )

            # 处理流式响应
            async for chunk in stream:
                # 将字典转换为JSON字符串
                chunk_data = StreamTranslationChunk(**chunk)
                json_str = chunk_data.json()

                # SSE格式：data: {json}\n\n
                yield f"data: {json_str}\n\n"

        except Exception as e:
            logging.error(f"流式翻译异常: {str(e)}", exc_info=True)
            error_chunk = StreamTranslationChunk(
                type="error", error=f"流式翻译异常: {str(e)}", error_type="stream_error"
            )
            yield f"data: {error_chunk.json()}\n\n"

    # 记录使用情况（异步，不阻塞流式响应）
    try:
        remaining = user_service.record_usage(
            username, operation_type=request.operation, text_length=len(request.text)
        )
        logging.info(f"用户 {username} 流式翻译使用记录，剩余次数: {remaining}")
    except Exception as e:
        logging.error(f"记录流式翻译使用失败: {str(e)}")
        # 不中断流式响应，仅记录错误

    # 返回流式响应
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用Nginx缓冲
        },
    )


@app.post("/api/text/refine-stream")
@api_error_handler
async def refine_stream(
    http_request: Request,
    request: StreamRefineTextRequest,
    user: UserObject = Depends(get_current_user),
):
    """流式文本修改端点

    使用 Server-Sent Events (SSE) 返回流式修改结果
    """
    # 提取用户名
    username = user.username if hasattr(user, "username") else str(user)

    # 速率限制检查
    allowed, wait_time = rate_limiter.is_allowed(username)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=ErrorResponse(
                error_code="RATE_LIMIT_EXCEEDED",
                message=f"请求过于频繁，请等待 {wait_time} 秒",
                details={"wait_time": wait_time, "username": username},
            ).dict(),
        )

    # 文本验证
    is_valid, message = TextValidator.validate_for_gemini(request.text)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="TEXT_VALIDATION_ERROR",
                message=message,
                details={"text_length": len(request.text)},
            ).dict(),
        )

    # 构建隐藏指令
    hidden_prompts = []
    for directive in request.directives:
        if directive in SHORTCUT_ANNOTATIONS:
            hidden_prompts.append(f"- {SHORTCUT_ANNOTATIONS[directive]}")

    hidden_instructions = "\n".join(hidden_prompts)

    # 提取批注信息
    annotations = extract_annotations_with_context(request.text)
    if annotations:
        logging.info(f"检测到 {len(annotations)} 个局部批注")
        # 记录更详细的批注信息，便于调试
        for i, anno in enumerate(annotations):
            logging.info(f"批注 {i + 1}: 句子='{anno['sentence']}', 内容='{anno['content']}'")

    # 构建prompt
    prompt = build_english_refine_prompt(request.text, hidden_instructions, annotations)

    # 记录完整的prompt用于调试
    logging.info(f"流式文本修改 - 完整的提示词: {prompt}")

    # 获取API密钥（优先从环境变量获取，其次从请求头获取）
    gemini_api_key = None

    # 从环境变量获取Gemini API密钥
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    logging.info(f"refine_stream函数: 从环境变量获取GEMINI_API_KEY: {gemini_api_key is not None}")
    if not gemini_api_key:
        # 从请求头获取
        gemini_api_key = http_request.headers.get("X-Gemini-Api-Key")
        logging.info(
            f"refine_stream函数: 从请求头获取X-Gemini-Api-Key: {gemini_api_key is not None}"
        )

    # 检查API密钥是否存在
    if not gemini_api_key:
        logging.warning("Gemini API密钥未提供：环境变量和请求头中都未找到")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="GEMINI_API_KEY_MISSING",
                message="需要提供Gemini API密钥（可通过环境变量GEMINI_API_KEY或侧边栏输入设置）",
                details={"service": "Gemini"},
            ).dict(),
        )

    async def stream_generator():
        """流式生成器，产生SSE格式的数据"""
        try:
            # 调用流式翻译服务（与翻译共用同一个流式函数），使用 gemini-2.5-flash 作为主模型
            stream = generate_gemini_content_stream(
                prompt=prompt,
                api_key=gemini_api_key,
                primary_model="gemini-2.5-flash",
                fallback_model="gemini-2.5-pro",
            )

            # 处理流式响应
            async for chunk in stream:
                # 将字典转换为JSON字符串
                chunk_data = StreamRefineTextChunk(**chunk)
                json_str = chunk_data.json()

                # SSE格式：data: {json}\n\n
                yield f"data: {json_str}\n\n"

        except Exception as e:
            logging.error(f"流式文本修改异常: {str(e)}", exc_info=True)
            error_chunk = StreamRefineTextChunk(
                type="error",
                error=f"流式文本修改异常: {str(e)}",
                error_type="stream_error",
            )
            yield f"data: {error_chunk.json()}\n\n"

    # 返回流式响应
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用Nginx缓冲
        },
    )


@app.post("/api/text/refine")
@api_error_handler
async def refine_text(
    http_request: Request,
    request: RefineTextRequest,
    user: UserObject = Depends(get_current_user),
):
    """英文精修"""

    # 提取用户名
    username = user.username if hasattr(user, "username") else str(user)

    # 速率限制检查
    allowed, wait_time = rate_limiter.is_allowed(username)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=ErrorResponse(
                error_code="RATE_LIMIT_EXCEEDED",
                message=f"请求过于频繁，请等待 {wait_time} 秒",
                details={"wait_time": wait_time, "username": username},
            ).dict(),
        )

    # 构建隐藏指令
    hidden_prompts = []
    for directive in request.directives:
        if directive in SHORTCUT_ANNOTATIONS:
            hidden_prompts.append(f"- {SHORTCUT_ANNOTATIONS[directive]}")

    hidden_instructions = "\n".join(hidden_prompts)

    # 提取批注信息
    annotations = extract_annotations_with_context(request.text)
    if annotations:
        logging.info(f"检测到 {len(annotations)} 个局部批注")
        # 记录更详细的批注信息，便于调试
        for i, anno in enumerate(annotations):
            logging.info(f"批注 {i + 1}: 句子='{anno['sentence']}', 内容='{anno['content']}'")

    # 构建prompt
    prompt = build_english_refine_prompt(request.text, hidden_instructions, annotations)

    # 记录完整的prompt用于调试
    logging.info(f"完整的提示词: {prompt}")

    # 生成缓存键
    cache_key = generate_safe_hash_for_cache(request.text, "_".join(request.directives))

    # 检查缓存
    cached_result = gemini_cache.get(cache_key)
    if cached_result:
        logging.info(f"使用缓存结果: {cache_key}")
        return cached_result

    # 获取API密钥（优先从环境变量获取，其次从请求头获取）
    gemini_api_key = None
    source = "环境变量"

    # 从环境变量获取Gemini API密钥
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        # 从请求头获取
        gemini_api_key = http_request.headers.get("X-Gemini-Api-Key")
        source = "请求头"

    # 调试日志：记录API密钥信息
    if gemini_api_key:
        key_prefix = (
            gemini_api_key[:8] if len(gemini_api_key) > 8 else gemini_api_key[: len(gemini_api_key)]
        )
        logging.info(f"从{source}获取到Gemini API密钥，前缀: {key_prefix}...")
    else:
        logging.warning(f"Gemini API密钥未提供：{source}中未找到")

    # 检查API密钥是否存在
    if not gemini_api_key:
        logging.warning("Gemini API密钥未提供：环境变量和请求头中都未找到")
        # 记录所有请求头用于调试
        all_headers = dict(http_request.headers)
        logging.info(f"所有请求头: {all_headers}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="GEMINI_API_KEY_MISSING",
                message="需要提供Gemini API密钥（可通过环境变量GEMINI_API_KEY或侧边栏输入设置）",
                details={"service": "Gemini"},
            ).dict(),
        )

    # 调用 Gemini API，文本相关功能使用 gemini-2.5-flash 作为主模型
    result = generate_gemini_content_with_fallback(
        prompt,
        api_key=gemini_api_key,
        primary_model="gemini-2.5-flash",
        fallback_model="gemini-2.5-pro",
    )

    if not result["success"]:
        error_message = result.get("error", "处理失败")
        error_type = result.get("error_type", "unknown")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error_code="GEMINI_API_ERROR",
                message=error_message,
                details={"error_type": error_type},
            ).dict(),
        )

    response_data = {
        "success": True,
        "text": result["text"],
        "model_used": result.get("model_used", "unknown"),
        "annotations_processed": len(annotations) if annotations else 0,
    }

    # 缓存结果
    gemini_cache.set(cache_key, response_data)

    return response_data


@app.post("/api/text/detect-ai")
@api_error_handler
async def detect_ai(
    http_request: Request,
    request: AIDetectionRequest,
    user: UserObject = Depends(get_current_user),
):
    """AI内容检测"""

    # 提取用户名
    username = user.username if hasattr(user, "username") else str(user)

    # 速率限制检查
    allowed, wait_time = rate_limiter.is_allowed(username)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=ErrorResponse(
                error_code="RATE_LIMIT_EXCEEDED",
                message=f"请求过于频繁，请等待 {wait_time} 秒",
                details={"wait_time": wait_time, "username": username},
            ).dict(),
        )

    # 优先从环境变量读取GPTZero API密钥
    gptzero_api_key = None
    source = "环境变量"

    # 首先尝试从环境变量读取
    gptzero_api_key = os.environ.get("GPTZERO_API_KEY")
    if gptzero_api_key:
        logging.info("从环境变量 GPTZERO_API_KEY 获取到GPTZero API密钥")
        source = "环境变量"
    else:
        # 如果环境变量不存在，从请求头中提取API密钥（向后兼容）
        gptzero_api_key = http_request.headers.get("X-Gptzero-Api-Key")
        if gptzero_api_key:
            logging.info("从请求头 X-Gptzero-Api-Key 获取到GPTZero API密钥")
            source = "请求头"
        else:
            # 尝试其他可能的请求头名称
            possible_headers = [
                "X-Gptzero-Api-Key",
                "x-gptzero-api-key",
                "X-GPTZERO-API-KEY",
                "gptzero-api-key",
                "Gptzero-Api-Key",
            ]
            for header_name in possible_headers:
                value = http_request.headers.get(header_name)
                if value:
                    gptzero_api_key = value
                    logging.info(f"从请求头 '{header_name}' 获取到GPTZero API密钥")
                    source = "请求头"
                    break

    # 检查API密钥是否存在
    if not gptzero_api_key:
        logging.warning("GPTZero API密钥未提供：环境变量和请求头中都未找到")
        # 记录所有请求头用于调试
        all_headers = dict(http_request.headers)
        logging.info(f"所有请求头: {all_headers}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="GPTZERO_API_KEY_MISSING",
                message="需要提供GPTZero API密钥（可通过环境变量GPTZERO_API_KEY或请求头X-Gptzero-Api-Key提供）",
                details={"service": "GPTZero"},
            ).dict(),
        )

    # 调试日志：记录API密钥信息
    key_prefix = (
        gptzero_api_key[:8] if len(gptzero_api_key) > 8 else gptzero_api_key[: len(gptzero_api_key)]
    )
    logging.info(f"从{source}获取到GPTZero API密钥，前缀: {key_prefix}...")

    # 使用获取到的API密钥
    final_gptzero_api_key = gptzero_api_key

    # 生成缓存键
    cache_key = generate_safe_hash_for_cache(request.text, "gptzero")

    # 检查缓存
    cached_result = gptzero_cache.get(cache_key)
    if cached_result:
        logging.info(f"使用缓存结果: {cache_key}")
        return cached_result

    result = check_gptzero(request.text, final_gptzero_api_key)

    if not result["success"]:
        error_message = result.get("message", "检测失败")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error_code="GPTZERO_API_ERROR",
                message=error_message,
                details={"service": "GPTZero"},
            ).dict(),
        )

    # 缓存结果
    gptzero_cache.set(cache_key, result)

    # 记录AI检测使用
    try:
        user_service.record_usage(
            username, operation_type="ai_detection", text_length=len(request.text)
        )
    except Exception as e:
        logging.warning(f"记录AI检测使用失败，但不影响返回结果: {str(e)}")

    return result


@app.post("/api/chat")
@api_error_handler
async def chat_endpoint(
    http_request: Request,
    request: AIChatRequest,
    user: UserObject = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """AI聊天对话"""
    start_time = time.time()

    logging.info(
        f"chat_endpoint called: literature_research_mode={request.literature_research_mode}, messages_count={len(request.messages)}"
    )
    # logging.info(f"DEBUG: Full request dict: {request.dict()}")  # 注释掉，避免GBK编码问题
    logging.info(
        f"DEBUG: Type of literature_research_mode: {type(request.literature_research_mode)}, Value: {request.literature_research_mode}"
    )
    # 提取用户名
    username = user.username if hasattr(user, "username") else str(user)

    # 调试日志：显示接收到的请求参数
    logging.info(
        f"chat_endpoint: 收到聊天请求，用户: {username}, 消息数量: {len(request.messages)}"
    )
    logging.info(f"chat_endpoint: literature_research_mode 值: {request.literature_research_mode}")

    # 速率限制检查
    allowed, wait_time = rate_limiter.is_allowed(username)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=ErrorResponse(
                error_code="RATE_LIMIT_EXCEEDED",
                message=f"请求过于频繁，请等待{wait_time}秒",
                details={"wait_time": wait_time},
            ).dict(),
        )

    # 检查用户限制
    user_info = user_service.get_user_info(username)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error_code="USER_NOT_FOUND",
                message="用户不存在",
                details={"username": username},
            ).dict(),
        )

    # 转换消息格式为chat_with_gemini所需的格式
    messages = []
    for msg in request.messages:
        messages.append({"role": msg.role, "content": msg.content})

    # 获取API密钥（优先从环境变量获取，其次从请求头获取）
    api_key = None
    source = "环境变量"

    # 从环境变量获取Gemini API密钥
    api_key = os.environ.get("GEMINI_API_KEY")
    logging.info(f"chat_endpoint函数: 从环境变量获取GEMINI_API_KEY: {api_key is not None}")
    if not api_key:
        # 从请求头获取
        api_key = http_request.headers.get("X-Gemini-Api-Key")
        source = "请求头"
        logging.info(f"chat_endpoint函数: 从请求头获取X-Gemini-Api-Key: {api_key is not None}")

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="API_KEY_MISSING",
                message="未提供Gemini API密钥",
                details={"hint": "请在侧边栏输入Gemini API密钥，或设置GEMINI_API_KEY环境变量"},
            ).dict(),
        )

    logging.info(f"使用{source}的Gemini API密钥进行聊天，用户: {username}")

    logging.info(
        f"chat_endpoint 请求数据: literature_research_mode={request.literature_research_mode}, messages_count={len(request.messages)}"
    )
    # 检查是否启用文献调研模式
    logging.info(
        f"DEBUG: request.literature_research_mode type: {type(request.literature_research_mode)}, value: {request.literature_research_mode}"
    )
    if request.literature_research_mode:
        logging.info(f"文献调研模式已启用，用户: {username}")
        logging.info(f"生成文献综述选项: {request.generate_literature_review}")

        # 检查是否启用后台工作器模式
        if settings.ENABLE_BACKGROUND_WORKER:
            logging.info(f"后台工作器模式已启用，将创建后台任务处理文献调研请求")

            # 获取用户ID
            user_obj = db.query(User).filter(User.username == username).first()
            if not user_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=ErrorResponse(
                        error_code="USER_NOT_FOUND",
                        message="用户不存在",
                        details={"username": username},
                    ).dict(),
                )

            # 创建请求数据
            request_data = {
                "prompt": "",
                "generate_literature_review": request.generate_literature_review,
                "manus_api_key": os.environ.get("MANUS_API_KEY"),
            }

            # 提取用户的最新消息作为prompt
            for msg in reversed(request.messages):
                if msg.role == "user":
                    request_data["prompt"] = msg.content.strip()
                    break

            if not request_data["prompt"]:
                request_data["prompt"] = "请帮助我进行学术研究"  # 默认prompt

            # 创建后台任务
            task_service = get_background_task_service(db)
            try:
                task = task_service.create_task(
                    user_id=user_obj.id,
                    task_type="chat_literature_research",
                    request_data=request_data,
                    estimated_time=600,  # 默认10分钟
                )

                logging.info(f"创建后台任务成功: id={task.id}, type=chat_literature_research, user_id={user_obj.id}")

                # 返回后台任务响应
                return BackgroundTaskResponse(
                    success=True,
                    message="文献调研任务已提交到后台处理，请稍后查询结果",
                    task_id=task.id,
                    status=task.status,
                    estimated_time=600,
                )

            except Exception as e:
                logging.error(f"创建后台任务失败: {str(e)}", exc_info=True)
                # 如果后台任务创建失败，回退到同步处理模式
                logging.warning(f"后台任务创建失败，将使用同步处理模式: {str(e)}")

        # 提取用户的最新消息作为prompt
        prompt = ""
        for msg in reversed(request.messages):
            if msg.role == "user":
                prompt = msg.content.strip()
                break

        if not prompt:
            prompt = "请帮助我进行学术研究"  # 默认prompt

        logging.info(f"文献调研原始prompt: {repr(prompt[:100])}...")

        # 根据生成文献综述选项构建提示词（使用新模板系统）
        final_prompt = build_literature_research_prompt(
            prompt=prompt,
            generate_literature_review=request.generate_literature_review,
            use_cache=True,  # 启用缓存提高性能
        )
        logging.info("使用新提示词模板系统构建文献调研提示词")

        prompt = final_prompt
        logging.info(f"最终prompt预览: {repr(prompt[:200])}...")

        # 获取Manus API密钥
        manus_api_key = os.environ.get("MANUS_API_KEY")
        logging.info(
            f"文献调研模式: MANUS_API_KEY exists: {manus_api_key is not None}, length: {len(manus_api_key) if manus_api_key else 0}"
        )
        if not manus_api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    error_code="API_KEY_MISSING",
                    message="未提供Manus API密钥",
                    details={"hint": "请设置MANUS_API_KEY环境变量"},
                ).dict(),
            )

        # 使用Manus API进行通用对话
        try:
            result = chat_with_manus(
                prompt=prompt,
                api_key=manus_api_key,
                generate_literature_review=request.generate_literature_review,
                prompt_already_built=True
            )

            if result.get("success"):
                text = result.get("text", "")
                # 如果文本为空，提供默认回复
                if not text:
                    text = "已处理您的请求，但没有生成具体的回复内容。"

                # 记录响应体大小
                text_bytes = len(text.encode('utf-8'))
                logging.info(f"Manus API响应体大小: {text_bytes} 字节 ({text_bytes/1024:.2f} KB)")
                if text_bytes > settings.MAX_RESPONSE_SIZE_BYTES:  # 大于配置的最大响应大小
                    logging.warning(f"Manus API响应体过大: {text_bytes/1024/1024:.2f} MB，超过最大限制 {settings.MAX_RESPONSE_SIZE_BYTES/1024/1024:.2f} MB，可能影响网络传输")
                    # 对于过大的响应，使用流式响应分块发送
                    # 创建JSON响应
                    import json
                    response_data = AIChatResponse(
                        success=True,
                        text=text,
                        session_id=request.session_id,
                        model_used="manus-ai",
                        steps=result.get("steps", []),  # 传递Manus API步骤信息
                    )
                    json_str = json.dumps(response_data.dict(), ensure_ascii=False)

                    # 将JSON字符串分块发送
                    chunk_size = settings.CHUNK_SIZE_BYTES

                    def generate_chunks():
                        """生成JSON字符串的分块

                        Yields:
                            bytes: 编码为UTF-8的JSON字符串分块
                        """
                        for i in range(0, len(json_str), chunk_size):
                            chunk = json_str[i:i + chunk_size]
                            yield chunk.encode('utf-8')
                            logging.debug(f"Sent chunk {i//chunk_size + 1}, size: {len(chunk)} bytes")

                    return StreamingResponse(
                        generate_chunks(),
                        media_type="application/json",
                        headers={
                            "Transfer-Encoding": "chunked",
                            "X-Response-Size": str(text_bytes),
                            "X-Response-Chunks": str((len(json_str) + chunk_size - 1) // chunk_size),
                            "X-Response-Streaming": "true"
                        }
                    )
                elif text_bytes > 1024 * 100:  # 大于100KB
                    logging.info(f"Manus API响应体较大: {text_bytes/1024:.2f} KB")

                # 记录总处理时间
                total_time = time.time() - start_time
                logging.info(f"chat_endpoint Manus API总处理时间: {total_time:.2f}秒, 响应大小: {text_bytes}字节")

                return AIChatResponse(
                    success=True,
                    text=text,
                    session_id=request.session_id,
                    model_used="manus-ai",
                    steps=result.get("steps", []),  # 传递Manus API步骤信息
                )
            else:
                # 记录总处理时间
                total_time = time.time() - start_time
                logging.info(f"chat_endpoint Manus API失败，总处理时间: {total_time:.2f}秒")

                return AIChatResponse(
                    success=False,
                    text="",
                    session_id=request.session_id,
                    model_used="manus-ai",
                    steps=[],  # 失败时返回空步骤列表
                    error=result.get("error", "Manus API对话失败"),
                )

        except Exception as e:
            logging.error(f"Manus API对话失败: {str(e)}", exc_info=True)
            return AIChatResponse(
                success=False,
                text="",
                session_id=request.session_id,
                model_used="manus-ai",
                steps=[],  # Manus API异常时返回空步骤列表
                error=f"Manus API对话失败: {str(e)}",
            )

    # 普通聊天模式 - 调用聊天服务
    try:
        result = chat_with_gemini(messages=messages, api_key=api_key)

        if result.get("success"):
            return AIChatResponse(
                success=True,
                text=result.get("text", ""),
                session_id=request.session_id,
                model_used=result.get("model_used", "unknown"),
                steps=[],  # 普通聊天模式返回空步骤列表
            )
        else:
            return AIChatResponse(
                success=False,
                text="",
                session_id=request.session_id,
                model_used=result.get("model_used", "unknown"),
                steps=[],  # 普通聊天模式失败时返回空步骤列表
                error=result.get("error", "未知错误"),
            )

    except Exception as e:
        logging.error(f"聊天请求处理失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error_code="CHAT_PROCESSING_FAILED",
                message="聊天请求处理失败",
                details={"error": str(e)},
            ).dict(),
        ) from e


@app.get("/api/tasks/{task_id}/status")
@api_error_handler
async def get_task_status(
    task_id: int,
    user: UserObject = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取后台任务状态"""
    # 获取任务
    task_service = get_background_task_service(db)
    task = task_service.get_task(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error_code="TASK_NOT_FOUND",
                message="任务不存在",
                details={"task_id": task_id},
            ).dict(),
        )

    # 检查任务是否属于当前用户（非管理员用户只能查看自己的任务）
    username = user.username if hasattr(user, "username") else str(user)
    user_obj = db.query(User).filter(User.username == username).first()

    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error_code="USER_NOT_FOUND",
                message="用户不存在",
                details={"username": username},
            ).dict(),
        )

    # 非管理员用户只能查看自己的任务
    if not user_obj.is_admin and task.user_id != user_obj.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorResponse(
                error_code="ACCESS_DENIED",
                message="无权访问此任务",
                details={"task_id": task_id},
            ).dict(),
        )

    # 计算进度百分比（如果任务正在处理中）
    progress = None
    estimated_remaining_time = None
    step_details = None

    # 优先使用数据库中的进度信息
    if task.progress_percentage is not None:
        progress = float(task.progress_percentage)
    elif task.status == "processing" and task.started_at:
        # 后备：简单进度估算：基于已处理时间
        elapsed_time = (datetime.now() - task.started_at).total_seconds()
        # 假设任务总时间为10分钟（600秒）
        total_estimated_time = 600
        progress = min(95, (elapsed_time / total_estimated_time) * 100)  # 最多显示95%
        estimated_remaining_time = max(0, total_estimated_time - elapsed_time)
    elif task.status == "completed":
        progress = 100
        estimated_remaining_time = 0

    # 解析结果数据
    result_data = None
    if task.result_data:
        try:
            result_data = json.loads(task.result_data)
        except (json.JSONDecodeError, TypeError):
            result_data = task.result_data

    # 解析步骤详情数据
    if task.step_details:
        try:
            step_details = json.loads(task.step_details)
        except (json.JSONDecodeError, TypeError):
            step_details = {"raw": task.step_details}

    # 创建task对象以匹配前端期望的BackgroundTask接口
    task_obj = {
        "id": task.id,
        "user_id": task.user_id,
        "task_type": task.task_type,
        "status": task.status,
        "request_data": json.loads(task.request_data) if task.request_data else None,
        "result_data": result_data,
        "error_message": task.error_message,
        "attempts": task.attempts,
        "max_attempts": task.max_attempts,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
        "progress_percentage": progress,
        "current_step": task.current_step,
        "total_steps": task.total_steps,
        "step_description": task.step_description,
        "step_details": step_details,
    }

    return TaskStatusResponse(
        success=True,
        task=task_obj,
        message=None,
        error=None,
        # 向后兼容字段
        task_id=task.id,
        status=task.status,
        progress=progress,
        step_description=task.step_description,
        step_details=step_details,
        current_step=task.current_step,
        total_steps=task.total_steps,
        result_data=result_data,
        error_message=task.error_message,
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        estimated_remaining_time=int(estimated_remaining_time) if estimated_remaining_time is not None else None,
    )


@app.post("/api/tasks/poll")
@api_error_handler
async def poll_task_status(
    request: TaskPollRequest,
    user: UserObject = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """轮询任务状态（兼容性端点）"""
    # 直接调用get_task_status逻辑
    return await get_task_status(request.task_id, user, db)


@app.get("/api/health")
async def health_check():
    """健康检查 - 简化版本，确保应用本身正常运行"""
    try:
        # 基本应用状态检查
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "checks": {
                "app": "ok",
                "database": "unknown",
                "external_apis": "not_checked",  # 不检查外部API以避免启动失败
            },
        }

        # 可选：简单数据库连接检查（不阻塞）
        try:
            # 尝试快速数据库连接
            db = get_session_local()()
            db.execute(text("SELECT 1"))
            db.close()
            health_status["checks"]["database"] = "ok"
        except Exception as e:
            health_status["checks"]["database"] = f"error: {str(e)[:50]}"
            # 不将状态降级为degraded，因为应用可能仍能运行

        return health_status
    except Exception as e:
        # 如果健康检查本身失败，返回错误（但保持HTTP 200状态码，让应用继续运行）
        logging.error(f"健康检查执行失败: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)[:100],
            "checks": {
                "app": "error",
                "database": "unknown",
                "external_apis": "unknown",
            },
        }


# ==========================================
# 提示词性能监控API
# ==========================================


@app.get("/api/debug/prompt-metrics")
@api_error_handler
async def get_prompt_metrics():
    """获取提示词性能指标"""
    from prompt_cache import prompt_cache_manager
    from prompt_monitor import prompt_performance_monitor

    return {
        "timestamp": datetime.now().isoformat(),
        "performance_metrics": prompt_performance_monitor.get_report(),
        "cache_metrics": prompt_cache_manager.get_stats(),
        "config": {
            "default_template_version": "compact",
            "cache_enabled": True,
            "cache_ttl_seconds": 3600,
            "cache_max_entries": 1000,
        },
    }


@app.post("/api/debug/prompt-cache/clear")
@api_error_handler
async def clear_prompt_cache():
    """清空提示词缓存"""
    from prompt_cache import prompt_cache_manager

    prompt_cache_manager.clear()

    return {
        "success": True,
        "message": "提示词缓存已清空",
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/api/debug/prompt-metrics/reset")
@api_error_handler
async def reset_prompt_metrics():
    """重置提示词性能指标"""
    from prompt_monitor import prompt_performance_monitor

    prompt_performance_monitor.reset_metrics()

    return {
        "success": True,
        "message": "提示词性能指标已重置",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/debug/prompt-test")
@api_error_handler
async def test_prompt_build():
    """测试提示词构建性能"""
    from prompts import test_prompt_build_performance

    return test_prompt_build_performance()


# ==========================================
# 管理员API
# ==========================================


@app.post("/api/admin/login")
@api_error_handler
async def admin_login(request: AdminLoginRequest):
    """管理员登录"""
    if request.password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error_code="ADMIN_AUTHENTICATION_FAILED",
                message="密码错误",
                details={"service": "admin_login"},
            ).dict(),
        )

    timestamp = str(int(time.time()))
    token_string = f"admin:{timestamp}"
    token_hash = hashlib.sha256(token_string.encode()).hexdigest()[:16]
    token = f"admin:{timestamp}:{token_hash}"

    return {"success": True, "token": token}


@app.get("/api/admin/users")
@api_error_handler
async def get_all_users(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取所有用户信息（管理员）"""
    token = credentials.credentials
    if not token.startswith("admin:"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorResponse(
                error_code="ADMIN_PERMISSION_REQUIRED",
                message="需要管理员权限",
                details={"token_provided": token[:20] if token else None},
            ).dict(),
        )

    users = user_service.get_all_users()
    return {"users": users}


@app.post("/api/admin/users/update")
@api_error_handler
async def update_user(
    request: UpdateUserRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """更新用户信息（管理员）"""
    token = credentials.credentials
    if not token.startswith("admin:"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorResponse(
                error_code="ADMIN_PERMISSION_REQUIRED",
                message="需要管理员权限",
                details={"token_provided": token[:20] if token else None},
            ).dict(),
        )

    success, message = user_service.update_user(
        request.username,
        request.password,
        request.daily_translation_limit,
        request.daily_ai_detection_limit,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="USER_UPDATE_FAILED",
                message=message,
                details={"username": request.username},
            ).dict(),
        )

    return {"success": True, "message": message}


@app.post("/api/admin/users/add")
@api_error_handler
async def add_user(
    request: AddUserRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """添加新用户（管理员）"""
    token = credentials.credentials
    if not token.startswith("admin:"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorResponse(
                error_code="ADMIN_PERMISSION_REQUIRED",
                message="需要管理员权限",
                details={"token_provided": token[:20] if token else None},
            ).dict(),
        )

    success, message = user_service.add_user(
        request.username,
        request.password,
        request.daily_translation_limit,
        request.daily_ai_detection_limit,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="USER_ADD_FAILED",
                message=message,
                details={"username": request.username},
            ).dict(),
        )

    return {"success": True, "message": message}


@app.get("/api/test")
async def test_endpoint():
    return {"message": "Test endpoint works", "status": "ok"}


# 添加启动事件来打印所有路由
@app.on_event("startup")
async def print_routes():
    """打印所有注册的路由"""
    logger.info("=== 注册的API路由 ===")
    for route in app.routes:
        if hasattr(route, "methods"):
            logger.info(f"{route.path} - {route.methods}")
    logger.info("===================")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
