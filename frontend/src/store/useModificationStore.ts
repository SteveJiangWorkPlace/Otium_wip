import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ModificationState {
  inputText: string;
  loading: boolean;
  selectedDirectives: string[];
  modifiedText: string;
  showAnnotations: boolean;

  setInputText: (text: string) => void;
  setLoading: (loading: boolean) => void;
  setSelectedDirectives: (directives: string[]) => void;
  setModifiedText: (text: string) => void;
  setShowAnnotations: (show: boolean) => void;
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

      setInputText: (text: string) => set({ inputText: text }),
      setLoading: (loading: boolean) => set({ loading }),
      setSelectedDirectives: (directives: string[]) => set({ selectedDirectives: directives }),
      setModifiedText: (text: string) => set({ modifiedText: text }),
      setShowAnnotations: (show: boolean) => set({ showAnnotations: show }),
      clear: () => set({
        inputText: '',
        selectedDirectives: [],
        modifiedText: '',
        loading: false,
      }),
    }),
    {
      name: 'modification-storage',
    }
  )
);