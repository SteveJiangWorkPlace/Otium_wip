import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';
import { useCorrectionStore } from '../store/useCorrectionStore';
import { useGlobalProgressStore } from '../store/useGlobalProgressStore';
import { useAIChatStore } from '../store/useAIChatStore';
import { apiClient } from '../api/client';
import { cleanTextFromMarkdown, renderMarkdownAsHtml } from '../utils/textCleaner';
import Card from '../components/ui/Card/Card';
import Textarea from '../components/ui/Textarea/Textarea';
import Button from '../components/ui/Button/Button';
import GlobalProgressBar from '../components/GlobalProgressBar/GlobalProgressBar';
import AIChatPanel from '../components/AIChatPanel/AIChatPanel';
import styles from './TextCorrection.module.css';

const TextCorrection: React.FC = () => {
  const navigate = useNavigate();
  const { userInfo, updateUserInfo } = useAuthStore();

  const {
    inputText,
    loading,
    loadingStep,
    resultText,
    setInputText,
    setLoading,
    setLoadingStep,
    setResultText,
    setEditableText,
    clear,
  } = useCorrectionStore();

  const { showProgress, hideProgress, updateProgress } = useGlobalProgressStore();

  // AI聊天状态
  const { conversations, toggleExpanded, setCurrentPage } = useAIChatStore();

  const containerRef = useRef<HTMLDivElement>(null);
  const pageKey = 'global';

  // 成功通知状态
  const [successNotification, setSuccessNotification] = useState<string | null>(null);
  const notificationTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

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

  const handleErrorCheck = async () => {
    if (!inputText.trim()) {
      alert('请先输入文本');
      return;
    }

    // 显示全局进度
    showProgress('智能纠错运行中，请稍后', 'correction');

    setLoading(true);
    setLoadingStep('error_checking');
    try {
      const response = await apiClient.checkText({
        text: inputText,
        operation: 'error_check',
      });

      if (response.success) {
        setResultText(response.text);
        setEditableText(response.text);
        // 更新进度消息
        updateProgress('智能纠错完成');
        // 2秒后隐藏进度（全局状态栏会显示完成状态）
        setTimeout(() => {
          hideProgress();
        }, 2000);

        // 处理成功后，获取最新的用户信息以更新剩余次数（如果API扣除了次数）
        try {
          const updatedUserInfo = await apiClient.getCurrentUser();
          updateUserInfo(updatedUserInfo);
          console.log('用户信息已更新');
        } catch (error) {
          console.warn('获取更新后的用户信息失败:', error);
          // 不再需要处理剩余次数，现在只使用每日限制
        }
      }
    } catch (error) {
      let errorMessage = '处理失败，请稍后重试';
      if (error instanceof Error) {
        errorMessage = error.message;
      } else if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as any;
        errorMessage = axiosError.response?.data?.detail || errorMessage;
      }
      updateProgress(`智能纠错失败: ${errorMessage}`);
      // 2秒后隐藏进度
      setTimeout(() => {
        hideProgress();
      }, 2000);
      alert(errorMessage);
    } finally {
      setLoading(false);
      setLoadingStep(null);
    }
  };

  const handleClear = () => {
    clear();
  };

  const handleCopyInput = () => {
    if (inputText) {
      try {
        navigator.clipboard.writeText(inputText);
        showNotification('已复制输入文本到剪贴板');
      } catch (error) {
        console.error('复制失败:', error);
        showNotification('复制失败，请手动复制');
      }
    }
  };

  const handleCopyResult = () => {
    if (resultText) {
      try {
        // 清理markdown符号后复制
        const cleanedText = cleanTextFromMarkdown(resultText);
        navigator.clipboard.writeText(cleanedText);
        showNotification('已复制到剪贴板');
      } catch (error) {
        console.error('复制失败:', error);
        showNotification('复制失败，请手动复制');
      }
    }
  };

  const renderHighlightedText = (text: string) => {
    // 先将markdown符号转换为HTML（处理粗体、斜体、换行等）
    let highlightedText = renderMarkdownAsHtml(text);

    // 将粗体标签（<strong>和<b>）转换为高亮标记，用于突出显示修改部分
    highlightedText = highlightedText.replace(
      /<strong>(.*?)<\/strong>/g,
      '<mark style="background-color: var(--color-black); color: var(--color-white); padding: 2px 4px; border-radius: 4px;">$1</mark>'
    );
    highlightedText = highlightedText.replace(
      /<b>(.*?)<\/b>/g,
      '<mark style="background-color: var(--color-black); color: var(--color-white); padding: 2px 4px; border-radius: 4px;">$1</mark>'
    );
    // 保持<i>和<em>斜体标签不变
    return { __html: highlightedText };
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
    <div className={styles.correctionContainer} ref={containerRef}>
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
                  <h2 className={styles.cardTitle}>输入中文文本</h2>
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
                      <Button
                        variant="primary"
                        size="small"
                        onClick={handleErrorCheck}
                        loading={loading && loadingStep === 'error_checking'}
                        disabled={loading}
                      >
                        智能纠错
                      </Button>
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
              </Card>

              {/* 结果显示 */}
              {resultText && (
                <Card variant="ghost" padding="medium" className={styles.resultCard}>
                  <div className={styles.resultHeader}>
                    <h3 className={styles.resultTitle}>纠错结果</h3>
                    <Button variant="ghost" size="small" onClick={handleCopyResult}>
                      复制结果
                    </Button>
                  </div>
                  <div
                    className={styles.resultText}
                    dangerouslySetInnerHTML={renderHighlightedText(resultText)}
                  />
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

export default TextCorrection;
