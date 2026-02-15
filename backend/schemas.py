"""
数据模型定义

包含所有Pydantic模型，用于请求/响应数据验证和序列化。
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# ==========================================
# 请求模型
# ==========================================

class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str
    password: str


class CheckTextRequest(BaseModel):
    """文本检查请求模型"""
    text: str
    operation: str  # "error_check", "translate_us", "translate_uk"
    version: Optional[str] = "professional"


class RefineTextRequest(BaseModel):
    """文本润色请求模型"""
    text: str
    directives: List[str] = []


class AIDetectionRequest(BaseModel):
    """AI检测请求模型"""
    text: str


class AdminLoginRequest(BaseModel):
    """管理员登录请求模型"""
    password: str


class UpdateUserRequest(BaseModel):
    """更新用户请求模型"""
    username: str
    daily_translation_limit: Optional[int] = None
    daily_ai_detection_limit: Optional[int] = None
    password: Optional[str] = None


class AddUserRequest(BaseModel):
    """添加用户请求模型"""
    username: str
    password: str
    daily_translation_limit: int = 10
    daily_ai_detection_limit: int = 10


class SendVerificationRequest(BaseModel):
    """发送验证码请求模型"""
    email: str


class VerifyEmailRequest(BaseModel):
    """验证邮箱请求模型"""
    email: str
    code: str


class RegisterRequest(BaseModel):
    """注册请求模型"""
    username: str
    email: str
    password: str
    verification_token: str  # 邮箱验证成功后获得的令牌


class PasswordResetRequest(BaseModel):
    """密码重置请求模型"""
    email: str


class ResetPasswordRequest(BaseModel):
    """重置密码请求模型"""
    token: str  # 重置令牌
    new_password: str


class CheckUsernameRequest(BaseModel):
    """检查用户名请求模型"""
    username: str


# ==========================================
# 响应模型
# ==========================================

class UserInfo(BaseModel):
    """用户信息模型"""
    username: str
    daily_translation_limit: int
    daily_ai_detection_limit: int
    daily_translation_used: int
    daily_ai_detection_used: int
    is_admin: bool
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class UserInfoWithEmail(BaseModel):
    """带邮箱的用户信息模型"""
    username: str
    email: Optional[str] = None
    email_verified: bool = False
    daily_translation_limit: int
    daily_ai_detection_limit: int
    daily_translation_used: int
    daily_ai_detection_used: int
    is_admin: bool
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class VerificationResponse(BaseModel):
    """验证响应模型"""
    success: bool
    message: str
    verification_token: Optional[str] = None  # 邮箱验证成功后的临时令牌


class CheckUsernameResponse(BaseModel):
    """检查用户名响应模型"""
    available: bool
    message: str


class CheckEmailResponse(BaseModel):
    """检查邮箱响应模型"""
    available: bool
    message: str


class PasswordResetResponse(BaseModel):
    """密码重置响应模型"""
    success: bool
    message: str
    username: Optional[str] = None  # 重置成功的用户名


class ErrorResponse(BaseModel):
    """统一错误响应模型"""
    success: bool = False
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None


# ==========================================
# 通用响应模型
# ==========================================

class SuccessResponse(BaseModel):
    """成功响应模型"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class CheckTextResponse(BaseModel):
    """文本检查响应模型"""
    original_text: str
    processed_text: str
    annotations: List[Dict[str, Any]]


class RefineTextResponse(BaseModel):
    """文本润色响应模型"""
    original_text: str
    refined_text: str
    changes: List[Dict[str, Any]]


class AIDetectionResponse(BaseModel):
    """AI检测响应模型"""
    text: str
    ai_probability: float
    is_ai_generated: bool
    details: Dict[str, Any]


# ==========================================
# 统计和管理模型
# ==========================================

class UsageStats(BaseModel):
    """使用统计模型"""
    total_users: int
    active_users: int
    total_translations: int
    recent_translations: List[Dict[str, Any]]


class TranslationDirective(BaseModel):
    """翻译指令模型"""
    id: str
    name: str
    description: str
    content: str
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ==========================================
# AI聊天模型
# ==========================================

class AIChatMessage(BaseModel):
    """AI聊天消息模型"""
    role: str  # "user"或"assistant"
    content: str


class AIChatRequest(BaseModel):
    """AI聊天请求模型"""
    messages: List[AIChatMessage]
    session_id: Optional[str] = None  # 可选，用于保持对话上下文


class AIChatResponse(BaseModel):
    """AI聊天响应模型"""
    success: bool
    text: str
    session_id: Optional[str] = None
    model_used: str
    error: Optional[str] = None


# ==========================================
# 流式翻译模型
# ==========================================

class StreamTranslationRequest(BaseModel):
    """流式翻译请求模型"""
    text: str
    operation: str  # "translate_us", "translate_uk"
    version: Optional[str] = "professional"


class StreamTranslationChunk(BaseModel):
    """流式翻译数据块模型"""
    type: str  # "chunk", "sentence", "complete", "error"
    text: Optional[str] = None
    full_text: Optional[str] = None
    index: Optional[int] = None  # 句子索引
    total: Optional[int] = None  # 总句子数
    chunk_index: Optional[int] = None  # 块索引
    error: Optional[str] = None
    error_type: Optional[str] = None
    total_sentences: Optional[int] = None


# ==========================================
# 流式文本修改模型
# ==========================================

class StreamRefineTextRequest(BaseModel):
    """流式文本修改请求模型"""
    text: str
    directives: List[str] = []


class StreamRefineTextChunk(BaseModel):
    """流式文本修改数据块模型"""
    type: str  # "chunk", "sentence", "complete", "error"
    text: Optional[str] = None
    full_text: Optional[str] = None
    index: Optional[int] = None  # 句子索引
    total: Optional[int] = None  # 总句子数
    chunk_index: Optional[int] = None  # 块索引
    error: Optional[str] = None
    error_type: Optional[str] = None
    total_sentences: Optional[int] = None