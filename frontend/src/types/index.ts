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
}

// AI聊天响应
export interface AIChatResponse {
  success: boolean;
  text: string;
  session_id?: string;
  model_used: string;
  error?: string;
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
  ai_score?: number;          // AI 特征分数（0-1）
  full_text?: string;         // 完整文本
  detailed_scores?: Array<{   // 每句话的详细分数
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