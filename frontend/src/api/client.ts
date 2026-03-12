import axios, { AxiosError } from 'axios';
import { useAuthStore } from '../store/useAuthStore';
import { debugLog } from '../utils/logger';
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
  AIChatStreamChunk,
  StreamTranslationRequest,
  StreamTranslationChunk,
  StreamRefineTextRequest,
  StreamRefineTextChunk,
  BackgroundTask,
  CreateBackgroundTaskRequest,
  CreateBackgroundTaskResponse,
  GetTaskStatusResponse,
} from '../types';
import { BackgroundTaskStatus } from '../types';

debugLog('api client module loaded - REACT_APP_API_BASE_URL:', process.env.REACT_APP_API_BASE_URL);

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
debugLog('api client base url:', API_BASE_URL);

const axiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 1800000,
  headers: {
    'Content-Type': 'application/json',
  },
});

const isTokenFormatValid = (rawValue: string): boolean => {
  const token = rawValue.trim();
  if (!token) return false;

  if (token.startsWith('admin:')) {
    const parts = token.split(':');
    return parts.length === 3 && parts[1].length > 0 && parts[2].length > 0;
  }

  return token.split('.').length === 3;
};

const getPreferredAuthToken = (): string | undefined => {
  const tokenSources = [
    { key: 'auth_token', value: localStorage.getItem('auth_token') },
    { key: 'admin_token', value: localStorage.getItem('admin_token') },
    { key: 'token', value: localStorage.getItem('token') },
  ];
  const validSource = tokenSources.find((entry) => entry.value && isTokenFormatValid(entry.value));
  const fallbackSource = tokenSources.find((entry) => entry.value && entry.value.trim() !== '');
  return (validSource ?? fallbackSource)?.value?.trim();
};

axiosInstance.interceptors.request.use(
  (config) => {
    debugLog('request interceptor - url:', config.url);
    debugLog('request interceptor - method:', config.method);

    const token = getPreferredAuthToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    try {
      const apiKeysStr = localStorage.getItem('otium_api_keys');
      debugLog(
        'request interceptor - custom API keys (otium_api_keys):',
        apiKeysStr ? 'configured' : 'not configured'
      );
      debugLog('request interceptor - localStorage keys:', Object.keys(localStorage));

      if (apiKeysStr) {
        const apiKeys = JSON.parse(apiKeysStr);
        debugLog('request interceptor - parsed API keys:', {
          hasGeminiApiKey: !!(apiKeys.geminiApiKey && apiKeys.geminiApiKey.trim()),
          hasGptzeroApiKey: !!(apiKeys.gptzeroApiKey && apiKeys.gptzeroApiKey.trim()),
          geminiLength: apiKeys.geminiApiKey ? apiKeys.geminiApiKey.length : 0,
          gptzeroLength: apiKeys.gptzeroApiKey ? apiKeys.gptzeroApiKey.length : 0,
          geminiKeyPreview: apiKeys.geminiApiKey
            ? `${apiKeys.geminiApiKey.substring(0, Math.min(5, apiKeys.geminiApiKey.length))}...`
            : 'empty',
          gptzeroKeyPreview: apiKeys.gptzeroApiKey
            ? `${apiKeys.gptzeroApiKey.substring(0, Math.min(5, apiKeys.gptzeroApiKey.length))}...`
            : 'empty',
        });

        if (apiKeys.geminiApiKey && apiKeys.geminiApiKey.trim() !== '') {
          const keyPrefix = apiKeys.geminiApiKey.substring(
            0,
            Math.min(8, apiKeys.geminiApiKey.length)
          );
          debugLog('request interceptor - set X-Gemini-Api-Key header, prefix:', keyPrefix + '...');
          config.headers['X-Gemini-Api-Key'] = apiKeys.geminiApiKey;
        }

        if (apiKeys.gptzeroApiKey && apiKeys.gptzeroApiKey.trim() !== '') {
          const keyPrefix = apiKeys.gptzeroApiKey.substring(
            0,
            Math.min(8, apiKeys.gptzeroApiKey.length)
          );
          debugLog(
            'request interceptor - set X-Gptzero-Api-Key header, prefix:',
            keyPrefix + '...'
          );
          config.headers['X-Gptzero-Api-Key'] = apiKeys.gptzeroApiKey;
        }
      } else {
        debugLog('request interceptor - using backend default API keys');
      }

      debugLog('request interceptor - final headers:', JSON.stringify(config.headers, null, 2));
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
    const shouldDisableRetry = Boolean((error.config as any)?._disableRetry);

    const extractErrorMessage = (): string => {
      if (!response) return 'Network error, please check your connection.';

      const data = response.data;
      if (data && typeof data === 'object') {
        if (typeof data.message === 'string' && data.message) {
          return data.message;
        }

        if (data.detail) {
          if (typeof data.detail === 'string') {
            return data.detail;
          }
          if (typeof data.detail === 'object') {
            const detailObj = data.detail as Record<string, any>;
            if (typeof detailObj.message === 'string' && detailObj.message) {
              return detailObj.message;
            }
            return JSON.stringify(detailObj);
          }
        }
      }

      switch (status) {
        case 400:
          return 'Bad request parameters';
        case 401:
          return 'Unauthorized, please log in again';
        case 403:
          return 'Permission denied';
        case 404:
          return 'Requested resource not found';
        case 429:
          return 'Too many requests, please try again later';
        case 500:
          return 'Internal server error';
        case 502:
          return 'Bad gateway';
        case 503:
          return 'Service unavailable';
        case 504:
          return 'Gateway timeout';
        default:
          return `Request failed (status ${status})`;
      }
    };

    if (!shouldDisableRetry && status === 429) {
      const maxRetries = 3;
      const retryCount = (error.config as any)?._retryCount || 0;

      if (retryCount < maxRetries) {
        const retryAfterHeader = (response?.headers as any)?.['retry-after'];
        const retryAfter = retryAfterHeader
          ? parseInt(retryAfterHeader, 10)
          : Math.pow(2, retryCount);

        debugLog(`429 retry after ${retryAfter}s (${retryCount + 1}/${maxRetries})`);

        const newConfig = {
          ...error.config,
          _retryCount: retryCount + 1,
        };

        await new Promise((resolve) => setTimeout(resolve, retryAfter * 1000));
        return axiosInstance.request(newConfig);
      }
    }

    if (!shouldDisableRetry && (status === 503 || status === 502 || status === 504)) {
      const maxRetries = 4;
      const retryCount = (error.config as any)?._retryCount || 0;

      if (retryCount < maxRetries) {
        const retryIntervals = [25, 50, 75, 100];
        const retryAfter = retryIntervals[retryCount];
        debugLog(
          `server error ${status}, retry after ${retryAfter}s (${retryCount + 1}/${maxRetries})`
        );

        const newConfig = {
          ...error.config,
          _retryCount: retryCount + 1,
        };

        await new Promise((resolve) => setTimeout(resolve, retryAfter * 1000));
        return axiosInstance.request(newConfig);
      }
    }

    if (status === 401) {
      try {
        useAuthStore.getState().logout();
      } catch (error) {
        console.error('logout failed:', error);

        localStorage.removeItem('token');
        localStorage.removeItem('auth_token');
        localStorage.removeItem('admin_token');
      }
      window.location.href = '/login';
      error.message = 'Unauthorized, please log in again';
      return Promise.reject(error);
    }

    const errorMessage = extractErrorMessage();
    error.message = errorMessage;
    return Promise.reject(error);
  }
);

const getHttpStatus = (error: unknown): number | undefined => {
  if (axios.isAxiosError(error)) {
    return error.response?.status;
  }
  return undefined;
};

const getStreamingHeaders = (): Record<string, string> => {
  const token = getPreferredAuthToken();
  const apiKeysStr = localStorage.getItem('otium_api_keys');
  const apiKeys = apiKeysStr ? JSON.parse(apiKeysStr) : {};
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  if (apiKeys.geminiApiKey && apiKeys.geminiApiKey.trim()) {
    headers['X-Gemini-Api-Key'] = apiKeys.geminiApiKey;
  }

  return headers;
};

async function* parseSSEStream<T>(
  response: Response,
  onProgress?: (chunk: T) => void
): AsyncGenerator<T, void, unknown> {
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Streaming request failed: ${response.status} ${errorText}`);
  }

  if (!response.body) {
    throw new Error('Response body is not readable');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split('\n\n');
      buffer = events.pop() || '';

      for (const eventBlock of events) {
        const dataLines = eventBlock
          .split('\n')
          .filter((line) => line.startsWith('data: '))
          .map((line) => line.substring(6).trim())
          .filter(Boolean);

        if (dataLines.length === 0) {
          continue;
        }

        const jsonStr = dataLines.join('\n');
        try {
          const chunkData = JSON.parse(jsonStr) as T;
          if (onProgress) {
            onProgress(chunkData);
          }
          yield chunkData;
        } catch (error) {
          console.error('Failed to parse SSE data:', error, 'raw data:', jsonStr);
        }
      }
    }

    const remaining = buffer.trim();
    if (remaining) {
      const dataLines = remaining
        .split('\n')
        .filter((line) => line.startsWith('data: '))
        .map((line) => line.substring(6).trim())
        .filter(Boolean);

      if (dataLines.length > 0) {
        const jsonStr = dataLines.join('\n');
        const chunkData = JSON.parse(jsonStr) as T;
        if (onProgress) {
          onProgress(chunkData);
        }
        yield chunkData;
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export const apiClient = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await axiosInstance.post<LoginResponse>('/login', data, {
      _disableRetry: true,
    } as any);
    return response.data;
  },

  adminLogin: async (data: AdminLoginRequest): Promise<LoginResponse> => {
    const response = await axiosInstance.post<LoginResponse>('/admin/login', data);
    return response.data;
  },

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
      },
      {
        _disableRetry: true,
      } as any
    );
    return response.data;
  },

  checkText: async (data: CheckTextRequest): Promise<CheckTextResponse> => {
    const response = await axiosInstance.post<CheckTextResponse>('/text/check', data);
    return response.data;
  },

  checkTextStream: async function* (
    data: CheckTextRequest,
    options?: {
      onProgress?: (chunk: StreamTranslationChunk) => void;
      signal?: AbortSignal;
    }
  ) {
    const { onProgress, signal } = options || {};
    const headers = getStreamingHeaders();
    const response = await fetch(`${API_BASE_URL}/api/text/error-check-stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
      signal,
    });

    for await (const chunk of parseSSEStream<StreamTranslationChunk>(response, onProgress)) {
      yield chunk;
    }
  },

  translateStream: async function* (
    data: StreamTranslationRequest,
    options?: {
      onProgress?: (chunk: StreamTranslationChunk) => void;
      signal?: AbortSignal;
    }
  ) {
    const { onProgress, signal } = options || {};
    const headers = getStreamingHeaders();

    const response = await fetch(`${API_BASE_URL}/api/text/translate-stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
      signal,
    });

    for await (const chunk of parseSSEStream<StreamTranslationChunk>(response, onProgress)) {
      yield chunk;
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
    const headers = getStreamingHeaders();

    const response = await fetch(`${API_BASE_URL}/api/text/refine-stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
      signal,
    });

    for await (const chunk of parseSSEStream<StreamRefineTextChunk>(response, onProgress)) {
      yield chunk;
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

  chat: async (data: AIChatRequest): Promise<AIChatResponse> => {
    const response = await axiosInstance.post<AIChatResponse>('/chat', data);
    return response.data;
  },

  chatStream: async function* (
    data: AIChatRequest,
    options?: {
      onProgress?: (chunk: AIChatStreamChunk) => void;
      signal?: AbortSignal;
    }
  ) {
    const { onProgress, signal } = options || {};
    const headers = getStreamingHeaders();
    const response = await fetch(`${API_BASE_URL}/api/chat-stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
      signal,
    });

    for await (const chunk of parseSSEStream<AIChatStreamChunk>(response, onProgress)) {
      yield chunk;
    }
  },

  createBackgroundTask: async (
    data: CreateBackgroundTaskRequest
  ): Promise<CreateBackgroundTaskResponse> => {
    const response = await axiosInstance.post<CreateBackgroundTaskResponse>(
      '/background-tasks',
      data
    );
    return response.data;
  },

  getTaskStatus: async (taskId: number): Promise<GetTaskStatusResponse> => {
    const response = await axiosInstance.get<GetTaskStatusResponse>(`/tasks/${taskId}/status`);
    return response.data;
  },

  pollTaskResult: async (
    taskId: number,
    options?: {
      interval?: number;
      maxAttempts?: number;
      maxElapsedMs?: number;
      onProgress?: (task: BackgroundTask) => void;
      signal?: AbortSignal;
    }
  ): Promise<BackgroundTask> => {
    const {
      interval = 1000,
      maxAttempts = 300,
      maxElapsedMs = 12 * 60 * 1000,
      onProgress,
      signal,
    } = options || {};
    let attempts = 0;
    let currentInterval = interval;
    const startedAt = Date.now();

    while (attempts < maxAttempts) {
      if (signal?.aborted) {
        throw new Error('Polling aborted');
      }
      if (Date.now() - startedAt > maxElapsedMs) {
        throw new Error(
          `Polling task ${taskId} timed out after ${(maxElapsedMs / 60000).toFixed(1)} minutes`
        );
      }

      attempts++;
      try {
        const response = await axiosInstance.get<GetTaskStatusResponse>(`/tasks/${taskId}/status`, {
          signal,
          timeout: 25000,
        });
        const { success, task, error } = response.data;

        if (!success) {
          throw new Error(error || 'Failed to get task status');
        }

        if (onProgress) {
          onProgress(task);
        }

        if (task.status === BackgroundTaskStatus.COMPLETED) {
          return task;
        }

        if (task.status === BackgroundTaskStatus.FAILED) {
          throw new Error(task.error_message || 'Task processing failed');
        }

        if (
          task.status === BackgroundTaskStatus.PENDING ||
          task.status === BackgroundTaskStatus.PROCESSING
        ) {
          const interval = currentInterval;
          await new Promise((resolve) => setTimeout(resolve, interval));
          currentInterval = Math.min(currentInterval * 1.5, 10000);
          continue;
        }

        const interval = currentInterval;
        await new Promise((resolve) => setTimeout(resolve, interval));
        currentInterval = Math.min(currentInterval * 1.5, 10000);
      } catch (error) {
        if (signal?.aborted) {
          throw new Error('Polling aborted');
        }

        const status = getHttpStatus(error);
        if (status && [400, 401, 403, 404, 422].includes(status)) {
          throw new Error(
            `Polling task ${taskId} failed: HTTP ${status} (task missing, permission denied, or invalid login state)`
          );
        }

        if (attempts < maxAttempts) {
          console.warn(`Polling task ${taskId} failed, retry ${attempts}/${maxAttempts}:`, error);
          const interval = currentInterval;
          await new Promise((resolve) => setTimeout(resolve, interval));
          currentInterval = Math.min(currentInterval * 1.5, 10000);
        } else {
          throw new Error(
            `Polling task ${taskId} timed out: ${error instanceof Error ? error.message : String(error)}`
          );
        }
      }
    }

    throw new Error(`Polling task ${taskId} timed out after ${maxAttempts} attempts`);
  },

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

  // ==================== Admin stats ====================

  getStats: async (): Promise<UsageStats> => {
    const response = await axiosInstance.get<UsageStats>('/admin/stats');
    return response.data;
  },

  // ==================== Current user ====================

  getCurrentUser: async (): Promise<UserInfo> => {
    // Try known endpoints. Prefer currently implemented backend route first.
    const endpoints = ['/user/info', '/user/me', '/user/profile', '/profile', '/user'];

    for (const endpoint of endpoints) {
      try {
        const response = await axiosInstance.get(endpoint);

        const data = response.data;
        if (data.user_info || data.user || data.username) {
          const userInfo = data.user_info || data.user || data;
          if (userInfo.username && userInfo.monthly_translation_limit !== undefined) {
            return userInfo;
          }
        }
      } catch (error) {
        // Expected during endpoint probing in mixed deployments (e.g. /user/me -> 404).
        debugLog(`getCurrentUser endpoint probe failed: ${endpoint}`, error);
      }
    }

    throw new Error('Unable to load current user info: all endpoint probes failed');
  },

  // ==================== Admin user management ====================

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

export default axiosInstance;
