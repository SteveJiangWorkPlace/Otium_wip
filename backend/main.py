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

# 加载环境变量
load_dotenv()

# 日志配置
log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info(f"日志级别设置为: {log_level_str} ({log_level})")

logger = logging.getLogger(__name__)

def is_expired(expiry_date_str):
    """检查日期是否已过期"""
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
            logger.error(f"无法识别的日期格式: {expiry_date_str}")
            return False  # 如果无法解析，默认为未过期，避免错误阻止用户访问
        except Exception as e:
            logger.error(f"日期处理错误: {expiry_date_str}, 错误: {e}")
            return False  # 如果出现其他错误，默认为未过期
    except Exception as e:
        logger.error(f"日期处理异常: {expiry_date_str}, 错误: {e}")
        return False  # 如果出现其他异常，默认为未过期
    
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
    allow_origins=["*"],  # 允许所有源，仅在开发环境使用
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# ==========================================
# 数据模型
# ==========================================

class LoginRequest(BaseModel):
    username: str
    password: str

class CheckTextRequest(BaseModel):
    text: str
    operation: str  # "error_check", "translate_us", "translate_uk"
    version: Optional[str] = "professional"

class RefineTextRequest(BaseModel):
    text: str
    directives: List[str] = []

class AIDetectionRequest(BaseModel):
    text: str

class UserInfo(BaseModel):
    username: str
    expiry_date: str
    max_translations: int
    used_translations: int
    remaining_translations: int

class AdminLoginRequest(BaseModel):
    password: str

class UpdateUserRequest(BaseModel):
    username: str
    expiry_date: Optional[str] = None
    max_translations: Optional[int] = None
    password: Optional[str] = None

class AddUserRequest(BaseModel):
    username: str
    password: str
    expiry_date: str
    max_translations: int

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
# 异常类定义
# ==========================================

class APIError(Exception):
    """API 错误基类"""
    pass

class GeminiAPIError(APIError):
    """Gemini API 错误"""
    def __init__(self, message, error_type="unknown"):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)

class GPTZeroAPIError(APIError):
    """GPTZero API 错误"""
    pass

class RateLimitError(APIError):
    """速率限制错误"""
    pass

class ValidationError(APIError):
    """文本验证错误"""
    pass

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
            logging.error(f"参数验证错误: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    error_code="VALIDATION_ERROR",
                    message=str(e) or "参数验证失败",
                    details={"exception_type": "ValueError"}
                ).dict()
            )
        except RateLimitError as e:
            # 速率限制错误
            logging.error(f"速率限制错误: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=ErrorResponse(
                    error_code="RATE_LIMIT_EXCEEDED",
                    message=str(e) or "请求过于频繁，请稍后再试",
                    details={"exception_type": "RateLimitError"}
                ).dict()
            )
        except GeminiAPIError as e:
            # Gemini API 错误
            logging.error(f"Gemini API 错误: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error_code="GEMINI_API_ERROR",
                    message=str(e) or "Gemini API 处理失败",
                    details={"exception_type": "GeminiAPIError", "error_type": e.error_type}
                ).dict()
            )
        except GPTZeroAPIError as e:
            # GPTZero API 错误
            logging.error(f"GPTZero API 错误: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error_code="GPTZERO_API_ERROR",
                    message=str(e) or "GPTZero API 处理失败",
                    details={"exception_type": "GPTZeroAPIError"}
                ).dict()
            )
        except ValidationError as e:
            # 文本验证错误
            logging.error(f"文本验证错误: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    error_code="TEXT_VALIDATION_ERROR",
                    message=str(e) or "文本验证失败",
                    details={"exception_type": "ValidationError"}
                ).dict()
            )
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
                    details={"exception_type": e.__class__.__name__}
                ).dict()
            )
    return wrapper

# ==========================================
# 用户限制管理
# ==========================================

class UserLimitManager:
    """管理用户使用限制，包括时间和使用次数"""
    
    def __init__(self):
        # 修复文件存储路径问题
        self.usage_db_path = os.environ.get("USAGE_DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "usage_data.json"))
        self.allowed_users = {}
        self.load_allowed_users()
        # 线程锁，防止同一进程内的并发访问
        self._lock = threading.RLock()
        logger.info(f"用户数据存储路径: {self.usage_db_path}")
    
    def load_allowed_users(self):
        """从环境变量或配置文件加载允许的用户"""
        try:
            # 尝试从环境变量 ALLOWED_USERS 获取用户配置
            # 如果环境变量不存在，则使用空的 JSON 对象 "{}" 作为默认值
            users_env = os.environ.get("ALLOWED_USERS", "{}")
            
            # 将 JSON 字符串解析为 Python 字典
            users_data = json.loads(users_env)
            
            # 遍历所有用户数据
            for username, data in users_data.items():
                # 获取用户过期日期，如果不存在则默认为 2099-12-31
                expiry_date = data.get("expiry_date", "2099-12-31")
                
                # 验证日期格式是否正确
                try:
                    datetime.strptime(expiry_date, '%Y-%m-%d')
                except ValueError:
                    # 如果日期格式不正确，记录警告并使用默认值
                    logging.warning(f"用户 {username} 的过期日期格式不正确: {expiry_date}，设置为默认值")
                    expiry_date = "2099-12-31"
                
                # 将用户信息添加到 allowed_users 字典中
                self.allowed_users[username] = {
                    "expiry_date": expiry_date,
                    "max_translations": data.get("max_translations", 1000),  # 默认翻译次数限制为 1000
                    "password": data.get("password", "")  # 默认密码为空字符串
                }
        except Exception as e:
            # 如果解析过程中出现任何错误，记录警告并使用默认配置
            logging.warning(f"无法加载用户配置，使用默认配置: {e}")
            self.allowed_users = {
                "test": {
                    "expiry_date": "2099-12-31",
                    "max_translations": 10,
                    "password": "test123"
                },
                "test_user": {
                    "expiry_date": "2026-12-31",
                    "max_translations": 1000,
                    "password": "test123"
                }
            }
        
        # 自动添加管理员用户（如果环境变量中有配置）
        admin_username = os.environ.get("ADMIN_USERNAME")
        admin_password = os.environ.get("ADMIN_PASSWORD")
        if admin_username and admin_password:
            if admin_username not in self.allowed_users:
                self.allowed_users[admin_username] = {
                    "expiry_date": "2099-12-31",
                    "max_translations": 99999,  # 管理员有非常大的翻译次数限制
                    "password": admin_password
                }
                logging.info(f"自动添加管理员用户: {admin_username}")
            else:
                # 如果已存在，确保密码和配置正确
                self.allowed_users[admin_username]["password"] = admin_password
                self.allowed_users[admin_username]["expiry_date"] = "2099-12-31"
                self.allowed_users[admin_username]["max_translations"] = 99999
                logging.info(f"更新管理员用户配置: {admin_username}")
    
    def load_usage_data(self):
        """加载使用数据"""
        try:
            if os.path.exists(self.usage_db_path):
                logging.info(f"从文件加载使用数据: {self.usage_db_path}")
                with open(self.usage_db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logging.info(f"成功加载 {len(data)} 个用户的使用数据")
                    return data
            else:
                logging.info(f"使用数据文件不存在: {self.usage_db_path}，返回空数据")
                return {}
        except Exception as e:
            logging.error(f"加载使用数据失败: {str(e)}", exc_info=True)
            return {}
    
    def save_usage_data(self, data):
        """保存使用数据（兼容旧版本，新代码请使用_atomic_save_usage_data）"""
        try:
            # 确保目录存在
            dir_path = os.path.dirname(self.usage_db_path)
            if dir_path:  # 如果目录路径不为空
                os.makedirs(dir_path, exist_ok=True)
                logging.info(f"确保目录存在: {dir_path}")

            logging.info(f"正在保存使用数据到: {self.usage_db_path}")
            with open(self.usage_db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logging.info(f"使用数据保存成功，包含 {len(data)} 个用户的使用记录")
            return True
        except Exception as e:
            logging.error(f"保存使用数据失败: {str(e)}", exc_info=True)
            return False

    def _atomic_save_usage_data(self, data):
        """原子性保存使用数据，使用文件锁防止多进程并发"""
        lock_file = self.usage_db_path + ".lock"
        temp_file = self.usage_db_path + ".tmp"
        max_retries = 3
        retry_delay = 0.1  # 秒

        for attempt in range(max_retries):
            try:
                # 尝试创建锁文件（独占创建）
                lock_fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                # 成功获取锁
                try:
                    # 确保目录存在
                    dir_path = os.path.dirname(self.usage_db_path)
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)

                    # 写入临时文件
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

                    # 原子性重命名（POSIX和Windows都保证原子性）
                    os.replace(temp_file, self.usage_db_path)

                    logging.info(f"原子保存成功，包含 {len(data)} 个用户的使用记录")
                    return
                finally:
                    # 释放锁：关闭文件描述符并删除锁文件
                    os.close(lock_fd)
                    try:
                        os.unlink(lock_file)
                    except:
                        pass

            except (OSError, IOError) as e:
                # 锁文件已存在，表示其他进程正在操作
                if attempt < max_retries - 1:
                    logging.debug(f"等待文件锁，重试 {attempt + 1}/{max_retries}")
                    time.sleep(retry_delay)
                else:
                    logging.warning(f"无法获取文件锁，使用线程锁保护的单进程保存")
                    # 降级方案：使用线程锁保护的标准保存
                    with self._lock:
                        self.save_usage_data(data)
                    return
            except Exception as e:
                logging.error(f"原子保存失败: {str(e)}", exc_info=True)
                raise RuntimeError(f"原子保存失败: {str(e)}")
    
    def is_user_allowed(self, username, password=None):
        """检查用户是否被允许使用"""
        logging.info(f"=== 登录验证开始 ===")
        logging.info(f"用户名: {username}")
        logging.info(f"输入密码: {'*****' if password else 'None'}")
        logging.info(f"所有用户: {list(self.allowed_users.keys())}")
        
        if username not in self.allowed_users:
            logging.error(f"用户不存在: {username}")
            return False, "用户不存在"
        
        user_data = self.allowed_users[username]
        logging.info(f"用户数据: {user_data}")
        
        if password is not None and user_data.get("password", "") != password:
            logging.error(f"密码不匹配！输入: '{password}', 存储: '{user_data.get('password', '')}'")
            return False, "密码错误"
        
        logging.info(f"密码验证通过！")
        
        # 检查账户有效期
        expiry_date_str = user_data.get('expiry_date', '2099-12-31')
        logging.info(f"检查账户有效期: {expiry_date_str}")
        
        if is_expired(expiry_date_str):
            logging.error(f"账户已过期: {expiry_date_str}")
            return False, f"账户已于 {expiry_date_str} 过期"
        
        logging.info("账户有效期检查通过")
        
        usage_data = self.load_usage_data()
        user_usage = usage_data.get(username, {"translations": 0})
        used_translations = user_usage["translations"]
        max_translations = user_data["max_translations"]
        logging.info(f"用户使用量检查: 已使用 {used_translations}/{max_translations} 次翻译")
        if used_translations >= max_translations:
            return False, f"已达到最大翻译次数限制 ({max_translations})"
        
        return True, "验证通过"
    
    def record_translation(self, username):
        """记录一次翻译使用，使用线程锁确保原子性"""
        # 添加类型检查和转换
        if hasattr(username, 'username'):
            username = username.username
        elif not isinstance(username, (str, int)):
            username = str(username)

        # 检查用户是否存在
        if username not in self.allowed_users:
            logging.error(f"用户 {username} 不在允许的用户列表中，无法记录翻译使用")
            raise ValueError(f"用户 {username} 不存在")

        # 使用可重入锁确保原子操作
        with self._lock:
            usage_data = self.load_usage_data()
            previous_count = usage_data.get(username, {"translations": 0})["translations"]

            if username not in usage_data:
                usage_data[username] = {"translations": 0}

            usage_data[username]["translations"] += 1
            new_count = usage_data[username]["translations"]

            logging.info(f"记录翻译使用: 用户 {username}, 之前次数: {previous_count}, 现在次数: {new_count}")

            # 保存使用数据，失败时抛出异常
            try:
                self._atomic_save_usage_data(usage_data)
                logging.info(f"翻译使用记录保存成功: 用户 {username}, 总使用次数: {new_count}")
            except Exception as e:
                logging.error(f"保存翻译使用记录失败，数据可能丢失！用户: {username}, 次数: {new_count}, 错误: {str(e)}")
                raise RuntimeError(f"无法保存翻译使用记录: {str(e)}")

            max_translations = self.allowed_users[username]["max_translations"]
            remaining = max_translations - new_count
            logging.info(f"用户 {username} 剩余翻译次数: {remaining}/{max_translations}")

            return remaining

    def get_user_info(self, username):
        """获取用户信息"""
        # 添加类型检查和转换
        if hasattr(username, 'username'):
            username = username.username
        elif not isinstance(username, (str, int)):
            username = str(username)
            
        if username not in self.allowed_users:
            return None
        
        user_data = self.allowed_users[username]
        usage_data = self.load_usage_data()
        user_usage = usage_data.get(username, {"translations": 0})
        used_translations = user_usage["translations"]
        max_translations = user_data["max_translations"]
        remaining = max_translations - used_translations

        logging.info(f"获取用户信息: {username}, 已使用 {used_translations}/{max_translations} 次翻译, 剩余 {remaining} 次")

        return {
            "username": username,
            "expiry_date": user_data["expiry_date"],
            "max_translations": max_translations,
            "used_translations": used_translations,
            "remaining_translations": remaining
        }
    
    def update_user(self, username: str, expiry_date: str = None, max_translations: int = None, password: str = None):
        """更新用户信息"""
        if username not in self.allowed_users:
            return False, "用户不存在"
        
        if expiry_date:
            self.allowed_users[username]["expiry_date"] = expiry_date
        if max_translations is not None:
            self.allowed_users[username]["max_translations"] = max_translations
        if password:
            self.allowed_users[username]["password"] = password
        
        # 这里应该持久化到文件或数据库
        # 简化起见，仅在内存中更新
        return True, "更新成功"
    
    def add_user(self, username: str, password: str, expiry_date: str, max_translations: int):
        """添加新用户"""
        if username in self.allowed_users:
            return False, "用户已存在"
        
        self.allowed_users[username] = {
            "expiry_date": expiry_date,
            "max_translations": max_translations,
            "password": password
        }
        
        return True, "添加成功"
    
    def get_all_users(self):
        """获取所有用户信息"""
        users = []
        usage_data = self.load_usage_data()
        
        for username in self.allowed_users:
            user_info = self.get_user_info(username)
            if user_info:
                users.append(user_info)
        
        return users

# ==========================================
# 速率限制器（按用户）
# ==========================================

class RateLimiter:
    """速率限制器 - 按用户控制API调用频率"""
    
    def __init__(self, max_calls=5, time_window=60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = {}  # {user_id: deque()}
    
    def is_allowed(self, user_id):
        """检查是否允许调用"""
        # 添加类型检查和转换
        if hasattr(user_id, 'username'):
            user_id = user_id.username
        elif not isinstance(user_id, (str, int)):
            user_id = str(user_id)
            
        current_time = time.time()
    
        if user_id not in self.calls:
            self.calls[user_id] = deque()
        
        user_calls = self.calls[user_id]
        
        # 清理过期记录
        while user_calls and user_calls[0] < current_time - self.time_window:
            user_calls.popleft()
        
        if len(user_calls) < self.max_calls:
            user_calls.append(current_time)
            return True, None
        
        next_available = user_calls[0] + self.time_window
        wait_time = int(max(0, next_available - current_time))
        return False, wait_time
    
    def reset(self, user_id: str):
        """重置指定用户的限制器"""
        # 添加类型检查和转换
        if hasattr(user_id, 'username'):
            user_id = user_id.username
        elif not isinstance(user_id, (str, int)):
            user_id = str(user_id)
            
        if user_id in self.calls:
            self.calls[user_id].clear()

# ==========================================
# 文本验证器
# ==========================================

class TextValidator:
    """文本验证器"""
    
    GEMINI_MAX_CHARS = 30000
    GPTZERO_MAX_CHARS = 25000
    UI_MAX_CHARS = 2000
    GEMINI_MIN_CHARS = 1
    GPTZERO_MIN_CHARS = 250
    
    @staticmethod
    def _validate_base(text, min_chars, max_chars, api_name):
        if not text or len(text.strip()) == 0:
            return False, "文本不能为空"
        
        text_length = len(text)
        
        if text_length < min_chars:
            return False, f"文本过短，{api_name} 要求至少 {min_chars} 字符，当前 {text_length} 字符"
        
        if text_length > max_chars:
            return False, f"文本过长，{api_name} 限制为 {max_chars} 字符，当前 {text_length} 字符"
        
        return True, "验证通过"
    
    @staticmethod
    def validate_for_gemini(text):
        return TextValidator._validate_base(
            text, 
            TextValidator.GEMINI_MIN_CHARS, 
            TextValidator.GEMINI_MAX_CHARS, 
            "Gemini API"
        )
    
    @staticmethod
    def validate_for_gptzero(text):
        return TextValidator._validate_base(
            text, 
            TextValidator.GPTZERO_MIN_CHARS, 
            TextValidator.GPTZERO_MAX_CHARS, 
            "GPTZero API"
        )

# ==========================================
# 缓存管理（模拟Streamlit缓存）
# ==========================================

class CacheManager:
    """简单的内存缓存管理器"""
    
    def __init__(self, ttl=3600, max_entries=100):
        self.cache = {}
        self.ttl = ttl
        self.max_entries = max_entries
    
    def get(self, key):
        """获取缓存"""
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                return entry["value"]
            else:
                del self.cache[key]
        return None
    
    def set(self, key, value):
        """设置缓存"""
        # 如果缓存满了，删除最旧的条目
        if len(self.cache) >= self.max_entries:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]
        
        self.cache[key] = {
            "value": value,
            "timestamp": time.time()
        }
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()

# ==========================================
# 全局实例
# ==========================================

user_manager = UserLimitManager()
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
# Prompt 构建函数（与原代码完全一致）
# ==========================================

def build_error_check_prompt(chinese_text):
    """构建用于智能纠错的提示词"""
    return f"""
    你是中文文本校对专家。请检查并直接修改以下文本中的三类错误：错别字、漏字和重复字。
    
    直接修改这三类错误，不要只是标记它们。同时，不要修改表达方式、语法结构或其他内容。
    不修改专业术语，不修改写作风格，不修改标点符号（除非明显错误）。
    
    输入文本:
    {chinese_text}
    
    输出格式:
    - 返回修改后的完整文本
    - 对于每处修改，用**双星号**将修改后的内容包围起来，例如"这是一个**正确**的例子"
    - 不要添加任何解释或评论，只返回修改后的文本
    - 如无错误，直接返回原文
    """

def build_academic_translate_prompt(chinese_text, style="US", version="professional"):
    """构建翻译提示词"""
    spelling_rule = "American Spelling (Color, Honor, Analyze)" if style == "US" else "British Spelling (Colour, Honour, Analyse)"
    
    if version == "basic":
        sentence_structure_guideline = """**Sentence Structure (Basic Rule)**: Strictly avoid using the "comma + verb-ing" structure (e.g., ", revealing trends"). Instead, use relative clauses (e.g., ", which revealed..."), coordination (e.g., "and revealed..."), or start new sentences where appropriate for better flow."""
    else:
        sentence_structure_guideline = """**Sentence Structure Variety (Balanced Rule)**: AI models often overuse the "comma + verb-ing" structure (e.g., ", revealing trends"). Do not strictly ban it, as it is valid in academic English, but **use it sparingly** to avoid a repetitive "AI tone." Instead, prioritize variety by using relative clauses (e.g., ", which revealed..."), coordination (e.g., "and revealed..."), or starting new sentences where appropriate for better flow."""
    
    return f"""
    You are an expert academic translator specializing in translating Chinese academic papers into English.
    
    **Task:** Translate the Chinese academic text into professional academic English.
    
    **Spelling Convention:** {spelling_rule}
    
    **Input (Chinese Academic Text):**
    {chinese_text}
    
    **TRANSLATION GUIDELINES:**
    1. **Academic Style**: Maintain formal academic tone appropriate for scholarly publications.
    2. **Technical Terminology**: Preserve specialized terminology and translate it accurately.
    3. **Paragraph Structure**: Maintain the original paragraph structure.
    4. **Citations**: Preserve any citation formats or references in their original form.
    5. **Natural Translation**: Focus on accuracy and clarity rather than stylistic concerns.
    6. {sentence_structure_guideline}
    7. **IMPORTANT - Remove Markdown**: Remove all Markdown formatting symbols like asterisks (*), double asterisks (**), underscores (_), etc. from the output. Provide clean text without any Markdown formatting.
    8. **Punctuation with Quotation Marks**: For general text (not formal citations), always place commas, periods, and other punctuation marks OUTSIDE of quotation marks, not inside. For example, use "example", not "example,". For formal citations, maintain the original citation style's punctuation rules.
    9. **Names Capitalization**: Always properly capitalize all personal names, organizational names, and proper nouns. Ensure that all names of people, institutions, theories named after people, etc. are correctly capitalized in the English translation.
    
    **Output:**
    Provide ONLY the translated English text without explanations, comments, or any Markdown formatting symbols.
    """

def preprocess_annotations(text):
    """将【】批注转换为更明确的格式，确保只与前面的句子关联"""
    # 处理【】格式批注
    processed = text
    for match in re.finditer(r'([^。！？.!?]+[。！？.!?]+)【([^】]*)】', processed):
        sentence = match.group(1)
        annotation = match.group(2)
        full_match = match.group(0)
        replacement = f"{sentence}[LOCAL INSTRUCTION ONLY FOR THIS SENTENCE: {annotation}]"
        processed = processed.replace(full_match, replacement)
    
    # 处理[]格式批注
    for match in re.finditer(r'([^。！？.!?]+[。！？.!?]+)\[([^\]]*)\]', processed):
        sentence = match.group(1)
        annotation = match.group(2)
        full_match = match.group(0)
        replacement = f"{sentence}[LOCAL INSTRUCTION ONLY FOR THIS SENTENCE: {annotation}]"
        processed = processed.replace(full_match, replacement)
    
    return processed

def build_english_refine_prompt(text_with_instructions, hidden_instructions="", annotations=None):
    """构建英文精修提示词，强化局部批注的限制性"""
    # 使用改进的预处理函数
    processed_text = preprocess_annotations(text_with_instructions)
    
    # 构建句子到批注的映射，用于提示词中的具体示例
    sentence_annotation_examples = ""
    if annotations and len(annotations) > 0:
        examples = []
        for i, anno in enumerate(annotations[:3]):  # 最多使用前3个批注作为例子
            sentence = anno['sentence'].strip()
            instruction = anno['content'].strip()
            examples.append(f"- 句子 \"{sentence}\" 有批注 \"{instruction}\"，只修改这个句子，其他句子保持不变")
        
        if examples:
            sentence_annotation_examples = "本文中的具体批注例子:\n" + "\n".join(examples)
    
    # 增强批注提示部分
    annotation_notice = ""
    if annotations and len(annotations) > 0:
        annotation_notice = f"""
**CRITICAL INSTRUCTION - LOCAL ANNOTATIONS DETECTED**

This text contains {len(annotations)} local instruction(s) marked with 【】 or [].

EXTREMELY IMPORTANT RULE:
- Each annotation MUST ONLY modify the SINGLE sentence it is attached to
- Other sentences MUST remain COMPLETELY UNCHANGED unless affected by global directives
- This is a HARD CONSTRAINT that cannot be violated under any circumstances

{sentence_annotation_examples}
"""

    hidden_section = ""
    if hidden_instructions:
        hidden_section = f"""
**GLOBAL DIRECTIVES (APPLY TO ENTIRE DOCUMENT):**

The following directives should be applied consistently throughout the ENTIRE document:

{hidden_instructions}
"""

    return f"""
{annotation_notice}

You are an expert academic editor specializing in academic papers and scholarly writing.

**CRITICAL INSTRUCTION TYPES:**

**TYPE 1: LOCAL INSTRUCTIONS (in 【】 or [])**
- These are ATTACHED to specific sentences
- ONLY modify the sentence that IMMEDIATELY PRECEDES the instruction marker
- Example: "This is a sentence.【make it more formal】" → ONLY modify "This is a sentence."
- NEVER apply these instructions to any other sentence in the document
- The instruction ONLY affects the ONE sentence or phrase it is directly attached to
- All other sentences MUST remain COMPLETELY UNCHANGED

**TYPE 2: GLOBAL DIRECTIVES (listed in the section below)**
- These apply to the ENTIRE document consistently
- Apply these to ALL sentences throughout the text

**CRITICAL RULE - READ CAREFULLY:**
When you see "Sentence A.【instruction X】 Sentence B.", the instruction X ONLY applies to Sentence A.
Sentence B and all other sentences should NOT be affected by instruction X.

{hidden_section}

**CONCRETE EXAMPLES:**

Example 1:
Input: "The study shows significant results.【use more academic vocabulary】 The data supports this conclusion."
Correct Output: "The study **demonstrates substantial findings**. The data supports this conclusion."
Wrong Output: "The study **demonstrates substantial findings**. The data **corroborates this assertion**." ← WRONG! The instruction should NOT affect the second sentence.

Example 2:
Input: "First sentence. Second sentence.【make it concise】 Third sentence."
Correct Output: "First sentence. **Concise version**. Third sentence."
Wrong Output: "**Short**. **Brief**. **Concise**." ← WRONG! Only the second sentence should be modified.

Example 3:
Input: "The research methodology was comprehensive.【add more detail】 The results were analyzed carefully."
Correct Output: "The research methodology was comprehensive, **including both quantitative and qualitative approaches**. The results were analyzed carefully."
Wrong Output: "The research methodology was comprehensive, **including both quantitative and qualitative approaches**. The results were analyzed carefully**, using statistical software and peer review**." ← WRONG! The instruction only applies to the first sentence.

**PROCESSING STEPS:**
1. Read the text sentence by sentence from beginning to end
2. For each sentence:
   - Check if there is a 【】 or [] marker IMMEDIATELY AFTER it (within the same line)
   - If YES: Apply that specific instruction to THAT SENTENCE ONLY, then move to the next sentence
   - If NO: Only apply the GLOBAL DIRECTIVES (if any), then move to the next sentence
3. After processing all sentences, remove all instruction markers (【】/[]) from the output
4. Highlight all modified parts with double asterisks (e.g., **modified text**)
5. Ensure smooth transitions and maintain professional academic tone

**OUTPUT REQUIREMENTS:**
- Highlight modified parts with **double asterisks**
- Output MUST be in ENGLISH only
- Maintain original meaning and intent
- NO explanations, NO comments, NO meta-text
- ONLY output the refined text itself

Now, please refine the following text, remembering that local instructions ONLY apply to the sentence they are attached to:
{processed_text}
"""

# ==========================================
# 快捷批注命令（与原代码完全一致）
# ==========================================

SHORTCUT_ANNOTATIONS = {
    "主语修正": "将所有抽象概念作为主语的句子改写为以人为主语。例如，将'The framework suggests...'改为'Researchers using this framework suggest...'",
    "句式修正": "查找并修改所有'逗号 + -ing'结构的句子以及同位语句式。例如，将'The data was analyzed, revealing trends'改为'The data was analyzed and revealed trends'或拆分为两个句子, 将'Mr. Wang, our new project manager, will arrive tomorrow'改为'Mr. Wang is our new project manager. He will arrive tomorrow'",
    "符号修正": "检查所有引号内容，确保逗号和句号放在闭合的引号之外。例如，将'Smith stated that \"this is important,\"'改为'Smith stated that \"this is important\",''",
    "丰富句式": "识别句子长度过于一致的段落，调整为混合使用短句(5-10词)、中等句(15-20词)和长句(25-30词)",
    "灵活表达": "在适当位置添加破折号、分号，或将某些句子改为以'And'、'But'、'However'开头，以增加文本的自然流动性",
    "同义替换": "识别并替换过于学术化或AI风格的词汇，使用更简洁自然的同义词。例如，将'utilize'改为'use'，将'conceptualize'改为'think about'",
    "去AI词汇": "【CRITICAL ANTI-AI STYLE GUIDE】\n\n1. **FORBIDDEN STRUCTURES**:\n   - Adverbs (including adverbs used as logical connectors)\n   - -ing forms used as nouns (gerunds used nominally)\n   - Adverb + verb/adjective structures\n   - Main clause + , + -ing form as adverbial clause (e.g., 'The data was analyzed, revealing trends')\n\n2. **SENTENCE STRUCTURE REQUIREMENTS**:\n   - Use clauses to enhance logical connections (e.g., '..., which in turn leads to...' instead of '... this [verb]')\n   - Connect grammatically complete but conceptually unfinished thoughts with semicolons (;) instead of periods\n   - Ensure smooth flow and logical coherence throughout the text\n\n3. **PUNCTUATION RULES**:\n   - Never place periods or commas inside quotation marks\n   - All punctuation must be placed outside quotation marks\n\n4. **PROFESSIONALISM REQUIREMENTS**:\n   - Use precise, professional terminology\n   - Avoid colloquial expressions and informal language\n\n5. **BANNED VOCABULARY (HIGH AI TRACE)**:\n   [Phrases]: 'my goal is to', 'look forward to', 'Building on this', 'Building on this foundation', 'intend to'\n   [Verbs]: 'permit', 'address', 'command', 'cultivate', 'demonstrate' (use sparingly if necessary), 'draw'/'drawn to' (meaning 'attract')\n   [Nouns/Adjectives]: 'deep comprehension', 'privilege', 'testament', 'commitment', 'tenure'\n   [Other]: 'master' (and derivatives meaning 'skill mastery'), 'thereby' / 'thereby doing'"
}

# ==========================================
# Gemini API 调用（与原代码完全一致）
# ==========================================

def generate_gemini_content_with_fallback(prompt, api_key=None, primary_model="gemini-2.5-pro", fallback_model="gemini-3-pro-preview"):
    """带容错的 Gemini 内容生成"""
    logging.info(f"尝试使用主要模型 {primary_model} 生成内容")

    # 安全设置 - 使用 google.genai 的类型
    safety_settings = [
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_NONE"
        }
    ]
    
    def _try_model(model_name):
        max_retries = 3
        retry_delay = 2  # 秒

        for attempt in range(max_retries):
            try:
                # 只使用传入的API密钥，不再使用环境变量
                current_api_key = api_key
                if not current_api_key:
                    raise GeminiAPIError("未提供 Gemini API Key，请在侧边栏输入", "missing_key")

                # 调试日志：记录API密钥信息（不记录完整密钥）
                key_prefix = current_api_key[:8] if len(current_api_key) > 8 else current_api_key[:len(current_api_key)]
                logging.info(f"使用请求头中的Gemini API密钥，前缀: {key_prefix}...")

                # 创建客户端
                client = google.genai.Client(api_key=current_api_key)

                # 准备配置（包括安全设置）
                config = {
                    "safety_settings": safety_settings
                }

                # 生成内容
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config
                )

                # 提取响应文本
                # 注意：response 结构可能不同，需要检查
                text = ""
                if hasattr(response, 'text'):
                    text = response.text
                elif hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            text = candidate.content.parts[0].text
                        elif hasattr(candidate.content, 'text'):
                            text = candidate.content.text

                return {"success": True, "text": text, "model_used": model_name}

            except Exception as e:
                error_msg = str(e).lower()

                # 服务不可用错误
                if "service unavailable" in error_msg or "503" in error_msg or "unavailable" in error_msg:
                    logging.error(f"模型 {model_name} - 服务不可用: {str(e)}")
                    raise GeminiAPIError(f"Google API服务暂时不可用，请稍后再试", "service_unavailable")

                # 超时错误（包括 DeadlineExceeded 和 requests Timeout）
                elif "timeout" in error_msg or "deadline" in error_msg or "timed out" in error_msg:
                    logging.error(f"模型 {model_name} - 请求超时 (尝试 {attempt+1}/{max_retries}): {str(e)}")
                    if attempt < max_retries - 1:
                        logging.info(f"等待 {retry_delay} 秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    raise GeminiAPIError("请求超时（默认60秒），请检查网络连接", "timeout")

                # 网络连接错误
                elif "connect" in error_msg or "socket" in error_msg or "network" in error_msg or "connection" in error_msg:
                    logging.error(f"模型 {model_name} - 网络连接错误 (尝试 {attempt+1}/{max_retries}): {str(e)}")
                    if attempt < max_retries - 1:
                        logging.info(f"等待 {retry_delay} 秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    error_message = "无法连接到Google API服务。"
                    error_message += "\n可能的原因："
                    error_message += "\n1. 网络连接问题 - 请检查您的互联网连接"
                    error_message += "\n2. 防火墙或网络设置 - 如果您在中国，可能需要VPN才能访问Google服务"
                    error_message += "\n3. Google服务暂时不可用 - 请稍后再试"
                    error_message += "\n\n解决方案："
                    error_message += "\n• 检查网络连接是否正常"
                    error_message += "\n• 如果使用VPN，请确保VPN连接稳定"
                    raise GeminiAPIError(error_message, "network_error")

                # API配额错误
                elif "quota" in error_msg or "resource_exhausted" in error_msg:
                    logging.error(f"模型 {model_name} - API 配额已用尽: {str(e)}")
                    raise GeminiAPIError("API 配额已用尽，请稍后再试", "quota")

                # 速率限制
                elif "429" in error_msg or "rate_limit" in error_msg or "too many requests" in error_msg:
                    logging.error(f"模型 {model_name} - 速率限制: {str(e)}")
                    raise RateLimitError("请求过于频繁，请稍后再试")

                # API密钥无效
                elif "invalid" in error_msg or "api_key" in error_msg or "permission" in error_msg or "unauthorized" in error_msg:
                    logging.error(f"模型 {model_name} - API Key 无效: {str(e)}")
                    raise GeminiAPIError("API Key 无效或已过期，请检查配置", "invalid_key")

                # 其他API错误
                elif "api" in error_msg or "google" in error_msg or "genai" in error_msg:
                    logging.error(f"模型 {model_name} - API 错误: {str(e)}")
                    raise GeminiAPIError(f"API 错误: {str(e)}", "api_error")

                # 未知错误
                else:
                    logging.error(f"模型 {model_name} - 未知错误: {str(e)}", exc_info=True)
                    raise GeminiAPIError(f"未知错误: {str(e)}", "unknown")





        # 如果所有重试都失败（理论上不应该到达这里）
        raise GeminiAPIError(f"所有 {max_retries} 次重试均失败", "all_retries_failed")
    
    # 尝试主要模型
    try:
        return _try_model(primary_model)
    
    except GeminiAPIError as e:
        if e.error_type in ["blocked", "invalid_key"]:
            return {"success": False, "error": e.message, "error_type": e.error_type}
        
        logging.warning(f"主要模型 {primary_model} 失败，尝试备用模型 {fallback_model}")
        
        try:
            return _try_model(fallback_model)
        except GeminiAPIError as fallback_error:
            return {"success": False, "error": fallback_error.message, "error_type": fallback_error.error_type}
        except Exception as fallback_error:
            logging.error(f"备用模型也失败: {str(fallback_error)}", exc_info=True)
            return {"success": False, "error": "所有模型尝试均失败，请稍后再试", "error_type": "all_failed"}
    
    except RateLimitError as e:
        return {"success": False, "error": str(e), "error_type": "rate_limit"}
    
    except Exception as e:
        logging.error(f"未知错误: {str(e)}", exc_info=True)
        return {"success": False, "error": "系统错误，请稍后再试", "error_type": "unknown"}

# ==========================================
# GPTZero API 调用（与原代码完全一致）
# ==========================================

def check_gptzero(text, api_key):
    """使用GPTZero检测AI内容"""
    is_valid, message = TextValidator.validate_for_gptzero(text)
    if not is_valid:
        if "过长" in message:
            text = text[:TextValidator.GPTZERO_MAX_CHARS]
            logging.warning("文本已截断至GPTZero API限制")
        else:
            return {"success": False, "message": message}
    
    url = "https://api.gptzero.me/v2/predict/text"
    headers = {
        "x-api-key": api_key,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = {"document": text}
    
    max_retries = 3
    retry_count = 0
    current_delay = 2
    
    while retry_count < max_retries:
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if "documents" in result:
                if isinstance(result["documents"], dict):
                    doc = result["documents"]
                elif isinstance(result["documents"], list) and len(result["documents"]) > 0:
                    doc = result["documents"][0]
                else:
                    return {"success": False, "message": "未知的API响应格式"}
                
                return {
                    "ai_score": doc.get("completely_generated_prob", 0),
                    "success": True,
                    "message": "检测成功",
                    "detailed_scores": doc.get("sentences", []),
                    "full_text": text
                }
            else:
                return {"success": False, "message": "API返回了未知格式的数据"}
                
        except requests.exceptions.Timeout:
            retry_count += 1
            if retry_count >= max_retries:
                logging.error("GPTZero API请求超时，已达到最大重试次数")
                return {"success": False, "message": "检测请求超时，请稍后再试"}
            logging.warning(f"GPTZero API超时，{current_delay}秒后重试 ({retry_count}/{max_retries})")
            time.sleep(current_delay)
            current_delay *= 2
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            if status_code == 401:
                return {"success": False, "message": "API Key 无效或已过期"}
            elif status_code == 429:
                return {"success": False, "message": "请求过于频繁，请稍后再试"}
            else:
                return {"success": False, "message": f"API 请求失败（状态码 {status_code}）"}
        
        except Exception as e:
            logging.error(f"GPTZero API调用异常: {str(e)}", exc_info=True)
            return {"success": False, "message": "系统错误，请稍后再试"}
    
    return {"success": False, "message": "检测失败，已达到最大重试次数"}

# ==========================================
# 辅助函数
# ==========================================

def generate_safe_hash(text, key):
    """生成安全的哈希值，用于缓存键"""
    text_hash = hashlib.sha256(str(text).encode()).hexdigest()[:20]
    key_hash = hashlib.sha256(str(key).encode()).hexdigest()[:10]
    return f"{text_hash}_{key_hash}"

def contains_annotation(text):
    """检测文本是否包含【】或[]形式的批注标记"""
    return ('【' in text and '】' in text) or ('[' in text and ']' in text)

def extract_annotations(text):
    """提取文本中的所有批注及其所属句子"""
    annotations = []
    
    # 匹配格式：任何以句号、感叹号或问号结尾的文本，后面紧跟【】批注
    for match in re.finditer(r'([^。！？.!?]+[。！？.!?]+)【([^】]*)】', text):
        sentence = match.group(1)
        annotation_content = match.group(2)
        annotations.append({
            'type': '【】',
            'sentence': sentence,
            'content': annotation_content,
            'start': match.start(),
            'end': match.end(),
            'full_match': match.group(0)
        })
    
    # 同样处理方括号格式
    for match in re.finditer(r'([^。！？.!?]+[。！？.!?]+)\[([^\]]*)\]', text):
        sentence = match.group(1)
        annotation_content = match.group(2)
        annotations.append({
            'type': '[]',
            'sentence': sentence,
            'content': annotation_content,
            'start': match.start(),
            'end': match.end(),
            'full_match': match.group(0)
        })
    
    # 记录详细日志
    if annotations:
        logging.info(f"提取到 {len(annotations)} 个批注:")
        for i, anno in enumerate(annotations):
            logging.info(f"批注 {i+1}: 句子='{anno['sentence']}', 内容='{anno['content']}'")
    
    return annotations

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
        # 检查管理员用户是否在允许的用户列表中
        if ADMIN_USERNAME not in user_manager.allowed_users:
            logging.warning(f"管理员用户 {ADMIN_USERNAME} 未在 ALLOWED_USERS 中定义")
            # 可以继续，因为管理员密码验证通过

        logging.info("管理员登录成功")
        # 创建JWT令牌，包含角色信息
        token_data = {"sub": data.username, "role": "admin"}
        access_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        # 获取管理员用户信息，如果不在 allowed_users 中则创建默认信息
        user_info = user_manager.get_user_info(data.username)
        if not user_info:
            # 创建默认的管理员用户信息
            user_info = {
                "username": data.username,
                "role": "admin",
                "expiry_date": "2099-12-31",
                "max_translations": 9999,
                "used_translations": 0,
                "remaining_translations": 9999
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
    allowed, message = user_manager.is_user_allowed(data.username, data.password)
    if allowed:
        logging.info(f"用户 {data.username} 登录成功")

        # 创建JWT令牌，普通用户角色
        token_data = {"sub": data.username, "role": "user"}
        access_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        # 获取完整的用户信息
        user_info = user_manager.get_user_info(data.username)
        if not user_info:
            # 如果获取失败，创建基本用户信息
            user_info = {
                "username": data.username,
                "role": "user",
                "expiry_date": "2099-12-31",
                "max_translations": 100,
                "used_translations": 0,
                "remaining_translations": 100
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
    user_info = user_manager.get_user_info(username)
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
    cache_key = generate_safe_hash(request.text, f"{request.operation}_{request.version}")
    
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

    # 优先从环境变量读取Gemini API密钥
    gemini_api_key = None
    source = "环境变量"

    # 首先尝试从环境变量读取
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if gemini_api_key:
        logging.info("从环境变量 GEMINI_API_KEY 获取到Gemini API密钥")
        source = "环境变量"
    else:
        # 如果环境变量不存在，从请求头中提取API密钥
        possible_headers = [
            "X-Gemini-Api-Key",
            "x-gemini-api-key",
            "X-GEMINI-API-KEY",
            "gemini-api-key",
            "Gemini-Api-Key"
        ]
        for header_name in possible_headers:
            value = http_request.headers.get(header_name)
            if value:
                gemini_api_key = value
                logging.info(f"从请求头 '{header_name}' 获取到Gemini API密钥")
                source = "请求头"
                break

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

    # 调试日志：记录API密钥信息
    key_prefix = gemini_api_key[:8] if len(gemini_api_key) > 8 else gemini_api_key[:len(gemini_api_key)]
    logging.info(f"从{source}获取到Gemini API密钥，前缀: {key_prefix}...")

    # 调用 Gemini API
    result = generate_gemini_content_with_fallback(prompt, api_key=gemini_api_key)

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
            remaining = user_manager.record_translation(username)
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
    annotations = extract_annotations(request.text)
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
    cache_key = generate_safe_hash(request.text, "_".join(request.directives))
    
    # 检查缓存
    cached_result = gemini_cache.get(cache_key)
    if cached_result:
        logging.info(f"使用缓存结果: {cache_key}")
        return cached_result

    # 优先从环境变量读取Gemini API密钥
    gemini_api_key = None
    source = "环境变量"

    # 首先尝试从环境变量读取
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if gemini_api_key:
        logging.info("从环境变量 GEMINI_API_KEY 获取到Gemini API密钥")
        source = "环境变量"
    else:
        # 如果环境变量不存在，从请求头中提取API密钥
        possible_headers = [
            "X-Gemini-Api-Key",
            "x-gemini-api-key",
            "X-GEMINI-API-KEY",
            "gemini-api-key",
            "Gemini-Api-Key"
        ]
        for header_name in possible_headers:
            value = http_request.headers.get(header_name)
            if value:
                gemini_api_key = value
                logging.info(f"从请求头 '{header_name}' 获取到Gemini API密钥")
                source = "请求头"
                break

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

    # 调试日志：记录API密钥信息
    key_prefix = gemini_api_key[:8] if len(gemini_api_key) > 8 else gemini_api_key[:len(gemini_api_key)]
    logging.info(f"从{source}获取到Gemini API密钥，前缀: {key_prefix}...")

    # 调用 Gemini API
    result = generate_gemini_content_with_fallback(prompt, api_key=gemini_api_key)

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
    cache_key = generate_safe_hash(request.text, "gptzero")

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

@app.get("/api/health")
async def health_check():
    """健康检查"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    # 检查 Gemini API
    try:
        # 测试是否能连接到 Google API 服务
        response = requests.get("https://generativelanguage.googleapis.com", timeout=5)
        # 即使返回 401/403 也说明服务可达
        if response.status_code >= 500:
            raise Exception(f"Google API 服务不可用 (状态码: {response.status_code})")
        health_status["checks"]["gemini_api"] = "ok"
    except Exception as e:
        health_status["checks"]["gemini_api"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # 检查 GPTZero API
    try:
        response = requests.get("https://api.gptzero.me/health", timeout=5)
        health_status["checks"]["gptzero_api"] = "ok" if response.status_code == 200 else "error"
    except Exception as e:
        health_status["checks"]["gptzero_api"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status

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
    
    users = user_manager.get_all_users()
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
    
    success, message = user_manager.update_user(
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
    
    success, message = user_manager.add_user(
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
