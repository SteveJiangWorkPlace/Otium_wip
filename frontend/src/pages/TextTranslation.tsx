import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';
import { useTranslationStore } from '../store/useTranslationStore';
import { useGlobalProgressStore } from '../store/useGlobalProgressStore';
import { useAIChatStore } from '../store/useAIChatStore';
import { apiClient } from '../api/client';
import { cleanTextFromMarkdown, renderMarkdownAsHtml } from '../utils/textCleaner';
import Card from '../components/ui/Card/Card';
import Textarea from '../components/ui/Textarea/Textarea';
import Button from '../components/ui/Button/Button';
import GlobalProgressBar from '../components/GlobalProgressBar/GlobalProgressBar';
import AIChatPanel from '../components/AIChatPanel/AIChatPanel';
import styles from './TextTranslation.module.css';

const INPUT_TITLE = '\u8f93\u5165\u4e2d\u6587\u6587\u672c';
const VERSION_LABEL = '\u7ffb\u8bd1\u7248\u672c';
const ENGLISH_TYPE_LABEL = '\u82f1\u8bed\u4f53\u7cfb';
const PROFESSIONAL_LABEL = '\u4e13\u4e1a\u7248';
const BASIC_LABEL = '\u57fa\u7840\u7248';
const US_LABEL = '\u7f8e\u5f0f';
const UK_LABEL = '\u82f1\u5f0f';
const START_TRANSLATION_LABEL = '\u5f00\u59cb\u7ffb\u8bd1';
const CLEAR_LABEL = '\u6e05\u7a7a\u5168\u6587';
const COPY_FULL_TEXT_LABEL = '\u590d\u5236\u5168\u6587';
const COPY_RESULT_LABEL = '\u590d\u5236\u7ed3\u679c';
const INPUT_PLACEHOLDER = '\u8bf7\u8f93\u5165\u4e2d\u6587\u6587\u672c...';
const RESULT_PLACEHOLDER = '\u7ffb\u8bd1\u7ed3\u679c...';
const TO_EDIT_MODE_LABEL = '\u5207\u6362\u5230\u7f16\u8f91\u6a21\u5f0f';
const TO_PREVIEW_MODE_LABEL = '\u5207\u6362\u5230\u9884\u89c8\u6a21\u5f0f';
const SHOW_AI_TITLE = '\u663e\u793a Otium \u52a9\u624b';
const HIDE_AI_TITLE = '\u9690\u85cf Otium \u52a9\u624b';
const INPUT_EMPTY_ALERT = '\u8bf7\u5148\u8f93\u5165\u6587\u672c\u3002';
const TRANSLATING_PROGRESS_US = '\u6b63\u5728\u751f\u6210\u7f8e\u5f0f\u8bd1\u6587';
const TRANSLATING_PROGRESS_UK = '\u6b63\u5728\u751f\u6210\u82f1\u5f0f\u8bd1\u6587';
const TRANSLATION_DONE_PROGRESS = '\u667a\u80fd\u7ffb\u8bd1\u5df2\u5b8c\u6210\u3002';
const TRANSLATION_FAILED_DEFAULT =
  '\u7ffb\u8bd1\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\u3002';
const TRANSLATION_EMPTY_RESULT =
  '\u7ffb\u8bd1\u672a\u8fd4\u56de\u53ef\u663e\u793a\u5185\u5bb9\u3002';
const COPY_INPUT_SUCCESS = '\u8f93\u5165\u6587\u672c\u5df2\u590d\u5236\u3002';
const COPY_RESULT_SUCCESS = '\u7ed3\u679c\u5df2\u590d\u5236\u3002';
const COPY_FAILED = '\u590d\u5236\u5931\u8d25\u3002';
const REFRESH_USER_FAILED = '\u5237\u65b0\u7528\u6237\u4fe1\u606f\u5931\u8d25:';
const VERSION_HELP_TITLE =
  '\u4e13\u4e1a\u7248\uff1a\u5141\u8bb8\u66f4\u81ea\u7136\u7684\u5b66\u672f\u8868\u8fbe\u3002&#13;&#10;' +
  '\u57fa\u7840\u7248\uff1a\u8f93\u51fa\u66f4\u514b\u5236\u3001\u66f4\u7b80\u6d01\u3002';

const TRANSLATING_MESSAGES = {
  american: [
    '\u6b63\u5728\u751f\u6210\u7f8e\u5f0f\u8bd1\u6587\u81ea\u7531\u7684\u5473\u9053',
    '\u7f8e\u5f0f\u82f1\u8bed\u6765\u54af\uff0c\u5e26\u7740\u6c49\u5821\u7684\u9999\u6c14',
    '\u6b63\u5728\u53ec\u5524\u7f8e\u5f0f\u7ffb\u8bd1\u7cbe\u7075',
    '\u7f8e\u5f0f\u8bd1\u6587\u751f\u6210\u4e2d\uff0c\u5f88American',
    '\u6b63\u5728\u7528\u7f8e\u5f0f\u601d\u7ef4\u7ffb\u8bd1',
    '\u7f8e\u5f0f\u82f1\u8bed\u52a0\u8f7d\u4e2d\uff0cyeahhhh~',
    '\u7ffb\u8bd1\u6210\u7f8e\u5f0f\u4e2d\uff0c\u81ea\u7531\u800c\u968f\u6027',
    '\u6b63\u5728\u751f\u6210\u7f8e\u5f0f\u8bd1\u6587\uff0c\u5e26\u70b9\u897f\u90e8\u725b\u4ed4\u98ce',
    "\u7f8e\u5f0f\u7ffb\u8bd1\u542f\u52a8\uff0cLet's go!",
    '\u6b63\u5728\u7f8e\u5f0f\u5316\u5904\u7406\u4e2d',
    '\u7f8e\u5f0f\u8bd1\u6587\u70f9\u996a\u4e2d\uff0c\u52a0\u70b9\u81ea\u7531\u8c03\u5473\u6599',
    '\u53ec\u5524\u7f8e\u5f0f\u82f1\u8bed\uff0c\u5e26\u7740\u70ed\u72d7\u548c\u53ef\u4e50',
    '\u6b63\u5728\u751f\u6210\u7f8e\u5f0f\u8bd1\u6587\uff0c\u4f18\u96c5\u53c8\u968f\u610f',
    '\u7f8e\u5f0f\u7ffb\u8bd1\u4e2d\uff0c\u611f\u53d7\u81ea\u7531\u7684\u6c14\u606f',
    '\u6b63\u5728\u7528\u7f8e\u56fd\u8154\u8c03\u7ffb\u8bd1',
  ],
  british: [
    '\u6b63\u5728\u751f\u6210\u82f1\u5f0f\u8bd1\u6587\u4f18\u96c5\u767b\u573a',
    '\u82f1\u5f0f\u82f1\u8bed\u6765\u54af\uff0c\u5e26\u7740\u4e0b\u5348\u8336\u7684\u6c14\u606f',
    '\u6b63\u5728\u53ec\u5524\u82f1\u5f0f\u7ffb\u8bd1\u7ba1\u5bb6',
    '\u82f1\u5f0f\u8bd1\u6587\u751f\u6210\u4e2d\uff0cvery British',
    '\u6b63\u5728\u7528\u82f1\u5f0f\u601d\u7ef4\u7ffb\u8bd1',
    '\u82f1\u5f0f\u82f1\u8bed\u52a0\u8f7d\u4e2d\uff0ccheerio~',
    '\u7ffb\u8bd1\u6210\u82f1\u5f0f\u4e2d\uff0c\u4f18\u96c5\u800c\u7ec5\u58eb',
    '\u6b63\u5728\u751f\u6210\u82f1\u5f0f\u8bd1\u6587\uff0c\u5e26\u70b9\u8d35\u65cf\u8303\u513f',
    '\u82f1\u5f0f\u7ffb\u8bd1\u542f\u52a8\uff0cBrilliant!',
    '\u6b63\u5728\u82f1\u5f0f\u5316\u5904\u7406\u4e2d',
    '\u82f1\u5f0f\u8bd1\u6587\u70f9\u996a\u4e2d\uff0c\u52a0\u70b9\u7ea2\u8336\u548c\u85b0\u8863\u8349',
    '\u53ec\u5524\u82f1\u5f0f\u82f1\u8bed\uff0c\u5e26\u7740\u96fe\u90fd\u7684\u97f5\u5473',
    '\u6b63\u5728\u751f\u6210\u82f1\u5f0f\u8bd1\u6587\uff0c\u8154\u8c03\u62ff\u634f\u4e86',
    '\u82f1\u5f0f\u7ffb\u8bd1\u4e2d\uff0c\u611f\u53d7\u7ec5\u58eb\u7684\u4f18\u96c5',
    '\u6b63\u5728\u7528\u4f26\u6566\u8154\u8c03\u7ffb\u8bd1',
  ],
} as const;

const getTranslationDisplayMessage = (type: 'american' | 'british') => {
  const messages = TRANSLATING_MESSAGES[type];
  return messages[Math.floor(Math.random() * messages.length)];
};

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
    setInputText,
    setVersion,
    setEnglishType,
    setLoading,
    setLoadingStep,
    setTranslatedText,
    setEditableText,
    clear,
  } = useTranslationStore();

  const { showProgress, hideProgress, updateProgress } = useGlobalProgressStore();
  const [copyNotification, setCopyNotification] = useState<string | null>(null);
  const [showFormatted, setShowFormatted] = useState<boolean>(true);
  const [isStreamingTranslation, setIsStreamingTranslation] = useState<boolean>(false);
  const [isWaitingForTranslationContent, setIsWaitingForTranslationContent] =
    useState<boolean>(false);
  const notificationTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const formattedResultRef = useRef<HTMLDivElement>(null);

  const { conversations, toggleExpanded, setCurrentPage } = useAIChatStore();
  const containerRef = useRef<HTMLDivElement>(null);
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

  useEffect(() => {
    if (!isStreamingTranslation || !formattedResultRef.current) {
      return;
    }

    formattedResultRef.current.scrollTop = formattedResultRef.current.scrollHeight;
  }, [editableText, isStreamingTranslation]);

  const showTimedNotification = (message: string) => {
    if (notificationTimerRef.current) {
      clearTimeout(notificationTimerRef.current);
    }

    setCopyNotification(message);
    notificationTimerRef.current = setTimeout(() => {
      setCopyNotification(null);
    }, 2000);
  };

  const handleTranslation = async () => {
    if (!inputText.trim()) {
      alert(INPUT_EMPTY_ALERT);
      return;
    }

    const progressMessage =
      englishType === 'us' ? TRANSLATING_PROGRESS_US : TRANSLATING_PROGRESS_UK;
    const displayMessage =
      englishType === 'us'
        ? getTranslationDisplayMessage('american')
        : getTranslationDisplayMessage('british');
    showProgress(progressMessage, 'translation');
    setIsStreamingTranslation(true);
    setIsWaitingForTranslationContent(true);
    setLoading(true);
    setLoadingStep('translating');
    setTranslatedText(displayMessage);
    setEditableText(displayMessage);

    try {
      let hasReceivedContent = false;
      let finalText = '';

      for await (const chunk of apiClient.translateStream({
        text: inputText,
        operation: englishType === 'us' ? 'translate_us' : 'translate_uk',
        version,
      })) {
        if (chunk.type === 'error') {
          throw new Error(chunk.error || TRANSLATION_FAILED_DEFAULT);
        }

        if (chunk.full_text) {
          hasReceivedContent = true;
          setIsWaitingForTranslationContent(false);
          finalText = chunk.full_text;
          setTranslatedText(chunk.full_text);
          setEditableText(chunk.full_text);
          continue;
        }

        if (chunk.type === 'chunk' && chunk.text) {
          hasReceivedContent = true;
          setIsWaitingForTranslationContent(false);
          finalText = `${finalText}${chunk.text}`;
          setTranslatedText(finalText);
          setEditableText(finalText);
          continue;
        }

        if (chunk.type === 'complete') {
          hasReceivedContent = true;
          setIsWaitingForTranslationContent(false);
          finalText = chunk.text || chunk.full_text || finalText;
          setTranslatedText(finalText);
          setEditableText(finalText);
        }
      }

      if (!hasReceivedContent) {
        throw new Error(TRANSLATION_EMPTY_RESULT);
      }

      updateProgress(TRANSLATION_DONE_PROGRESS);

      try {
        apiClient.getCurrentUser().then(updateUserInfo);
      } catch (error) {
        console.warn(REFRESH_USER_FAILED, error);
      }
    } catch (error) {
      let errorMessage = TRANSLATION_FAILED_DEFAULT;
      if (error instanceof Error) {
        errorMessage = error.message;
      }

      setTranslatedText('');
      setEditableText('');
      setIsWaitingForTranslationContent(false);
      updateProgress(`\u7ffb\u8bd1\u5931\u8d25: ${errorMessage}`);
      alert(errorMessage);
    } finally {
      setIsStreamingTranslation(false);
      setIsWaitingForTranslationContent(false);
      setLoading(false);
      setLoadingStep(null);
      setTimeout(() => {
        hideProgress();
      }, 1200);
    }
  };

  const handleClear = () => {
    setIsStreamingTranslation(false);
    setIsWaitingForTranslationContent(false);
    clear();
  };

  const handleCopyInput = () => {
    if (!inputText) {
      return;
    }

    try {
      navigator.clipboard.writeText(inputText);
      showTimedNotification(COPY_INPUT_SUCCESS);
    } catch (error) {
      console.error(COPY_FAILED, error);
      showTimedNotification(COPY_FAILED);
    }
  };

  const handleCopyResult = () => {
    if (!translatedText) {
      return;
    }

    try {
      const cleanedText = cleanTextFromMarkdown(translatedText);
      navigator.clipboard.writeText(cleanedText);
      showTimedNotification(COPY_RESULT_SUCCESS);
    } catch (error) {
      console.error(COPY_FAILED, error);
      showTimedNotification(COPY_FAILED);
    }
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
  const resultTitle = `${englishType === 'us' ? US_LABEL : UK_LABEL}${'\u7ffb\u8bd1\u7ed3\u679c'}`;
  const formatToggleText = showFormatted ? TO_EDIT_MODE_LABEL : TO_PREVIEW_MODE_LABEL;
  const aiToggleTitle = conversation.isExpanded ? HIDE_AI_TITLE : SHOW_AI_TITLE;

  return (
    <div className={styles.translationContainer} ref={containerRef}>
      {copyNotification && <div className={styles.copyNotification}>{copyNotification}</div>}
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
                  <div className={styles.versionSection}>
                    <div className={styles.selectionGroup}>
                      <div className={styles.selectionItem}>
                        <div className={styles.selectionLabel}>
                          <button className={styles.versionHelp} title={VERSION_HELP_TITLE}>
                            !
                          </button>
                          <span>{VERSION_LABEL}</span>
                        </div>
                        <div className={styles.selectionButtons}>
                          <Button
                            variant={version === 'professional' ? 'primary' : 'ghost'}
                            size="small"
                            onClick={() => setVersion('professional')}
                            disabled={loading}
                          >
                            {PROFESSIONAL_LABEL}
                          </Button>
                          <Button
                            variant={version === 'basic' ? 'primary' : 'ghost'}
                            size="small"
                            onClick={() => setVersion('basic')}
                            disabled={loading}
                          >
                            {BASIC_LABEL}
                          </Button>
                        </div>
                      </div>
                      <div className={styles.selectionItem}>
                        <div className={styles.selectionLabel}>
                          <span>{ENGLISH_TYPE_LABEL}</span>
                        </div>
                        <div className={styles.selectionButtons}>
                          <Button
                            variant={englishType === 'us' ? 'primary' : 'ghost'}
                            size="small"
                            onClick={() => setEnglishType('us')}
                            disabled={loading}
                          >
                            {US_LABEL}
                          </Button>
                          <Button
                            variant={englishType === 'uk' ? 'primary' : 'ghost'}
                            size="small"
                            onClick={() => setEnglishType('uk')}
                            disabled={loading}
                          >
                            {UK_LABEL}
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
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
                    rows={25}
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
                        onClick={handleTranslation}
                        loading={loading && loadingStep === 'translating'}
                        disabled={loading}
                      >
                        {START_TRANSLATION_LABEL}
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

              {translatedText && (
                <Card variant="ghost" padding="medium" className={styles.resultCard}>
                  <div className={styles.resultHeader}>
                    <div className={styles.resultTitleRow}>
                      <h3 className={styles.resultTitle}>{resultTitle}</h3>
                      <div className={styles.resultActions}>
                        <div className={styles.formatToggleContainer}>
                          <span className={styles.formatToggleLabel}>{formatToggleText}</span>
                          <button
                            className={styles.formatToggle}
                            onClick={() => setShowFormatted(!showFormatted)}
                            title={formatToggleText}
                            data-state={showFormatted ? 'off' : 'on'}
                            aria-label={formatToggleText}
                          />
                        </div>
                        <Button variant="ghost" size="small" onClick={handleCopyResult}>
                          {COPY_RESULT_LABEL}
                        </Button>
                      </div>
                    </div>
                  </div>
                  {showFormatted ? (
                    <div className={styles.formattedResult} ref={formattedResultRef}>
                      {isStreamingTranslation && isWaitingForTranslationContent ? (
                        <div className={styles.loadingPlaceholder}>
                          <span>{editableText}</span>
                          <div className={styles.waveDots}>
                            <div className={styles.waveDot} />
                            <div className={styles.waveDot} />
                            <div className={styles.waveDot} />
                          </div>
                        </div>
                      ) : (
                        <div
                          className={styles.formattedResultContent}
                          dangerouslySetInnerHTML={{
                            __html: renderMarkdownAsHtml(editableText),
                          }}
                        />
                      )}
                    </div>
                  ) : (
                    <Textarea
                      value={editableText}
                      onChange={(e) => setEditableText(e.target.value)}
                      placeholder={RESULT_PLACEHOLDER}
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
