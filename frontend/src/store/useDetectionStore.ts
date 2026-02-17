import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { AIDetectionResponse } from '../types';

interface DetectionState {
  inputText: string;
  detectionResult: AIDetectionResponse | null;
  shouldDetect: boolean;

  setInputText: (text: string) => void;
  setDetectionResult: (result: AIDetectionResponse | null) => void;
  setShouldDetect: (should: boolean) => void;
  clear: () => void;
}

export const useDetectionStore = create<DetectionState>()(
  persist(
    (set) => ({
      inputText: '',
      detectionResult: null,
      shouldDetect: false,

      setInputText: (text: string) => set({ inputText: text }),
      setDetectionResult: (result: AIDetectionResponse | null) => set({ detectionResult: result }),
      setShouldDetect: (should: boolean) => set({ shouldDetect: should }),
      clear: () =>
        set({
          inputText: '',
          detectionResult: null,
          shouldDetect: false,
        }),
    }),
    {
      name: 'detection-storage',
    }
  )
);
