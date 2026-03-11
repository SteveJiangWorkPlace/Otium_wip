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
  timeout: 1800000, // 濠电姭鎷冮崨顓濈捕婵犳鍠氶崑鐔煎箹妤ｅ啫宸濇い鏃傜摂濡差垶姊洪崫鍕殭闁绘牜鍘ц灋闁秆勵殔缁€?800缂傚倷绀侀ˇ鎵暜椤忓棙顫?0闂備礁鎲＄敮鎺懳涘┑瀣闁瑰墽绮弲顒€顭块懜鐢点€掔紒鈧径鎰厱闁哄诞鍛ㄩ梺鍛娗滈崐婵嗙暦閵夛附鍎熼柨婵嗙凹缁辨弸unicorn timeout闂佽崵濮崇粈浣规櫠娴犲鍋?
  headers: {
    'Content-Type': 'application/json',
  },
});

// 闂備礁鎲￠懝楣冩偋閸℃稒鍤愰柣鏂挎憸閳绘棃鏌曢崼婵嗩伃闁搞倕顑夐弻鐔煎礄閵堝顎嶉梺绯曟櫅閹虫ê鐣烽幎钘壩╃憸搴ㄦ偩闁秵鈷戞い鎰剁稻椤绱掓０婵嗕喊闁轰礁绉撮悾婵嬪焵椤掑倸鍨濋柣鎴烆焽閳绘棃鏌嶈閸撴艾顕ラ崟顖氱妞ゆ挾鍠庨埀?token 闂?API keys
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

    // 429 闂傚倷鐒︾€笛囨偡閵娾晩鏁嬮柕鍫濐槹閸ゅ﹥銇勮箛鎾愁仼鐞氱喖姊绘担鐟扮祷缂佸鍏橀幆?
    if (status === 429) {
      const maxRetries = 3;
      const retryCount = (error.config as any)?._retryCount || 0;

      if (retryCount < maxRetries) {
        // 闂佽崵濮崇欢銈囨閺囥垺鍋╅柤濮愬€楁す鍐差熆鐠虹尨鍔熺紒鎰剁節閺岋繝宕橀妸褍鐓熷┑鈽嗗亜濞硷繝寮澶婇唶闁靛繆鏅滈崑銉╂⒑?
        const retryAfterHeader = (response?.headers as any)?.['retry-after'];
        const retryAfter = retryAfterHeader
          ? parseInt(retryAfterHeader, 10)
          : Math.pow(2, retryCount); // 闂備礁婀遍…鍫澝洪敃鍌氭辈闁绘柨鍚嬮悞濠氭煃瑜滈崜鐔煎蓟閸℃稑绀岄柨娑樺閻?, 2, 4 缂?

        debugLog(`429 retry after ${retryAfter}s (${retryCount + 1}/${maxRetries})`);

        // 闂備礁鎼粔鏉懨洪埡鍜佹晩闁搞儺鍓氶悡鍌溾偓骞垮劚閻楀繐危閹间焦鍋ｅù锝嗗絻婢ф煡鏌?
        const newConfig = {
          ...error.config,
          _retryCount: retryCount + 1,
        };

        // 缂傚倷鐒︾粙鎴λ囬婊勵偨闁绘梻鍘х憴锕傚箹濞ｎ剙濡兼繛鍛灲閹?
        await new Promise((resolve) => setTimeout(resolve, retryAfter * 1000));
        return axiosInstance.request(newConfig);
      }
    }

    // 503/502/504 闂備礁鎼悧鍡欑矓鐎涙ɑ鍙忛柣鏃傚帶闂傤垶鏌曟繛鐐珕闁哄應鏅犻幃褰掑炊鐠鸿櫣浠撮梺鎼炲€栫划鎾崇暦濠靛惟闁宠桨鐒﹂鐔兼煟閻樺弶澶勬繛娴嬫櫇濡叉劕鈻庨幘鏉戜缓闂侀潧顭堥崐妤呮嚌閹岀唵閻犲搫鎼顐︽煙椤旂⒈娈糴nder闂備礁鎲￠崝鏇㈠床閺屻儱绠氶幖娣妼缁€澶嬨亜椤撶喎绗х紒鈧?
    if (status === 503 || status === 502 || status === 504) {
      const maxRetries = 4;
      const retryCount = (error.config as any)?._retryCount || 0;

      if (retryCount < maxRetries) {
        // 闂備焦鎮堕崕閬嶅箹椤愶附鍋╁Δ锝呭暞閳锋帡鏌熺紒銏犳灍妞ゆ捇绠栧娲箵閹烘枬銉╂煟閿旇鐏﹂柡?5, 50, 75, 100缂傚倷绀侀ˇ鎵暜椤忓棙顫曟繛鍡樻尭缁犳垿鏌ゆ慨鎰偓妤呭箹閼测斁鍋撻崹顐ｇ凡闁瑰啿绻愰—鍐磼閻愮补鎷?50缂傚倷绀侀ˇ鎵暜椤忓棙顫曟繝闈涚墢濡?.2闂備礁鎲＄敮鎺懳涘┑瀣闁瑰墽绮弲?
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

    // 401 闂傚倷鐒︾€笛囨偡閵娾晩鏁嬮柕鍫濇川绾惧ジ鏌ｉ弬鍨暢妞ゅ繘浜堕幃褰掑传閸曨厽鐎┑鐐存綑濡繈骞嗛崒婊勫珰闁肩⒈鍓涘崗
    if (status === 401) {
      // 闂佽崵濮撮鍛村疮娴兼潙鏋佹い锔藉Иgout闂備礁鎲￠崹鍏兼叏閵堝姹查柣鏃€鐏氶埀顒佸浮瀹曘劎鈧稒顭囪ぐ鎴︽⒑閸︻収鏆柛瀣崌閺岋繝宕煎┑鎰銈嗘崄瀹曠敻骞忛悩铏闁告繂瀚呴敃鍌涚厵妞ゆ垼娉曢ˇ锕傛煙妞嬪孩鐤乼ore闂備胶绮…鍫ュ春閺嶎厼鐒?
      try {
        useAuthStore.getState().logout();
      } catch (error) {
        console.error('logout failed:', error);
        // 濠电儑绲藉ú锔炬崲閸屾粏濮抽柟鎯板Г閺咁剚鎱ㄥ鍡楀箻妞ゅ繑鎮傚濠氬礋閸倣鎭沰en
        localStorage.removeItem('token');
        localStorage.removeItem('auth_token');
        localStorage.removeItem('admin_token');
      }
      window.location.href = '/login';
      error.message = 'Unauthorized, please log in again';
      return Promise.reject(error);
    }

    // 闂備胶顭堢换鎴濓耿閸︻厼鍨濇い鎺戝閻撱儲绻涢崱妯轰刊闁搞倖鐗犻弻銊モ槈濞嗘劗娈ょ紓渚囧枤閸庛倗绮欐径鎰劦妞ゆ帒瀚悡銉︾箾閸℃ê淇柛銈嗙墬缁绘盯骞嬪┑鍫濐杸婵炲鍘ч幊姗€鎮伴鈧幊婊堟濞戞艾绲剧紓?
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

// 闂?apiClient 闂佽姘﹂～澶愭儗椤斿墽涓嶉柣鏂挎憸閳绘棃鏌ｉ幋鐐嗘垿鎮甸鈧娲敃閿濆牆顥濆銈嗘处閸犳岸骞愰幒妤€鐓￠柛娑卞灣椤︻喗绻涢幋鐐村碍缂佸娅曠换娑㈠炊椤掍礁浠洪梺闈浥堥弲婵堟暜濞戙垺鍋ｅù锝夋涧閳ь剚娲熼、姘舵焼瀹ュ懐顦?
export const apiClient = {
  // ==================== 闂備焦妞垮鍧楀礉瀹ュ鏄ユ繛鎴炵婵ジ鏌曢崼婵堝ⅱ婵?====================

  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await axiosInstance.post<LoginResponse>('/login', data);
    return response.data;
  },

  adminLogin: async (data: AdminLoginRequest): Promise<LoginResponse> => {
    const response = await axiosInstance.post<LoginResponse>('/admin/login', data);
    return response.data;
  },

  // ==================== 闂備焦妞垮鍧楀礉瀹ュ鏄ユ繛鎴炃氶弸鏍煏婵炲灝鍔氶柡鍌楀亾闂備礁鎲＄划宀勬嚐椤栫偞鍎婇柟杈鹃檮閸庢ê銆掑锝呬壕闂侀潻绲介幗婊呮?====================

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

  // ==================== 闂備礁鎼崐绋棵洪敃鈧敃銏ゆ偋閸繄绐為梺鍛婃处閸樹粙宕?====================

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

    // 濠电偠鎻紞鈧繛澶嬫礋瀵?fetch API 闂佸搫顦弲婊呯矙閺嶎厹鈧線骞嬪婵婎潐閹峰懘宕妷褜鏀ㄩ梺鑽ゅТ濞差參寮ㄩ柆宥嗗剳?
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

    // 濠电偠鎻紞鈧繛澶嬫礋瀵?fetch API 闂佸搫顦弲婊呯矙閺嶎厹鈧線骞嬪婵婎潐閹峰懘宕妷褜鏀ㄩ梺鑽ゅТ濞差參寮ㄩ柆宥嗗剳?
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

  // ==================== AI闂備胶鍘у畷顒勬晝閵堝桅?====================
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

  // ==================== 闂備礁鎲￠懝鐐殽濮濆被浜归悗娑欘焽椤╃兘鎮归崶銊ョ祷妞ゎ偁鍊楃槐鎺楁偑閸涱垳锛熼梺?====================

  // 闂備礁鎲＄敮妤冪矙閹寸姷纾介柟鎹愵嚙鐟欙箓骞栫划鍏夊亾閹惰棄褰欏┑鐐差嚟婵箖顢氳閹便劑鎮㈤崗鍏兼珫闂佸壊鍋呯换鍌炲吹閹烘柡鍋撳▓鍨灈闁哥喍鍗冲?- 闂備胶绮划宥咁熆濡尨鑰挎い蹇撶墛閻掔粯鎱ㄥΟ铏癸紞缂?chat缂傚倷鐒﹀Λ蹇涘垂閹惰棄纾婚柨婵嗩槸缁€鍡樼箾閹寸儐鐒界紒鎲嬬畵閺?
  createBackgroundTask: async (
    data: CreateBackgroundTaskRequest
  ): Promise<CreateBackgroundTaskResponse> => {
    // 婵犵數鍋涢ˇ顓㈠礉瀹ュ绀堝ù鐓庣摠閺咁剚鎱ㄥΟ铏癸紞缂佺姷鎳撻埥澶愬箼閸愌呮晼濡炪倕娴氶崜鐔煎箖濞嗘挻鍋￠柡澶庡劵椤斿姊洪懝鐗堢彧闁搞劍绻勭划顓熷緞鐏炵浜炬繛鎴烆仾椤忓嫸鑰挎い蹇撶墛閺咁剛鈧厜鍋撻柍褜鍓熼悰顕€宕堕鈧幑鍫曟煏婵炲灝鍔滈柛濠勬暬閺屾稑鈻庨幙鍐╂闂佺懓绠嶉崹钘夌暦濠靛鏅搁柣姗嗗亜娴滅偓鎱ㄥΟ铏癸紞缂?chat缂傚倷鐒﹀Λ蹇涘垂閹惰棄纾婚柨婵嗩槸缁€鍡樼箾閹寸儐鐒界紒?
    const response = await axiosInstance.post<CreateBackgroundTaskResponse>(
      '/background-tasks',
      data
    );
    return response.data;
  },

  // 闂備礁鍚嬮崕鎶藉床閼艰翰浜归柛銉ｅ妿椤╃兘鎮归崶銊ョ祷妞ゎ偁鍊濋弻锝呂熼崹顔惧帿闂?
  getTaskStatus: async (taskId: number): Promise<GetTaskStatusResponse> => {
    const response = await axiosInstance.get<GetTaskStatusResponse>(`/tasks/${taskId}/status`);
    return response.data;
  },

  // 闂佸搫顦遍崕鎰板窗濞戙埄鏁嬫俊銈勮兌椤╃兘鎮归崶銊ョ祷妞ゎ偁鍊楃槐鎾存媴鐟欏嫬闉嶉梺璇茬箰椤︾敻寮澶婇唶婵犲﹤鍟犻弸蹇涙⒑濞茬粯濞囬柛鏂跨Ф閳ь剙鐏氬畝绋款嚕椤愶絽顕辩紒顔炬嚀娴滈箖鏌嶈閸撶喖寮婚崱娑樼闁挎稑瀚ˇ?
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
          timeout: 25000, // 闂佸搫顦遍崕鎰板窗濞戙埄鏁嬫俊銈呮噹缁犳娊鏌曟径鍫濆姎缂傚秵鎸搁湁闁挎繂鐗婄涵鍫曟煛娴ｉ潧鈧繂顕ｇ€电硶鍋撻棃娑欐喐闁告瑦宀搁幃娲箳閹寸偛娅ゅ┑锛勫仜閸婂潡寮鍛殕闁告洦浜炵槐姘舵⒑缁嬭法绠扮紒澶嬫綑閻ｇ兘鎮㈢亸浣圭€婚梻鍕喘椤㈡岸顢楅埀顒佹櫏闂佺鐬奸崑鐐残掗幇鐗堢厸闁告劑鍔庨崺锝嗕繆椤愩垺鍋ユ鐐村姍瀹曟帒鈹戦崶褔妫?
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

  // ==================== 闂備礁婀遍…鍫澝洪敐澶婄闁靛牆娲ㄦ稉宥夋煥濞戞ê顏柛?====================

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

  // ==================== 缂傚倷鑳舵刊瀵告閺囥垹绠栧┑鐘叉搐瀹告繃淇婇婵嗕汗闁糕晝濞€閹?====================

  getStats: async (): Promise<UsageStats> => {
    const response = await axiosInstance.get<UsageStats>('/admin/stats');
    return response.data;
  },

  // ==================== 闁荤喐绮庢晶妤呭箰閸涘﹥娅犻柣妯肩帛閸嬨劑鏌曟繝蹇曠暠闁绘挻娲栬彁闁搞儻绲芥晶鎻捗?====================

  getCurrentUser: async (): Promise<UserInfo> => {
    // Try known endpoints. Prefer currently implemented backend route first.
    const endpoints = ['/user/info', '/user/me', '/user/profile', '/profile', '/user'];

    for (const endpoint of endpoints) {
      try {
        const response = await axiosInstance.get(endpoint);

        // 婵犵妲呴崑鈧柛瀣崌閺岋紕浠︾拠鎻掑Г缂備胶绮崹鍨暦閸洘鍊烽柛顭戝亞閺嗙娀姊烘潪鎷屽厡濠⒀勵殔閻ｅ灚绗熼埀顒€顕ｆ导鎼晬婵﹩鍘奸崜銊╂⒑閸濆嫮澧曟い锕備憾瀵偊濡舵径濠勵吅闂佺偓鑹鹃崐椋庢崲閸℃稒鐓欐い鎾楀啰浠╅梺鐑╁閸愶絾鐏?
        const data = response.data;
        if (data.user_info || data.user || data.username) {
          const userInfo = data.user_info || data.user || data;
          // 缂備胶铏庨崣搴ㄥ窗閺囩姵宕叉慨姗嗗幗娴溿倝鏌￠崒娑橆嚋缂佲偓閳ь剟姊哄Ч鍥у閻庢凹鍙冨鎶芥偄閻撳海顔夊銈嗘婵倗绮婚幒妤冨彄闁搞儜鍕畬濡炪倐鏅粻鎾诲箚閸愵喖绀嬫い鎰╁€栭幉璇测攽?
          if (userInfo.username && userInfo.daily_translation_limit !== undefined) {
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

  // ==================== 缂傚倷鑳舵刊瀵告閺囥垹绠栧┑鐘叉搐瀹告繃淇婇姘倯闁哄棗绻橀弻鐔煎箻椤曞懏顥栧銈嗘尰閹倿骞?====================

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

// 闂?axiosInstance 闂佽崵濮崇粈浣规櫠娴犲鍋柛鈩冾焽閳绘梹绻涘顔荤敖閻㈩垱鐩幃瑙勬媴闂堟稈鍋撻弴銏╂晪闂侇剙绉寸粈?
export default axiosInstance;
