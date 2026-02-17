/**
 * 重置所有应用程序状态存储
 * 在用户登录/登出时调用，确保干净的状态
 */
import { useTranslationStore } from '../store/useTranslationStore';
import { useCorrectionStore } from '../store/useCorrectionStore';
import { useModificationStore } from '../store/useModificationStore';
import { useDetectionStore } from '../store/useDetectionStore';
import { useAIChatStore } from '../store/useAIChatStore';

export const resetAllStores = () => {
  // 获取store实例（注意：这只能在组件外部使用，因为store是单例）
  // 这里我们直接调用store的清除方法
  try {
    // 清除各个模块的store
    useTranslationStore.getState().clear();
    useCorrectionStore.getState().clear();
    useModificationStore.getState().clear();
    useDetectionStore.getState().clear();

    // AI聊天store需要清除所有页面的对话
    const aiChatStore = useAIChatStore.getState();
    const conversations = aiChatStore.conversations;
    if (conversations) {
      Object.keys(conversations).forEach((page) => {
        aiChatStore.clearConversation(page);
      });
    }

    console.log('所有store状态已重置');
  } catch (error) {
    console.error('重置store时出错:', error);
  }
};
