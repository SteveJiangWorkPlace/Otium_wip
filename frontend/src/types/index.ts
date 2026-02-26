import { AxiosError } from 'axios';

// ==================== 基础类型 ====================

// 翻译指令类型
export interface TranslationDirective {
  id: string;
  name: string;
  prompt: string;
  category?: string;
}

// ==================== 请求类型 ====================

// 文本检查请求（纠错/翻译）
export interface CheckTextRequest {
  text: string;
  operation: 'error_check' | 'translate_us' | 'translate_uk';
  version?: 'professional' | 'basic';
}

// 文本润色请求
export interface RefineTextRequest {
  text: string;
  directives: string[];
}

// AI 检测请求
export interface AIDetectionRequest {
  text: string;
}

// AI聊天消息（API格式）
export interface AIChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

// AI聊天请求
export interface AIChatRequest {
  messages: AIChatMessage[];
  session_id?: string;
  deep_research_mode?: boolean; // 文献调研模式开关，使用Manus API进行文献调研式回复
  generate_literature_review?: boolean; // 生成文献综述选项，控制文献调研输出格式
}

// AI聊天响应
export interface AIChatResponse {
  success: boolean;
  text: string;
  session_id?: string;
  model_used: string;
  error?: string;
  steps?: string[]; // Manus API步骤信息，仅文献调研模式使用
}

// 流式翻译请求
export interface StreamTranslationRequest {
  text: string;
  operation: 'translate_us' | 'translate_uk';
  version?: 'professional' | 'basic';
}

// 流式翻译数据块
export interface StreamTranslationChunk {
  type: 'chunk' | 'sentence' | 'complete' | 'error';
  text?: string;
  full_text?: string;
  index?: number; // 句子索引
  total?: number; // 总句子数
  chunk_index?: number; // 块索引
  error?: string;
  error_type?: string;
  total_sentences?: number;
}

// 流式文本修改请求
export interface StreamRefineTextRequest {
  text: string;
  directives: string[];
}

// 流式文本修改数据块
export interface StreamRefineTextChunk {
  type: 'chunk' | 'sentence' | 'complete' | 'error';
  text?: string;
  full_text?: string;
  index?: number; // 句子索引
  total?: number; // 总句子数
  chunk_index?: number; // 块索引
  error?: string;
  error_type?: string;
  total_sentences?: number;
}

// 用户登录请求
export interface LoginRequest {
  username: string;
  password: string;
}

// 管理员登录请求
export interface AdminLoginRequest {
  password: string;
}

// 发送验证码请求
export interface SendVerificationRequest {
  email: string;
}

// 验证邮箱请求
export interface VerifyEmailRequest {
  email: string;
  code: string;
}

// 注册请求
export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  verification_token: string;
}

// 密码重置请求
export interface PasswordResetRequest {
  email: string;
}

// 重置密码请求
export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

// 检查用户名请求
export interface CheckUsernameRequest {
  username: string;
}

// ==================== 响应类型 ====================

// 文本处理响应
export interface CheckTextResponse {
  success: boolean;
  text: string;
  remaining_translations?: number;
  message?: string;
}

// 文本润色响应
export interface RefineTextResponse {
  success: boolean;
  text: string;
  message?: string;
}

// AI 检测响应（完整版本）
export interface AIDetectionResponse {
  success?: boolean;
  is_ai_generated: boolean;
  confidence: number;
  details: string;
  ai_score?: number; // AI 特征分数（0-1）
  full_text?: string; // 完整文本
  detailed_scores?: Array<{
    // 每句话的详细分数
    sentence: string;
    generated_prob: number;
  }>;
}

// 登录响应
export interface LoginResponse {
  success: boolean;
  token: string;
  user_info?: UserInfo;
  message?: string;
}

// 用户信息
export interface UserInfo {
  username: string;
  daily_translation_limit: number;
  daily_ai_detection_limit: number;
  daily_translation_used: number;
  daily_ai_detection_used: number;
  is_admin: boolean;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

// 带邮箱的用户信息
export interface UserInfoWithEmail {
  username: string;
  email?: string;
  email_verified?: boolean;
  daily_translation_limit: number;
  daily_ai_detection_limit: number;
  daily_translation_used: number;
  daily_ai_detection_used: number;
  is_admin: boolean;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

// 验证响应
export interface VerificationResponse {
  success: boolean;
  message: string;
  verification_token?: string;
}

// 检查用户名响应
export interface CheckUsernameResponse {
  available: boolean;
  message: string;
}

// 检查邮箱响应
export interface CheckEmailResponse {
  available: boolean;
  message: string;
}

// 密码重置响应
export interface PasswordResetResponse {
  success: boolean;
  message: string;
  username?: string;
}

// ==================== 管理员相关 ====================

// 使用统计
export interface UsageStats {
  total_translations: number;
  total_ai_detections: number;
  user_count: number;
  daily_stats: DailyStats[];
}

// 每日统计
export interface DailyStats {
  date: string;
  translations: number;
  ai_detections: number;
}

// ==================== 通用响应 ====================

// API 响应基础类型
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// API 错误类型（兼容新旧格式）
export interface ApiError {
  // 旧格式字段
  detail: string | Record<string, any>;
  status?: number;

  // 新统一错误响应格式
  success?: boolean;
  error_code?: string;
  message?: string;
  details?: Record<string, any>;
}

// ==================== 导出 Axios 错误类型 ====================
export type { AxiosError };
