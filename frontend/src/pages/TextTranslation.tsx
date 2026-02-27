import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';
import { useTranslationStore } from '../store/useTranslationStore';
import { useGlobalProgressStore } from '../store/useGlobalProgressStore';
import { useAIChatStore } from '../store/useAIChatStore';
import { apiClient } from '../api/client';
import { cleanTextFromMarkdown, renderMarkdownAsHtml } from '../utils/textCleaner';
import type { StreamTranslationRequest } from '../types';
import Card from '../components/ui/Card/Card';
import Textarea from '../components/ui/Textarea/Textarea';
import Button from '../components/ui/Button/Button';
import GlobalProgressBar from '../components/GlobalProgressBar/GlobalProgressBar';
import AIChatPanel from '../components/AIChatPanel/AIChatPanel';
import styles from './TextTranslation.module.css';

const TextTranslation: React.FC = () => {
  const navigate = useNavigate();
  const { userInfo, updateUserInfo } = useAuthStore();

  const {
    inputText,
    version,
    englishType,
    loading,
    loadingStep,
    translatedText,
    editableText,
    streaming,
    partialText,
    cancelStream,
    setInputText,
    setVersion,
    setEnglishType,
    setTranslatedText,
    setEditableText,
    setStreaming,
    setPartialText,
    appendPartialText,
    setSentences,
    addSentence,
    setCurrentSentenceIndex,
    setTotalSentences,
    setStreamError,
    setCancelStream,
    resetStreamState,
    clear,
  } = useTranslationStore();

  const { showProgress, hideProgress, updateProgress } = useGlobalProgressStore();

  // 复制通知状态
  const [copyNotification, setCopyNotification] = useState<string | null>(null);
  const notificationTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // 格式化显示状态
  const [showFormatted, setShowFormatted] = useState<boolean>(true);

  // AI聊天状态
  const { conversations, toggleExpanded, setCurrentPage } = useAIChatStore();
  const containerRef = useRef<HTMLDivElement>(null);
  const pageKey = 'global';

  // 初始化当前页面
  useEffect(() => {
    setCurrentPage(pageKey);
  }, [setCurrentPage]);

  // 清理通知定时器
  useEffect(() => {
    return () => {
      if (notificationTimerRef.current) {
        clearTimeout(notificationTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!userInfo) {
      navigate('/login');
    }
  }, [userInfo, navigate]);

  const handleTranslation = async () => {
    if (!inputText.trim()) {
      alert('请先输入文本');
      return;
    }

    await handleStreamTranslation();
  };

  const handleStreamTranslation = async () => {
    if (!inputText.trim()) {
      alert('请先输入文本');
      return;
    }

    // 显示全局进度
    showProgress('智能翻译运行中，请稍后', 'translation');

    // 重置流式状态
    resetStreamState();
    setStreaming(true);
    setPartialText('');
    setSentences([]);
    setCurrentSentenceIndex(0);
    setTotalSentences(0);
    setStreamError(null);

    // 创建AbortController用于取消请求
    const abortController = new AbortController();
    setCancelStream(() => () => {
      abortController.abort();
      hideProgress();
    });

    try {
      // 构建流式翻译请求
      const streamRequest: StreamTranslationRequest = {
        text: inputText,
        operation: englishType === 'us' ? 'translate_us' : 'translate_uk',
        version: version,
      };

      // 调用流式翻译API
      const streamGenerator = apiClient.translateStream(streamRequest, {
        signal: abortController.signal,
        onProgress: (chunk) => {
          // 处理不同类型的块
          switch (chunk.type) {
            case 'chunk':
              if (chunk.text) {
                appendPartialText(chunk.text);
              }
              break;
            case 'sentence':
              // 句子数据现在显示，实现逐句翻译效果
              if (chunk.text && chunk.index !== undefined) {
                // 添加或更新句子
                addSentence(chunk.text, chunk.index);
                setCurrentSentenceIndex(chunk.index);
                setTotalSentences(chunk.total || 0);
              }
              break;
            case 'complete':
              if (chunk.text) {
                setTranslatedText(chunk.text);
                setEditableText(chunk.text);
                setStreaming(false);
                // 更新进度消息
                updateProgress('智能翻译完成');
                // 2秒后隐藏进度（全局状态栏会显示完成状态）
                setTimeout(() => {
                  hideProgress();
                }, 2000);

                // 更新用户信息
                try {
                  apiClient.getCurrentUser().then(updateUserInfo);
                } catch (error) {
                  console.warn('获取更新后的用户信息失败:', error);
                }
              }
              break;
            case 'error':
              setStreamError(chunk.error || '未知错误');
              setStreaming(false);
              updateProgress(`智能翻译错误: ${chunk.error}`);
              // 2秒后隐藏进度
              setTimeout(() => {
                hideProgress();
              }, 2000);
              alert(`流式翻译错误: ${chunk.error}`);
              break;
          }
        },
      });

      // 消费流式生成器
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      for await (const _ of streamGenerator) {
        // 数据已在onProgress回调中处理
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('流式翻译已取消');
        setStreamError('翻译已取消');
        updateProgress('智能翻译已取消');
      } else {
        let errorMessage = '流式翻译失败，请稍后重试';
        if (error instanceof Error) {
          errorMessage = error.message;
        }
        setStreamError(errorMessage);
        updateProgress(`智能翻译失败: ${errorMessage}`);
        alert(errorMessage);
      }
      setStreaming(false);
      // 2秒后隐藏进度
      setTimeout(() => {
        hideProgress();
      }, 2000);
    } finally {
      setCancelStream(null);
    }
  };

  const handleCancelStream = () => {
    if (cancelStream) {
      cancelStream();
      setStreaming(false);
      setCancelStream(null);
      setStreamError('翻译已取消');
      hideProgress();
    }
  };

  const handleClear = () => {
    clear();
  };

  const handleCopyInput = () => {
    if (inputText) {
      try {
        navigator.clipboard.writeText(inputText);
        // 清除之前的定时器
        if (notificationTimerRef.current) {
          clearTimeout(notificationTimerRef.current);
        }
        // 设置通知
        setCopyNotification('已复制输入文本到剪贴板');
        // 2秒后自动清除通知
        notificationTimerRef.current = setTimeout(() => {
          setCopyNotification(null);
        }, 2000);
      } catch (error) {
        console.error('复制失败:', error);
        // 可选：显示错误通知
        setCopyNotification('复制失败，请手动复制');
        notificationTimerRef.current = setTimeout(() => {
          setCopyNotification(null);
        }, 2000);
      }
    }
  };

  const handleCopyResult = () => {
    if (translatedText) {
      try {
        // 清理markdown符号后复制
        const cleanedText = cleanTextFromMarkdown(translatedText);
        navigator.clipboard.writeText(cleanedText);
        // 清除之前的定时器
        if (notificationTimerRef.current) {
          clearTimeout(notificationTimerRef.current);
        }
        // 设置通知
        setCopyNotification('已复制到剪贴板');
        // 2秒后自动清除通知
        notificationTimerRef.current = setTimeout(() => {
          setCopyNotification(null);
        }, 2000);
      } catch (error) {
        console.error('复制失败:', error);
        setCopyNotification('复制失败，请手动复制');
        notificationTimerRef.current = setTimeout(() => {
          setCopyNotification(null);
        }, 2000);
      }
    }
  };

  const conversation = conversations[pageKey] || {
    isExpanded: false,
    messages: [],
    inputText: '',
    loading: false,
    sessionId: null,
    splitPosition: 60,
  };

  const workspaceWidth = conversation.isExpanded ? 60 : 100;

  const handleEditText = (text: string) => {
    setEditableText(text);
  };

  return (
    <div className={styles.translationContainer} ref={containerRef}>
      {/* 复制成功通知 */}
      {copyNotification && <div className={styles.copyNotification}>{copyNotification}</div>}
      <div className={styles.pageContainer}>
        {/* 工作区 */}
        <div className={styles.workspaceContainer} style={{ width: `${workspaceWidth}%` }}>
          {/* 顶部状态栏：全局进度条 */}
          <div className={styles.topBarContainer}>
            <GlobalProgressBar />
          </div>

          <div className={styles.workspaceHeader}>{/* 标题已移除，AI按钮已移到输入区域 */}</div>

          <div className={styles.workspaceContent}>
            <div className={styles.content}>
              {/* 输入区域 */}
              <Card variant="ghost" padding="medium" className={styles.inputCard}>
                <div className={styles.inputHeader}>
                  <h2 className={styles.cardTitle}>输入中文文本</h2>
                  <div className={styles.versionSection}>
                    <div className={styles.selectionGroup}>
                      <div className={styles.selectionItem}>
                        <div className={styles.selectionLabel}>
                          <button
                            className={styles.versionHelp}
                            title="专业版：允许适当使用伴随状语从句以增强表达专业性&#13;&#10;基础版：严格避免使用AI句式以降低AI率"
                          >
                            !
                          </button>
                          <span>翻译版本</span>
                        </div>
                        <div className={styles.selectionButtons}>
                          <Button
                            variant={version === 'professional' ? 'primary' : 'ghost'}
                            size="small"
                            onClick={() => setVersion('professional')}
                            disabled={loading}
                          >
                            专业版
                          </Button>
                          <Button
                            variant={version === 'basic' ? 'primary' : 'ghost'}
                            size="small"
                            onClick={() => setVersion('basic')}
                            disabled={loading}
                          >
                            基础版
                          </Button>
                        </div>
                      </div>
                      <div className={styles.selectionItem}>
                        <div className={styles.selectionLabel}>
                          <span>英语体系</span>
                        </div>
                        <div className={styles.selectionButtons}>
                          <Button
                            variant={englishType === 'us' ? 'primary' : 'ghost'}
                            size="small"
                            onClick={() => setEnglishType('us')}
                            disabled={loading}
                          >
                            美式
                          </Button>
                          <Button
                            variant={englishType === 'uk' ? 'primary' : 'ghost'}
                            size="small"
                            onClick={() => setEnglishType('uk')}
                            disabled={loading}
                          >
                            英式
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div
                    className={styles.aiToggleButton}
                    onClick={() => toggleExpanded(pageKey)}
                    title={conversation.isExpanded ? '隐藏Otium' : '显示Otium'}
                  >
                    <img src="/google-gemini.svg" alt="Otium" className={styles.aiToggleIcon} />
                  </div>
                </div>

                <div className={styles.textareaWrapper}>
                  <Textarea
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder="请输入中文文本..."
                    rows={19}
                    resize="vertical"
                    fullWidth
                    maxLength={1000}
                  />
                  <div className={styles.charCount}>{inputText.length} / 1000</div>
                </div>

                <div className={styles.inputFooter}>
                  <div className={styles.buttonRow}>
                    <div className={styles.leftButtonGroup}>
                      {streaming ? (
                        <Button
                          variant="danger"
                          size="small"
                          onClick={handleCancelStream}
                          disabled={!cancelStream}
                        >
                          取消翻译
                        </Button>
                      ) : (
                        <Button
                          variant="primary"
                          size="small"
                          onClick={handleTranslation}
                          loading={loading && loadingStep === 'translating'}
                          disabled={loading || streaming}
                        >
                          开始翻译
                        </Button>
                      )}
                    </div>
                    <div className={styles.rightButtonGroup}>
                      <Button variant="ghost" size="small" onClick={handleClear} disabled={loading}>
                        清空全文
                      </Button>
                      <Button
                        variant="ghost"
                        size="small"
                        onClick={handleCopyInput}
                        disabled={loading || !inputText.trim()}
                      >
                        复制全文
                      </Button>
                    </div>
                  </div>
                </div>

                {/* 流式翻译实时结果显示 */}
                {streaming && partialText && (
                  <div className={styles.partialText}>
                    <div className={styles.partialTextLabel}>实时翻译进度</div>
                    <div className={styles.partialTextContent}>{partialText}</div>
                    <div className={styles.partialTextIndicator}>
                      <div className={styles.loadingSpinner} />
                      <span>翻译进行中...</span>
                    </div>
                  </div>
                )}
              </Card>

              {/* 翻译结果显示 */}
              {translatedText && (
                <Card variant="ghost" padding="medium" className={styles.resultCard}>
                  <div className={styles.resultHeader}>
                    <div className={styles.resultTitleRow}>
                      <h3 className={styles.resultTitle}>
                        {englishType === 'us' ? '美式' : '英式'}翻译结果
                      </h3>
                      <div className={styles.resultActions}>
                        <div className={styles.formatToggleContainer}>
                          <span className={styles.formatToggleLabel}>
                            {showFormatted ? '点击切换编辑模式' : '点击切换预览模式'}
                          </span>
                          <button
                            className={styles.formatToggle}
                            onClick={() => setShowFormatted(!showFormatted)}
                            title={showFormatted ? '点击切换到编辑模式' : '点击切换到预览模式'}
                            data-state={showFormatted ? 'off' : 'on'}
                            aria-label={showFormatted ? '点击切换到编辑模式' : '点击切换到预览模式'}
                          />
                        </div>
                        <Button variant="ghost" size="small" onClick={handleCopyResult}>
                          复制结果
                        </Button>
                      </div>
                    </div>
                  </div>
                  {showFormatted ? (
                    <div
                      className={styles.formattedResult}
                      dangerouslySetInnerHTML={{ __html: renderMarkdownAsHtml(editableText) }}
                    />
                  ) : (
                    <Textarea
                      value={editableText}
                      onChange={(e) => handleEditText(e.target.value)}
                      placeholder="翻译结果..."
                      rows={19}
                      resize="vertical"
                      fullWidth
                      className={styles.resultTextarea}
                    />
                  )}
                </Card>
              )}
            </div>
          </div>
        </div>

        {/* AI面板 */}
        {conversation.isExpanded && (
          <div className={styles.aiPanelContainer} style={{ width: '40%' }}>
            <AIChatPanel pageKey={pageKey} />
          </div>
        )}
      </div>
    </div>
  );
};

export default TextTranslation;
