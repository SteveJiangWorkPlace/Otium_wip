from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Set, Any
from jose import JWTError, jwt
import google.genai
# 导入类型用于类型提示
from google.genai import types
import google.genai.errors
# import google.api_core.exceptions
# from google.api_core.exceptions import ServiceUnavailable, DeadlineExceeded, InvalidArgument, PermissionDenied
# 这些异常现在由 google.genai.errors 提供
import requests
import json
import logging
import os
import time
import re
import platform
import threading
from datetime import datetime
from collections import deque
from functools import wraps
from dotenv import load_dotenv
import os
import hashlib
import uuid
import warnings

# 过滤Pydantic的ArbitraryTypeWarning警告
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 导入自定义模块
from services import (
    generate_gemini_content_with_fallback,
    check_gptzero,
    generate_safe_hash_for_cache,
    extract_annotations_with_context,
    contains_annotation_marker,
    chat_with_gemini
)
from exceptions import APIError, GeminiAPIError, GPTZeroAPIError, RateLimitError, ValidationError, api_error_handler
from utils import RateLimiter, TextValidator, CacheManager
from user_services.user_service import UserService
from models.database import init_database, get_session_local
from schemas import (
    LoginRequest, CheckTextRequest, RefineTextRequest, AIDetectionRequest,
    UserInfo, AdminLoginRequest, UpdateUserRequest, AddUserRequest, ErrorResponse,
    AIChatRequest, AIChatResponse
)
from config import settings, is_expired
from prompts import (
    build_error_check_prompt,
    build_academic_translate_prompt,
    build_english_refine_prompt,
    SHORTCUT_ANNOTATIONS,
    preprocess_annotations
)

# 加载环境变量
load_dotenv()

# 日志配置
log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info(f"日志级别设置为: {log_level_str} ({log_level})")

logger = logging.getLogger(__name__)

    
app = FastAPI(title="Just Trans API", version="1.0.0")

# 在应用初始化时添加环境变量检查日志
logging.info(f"应用启动，环境变量检查:")
logging.info(f"ADMIN_USERNAME 是否设置: {bool(os.environ.get('ADMIN_USERNAME'))}")
logging.info(f"ADMIN_PASSWORD 是否设置: {bool(os.environ.get('ADMIN_PASSWORD'))}")
logging.info(f"ADMIN_USERNAME 值: {os.environ.get('ADMIN_USERNAME', 'admin')}")
logging.info(f"ADMIN_PASSWORD 长度: {len(os.environ.get('ADMIN_PASSWORD', 'admin123'))}")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 临时允许所有来源，调试CORS问题
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# ==========================================
# 数据模型
# ==========================================


# 定义 OAuth2 方案，指定获取 Token 的地址（虽然我们现在是手动验证，但定义是必须的）
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

# JWT 配置
# 优先从JWT_SECRET_KEY环境变量读取，其次从SECRET_KEY读取，最后使用默认值（向后兼容）
SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or os.environ.get("SECRET_KEY", "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92")
ALGORITHM = "HS256"

# 检查SECRET_KEY是否为默认值，如果是则记录警告
DEFAULT_SECRET_KEY = "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92"
if SECRET_KEY == DEFAULT_SECRET_KEY:
    logging.warning("⚠️ SECRET_KEY使用的是默认值！在生产环境中应设置JWT_SECRET_KEY或SECRET_KEY环境变量来增强安全性")

# ==========================================
# 统一错误响应模型
# ==========================================

class ErrorResponse(BaseModel):
    """统一错误响应模型"""
    success: bool = False
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None

# ==========================================
# 全局实例
# ==========================================

# 初始化数据库
try:
    init_database()
    logging.info("数据库初始化成功")
except Exception as e:
    logging.error(f"数据库初始化失败: {e}")
    logging.warning("应用将在无数据库连接的情况下启动，部分功能可能不可用")

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
    def __getattr__(self, name):
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
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

        # 从 JWT 获取角色，如果没有则默认为普通用户
        role = payload.get("role", "user")

        return UserObject(username=username, role=role)
    except Exception as e:
        logging.error(f"Token 验证失败: {str(e)}", exc_info=True)
        raise credentials_exception

# ==========================================
# API 路由
# ==========================================

@app.post("/api/login")
@api_error_handler
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
                "is_active": True
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
            "message": "登录成功"
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
                "is_active": True
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
            "message": "登录成功"
        }
    else:
        logging.error(f"登录失败: {message}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error_code="AUTHENTICATION_FAILED",
                message="用户名或密码错误",
                details={"username": data.username}
            ).dict()
        )

@app.get("/api/user/info")
@api_error_handler
async def get_user_info(user: UserObject = Depends(get_current_user)):
    """获取用户信息"""
    username = user.username if hasattr(user, 'username') else str(user)
    user_info = user_service.get_user_info(username)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error_code="USER_NOT_FOUND",
                message="用户不存在",
                details={"username": username}
            ).dict()
        )
    return user_info

@app.post("/api/text/check")
@api_error_handler
async def check_text(http_request: Request, request: CheckTextRequest, user: UserObject = Depends(get_current_user)):
    """文本检查（纠错或翻译）"""

    # 提取用户名
    username = user.username if hasattr(user, 'username') else str(user)

    # 速率限制检查
    allowed, wait_time = rate_limiter.is_allowed(username)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=ErrorResponse(
                error_code="RATE_LIMIT_EXCEEDED",
                message=f"请求过于频繁，请等待 {wait_time} 秒",
                details={"wait_time": wait_time, "username": username}
            ).dict()
        )
    
    # 文本验证
    is_valid, message = TextValidator.validate_for_gemini(request.text)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="TEXT_VALIDATION_ERROR",
                message=message,
                details={"text_length": len(request.text)}
            ).dict()
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
        prompt = build_academic_translate_prompt(request.text, "US", request.version)
    elif request.operation == "translate_uk":
        prompt = build_academic_translate_prompt(request.text, "UK", request.version)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="UNSUPPORTED_OPERATION",
                message="不支持的操作类型",
                details={"operation": request.operation}
            ).dict()
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
        key_prefix = gemini_api_key[:8] if len(gemini_api_key) > 8 else gemini_api_key[:len(gemini_api_key)]
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
                details={"service": "Gemini"}
            ).dict()
        )


    # 调用 Gemini API，使用与AI聊天相同的模型优先级
    result = generate_gemini_content_with_fallback(
        prompt,
        api_key=gemini_api_key,
        primary_model="gemini-3-pro-preview",
        fallback_model="gemini-2.5-pro"
    )

    if not result["success"]:
        error_message = result.get("error", "处理失败")
        error_type = result.get("error_type", "unknown")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error_code="GEMINI_API_ERROR",
                message=error_message,
                details={"error_type": error_type}
            ).dict()
        )

    response_data = {
        "success": True,
        "text": result["text"],
        "model_used": result.get("model_used", "unknown")
    }
    
    # 如果是翻译操作，记录翻译次数
    if request.operation in ["translate_us", "translate_uk"]:
        try:
            remaining = user_service.record_translation(username, operation_type=request.operation, text_length=len(request.text))
            response_data["remaining_translations"] = remaining
        except ValueError as e:
            # 用户不存在或其他验证错误
            logging.error(f"记录翻译次数失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    error_code="USER_VALIDATION_ERROR",
                    message=str(e),
                    details={"username": username, "exception_type": "ValueError"}
                ).dict()
            )
        except RuntimeError as e:
            # 数据保存失败
            logging.error(f"保存翻译记录失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error_code="DATA_SAVE_ERROR",
                    message="系统错误：无法保存翻译记录",
                    details={"original_error": str(e), "exception_type": "RuntimeError"}
                ).dict()
            )
        except Exception as e:
            # 其他未知错误
            logging.error(f"记录翻译次数时发生未知错误: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error_code="INTERNAL_SERVER_ERROR",
                    message="系统内部错误",
                    details={"original_error": str(e), "exception_type": e.__class__.__name__}
                ).dict()
            )
    
    # 缓存结果
    gemini_cache.set(cache_key, response_data)
    
    return response_data

@app.post("/api/text/refine")
@api_error_handler
async def refine_text(http_request: Request, request: RefineTextRequest, user: UserObject = Depends(get_current_user)):
    """英文精修"""
    
    # 提取用户名
    username = user.username if hasattr(user, 'username') else str(user)

    # 速率限制检查
    allowed, wait_time = rate_limiter.is_allowed(username)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=ErrorResponse(
                error_code="RATE_LIMIT_EXCEEDED",
                message=f"请求过于频繁，请等待 {wait_time} 秒",
                details={"wait_time": wait_time, "username": username}
            ).dict()
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
            logging.info(f"批注 {i+1}: 句子='{anno['sentence']}', 内容='{anno['content']}'")
    
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
        key_prefix = gemini_api_key[:8] if len(gemini_api_key) > 8 else gemini_api_key[:len(gemini_api_key)]
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
                details={"service": "Gemini"}
            ).dict()
        )


    # 调用 Gemini API，使用与AI聊天相同的模型优先级
    result = generate_gemini_content_with_fallback(
        prompt,
        api_key=gemini_api_key,
        primary_model="gemini-3-pro-preview",
        fallback_model="gemini-2.5-pro"
    )

    if not result["success"]:
        error_message = result.get("error", "处理失败")
        error_type = result.get("error_type", "unknown")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error_code="GEMINI_API_ERROR",
                message=error_message,
                details={"error_type": error_type}
            ).dict()
        )

    response_data = {
        "success": True,
        "text": result["text"],
        "model_used": result.get("model_used", "unknown"),
        "annotations_processed": len(annotations) if annotations else 0
    }


    # 缓存结果
    gemini_cache.set(cache_key, response_data)

    return response_data

@app.post("/api/text/detect-ai")
@api_error_handler
async def detect_ai(http_request: Request, request: AIDetectionRequest, user: UserObject = Depends(get_current_user)):
    """AI内容检测"""
    
    # 提取用户名
    username = user.username if hasattr(user, 'username') else str(user)
    
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
                "Gptzero-Api-Key"
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
                details={"service": "GPTZero"}
            ).dict()
        )

    # 调试日志：记录API密钥信息
    key_prefix = gptzero_api_key[:8] if len(gptzero_api_key) > 8 else gptzero_api_key[:len(gptzero_api_key)]
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
                details={"service": "GPTZero"}
            ).dict()
        )
    
    # 缓存结果
    gptzero_cache.set(cache_key, result)
    
    return result


@app.post("/api/chat")
@api_error_handler
async def chat_endpoint(
    http_request: Request,
    request: AIChatRequest,
    user: UserObject = Depends(get_current_user)
):
    """AI聊天对话"""

    # 提取用户名
    username = user.username if hasattr(user, 'username') else str(user)

    # 速率限制检查
    allowed, wait_time = rate_limiter.is_allowed(username)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=ErrorResponse(
                error_code="RATE_LIMIT_EXCEEDED",
                message=f"请求过于频繁，请等待{wait_time}秒",
                details={"wait_time": wait_time}
            ).dict()
        )

    # 检查用户限制
    user_info = user_service.get_user_info(username)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error_code="USER_NOT_FOUND",
                message="用户不存在",
                details={"username": username}
            ).dict()
        )

    # 转换消息格式为chat_with_gemini所需的格式
    messages = []
    for msg in request.messages:
        messages.append({
            "role": msg.role,
            "content": msg.content
        })

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
                details={
                    "hint": "请在侧边栏输入Gemini API密钥，或设置GEMINI_API_KEY环境变量"
                }
            ).dict()
        )

    logging.info(f"使用{source}的Gemini API密钥进行聊天，用户: {username}")

    # 调用聊天服务
    try:
        result = chat_with_gemini(messages=messages, api_key=api_key)

        if result.get("success"):
            return AIChatResponse(
                success=True,
                text=result.get("text", ""),
                session_id=request.session_id,
                model_used=result.get("model_used", "unknown")
            )
        else:
            return AIChatResponse(
                success=False,
                text="",
                session_id=request.session_id,
                model_used=result.get("model_used", "unknown"),
                error=result.get("error", "未知错误")
            )

    except Exception as e:
        logging.error(f"聊天请求处理失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error_code="CHAT_PROCESSING_FAILED",
                message="聊天请求处理失败",
                details={"error": str(e)}
            ).dict()
        )


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
                "external_apis": "not_checked"  # 不检查外部API以避免启动失败
            }
        }

        # 可选：简单数据库连接检查（不阻塞）
        try:
            # 尝试快速数据库连接
            db = get_session_local()()
            db.execute("SELECT 1")
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
                "external_apis": "unknown"
            }
        }

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
                details={"service": "admin_login"}
            ).dict()
        )
    
    timestamp = str(int(time.time()))
    token_string = f"admin:{timestamp}"
    token_hash = hashlib.sha256(token_string.encode()).hexdigest()[:16]
    token = f"admin:{timestamp}:{token_hash}"
    
    return {
        "success": True,
        "token": token
    }

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
                details={"token_provided": token[:20] if token else None}
            ).dict()
        )
    
    users = user_service.get_all_users()
    return {"users": users}

@app.post("/api/admin/users/update")
@api_error_handler
async def update_user(request: UpdateUserRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """更新用户信息（管理员）"""
    token = credentials.credentials
    if not token.startswith("admin:"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorResponse(
                error_code="ADMIN_PERMISSION_REQUIRED",
                message="需要管理员权限",
                details={"token_provided": token[:20] if token else None}
            ).dict()
        )
    
    success, message = user_service.update_user(
        request.username,
        request.expiry_date,
        request.max_translations,
        request.password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="USER_UPDATE_FAILED",
                message=message,
                details={"username": request.username}
            ).dict()
        )
    
    return {"success": True, "message": message}

@app.post("/api/admin/users/add")
@api_error_handler
async def add_user(request: AddUserRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """添加新用户（管理员）"""
    token = credentials.credentials
    if not token.startswith("admin:"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorResponse(
                error_code="ADMIN_PERMISSION_REQUIRED",
                message="需要管理员权限",
                details={"token_provided": token[:20] if token else None}
            ).dict()
        )
    
    success, message = user_service.add_user(
        request.username,
        request.password,
        request.expiry_date,
        request.max_translations
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="USER_ADD_FAILED",
                message=message,
                details={"username": request.username}
            ).dict()
        )
    
    return {"success": True, "message": message}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)