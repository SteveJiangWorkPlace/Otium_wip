import { useState, useEffect } from 'react';

export interface ApiKeys {
  geminiApiKey: string;
  gptzeroApiKey: string;
}

const API_KEYS_STORAGE_KEY = 'otium_api_keys';

// 简单的API密钥管理钩子
export const useApiKeys = () => {
  const [apiKeys, setApiKeys] = useState<ApiKeys>({
    geminiApiKey: '',
    gptzeroApiKey: '',
  });

  // 从localStorage加载API密钥
  useEffect(() => {
    const savedKeys = localStorage.getItem(API_KEYS_STORAGE_KEY);
    console.log(
      'useApiKeys - 从localStorage加载, 键名:',
      API_KEYS_STORAGE_KEY,
      '数据:',
      savedKeys ? '存在' : '不存在'
    );

    if (savedKeys) {
      try {
        const parsedKeys = JSON.parse(savedKeys);
        console.log('useApiKeys - 解析后的密钥:', {
          geminiLength: parsedKeys.geminiApiKey ? parsedKeys.geminiApiKey.length : 0,
          gptzeroLength: parsedKeys.gptzeroApiKey ? parsedKeys.gptzeroApiKey.length : 0,
          geminiPreview: parsedKeys.geminiApiKey
            ? `${parsedKeys.geminiApiKey.substring(0, Math.min(5, parsedKeys.geminiApiKey.length))}...`
            : '空',
          gptzeroPreview: parsedKeys.gptzeroApiKey
            ? `${parsedKeys.gptzeroApiKey.substring(0, Math.min(5, parsedKeys.gptzeroApiKey.length))}...`
            : '空',
        });

        setApiKeys({
          geminiApiKey: parsedKeys.geminiApiKey || '',
          gptzeroApiKey: parsedKeys.gptzeroApiKey || '',
        });
      } catch (error) {
        console.error('解析API密钥失败:', error);
      }
    }
  }, []);

  // 保存API密钥到localStorage
  const saveApiKeys = (keys: ApiKeys) => {
    try {
      console.log('useApiKeys - 保存API密钥到localStorage:', {
        geminiLength: keys.geminiApiKey ? keys.geminiApiKey.length : 0,
        gptzeroLength: keys.gptzeroApiKey ? keys.gptzeroApiKey.length : 0,
        geminiPreview: keys.geminiApiKey
          ? `${keys.geminiApiKey.substring(0, Math.min(5, keys.geminiApiKey.length))}...`
          : '空',
        gptzeroPreview: keys.gptzeroApiKey
          ? `${keys.gptzeroApiKey.substring(0, Math.min(5, keys.gptzeroApiKey.length))}...`
          : '空',
      });

      localStorage.setItem(API_KEYS_STORAGE_KEY, JSON.stringify(keys));

      // 验证保存是否成功
      const saved = localStorage.getItem(API_KEYS_STORAGE_KEY);
      console.log('useApiKeys - 验证保存结果:', saved ? '成功' : '失败');

      setApiKeys(keys);
      return true;
    } catch (error) {
      console.error('保存API密钥失败:', error);
      return false;
    }
  };

  // 更新单个API密钥
  const updateApiKey = (key: keyof ApiKeys, value: string) => {
    const newKeys = { ...apiKeys, [key]: value.trim() };
    return saveApiKeys(newKeys);
  };

  // 获取API密钥状态
  const hasGeminiApiKey = () => apiKeys.geminiApiKey.trim() !== '';
  const hasGptzeroApiKey = () => apiKeys.gptzeroApiKey.trim() !== '';

  return {
    apiKeys,
    saveApiKeys,
    updateApiKey,
    hasGeminiApiKey,
    hasGptzeroApiKey,
  };
};
