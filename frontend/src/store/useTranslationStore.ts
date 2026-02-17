import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface TranslationState {
  inputText: string;
  version: 'professional' | 'basic';
  englishType: 'us' | 'uk';
  loading: boolean;
  loadingStep: 'translating' | null;
  translatedText: string;
  editableText: string;

  // 流式翻译状态
  streaming: boolean;
  partialText: string;
  sentences: string[];
  currentSentenceIndex: number;
  totalSentences: number;
  streamError: string | null;
  cancelStream: (() => void) | null;

  setInputText: (text: string) => void;
  setVersion: (version: 'professional' | 'basic') => void;
  setEnglishType: (type: 'us' | 'uk') => void;
  setLoading: (loading: boolean) => void;
  setLoadingStep: (step: 'translating' | null) => void;
  setTranslatedText: (text: string) => void;
  setEditableText: (text: string) => void;

  // 流式翻译操作
  setStreaming: (streaming: boolean) => void;
  setPartialText: (text: string) => void;
  appendPartialText: (text: string, isNewSentence?: boolean) => void;
  setSentences: (sentences: string[]) => void;
  addSentence: (sentence: string, index?: number) => void;
  setCurrentSentenceIndex: (index: number) => void;
  setTotalSentences: (total: number) => void;
  setStreamError: (error: string | null) => void;
  setCancelStream: (cancelFn: (() => void) | null) => void;
  resetStreamState: () => void;
  clear: () => void;
}

export const useTranslationStore = create<TranslationState>()(
  persist(
    (set) => ({
      inputText: '',
      version: 'professional',
      englishType: 'us',
      loading: false,
      loadingStep: null,
      translatedText: '',
      editableText: '',

      // 流式翻译状态初始值
      streaming: false,
      partialText: '',
      sentences: [],
      currentSentenceIndex: 0,
      totalSentences: 0,
      streamError: null,
      cancelStream: null,

      setInputText: (text: string) => set({ inputText: text }),
      setVersion: (version: 'professional' | 'basic') => set({ version }),
      setEnglishType: (englishType: 'us' | 'uk') => set({ englishType }),
      setLoading: (loading: boolean) => set({ loading }),
      setLoadingStep: (step: 'translating' | null) => set({ loadingStep: step }),
      setTranslatedText: (text: string) => set({ translatedText: text }),
      setEditableText: (text: string) => set({ editableText: text }),

      // 流式翻译操作
      setStreaming: (streaming: boolean) => set({ streaming }),
      setPartialText: (text: string) => set({ partialText: text }),
      appendPartialText: (text: string, isNewSentence?: boolean) =>
        set((state) => ({
          partialText: state.partialText + (isNewSentence && state.partialText ? '\n' : '') + text,
        })),
      setSentences: (sentences: string[]) => set({ sentences }),
      addSentence: (sentence: string, index?: number) =>
        set((state) => {
          const newSentences = [...state.sentences];
          if (index !== undefined && index >= 0 && index <= newSentences.length) {
            newSentences.splice(index, 0, sentence);
          } else {
            newSentences.push(sentence);
          }
          return { sentences: newSentences };
        }),
      setCurrentSentenceIndex: (index: number) => set({ currentSentenceIndex: index }),
      setTotalSentences: (total: number) => set({ totalSentences: total }),
      setStreamError: (error: string | null) => set({ streamError: error }),
      setCancelStream: (cancelFn: (() => void) | null) => set({ cancelStream: cancelFn }),
      resetStreamState: () =>
        set({
          streaming: false,
          partialText: '',
          sentences: [],
          currentSentenceIndex: 0,
          totalSentences: 0,
          streamError: null,
          cancelStream: null,
        }),
      clear: () =>
        set({
          inputText: '',
          translatedText: '',
          editableText: '',
          loading: false,
          loadingStep: null,
          // 同时重置流式状态
          streaming: false,
          partialText: '',
          sentences: [],
          currentSentenceIndex: 0,
          totalSentences: 0,
          streamError: null,
          cancelStream: null,
        }),
    }),
    {
      name: 'translation-storage',
    }
  )
);
