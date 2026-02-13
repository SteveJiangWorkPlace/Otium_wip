import { create } from 'zustand';

export type TaskType = 'correction' | 'translation' | 'ai-detection' | 'modification' | 'general';

export interface GlobalProgressState {
  // 进度状态
  isVisible: boolean;
  message: string;
  taskType: TaskType | null;
  showDots: boolean;
  lastCompletedTask: TaskType | null;

  // 操作
  showProgress: (message: string, taskType?: TaskType) => void;
  updateProgress: (message: string) => void;
  hideProgress: () => void;
  setShowDots: (show: boolean) => void;
  clearProgress: () => void;
  setLastCompletedTask: (taskType: TaskType | null) => void;
}

export const useGlobalProgressStore = create<GlobalProgressState>((set) => ({
  // 初始状态
  isVisible: false,
  message: '',
  taskType: null,
  showDots: false,
  lastCompletedTask: null,

  // 显示进度
  showProgress: (message: string, taskType?: TaskType) => set({
    isVisible: true,
    message,
    taskType: taskType || null,
    showDots: true,
  }),

  // 更新进度消息
  updateProgress: (message: string) => set((state) => ({
    message,
    // 保持其他状态不变
    isVisible: state.isVisible,
    taskType: state.taskType,
    showDots: state.showDots,
  })),

  // 隐藏进度（任务完成时调用）- 只清除点号动画，保持完成状态显示
  hideProgress: () => set((state) => ({
    // 保持可见，让完成状态继续显示
    isVisible: true,
    // 保持消息不变（如"智能文本修改完成"），但GlobalProgressBar会显示简单直白的完成消息
    message: state.message,
    showDots: false,
    // 保存已完成的任务类型
    lastCompletedTask: state.taskType,
  })),

  // 设置是否显示点号动画
  setShowDots: (show: boolean) => set({ showDots: show }),

  // 清除所有进度状态
  clearProgress: () => set({
    isVisible: false,
    message: '',
    taskType: null,
    showDots: false,
    lastCompletedTask: null,
  }),

  // 设置最后完成的任务
  setLastCompletedTask: (taskType: TaskType | null) => set({ lastCompletedTask: taskType }),
}));