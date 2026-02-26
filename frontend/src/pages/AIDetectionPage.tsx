import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';
import { useDetectionStore } from '../store/useDetectionStore';
import { useGlobalProgressStore } from '../store/useGlobalProgressStore';
import { useAIChatStore } from '../store/useAIChatStore';
import Card from '../components/ui/Card/Card';
import Textarea from '../components/ui/Textarea/Textarea';
import Button from '../components/ui/Button/Button';
import GlobalProgressBar from '../components/GlobalProgressBar/GlobalProgressBar';
import AIDetection from '../components/AIDetection';
import AIChatPanel from '../components/AIChatPanel/AIChatPanel';
import { AIDetectionResponse } from '../types';
import styles from './AIDetectionPage.module.css';

const AIDetectionPage: React.FC = () => {
  const navigate = useNavigate();
  const { userInfo } = useAuthStore();

  const {
    inputText,
    detectionResult,
    shouldDetect,
    setInputText,
    setDetectionResult,
    setShouldDetect,
    clear,
  } = useDetectionStore();

  const { showProgress, hideProgress, updateProgress } = useGlobalProgressStore();

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

  // 当输入文本变化时重置检测状态
  useEffect(() => {
    setShouldDetect(false);
    // 如果输入文本不为空且与保存结果的文本不匹配，清除保存的结果
    if (detectionResult && inputText.trim() && inputText.trim() !== detectionResult.full_text) {
      setDetectionResult(null);
    }
  }, [inputText, detectionResult, setShouldDetect, setDetectionResult]);

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

  const handleClear = () => {
    clear();
  };

  const handleCopyInput = () => {
    if (inputText) {
      navigator.clipboard.writeText(inputText);
      showNotification('已复制输入文本到剪贴板');
    }
  };

  const handleDetectionComplete = (result: AIDetectionResponse) => {
    setDetectionResult(result);
    // 更新进度消息
    updateProgress('AI检测完成');
    // 2秒后隐藏进度
    setTimeout(() => {
      hideProgress();
    }, 2000);
    // 不再显示页面中间的通知，只在全局状态栏显示
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
    <div className={styles.detectionContainer} ref={containerRef}>
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
                  <h2 className={styles.cardTitle}>输入待检测文本</h2>
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
                    placeholder="请输入待检测的文本..."
                    rows={19}
                    resize="vertical"
                    fullWidth
                    maxLength={5000}
                  />
                </div>

                <div className={styles.inputFooter}>
                  <div className={styles.buttonRow}>
                    <div className={styles.leftButtonGroup}>
                      <Button
                        variant="primary"
                        size="small"
                        onClick={() => {
                          if (!inputText.trim()) {
                            alert('请先输入文本');
                            return;
                          }
                          // 显示全局进度
                          showProgress('AI检测运行中，请稍后', 'ai-detection');
                          setShouldDetect(true);
                        }}
                        disabled={!inputText.trim()}
                      >
                        开始检测
                      </Button>
                    </div>
                    <div className={styles.rightButtonGroup}>
                      <Button variant="ghost" size="small" onClick={handleClear}>
                        清空全文
                      </Button>
                      <Button
                        variant="ghost"
                        size="small"
                        onClick={handleCopyInput}
                        disabled={!inputText.trim()}
                      >
                        复制全文
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>

              {/* AI检测组件 */}
              {(inputText.trim() || detectionResult) && (
                <AIDetection
                  text={inputText.trim() ? inputText : detectionResult?.full_text || ''}
                  onDetectionComplete={handleDetectionComplete}
                  autoDetect={shouldDetect}
                  result={detectionResult}
                  onCopyNotification={showNotification}
                />
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

export default AIDetectionPage;
