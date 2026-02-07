import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface CorrectionState {
  inputText: string;
  loading: boolean;
  loadingStep: 'error_checking' | null;
  resultText: string;
  editableText: string;

  setInputText: (text: string) => void;
  setLoading: (loading: boolean) => void;
  setLoadingStep: (step: 'error_checking' | null) => void;
  setResultText: (text: string) => void;
  setEditableText: (text: string) => void;
  clear: () => void;
}

export const useCorrectionStore = create<CorrectionState>()(
  persist(
    (set) => ({
      inputText: '',
      loading: false,
      loadingStep: null,
      resultText: '',
      editableText: '',

      setInputText: (text: string) => set({ inputText: text }),
      setLoading: (loading: boolean) => set({ loading }),
      setLoadingStep: (step: 'error_checking' | null) => set({ loadingStep: step }),
      setResultText: (text: string) => set({ resultText: text }),
      setEditableText: (text: string) => set({ editableText: text }),
      clear: () => set({
        inputText: '',
        resultText: '',
        editableText: '',
        loading: false,
        loadingStep: null
      }),
    }),
    {
      name: 'correction-storage',
    }
  )
);