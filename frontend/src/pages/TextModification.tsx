import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';
import { useModificationStore } from '../store/useModificationStore';
import { useGlobalProgressStore } from '../store/useGlobalProgressStore';
import { useAIChatStore } from '../store/useAIChatStore';
import { apiClient } from '../api/client';
import { debugLog } from '../utils/logger';
import { cleanTextFromMarkdown, renderMarkdownAsHtml } from '../utils/textCleaner';
import type { StreamRefineTextRequest } from '../types';
import Card from '../components/ui/Card/Card';
import Textarea from '../components/ui/Textarea/Textarea';
import Button from '../components/ui/Button/Button';
import { useToast } from '../components/ui/Toast';
import DirectiveSelector from '../components/DirectiveSelector';
import GlobalProgressBar from '../components/GlobalProgressBar/GlobalProgressBar';
import AIChatPanel from '../components/AIChatPanel/AIChatPanel';
import styles from './TextModification.module.css';

const TextModification: React.FC = () => {
  const navigate = useNavigate();
  const { userInfo } = useAuthStore();

  const {
    inputText,
    loading,
    selectedDirectives,
    modifiedText,
    showAnnotations,
    streaming,
    partialText,
    setInputText,
    setSelectedDirectives,
    setModifiedText,
    setShowAnnotations,
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
  } = useModificationStore();

  const { showProgress, hideProgress, updateProgress } = useGlobalProgressStore();
  const toast = useToast();

  // 成功通知状态
  const [successNotification, setSuccessNotification] = useState<string | null>(null);
  const notificationTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // AI聊天状态
  const { conversations, toggleExpanded, setCurrentPage } = useAIChatStore();

  const containerRef = useRef<HTMLDivElement>(null);
  const pageKey = 'global';

  // 初始化当前页面
  useEffect(() => {
    setCurrentPage(pageKey);
  }, [setCurrentPage]);

  useEffect(() => {
    if (!userInfo) {
      navigate('/login');
    }
  }, [userInfo, navigate]);

  // 清理通知定时器
  useEffect(() => {
    return () => {
      if (notificationTimerRef.current) {
        clearTimeout(notificationTimerRef.current);
      }
    };
  }, []);

  // 显示成功通知
  const showNotification = (message: string) => {
    // 清除之前的定时器
    if (notificationTimerRef.current) {
      clearTimeout(notificationTimerRef.current);
    }
    // 设置通知
    setSuccessNotification(message);
    // 2秒后自动清除通知
    notificationTimerRef.current = setTimeout(() => {
      setSuccessNotification(null);
    }, 2000);
  };

  const handleApplyModifications = async () => {
    if (!inputText.trim()) {
      toast.error('请先输入文本');
      return;
    }

    // 允许执行的条件：选择了指令 或 文本包含批注
    if (selectedDirectives.length === 0 && !containsAnnotations(inputText)) {
      toast.error('请至少选择一个修改指令或在文本中添加【】或[]格式的局部批注');
      return;
    }

    // 使用流式修改
    await handleStreamRefine();
  };

  const handleClear = () => {
    clear();
  };

  const handleCopyInput = () => {
    if (inputText) {
      navigator.clipboard.writeText(inputText);
      showNotification('已复制输入文本到剪贴板');
    }
  };

  const handleStreamRefine = async () => {
    // 显示全局进度
    showProgress('智能文本修改运行中，请稍后', 'modification');

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
      // 构建流式文本修改请求
      const streamRequest: StreamRefineTextRequest = {
        text: inputText,
        directives: selectedDirectives,
      };

      // 调用流式文本修改API
      const streamGenerator = apiClient.refineStream(streamRequest, {
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
              // 句子数据现在显示，实现逐句修改效果
              if (chunk.text && chunk.index !== undefined) {
                // 添加或更新句子
                addSentence(chunk.text, chunk.index);
                setCurrentSentenceIndex(chunk.index);
                setTotalSentences(chunk.total || 0);
              }
              break;
            case 'complete':
              if (chunk.text) {
                setModifiedText(chunk.text);
                setStreaming(false);
                // 更新进度消息
                updateProgress('智能文本修改完成');
                // 2秒后隐藏进度
                setTimeout(() => {
                  hideProgress();
                }, 2000);
                // 不再显示页面中间的通知，只在全局状态栏显示
              }
              break;
            case 'error':
              setStreamError(chunk.error || '未知错误');
              setStreaming(false);
              updateProgress(`智能文本修改错误: ${chunk.error}`);
              // 2秒后隐藏进度
              setTimeout(() => {
                hideProgress();
              }, 2000);
              toast.error(`流式文本修改错误: ${chunk.error}`);
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
        debugLog('流式文本修改已取消');
        setStreamError('修改已取消');
        updateProgress('智能文本修改已取消');
      } else {
        let errorMessage = '流式文本修改失败，请稍后重试';
        if (error instanceof Error) {
          errorMessage = error.message;
        }
        setStreamError(errorMessage);
        updateProgress(`智能文本修改失败: ${errorMessage}`);
        toast.error(errorMessage);
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

  const handleCopyResult = () => {
    if (modifiedText) {
      // 清理markdown符号后复制
      const cleanedText = cleanTextFromMarkdown(modifiedText);
      navigator.clipboard.writeText(cleanedText);
      showNotification('已复制修改结果到剪贴板');
    }
  };

  // 检测文本是否包含【】或[]批注
  const containsAnnotations = (text: string): boolean => {
    return /【.*?】|\[.*?\]/.test(text);
  };

  const renderAnnotatedText = (text: string) => {
    // 先使用markdown渲染函数处理基本格式
    let html = renderMarkdownAsHtml(text);

    // 对于批注显示模式，将粗体(<strong>)转换为高亮标记(<mark>)
    // 这样可以保持粗体文本的高亮效果
    html = html.replace(
      /<strong>(.*?)<\/strong>/g,
      '<mark style="background-color: var(--color-black); color: var(--color-white); padding: 2px 4px; border-radius: 4px;">$1</mark>'
    );
    // 同时处理可能存在的<b>标签
    html = html.replace(
      /<b>(.*?)<\/b>/g,
      '<mark style="background-color: var(--color-black); color: var(--color-white); padding: 2px 4px; border-radius: 4px;">$1</mark>'
    );

    return { __html: html };
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

  return (
    <div className={styles.modificationContainer} ref={containerRef}>
      {/* 成功通知 */}
      {successNotification && <div className={styles.copyNotification}>{successNotification}</div>}
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
                  <h2 className={styles.cardTitle}>输入待修改文本</h2>
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
                    placeholder="请输入待修改的文本..."
                    rows={19}
                    resize="vertical"
                    fullWidth
                    maxLength={5000}
                  />
                </div>

                <div className={styles.inputFooter}>
                  <div className={styles.buttonRow}>
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
              </Card>

              {/* cat用户的特殊提示 */}
              {userInfo?.username === 'cat' && (
                <div className={styles.catUserHint}>
                  <div
                    style={{
                      fontSize: 'var(--font-size-sm)',
                      color: 'var(--color-text-secondary)',
                      marginBottom: 'var(--spacing-3)',
                      lineHeight: 'var(--line-height-relaxed)',
                      backgroundColor: 'var(--color-background-secondary)',
                      padding: 'var(--spacing-3)',
                      borderRadius: 'var(--border-radius-md)',
                      borderLeft: '4px solid var(--color-primary)',
                    }}
                  >
                    在该工具用于修改或写作<strong>个人陈述</strong>时，建议的文本修改顺序：
                    <br />
                    1. <strong>去AI词汇</strong>：替换AI写作常用短语和词汇
                    <br />
                    2. <strong>去AI三板斧</strong>：修改AI写作常用的语法和符号习惯
                    <br />
                    3. <strong>人性化处理</strong>：将过于学术生硬的表达口语化
                  </div>
                </div>
              )}

              {/* 指令选择器 */}
              <DirectiveSelector
                selectedDirectives={selectedDirectives}
                onDirectivesChange={setSelectedDirectives}
                disabled={loading}
              />

              {/* 修改选项 */}
              {(selectedDirectives.length > 0 || containsAnnotations(inputText)) && (
                <Card variant="ghost" padding="medium" className={styles.optionsCard}>
                  <div className={styles.optionsHeader}>
                    <h3 className={styles.optionsTitle}>修改选项</h3>
                    <div className={styles.annotationsToggle}>
                      <label className={styles.toggleLabel}>
                        <input
                          type="checkbox"
                          checked={showAnnotations}
                          onChange={(e) => setShowAnnotations(e.target.checked)}
                        />
                        <span>显示【】批注</span>
                      </label>
                    </div>
                  </div>
                  <div className={styles.selectedDirectives}>
                    <div className={styles.directivesHeader}>
                      <h4 className={styles.directivesTitle}>
                        {selectedDirectives.length > 0
                          ? `已选指令 (${selectedDirectives.length})`
                          : containsAnnotations(inputText)
                            ? '检测到局部批注'
                            : ''}
                      </h4>
                      <Button
                        variant="primary"
                        size="small"
                        onClick={handleApplyModifications}
                        disabled={loading || streaming || !inputText.trim()}
                      >
                        应用修改
                      </Button>
                    </div>
                    {selectedDirectives.length > 0 && (
                      <div className={styles.directivesList}>
                        {selectedDirectives.map((directive) => (
                          <div key={directive} className={styles.directiveItem}>
                            <span className={styles.directiveName}>{directive}</span>
                          </div>
                        ))}
                      </div>
                    )}
                    {containsAnnotations(inputText) && selectedDirectives.length === 0 && (
                      <div className={styles.annotationsNotice}>
                        <p>检测到文本中包含【】或[]格式的局部批注指令</p>
                      </div>
                    )}
                  </div>
                </Card>
              )}

              {/* 修改结果展示 */}
              {(streaming || modifiedText) && (
                <Card variant="ghost" padding="medium" className={styles.resultCard}>
                  <div className={styles.resultHeader}>
                    <h3 className={styles.resultTitle}>{streaming ? '正在修改...' : '修改结果'}</h3>
                    {!streaming && (
                      <Button variant="ghost" size="small" onClick={handleCopyResult}>
                        复制结果
                      </Button>
                    )}
                  </div>
                  <div className={styles.resultContent}>
                    {streaming ? (
                      // 流式过程中的实时显示
                      <div className={styles.plainText}>
                        {partialText}
                        {streaming && <span className={styles.streamingCursor}>|</span>}
                      </div>
                    ) : showAnnotations ? (
                      // 流式完成后的批注显示
                      <div
                        className={styles.annotatedText}
                        dangerouslySetInnerHTML={renderAnnotatedText(modifiedText)}
                      />
                    ) : (
                      // 流式完成后的普通显示
                      <div className={styles.plainText}>{modifiedText}</div>
                    )}
                  </div>
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

export default TextModification;
