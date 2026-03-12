import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';
import { useCorrectionStore } from '../store/useCorrectionStore';
import { useGlobalProgressStore } from '../store/useGlobalProgressStore';
import { useAIChatStore } from '../store/useAIChatStore';
import { apiClient } from '../api/client';
import { cleanTextFromMarkdown } from '../utils/textCleaner';
import Card from '../components/ui/Card/Card';
import Textarea from '../components/ui/Textarea/Textarea';
import Button from '../components/ui/Button/Button';
import GlobalProgressBar from '../components/GlobalProgressBar/GlobalProgressBar';
import AIChatPanel from '../components/AIChatPanel/AIChatPanel';
import styles from './TextCorrection.module.css';

const INPUT_TITLE = '\u8f93\u5165\u4e2d\u6587\u6587\u672c';
const INPUT_PLACEHOLDER = '\u8bf7\u8f93\u5165\u4e2d\u6587\u6587\u672c...';
const START_BUTTON_LABEL = '\u667a\u80fd\u7ea0\u9519';
const CLEAR_LABEL = '\u6e05\u7a7a\u5168\u6587';
const COPY_FULL_TEXT_LABEL = '\u590d\u5236\u5168\u6587';
const RESULT_TITLE = '\u7ea0\u9519\u7ed3\u679c';
const COPY_RESULT_LABEL = '\u590d\u5236\u7ed3\u679c';
const SHOW_AI_TITLE = '\u663e\u793a Otium \u52a9\u624b';
const HIDE_AI_TITLE = '\u9690\u85cf Otium \u52a9\u624b';
const INPUT_EMPTY_ALERT = '\u8bf7\u5148\u8f93\u5165\u6587\u672c\u3002';
const COMPLETE_TEXT = '\u667a\u80fd\u7ea0\u9519\u5df2\u5b8c\u6210\u3002';
const EMPTY_RESULT_TEXT = '\u7ea0\u9519\u672a\u8fd4\u56de\u53ef\u663e\u793a\u5185\u5bb9\u3002';
const ERROR_DEFAULT_TEXT = '\u5904\u7406\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\u3002';
const COPY_INPUT_SUCCESS = '\u8f93\u5165\u6587\u672c\u5df2\u590d\u5236\u3002';
const COPY_RESULT_SUCCESS = '\u7ed3\u679c\u5df2\u590d\u5236\u3002';
const COPY_FAILED = '\u590d\u5236\u5931\u8d25\u3002';
const REFRESH_USER_FAILED = '\u5237\u65b0\u7528\u6237\u4fe1\u606f\u5931\u8d25:';

const CORRECTION_LOADING_MESSAGES = [
  '\u6b63\u5728\u68c0\u67e5\u7c97\u5fc3\u7a0b\u5ea6\uff08\u63a8\u773c\u955c\uff09',
  '\u6b63\u5728\u9010\u53e5\u68c0\u67e5\u7ec6\u8282',
  '\u6b63\u5728\u6293\u6355\u53ef\u7591\u9519\u5b57',
  '\u6b63\u5728\u6821\u51c6\u6587\u672c\u4e25\u8c28\u5ea6',
] as const;

const getCorrectionLoadingMessage = () =>
  CORRECTION_LOADING_MESSAGES[Math.floor(Math.random() * CORRECTION_LOADING_MESSAGES.length)];

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
  const { conversations, toggleExpanded, setCurrentPage } = useAIChatStore();

  const [successNotification, setSuccessNotification] = useState<string | null>(null);
  const [loadingMessage, setLoadingMessage] = useState<string>('');
  const containerRef = useRef<HTMLDivElement>(null);
  const notificationTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pageKey = 'global';

  useEffect(() => {
    setCurrentPage(pageKey);
  }, [setCurrentPage]);

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

  const showNotification = (message: string) => {
    if (notificationTimerRef.current) {
      clearTimeout(notificationTimerRef.current);
    }

    setSuccessNotification(message);
    notificationTimerRef.current = setTimeout(() => {
      setSuccessNotification(null);
    }, 2000);
  };

  const handleErrorCheck = async () => {
    if (!inputText.trim()) {
      alert(INPUT_EMPTY_ALERT);
      return;
    }

    const nextLoadingMessage = getCorrectionLoadingMessage();
    setLoadingMessage(nextLoadingMessage);
    showProgress(nextLoadingMessage, 'correction');
    setLoading(true);
    setLoadingStep('error_checking');
    setResultText(nextLoadingMessage);
    setEditableText(nextLoadingMessage);
    try {
      const response = await apiClient.checkText({
        text: inputText,
        operation: 'error_check',
      });

      if (!response.success || !response.text) {
        throw new Error(response.message || EMPTY_RESULT_TEXT);
      }

      setResultText(response.text);
      setEditableText(response.text);

      updateProgress(COMPLETE_TEXT);

      try {
        const updatedUserInfo = await apiClient.getCurrentUser();
        updateUserInfo(updatedUserInfo);
      } catch (error) {
        console.warn(REFRESH_USER_FAILED, error);
      }
    } catch (error) {
      let errorMessage = ERROR_DEFAULT_TEXT;
      if (error instanceof Error) {
        errorMessage = error.message;
      }

      setResultText('');
      setEditableText('');
      setLoadingMessage('');
      updateProgress(`\u667a\u80fd\u7ea0\u9519\u5931\u8d25: ${errorMessage}`);
      alert(errorMessage);
    } finally {
      setLoading(false);
      setLoadingStep(null);
      setTimeout(() => {
        hideProgress();
      }, 1200);
    }
  };

  const handleClear = () => {
    setLoadingMessage('');
    clear();
  };

  const handleCopyInput = () => {
    if (!inputText) {
      return;
    }

    try {
      navigator.clipboard.writeText(inputText);
      showNotification(COPY_INPUT_SUCCESS);
    } catch (error) {
      console.error(COPY_FAILED, error);
      showNotification(COPY_FAILED);
    }
  };

  const handleCopyResult = () => {
    if (!resultText) {
      return;
    }

    try {
      const cleanedText = cleanTextFromMarkdown(resultText);
      navigator.clipboard.writeText(cleanedText);
      showNotification(COPY_RESULT_SUCCESS);
    } catch (error) {
      console.error(COPY_FAILED, error);
      showNotification(COPY_FAILED);
    }
  };

  const renderHighlightedText = (text: string) => {
    const segments = text.split(/(\*\*[\s\S]*?\*\*|__[\s\S]*?__)/g).filter(Boolean);

    return segments.map((segment, index) => {
      const isDoubleAsterisk = segment.startsWith('**') && segment.endsWith('**');
      const isDoubleUnderscore = segment.startsWith('__') && segment.endsWith('__');

      if (isDoubleAsterisk || isDoubleUnderscore) {
        const content = segment.slice(2, -2);
        return (
          <mark key={index} className={styles.inlineHighlight}>
            {content}
          </mark>
        );
      }

      return <React.Fragment key={index}>{segment}</React.Fragment>;
    });
  };

  const conversation = conversations[pageKey] || {
    isExpanded: false,
    messages: [],
    inputText: '',
    loading: false,
    activeTaskId: null,
    sessionId: null,
    splitPosition: 60,
  };

  const workspaceWidth = conversation.isExpanded ? 60 : 100;
  const aiToggleTitle = conversation.isExpanded ? HIDE_AI_TITLE : SHOW_AI_TITLE;

  return (
    <div className={styles.correctionContainer} ref={containerRef}>
      {successNotification && <div className={styles.copyNotification}>{successNotification}</div>}
      <div className={styles.pageContainer}>
        <div className={styles.workspaceContainer} style={{ width: `${workspaceWidth}%` }}>
          <div className={styles.topBarContainer}>
            <GlobalProgressBar />
          </div>

          <div className={styles.workspaceHeader} />

          <div className={styles.workspaceContent}>
            <div className={styles.content}>
              <Card variant="ghost" padding="medium" className={styles.inputCard}>
                <div className={styles.inputHeader}>
                  <h2 className={styles.cardTitle}>{INPUT_TITLE}</h2>
                  <div
                    className={styles.aiToggleButton}
                    onClick={() => toggleExpanded(pageKey)}
                    title={aiToggleTitle}
                  >
                    <img src="/google-gemini.svg" alt="Otium" className={styles.aiToggleIcon} />
                  </div>
                </div>

                <div className={styles.textareaWrapper}>
                  <Textarea
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder={INPUT_PLACEHOLDER}
                    rows={24}
                    resize="vertical"
                    fullWidth
                    maxLength={1000}
                    className={styles.inputTextarea}
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
                        {START_BUTTON_LABEL}
                      </Button>
                    </div>
                    <div className={styles.rightButtonGroup}>
                      <Button variant="ghost" size="small" onClick={handleClear} disabled={loading}>
                        {CLEAR_LABEL}
                      </Button>
                      <Button
                        variant="ghost"
                        size="small"
                        onClick={handleCopyInput}
                        disabled={loading || !inputText.trim()}
                      >
                        {COPY_FULL_TEXT_LABEL}
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>

              {(loading || resultText) && (
                <Card variant="ghost" padding="medium" className={styles.resultCard}>
                  <div className={styles.resultHeader}>
                    <h3 className={styles.resultTitle}>{RESULT_TITLE}</h3>
                    {!loading && resultText && (
                      <Button variant="ghost" size="small" onClick={handleCopyResult}>
                        {COPY_RESULT_LABEL}
                      </Button>
                    )}
                  </div>
                  <div className={styles.resultText}>
                    {loading ? (
                      <div className={styles.loadingPlaceholder}>
                        <span>{loadingMessage || resultText}</span>
                        <div className={styles.waveDots}>
                          <div className={styles.waveDot} />
                          <div className={styles.waveDot} />
                          <div className={styles.waveDot} />
                        </div>
                      </div>
                    ) : (
                      renderHighlightedText(resultText)
                    )}
                  </div>
                </Card>
              )}
            </div>
          </div>
        </div>

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
