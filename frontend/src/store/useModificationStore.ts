import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ModificationState {
  inputText: string;
  loading: boolean;
  selectedDirectives: string[];
  modifiedText: string;
  showAnnotations: boolean;

  // 流式修改状态
  streaming: boolean;
  partialText: string;
  sentences: string[];
  currentSentenceIndex: number;
  totalSentences: number;
  streamError: string | null;
  cancelStream: (() => void) | null;

  setInputText: (text: string) => void;
  setLoading: (loading: boolean) => void;
  setSelectedDirectives: (directives: string[]) => void;
  setModifiedText: (text: string) => void;
  setShowAnnotations: (show: boolean) => void;

  // 流式修改操作
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

export const useModificationStore = create<ModificationState>()(
  persist(
    (set) => ({
      inputText: '',
      loading: false,
      selectedDirectives: [],
      modifiedText: '',
      showAnnotations: true,

      // 流式修改状态初始值
      streaming: false,
      partialText: '',
      sentences: [],
      currentSentenceIndex: 0,
      totalSentences: 0,
      streamError: null,
      cancelStream: null,

      setInputText: (text: string) => set({ inputText: text }),
      setLoading: (loading: boolean) => set({ loading }),
      setSelectedDirectives: (directives: string[]) => set({ selectedDirectives: directives }),
      setModifiedText: (text: string) => set({ modifiedText: text }),
      setShowAnnotations: (show: boolean) => set({ showAnnotations: show }),

      // 流式修改操作
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
          selectedDirectives: [],
          modifiedText: '',
          loading: false,
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
      name: 'modification-storage',
    }
  )
);
