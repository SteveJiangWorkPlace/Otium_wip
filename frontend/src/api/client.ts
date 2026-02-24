import axios, { AxiosError } from 'axios';
import { useAuthStore } from '../store/useAuthStore';
import type {
  CheckTextRequest,
  CheckTextResponse,
  RefineTextRequest,
  RefineTextResponse,
  AIDetectionRequest,
  AIDetectionResponse,
  LoginRequest,
  LoginResponse,
  AdminLoginRequest,
  UsageStats,
  TranslationDirective,
  ApiResponse,
  ApiError,
  UserInfo,
  AIChatRequest,
  AIChatResponse,
  StreamTranslationRequest,
  StreamTranslationChunk,
  StreamRefineTextRequest,
  StreamRefineTextChunk,
} from '../types';

console.log(
  'API客户端模块加载 - 环境变量REACT_APP_API_BASE_URL:',
  process.env.REACT_APP_API_BASE_URL
);

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
console.log('API客户端 - 使用的基础URL:', API_BASE_URL);

const axiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 300000, // 增加超时时间到300秒（5分钟），避免API调用超时
  headers: {
    'Content-Type': 'application/json',
  },
});

// 合并两个拦截器的逻辑，统一处理 token 和 API keys
axiosInstance.interceptors.request.use(
  (config) => {
    console.log('请求拦截器执行 - 请求URL:', config.url);
    console.log('请求拦截器执行 - 请求方法:', config.method);

    // 检查所有可能的 token 存储位置
    const token =
      localStorage.getItem('token') ||
      localStorage.getItem('auth_token') ||
      localStorage.getItem('admin_token');

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // 添加 API 密钥到请求头
    try {
      const apiKeysStr = localStorage.getItem('otium_api_keys');
      console.log(
        '请求拦截器 - 检查用户自定义API密钥 (otium_api_keys):',
        apiKeysStr ? '已设置' : '未设置（使用后端默认密钥）'
      );

      // 调试：列出所有localStorage项
      console.log('请求拦截器 - localStorage所有键:', Object.keys(localStorage));

      if (apiKeysStr) {
        const apiKeys = JSON.parse(apiKeysStr);
        console.log('请求拦截器 - 解析后的API密钥对象:', {
          hasGeminiApiKey: !!(apiKeys.geminiApiKey && apiKeys.geminiApiKey.trim()),
          hasGptzeroApiKey: !!(apiKeys.gptzeroApiKey && apiKeys.gptzeroApiKey.trim()),
          geminiLength: apiKeys.geminiApiKey ? apiKeys.geminiApiKey.length : 0,
          gptzeroLength: apiKeys.gptzeroApiKey ? apiKeys.gptzeroApiKey.length : 0,
          geminiKeyPreview: apiKeys.geminiApiKey
            ? `${apiKeys.geminiApiKey.substring(0, Math.min(5, apiKeys.geminiApiKey.length))}...`
            : '空',
          gptzeroKeyPreview: apiKeys.gptzeroApiKey
            ? `${apiKeys.gptzeroApiKey.substring(0, Math.min(5, apiKeys.gptzeroApiKey.length))}...`
            : '空',
        });

        if (apiKeys.geminiApiKey && apiKeys.geminiApiKey.trim() !== '') {
          const keyPrefix = apiKeys.geminiApiKey.substring(
            0,
            Math.min(8, apiKeys.geminiApiKey.length)
          );
          console.log('请求拦截器 - 设置X-Gemini-Api-Key头部，密钥前缀:', keyPrefix + '...');
          config.headers['X-Gemini-Api-Key'] = apiKeys.geminiApiKey;
          console.log('请求拦截器 - 已设置X-Gemini-Api-Key头部');
        } else {
          console.log('请求拦截器 - geminiApiKey为空或未设置');
        }

        if (apiKeys.gptzeroApiKey && apiKeys.gptzeroApiKey.trim() !== '') {
          const keyPrefix = apiKeys.gptzeroApiKey.substring(
            0,
            Math.min(8, apiKeys.gptzeroApiKey.length)
          );
          console.log('请求拦截器 - 设置X-Gptzero-Api-Key头部，密钥前缀:', keyPrefix + '...');
          config.headers['X-Gptzero-Api-Key'] = apiKeys.gptzeroApiKey;
          console.log('请求拦截器 - 已设置X-Gptzero-Api-Key头部');
        } else {
          console.log('请求拦截器 - gptzeroApiKey为空或未设置');
        }
      } else {
        console.log('请求拦截器 - 用户自定义API密钥未设置，将使用后端默认API密钥');
      }

      // 调试：打印所有请求头
      console.log('请求拦截器 - 最终的请求头:', JSON.stringify(config.headers, null, 2));
    } catch (error) {
      console.error('Failed to parse API keys from localStorage:', error);
    }

    return config;
  },
  (error) => Promise.reject(error)
);

axiosInstance.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const { response } = error;
    const status = response?.status;

    // 统一错误消息提取
    const extractErrorMessage = (): string => {
      if (!response) return '网络错误，请检查连接';

      const data = response.data;

      // 尝试从新统一错误格式提取
      if (data && typeof data === 'object') {
        // 优先使用 message 字段（新格式）
        if (typeof data.message === 'string' && data.message) {
          return data.message;
        }

        // 处理 detail 字段
        if (data.detail) {
          // detail 是字符串（旧格式）
          if (typeof data.detail === 'string') {
            return data.detail;
          }
          // detail 是对象（可能是新格式的字符串化）
          if (typeof data.detail === 'object') {
            const detailObj = data.detail as Record<string, any>;
            if (typeof detailObj.message === 'string' && detailObj.message) {
              return detailObj.message;
            }
            // 如果对象没有 message 字段，尝试序列化或使用默认
            return JSON.stringify(detailObj);
          }
        }
      }

      // 默认错误消息
      switch (status) {
        case 400:
          return '请求参数错误';
        case 401:
          return '未授权，请重新登录';
        case 403:
          return '权限不足';
        case 404:
          return '请求的资源不存在';
        case 429:
          return '请求过于频繁，请稍后重试';
        case 500:
          return '服务器内部错误';
        case 502:
          return '网关错误';
        case 503:
          return '服务不可用';
        case 504:
          return '网关超时';
        default:
          return `请求失败（状态码：${status}）`;
      }
    };

    // 429 错误自动重试
    if (status === 429) {
      const maxRetries = 3;
      const retryCount = (error.config as any)?._retryCount || 0;

      if (retryCount < maxRetries) {
        // 计算等待时间（秒）
        const retryAfterHeader = (response?.headers as any)?.['retry-after'];
        const retryAfter = retryAfterHeader
          ? parseInt(retryAfterHeader, 10)
          : Math.pow(2, retryCount); // 指数退避：1, 2, 4 秒

        console.log(`429 错误，${retryAfter} 秒后重试 (${retryCount + 1}/${maxRetries})`);

        // 标记重试计数
        const newConfig = {
          ...error.config,
          _retryCount: retryCount + 1,
        };

        // 等待后重试
        await new Promise((resolve) => setTimeout(resolve, retryAfter * 1000));
        return axiosInstance.request(newConfig);
      }
    }

    // 401 错误统一跳转登录
    if (status === 401) {
      // 调用logout函数清除所有认证状态和store状态
      try {
        useAuthStore.getState().logout();
      } catch (error) {
        console.error('调用logout时出错:', error);
        // 保底：清除token
        localStorage.removeItem('token');
        localStorage.removeItem('auth_token');
        localStorage.removeItem('admin_token');
      }
      window.location.href = '/login';
      error.message = '未授权，请重新登录';
      return Promise.reject(error);
    }

    // 其他错误：统一错误消息并拒绝
    const errorMessage = extractErrorMessage();
    error.message = errorMessage;
    return Promise.reject(error);
  }
);

// 将 apiClient 定义为普通对象，不使用默认导出
export const apiClient = {
  // ==================== 用户认证 ====================

  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await axiosInstance.post<LoginResponse>('/login', data);
    return response.data;
  },

  adminLogin: async (data: AdminLoginRequest): Promise<LoginResponse> => {
    const response = await axiosInstance.post<LoginResponse>('/admin/login', data);
    return response.data;
  },

  // ==================== 用户注册和密码重置 ====================

  sendVerificationCode: async (email: string): Promise<ApiResponse> => {
    const response = await axiosInstance.post<ApiResponse>('/register/send-verification', {
      email,
    });
    return response.data;
  },

  verifyEmail: async (
    email: string,
    code: string
  ): Promise<ApiResponse & { verification_token?: string }> => {
    const response = await axiosInstance.post<ApiResponse & { verification_token?: string }>(
      '/register/verify-email',
      { email, code }
    );
    return response.data;
  },

  checkUsername: async (username: string): Promise<{ available: boolean; message: string }> => {
    const response = await axiosInstance.get('/register/check-username', { params: { username } });
    return response.data;
  },

  checkEmail: async (email: string): Promise<{ available: boolean; message: string }> => {
    const response = await axiosInstance.get('/register/check-email', { params: { email } });
    return response.data;
  },

  register: async (
    username: string,
    email: string,
    password: string,
    verificationToken: string
  ): Promise<LoginResponse> => {
    const response = await axiosInstance.post<LoginResponse>('/register', {
      username,
      email,
      password,
      verification_token: verificationToken,
    });
    return response.data;
  },

  requestPasswordReset: async (email: string): Promise<ApiResponse & { username?: string }> => {
    const response = await axiosInstance.post<ApiResponse & { username?: string }>(
      '/password/reset-request',
      { email }
    );
    return response.data;
  },

  resetPassword: async (
    token: string,
    newPassword: string
  ): Promise<ApiResponse & { username?: string }> => {
    const response = await axiosInstance.post<ApiResponse & { username?: string }>(
      '/password/reset',
      {
        token,
        new_password: newPassword,
      }
    );
    return response.data;
  },

  // ==================== 文本处理 ====================

  checkText: async (data: CheckTextRequest): Promise<CheckTextResponse> => {
    const response = await axiosInstance.post<CheckTextResponse>('/text/check', data);
    return response.data;
  },

  translateStream: async function* (
    data: StreamTranslationRequest,
    options?: {
      onProgress?: (chunk: StreamTranslationChunk) => void;
      signal?: AbortSignal;
    }
  ) {
    const { onProgress, signal } = options || {};

    // 获取认证token和API密钥
    const token =
      localStorage.getItem('token') ||
      localStorage.getItem('auth_token') ||
      localStorage.getItem('admin_token');

    const apiKeysStr = localStorage.getItem('otium_api_keys');
    const apiKeys = apiKeysStr ? JSON.parse(apiKeysStr) : {};
    const geminiApiKey = apiKeys.geminiApiKey;

    // 构建请求头
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (geminiApiKey && geminiApiKey.trim()) {
      headers['X-Gemini-Api-Key'] = geminiApiKey;
    }

    // 使用 fetch API 进行流式请求
    const response = await fetch(`${API_BASE_URL}/api/text/translate-stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
      signal,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`流式翻译请求失败: ${response.status} ${errorText}`);
    }

    if (!response.body) {
      throw new Error('响应体不可读');
    }

    // 创建读取器
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.substring(6).trim();
            if (jsonStr) {
              try {
                const chunkData: StreamTranslationChunk = JSON.parse(jsonStr);
                if (onProgress) {
                  onProgress(chunkData);
                }
                yield chunkData;
              } catch (e) {
                console.error('解析SSE数据失败:', e, '原始数据:', jsonStr);
              }
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  },

  refineStream: async function* (
    data: StreamRefineTextRequest,
    options?: {
      onProgress?: (chunk: StreamRefineTextChunk) => void;
      signal?: AbortSignal;
    }
  ) {
    const { onProgress, signal } = options || {};

    // 获取认证token和API密钥
    const token =
      localStorage.getItem('token') ||
      localStorage.getItem('auth_token') ||
      localStorage.getItem('admin_token');

    const apiKeysStr = localStorage.getItem('otium_api_keys');
    const apiKeys = apiKeysStr ? JSON.parse(apiKeysStr) : {};
    const geminiApiKey = apiKeys.geminiApiKey;

    // 构建请求头
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (geminiApiKey && geminiApiKey.trim()) {
      headers['X-Gemini-Api-Key'] = geminiApiKey;
    }

    // 使用 fetch API 进行流式请求
    const response = await fetch(`${API_BASE_URL}/api/text/refine-stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
      signal,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`流式文本修改请求失败: ${response.status} ${errorText}`);
    }

    if (!response.body) {
      throw new Error('响应体不可读');
    }

    // 创建读取器
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.substring(6).trim();
            if (jsonStr) {
              try {
                const chunkData: StreamRefineTextChunk = JSON.parse(jsonStr);
                if (onProgress) {
                  onProgress(chunkData);
                }
                yield chunkData;
              } catch (e) {
                console.error('解析SSE数据失败:', e, '原始数据:', jsonStr);
              }
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  },

  refineText: async (data: RefineTextRequest): Promise<RefineTextResponse> => {
    const response = await axiosInstance.post<RefineTextResponse>('/text/refine', data);
    return response.data;
  },

  detectAI: async (data: AIDetectionRequest): Promise<AIDetectionResponse> => {
    const response = await axiosInstance.post<AIDetectionResponse>('/text/detect-ai', data);
    return response.data;
  },

  // ==================== AI聊天 ====================
  chat: async (data: AIChatRequest): Promise<AIChatResponse> => {
    const response = await axiosInstance.post<AIChatResponse>('/chat', data);
    return response.data;
  },

  // ==================== 指令管理 ====================

  getDirectives: async (): Promise<TranslationDirective[]> => {
    const response = await axiosInstance.get<TranslationDirective[]>('/directives');
    return response.data;
  },

  addDirective: async (
    directive: Omit<TranslationDirective, 'id'>
  ): Promise<ApiResponse<TranslationDirective>> => {
    const response = await axiosInstance.post<ApiResponse<TranslationDirective>>(
      '/admin/directives',
      directive
    );
    return response.data;
  },

  updateDirective: async (
    id: string,
    directive: Partial<TranslationDirective>
  ): Promise<ApiResponse<TranslationDirective>> => {
    const response = await axiosInstance.put<ApiResponse<TranslationDirective>>(
      `/admin/directives/${id}`,
      directive
    );
    return response.data;
  },

  deleteDirective: async (id: string): Promise<ApiResponse<void>> => {
    const response = await axiosInstance.delete<ApiResponse<void>>(`/admin/directives/${id}`);
    return response.data;
  },

  // ==================== 管理员统计 ====================

  getStats: async (): Promise<UsageStats> => {
    const response = await axiosInstance.get<UsageStats>('/admin/stats');
    return response.data;
  },

  // ==================== 当前用户信息 ====================

  getCurrentUser: async (): Promise<UserInfo> => {
    // 尝试多个可能的端点路径
    const endpoints = ['/user/me', '/user/info', '/user/profile', '/profile', '/user'];

    for (const endpoint of endpoints) {
      try {
        const response = await axiosInstance.get(endpoint);

        // 检查返回的数据是否有用户信息字段
        const data = response.data;
        if (data.user_info || data.user || data.username) {
          const userInfo = data.user_info || data.user || data;
          // 确保返回的数据有必要的字段
          if (userInfo.username && userInfo.daily_translation_limit !== undefined) {
            return userInfo;
          }
        }
      } catch (error) {
        console.error('获取用户信息失败:', error);
      }
    }

    throw new Error('无法获取用户信息：所有端点尝试失败');
  },

  // ==================== 管理员用户管理 ====================

  getAllUsers: async (): Promise<{ users: any[] }> => {
    const response = await axiosInstance.get('/admin/users');
    return response.data;
  },

  updateUser: async (data: any): Promise<{ success: boolean; message: string }> => {
    const response = await axiosInstance.post('/admin/users/update', data);
    return response.data;
  },

  addUser: async (data: any): Promise<{ success: boolean; message: string }> => {
    const response = await axiosInstance.post('/admin/users/add', data);
    return response.data;
  },

  deleteUser: async (username: string): Promise<{ success: boolean; message: string }> => {
    const response = await axiosInstance.delete(`/admin/users/${username}`);
    return response.data;
  },
};

// 将 axiosInstance 设置为默认导出
export default axiosInstance;
