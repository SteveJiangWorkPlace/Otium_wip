"""
数据模型定义

包含所有Pydantic模型，用于请求/响应数据验证和序列化。
"""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

# ==========================================
# 请求模型
# ==========================================


class LoginRequest(BaseModel):
    """登录请求模型"""

    username: str = Field(min_length=1, description="用户名不能为空")
    password: str = Field(min_length=1, description="密码不能为空")


class CheckTextRequest(BaseModel):
    """文本检查请求模型"""

    text: str = Field(min_length=1, description="文本不能为空")
    operation: str  # "error_check", "translate_us", "translate_uk"
    version: str | None = "professional"


class RefineTextRequest(BaseModel):
    """文本润色请求模型"""

    text: str = Field(min_length=1, description="文本不能为空")
    directives: list[str] = []


class AIDetectionRequest(BaseModel):
    """AI检测请求模型"""

    text: str = Field(min_length=1, description="文本不能为空")


class AdminLoginRequest(BaseModel):
    """管理员登录请求模型"""

    password: str


class UpdateUserRequest(BaseModel):
    """更新用户请求模型"""

    username: str = Field(min_length=1, description="用户名不能为空")
    daily_translation_limit: int | None = None
    daily_ai_detection_limit: int | None = None
    password: str | None = None


class AddUserRequest(BaseModel):
    """添加用户请求模型"""

    username: str = Field(min_length=1, description="用户名不能为空")
    password: str = Field(min_length=1, description="密码不能为空")
    daily_translation_limit: int = 3
    daily_ai_detection_limit: int = 3


class SendVerificationRequest(BaseModel):
    """发送验证码请求模型"""

    email: str


class VerifyEmailRequest(BaseModel):
    """验证邮箱请求模型"""

    email: str
    code: str


class RegisterRequest(BaseModel):
    """注册请求模型"""

    username: str = Field(min_length=1, description="用户名不能为空")
    email: str = Field(min_length=1, description="邮箱不能为空")
    password: str = Field(min_length=1, description="密码不能为空")
    verification_token: str = Field(
        min_length=1, description="验证令牌不能为空"
    )  # 邮箱验证成功后获得的令牌


class PasswordResetRequest(BaseModel):
    """密码重置请求模型"""

    email: str


class ResetPasswordRequest(BaseModel):
    """重置密码请求模型"""

    token: str  # 重置令牌
    new_password: str


class CheckUsernameRequest(BaseModel):
    """检查用户名请求模型"""

    username: str = Field(min_length=1, description="用户名不能为空")


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
    created_at: str | None = None
    updated_at: str | None = None


class UserInfoWithEmail(BaseModel):
    """带邮箱的用户信息模型"""

    username: str
    email: str | None = None
    email_verified: bool = False
    daily_translation_limit: int
    daily_ai_detection_limit: int
    daily_translation_used: int
    daily_ai_detection_used: int
    is_admin: bool
    is_active: bool
    created_at: str | None = None
    updated_at: str | None = None


class VerificationResponse(BaseModel):
    """验证响应模型"""

    success: bool
    message: str
    verification_token: str | None = None  # 邮箱验证成功后的临时令牌


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
    username: str | None = None  # 重置成功的用户名


class ErrorResponse(BaseModel):
    """统一错误响应模型"""

    success: bool = False
    error_code: str
    message: str
    details: dict[str, Any] | None = None


# ==========================================
# 通用响应模型
# ==========================================


class SuccessResponse(BaseModel):
    """成功响应模型"""

    success: bool = True
    message: str | None = None
    data: dict[str, Any] | None = None


class CheckTextResponse(BaseModel):
    """文本检查响应模型"""

    original_text: str
    processed_text: str
    annotations: list[dict[str, Any]]


class RefineTextResponse(BaseModel):
    """文本润色响应模型"""

    original_text: str
    refined_text: str
    changes: list[dict[str, Any]]


class AIDetectionResponse(BaseModel):
    """AI检测响应模型"""

    text: str
    ai_probability: float = Field(ge=0.0, le=1.0, description="AI生成概率，范围0.0-1.0")
    is_ai_generated: bool
    details: dict[str, Any]

    @field_validator("is_ai_generated")
    @classmethod
    def validate_is_ai_generated(cls, v):
        """验证is_ai_generated字段为布尔类型，防止字符串自动转换"""
        if not isinstance(v, bool):
            raise ValueError("is_ai_generated必须是布尔值")
        return v


# ==========================================
# 统计和管理模型
# ==========================================


class UsageStats(BaseModel):
    """使用统计模型"""

    total_users: int
    active_users: int
    total_translations: int
    recent_translations: list[dict[str, Any]]


class TranslationDirective(BaseModel):
    """翻译指令模型"""

    id: str
    name: str
    description: str
    content: str
    is_active: bool = True
    created_at: str | None = None
    updated_at: str | None = None


# ==========================================
# AI聊天模型
# ==========================================


class AIChatMessage(BaseModel):
    """AI聊天消息模型"""

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class AIChatRequest(BaseModel):
    """AI聊天请求模型"""

    messages: list[AIChatMessage] = Field(min_length=1, description="消息列表不能为空")
    session_id: str | None = None  # 可选，用于保持对话上下文
    literature_research_mode: bool = Field(
        default=False, description="文献调研模式开关，使用Manus API进行文献调研式回复"
    )
    generate_literature_review: bool = Field(
        default=False, description="生成文献综述选项，控制文献调研输出格式"
    )


class AIChatResponse(BaseModel):
    """AI聊天响应模型"""

    success: bool
    text: str
    session_id: str | None = None
    model_used: str
    error: str | None = None
    steps: list[str] | None = None  # Manus API步骤信息，仅文献调研模式使用


class BackgroundTaskResponse(BaseModel):
    """后台任务创建响应模型"""

    success: bool
    message: str
    task_id: int | None = None  # 任务ID，用于后续查询状态
    status: str | None = None  # 任务状态：pending, processing, completed, failed
    estimated_time: int | None = None  # 预估处理时间（秒）


class TaskStatusResponse(BaseModel):
    """任务状态查询响应模型"""

    success: bool
    task_id: int
    status: str  # pending, processing, completed, failed
    progress: float | None = None  # 进度百分比0-100
    step_description: str | None = None  # 当前步骤描述
    step_details: dict[str, Any] | None = None  # 详细步骤信息（JSON对象）
    current_step: int | None = None  # 当前步骤索引（从0开始）
    total_steps: int | None = None  # 总步骤数
    result_data: dict[str, Any] | None = None  # AI任务的处理结果数据，包含文本翻译、纠错或润色的具体输出内容
    error_message: str | None = None  # 错误信息
    started_at: str | None = None  # 任务开始处理的ISO格式时间戳，用于计算任务执行时长和监控性能
    completed_at: str | None = None  # 完成时间
    estimated_remaining_time: int | None = None  # 预估剩余时间（秒）


class TaskPollRequest(BaseModel):
    """任务轮询请求模型"""

    task_id: int


# ==========================================
# 流式翻译模型
# ==========================================


class StreamTranslationRequest(BaseModel):
    """流式翻译请求模型"""

    text: str = Field(min_length=1, description="文本不能为空")
    operation: str  # "translate_us", "translate_uk"
    version: str | None = "professional"


class StreamTranslationChunk(BaseModel):
    """流式翻译数据块模型"""

    type: str  # "chunk", "sentence", "complete", "error"
    text: str | None = None
    full_text: str | None = None
    index: int | None = None  # 句子索引
    total: int | None = None  # 总句子数
    chunk_index: int | None = None  # 块索引
    error: str | None = None
    error_type: str | None = None
    total_sentences: int | None = None


# ==========================================
# 流式文本修改模型
# ==========================================


class StreamRefineTextRequest(BaseModel):
    """流式文本修改请求模型"""

    text: str = Field(min_length=1, description="文本不能为空")
    directives: list[str] = []


class StreamRefineTextChunk(BaseModel):
    """流式文本修改数据块模型"""

    type: str  # "chunk", "sentence", "complete", "error"
    text: str | None = None
    full_text: str | None = None
    index: int | None = None  # 句子索引
    total: int | None = None  # 总句子数
    chunk_index: int | None = None  # 块索引
    error: str | None = None
    error_type: str | None = None
    total_sentences: int | None = None
