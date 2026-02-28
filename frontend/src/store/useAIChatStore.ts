import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface AIChatMessage {
  id?: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

interface ConversationState {
  isExpanded: boolean;
  messages: AIChatMessage[];
  inputText: string;
  loading: boolean;
  activeTaskId: number | null;
  sessionId: string | null;
  splitPosition: number; // 分割线位置（百分比，默认30）
}

interface AIChatState {
  // 每个页面对话独立存储，key为页面路径
  conversations: Record<string, ConversationState>;

  // 当前活动对话（基于当前页面）
  currentPage: string | null;

  // 文献调研模式（全局设置，使用Manus API）
  literatureResearchMode: boolean;

  // 生成文献综述选项（仅文献调研模式有效）
  generateLiteratureReview: boolean;

  // 操作方法
  setCurrentPage: (page: string) => void;
  toggleExpanded: (page: string) => void;
  addMessage: (page: string, message: AIChatMessage) => void;
  setInputText: (page: string, text: string) => void;
  setLoading: (page: string, loading: boolean) => void;
  setActiveTaskId: (page: string, taskId: number | null) => void;
  clearConversation: (page: string) => void;
  initializeConversation: (page: string) => void;
  setSplitPosition: (page: string, position: number) => void;
  toggleLiteratureResearchMode: () => void;
  setLiteratureResearchMode: (enabled: boolean) => void;
  toggleGenerateLiteratureReview: () => void;
  setGenerateLiteratureReview: (enabled: boolean) => void;
}

const DEFAULT_SPLIT_POSITION = 30;
const createMessageId = () =>
  `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;

const DEFAULT_CONVERSATION_STATE: ConversationState = {
  isExpanded: false,
  messages: [],
  inputText: '',
  loading: false,
  activeTaskId: null,
  sessionId: null,
  splitPosition: DEFAULT_SPLIT_POSITION,
};

export const useAIChatStore = create<AIChatState>()(
  persist(
    (set, get) => ({
      conversations: {},
      currentPage: null,
      literatureResearchMode: false, // 默认关闭文献调研模式
      generateLiteratureReview: false, // 默认不生成文献综述

      setCurrentPage: (page: string) => {
        set({ currentPage: page });
        get().initializeConversation(page);
      },

      toggleExpanded: (page: string) => {
        set((state) => {
          const conversations = { ...state.conversations };
          if (!conversations[page]) {
            conversations[page] = { ...DEFAULT_CONVERSATION_STATE };
          }
          conversations[page].isExpanded = !conversations[page].isExpanded;
          return { conversations };
        });
      },

      addMessage: (page: string, message: AIChatMessage) => {
        set((state) => {
          const conversations = { ...state.conversations };
          if (!conversations[page]) {
            conversations[page] = { ...DEFAULT_CONVERSATION_STATE };
          }
          const normalizedMessage: AIChatMessage = {
            ...message,
            id: message.id || createMessageId(),
          };
          conversations[page].messages.push(normalizedMessage);
          return { conversations };
        });
      },

      setInputText: (page: string, text: string) => {
        set((state) => {
          const conversations = { ...state.conversations };
          if (!conversations[page]) {
            conversations[page] = { ...DEFAULT_CONVERSATION_STATE };
          }
          conversations[page].inputText = text;
          return { conversations };
        });
      },

      setLoading: (page: string, loading: boolean) => {
        set((state) => {
          const conversations = { ...state.conversations };
          if (!conversations[page]) {
            conversations[page] = { ...DEFAULT_CONVERSATION_STATE };
          }
          conversations[page].loading = loading;
          return { conversations };
        });
      },

      setActiveTaskId: (page: string, taskId: number | null) => {
        set((state) => {
          const conversations = { ...state.conversations };
          if (!conversations[page]) {
            conversations[page] = { ...DEFAULT_CONVERSATION_STATE };
          }
          conversations[page].activeTaskId = taskId;
          return { conversations };
        });
      },

      clearConversation: (page: string) => {
        set((state) => {
          const conversations = { ...state.conversations };
          if (conversations[page]) {
            conversations[page] = {
              ...DEFAULT_CONVERSATION_STATE,
              isExpanded: conversations[page].isExpanded,
              splitPosition: conversations[page].splitPosition,
            };
          }
          return { conversations };
        });
      },

      initializeConversation: (page: string) => {
        set((state) => {
          const conversations = { ...state.conversations };
          if (!conversations[page]) {
            conversations[page] = { ...DEFAULT_CONVERSATION_STATE };
          }
          return { conversations };
        });
      },

      setSplitPosition: (page: string, position: number) => {
        set((state) => {
          const conversations = { ...state.conversations };
          if (!conversations[page]) {
            conversations[page] = { ...DEFAULT_CONVERSATION_STATE };
          }
          // 限制分割线位置在20%到80%之间
          conversations[page].splitPosition = Math.max(20, Math.min(80, position));
          return { conversations };
        });
      },

      toggleLiteratureResearchMode: () => {
        set((state) => ({
          literatureResearchMode: !state.literatureResearchMode,
        }));
      },

      setLiteratureResearchMode: (enabled: boolean) => {
        set({ literatureResearchMode: enabled });
      },

      toggleGenerateLiteratureReview: () => {
        set((state) => ({
          generateLiteratureReview: !state.generateLiteratureReview,
        }));
      },

      setGenerateLiteratureReview: (enabled: boolean) => {
        set({ generateLiteratureReview: enabled });
      },
    }),
    {
      name: 'ai-chat-storage',
    }
  )
);
