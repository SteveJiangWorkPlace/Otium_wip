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

  setInputText: (text: string) => void;
  setVersion: (version: 'professional' | 'basic') => void;
  setEnglishType: (type: 'us' | 'uk') => void;
  setLoading: (loading: boolean) => void;
  setLoadingStep: (step: 'translating' | null) => void;
  setTranslatedText: (text: string) => void;
  setEditableText: (text: string) => void;
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

      setInputText: (text: string) => set({ inputText: text }),
      setVersion: (version: 'professional' | 'basic') => set({ version }),
      setEnglishType: (englishType: 'us' | 'uk') => set({ englishType }),
      setLoading: (loading: boolean) => set({ loading }),
      setLoadingStep: (step: 'translating' | null) => set({ loadingStep: step }),
      setTranslatedText: (text: string) => set({ translatedText: text }),
      setEditableText: (text: string) => set({ editableText: text }),
      clear: () => set({
        inputText: '',
        translatedText: '',
        editableText: '',
        loading: false,
        loadingStep: null
      }),
    }),
    {
      name: 'translation-storage',
    }
  )
);