import { useAIChatStore } from '../store/useAIChatStore';

const AI_CHAT_STORAGE_KEY = 'ai-chat-storage';
const LEGACY_LITERATURE_STORAGE_KEY = 'literature-research-storage';

export const resetAIChatState = () => {
  try {
    useAIChatStore.setState({
      conversations: {},
      currentPage: null,
      literatureResearchMode: false,
      generateLiteratureReview: false,
    });

    const storeWithPersist = useAIChatStore as typeof useAIChatStore & {
      persist?: { clearStorage?: () => void };
    };
    storeWithPersist.persist?.clearStorage?.();
  } catch (error) {
    console.error('Failed to reset AI chat state:', error);
  }

  localStorage.removeItem(AI_CHAT_STORAGE_KEY);
  localStorage.removeItem(LEGACY_LITERATURE_STORAGE_KEY);
};
