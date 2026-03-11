import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';
import { useModificationStore } from '../store/useModificationStore';
import { useGlobalProgressStore } from '../store/useGlobalProgressStore';
import { useAIChatStore } from '../store/useAIChatStore';
import { apiClient } from '../api/client';
import { cleanTextFromMarkdown } from '../utils/textCleaner';
import Card from '../components/ui/Card/Card';
import Textarea from '../components/ui/Textarea/Textarea';
import Button from '../components/ui/Button/Button';
import { useToast } from '../components/ui/Toast';
import DirectiveSelector from '../components/DirectiveSelector';
import GlobalProgressBar from '../components/GlobalProgressBar/GlobalProgressBar';
import AIChatPanel from '../components/AIChatPanel/AIChatPanel';
import styles from './TextModification.module.css';

const INPUT_TITLE = '\u8f93\u5165\u5f85\u4fee\u6539\u6587\u672c';
const INPUT_PLACEHOLDER = '\u8bf7\u8f93\u5165\u5f85\u4fee\u6539\u7684\u6587\u672c...';
const SHOW_AI_TITLE = '\u663e\u793a Otium \u52a9\u624b';
const HIDE_AI_TITLE = '\u9690\u85cf Otium \u52a9\u624b';
const CLEAR_LABEL = '\u6e05\u7a7a\u5168\u6587';
const COPY_FULL_TEXT_LABEL = '\u590d\u5236\u5168\u6587';
const APPLY_MODIFICATIONS_LABEL = '\u5e94\u7528\u4fee\u6539';
const COPY_RESULT_LABEL = '\u590d\u5236\u7ed3\u679c';
const OPTIONS_TITLE = '\u4fee\u6539\u9009\u9879';
const SHOW_ANNOTATIONS_LABEL = '\u663e\u793a\u6279\u6ce8';
const RESULT_TITLE = '\u4fee\u6539\u7ed3\u679c';
const SELECTED_DIRECTIVES_PREFIX = '\u5df2\u9009\u6307\u4ee4';
const ANNOTATION_DETECTED_TITLE = '\u68c0\u6d4b\u5230\u5c40\u90e8\u6279\u6ce8';
const ANNOTATION_DETECTED_TEXT =
  '\u68c0\u6d4b\u5230\u6587\u672c\u4e2d\u5305\u542b\u3010\u3011\u6216 [] \u683c\u5f0f\u7684\u5c40\u90e8\u6279\u6ce8\u6307\u4ee4\u3002';
const CAT_HINT_TEXT =
  '\u5728\u8be5\u5de5\u5177\u7528\u4e8e\u4fee\u6539\u6216\u5199\u4f5c\u4e2a\u4eba\u9648\u8ff0\u65f6\uff0c\u5efa\u8bae\u7684\u6587\u672c\u4fee\u6539\u987a\u5e8f\uff1a';
const CAT_HINT_STEP_1 =
  '1. \u53bb AI \u8bcd\u6c47\uff1a\u66ff\u6362 AI \u5199\u4f5c\u5e38\u7528\u77ed\u8bed\u548c\u8bcd\u6c47';
const CAT_HINT_STEP_2 =
  '2. \u53bb AI \u4e09\u677f\u65a7\uff1a\u4fee\u6539 AI \u5199\u4f5c\u5e38\u7528\u7684\u8bed\u6cd5\u548c\u7b26\u53f7\u4e60\u60ef';
const CAT_HINT_STEP_3 =
  '3. \u4eba\u6027\u5316\u5904\u7406\uff1a\u5c06\u8fc7\u4e8e\u5b66\u672f\u5316\u7684\u8868\u8fbe\u53e3\u8bed\u5316';
const INPUT_EMPTY_ERROR = '\u8bf7\u5148\u8f93\u5165\u6587\u672c\u3002';
const DIRECTIVE_EMPTY_ERROR =
  '\u8bf7\u81f3\u5c11\u9009\u62e9\u4e00\u4e2a\u4fee\u6539\u6307\u4ee4\uff0c\u6216\u5728\u6587\u672c\u4e2d\u6dfb\u52a0\u3010\u3011\u6216 [] \u683c\u5f0f\u7684\u5c40\u90e8\u6279\u6ce8\u3002';
const RUNNING_PROGRESS = '\u6b63\u5728\u5e94\u7528\u4fee\u6539\u6307\u4ee4';
const COMPLETE_PROGRESS = '\u667a\u80fd\u6587\u672c\u4fee\u6539\u5df2\u5b8c\u6210\u3002';
const EMPTY_RESULT_ERROR = '\u4fee\u6539\u672a\u8fd4\u56de\u53ef\u663e\u793a\u5185\u5bb9\u3002';
const DEFAULT_ERROR =
  '\u6587\u672c\u4fee\u6539\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\u3002';
const COPY_INPUT_SUCCESS = '\u8f93\u5165\u6587\u672c\u5df2\u590d\u5236\u3002';
const COPY_RESULT_SUCCESS = '\u4fee\u6539\u7ed3\u679c\u5df2\u590d\u5236\u3002';
const COPY_FAILED = '\u590d\u5236\u5931\u8d25\u3002';

const MODIFYING_MESSAGES = [
  '\u6b63\u5728\u5e94\u7528\u4fee\u6539\u6307\u4ee4\u6539\u6539\u6539',
  '\u4fee\u6539\u4e2d\uff0c\u9a6c\u4e0a\u7115\u7136\u4e00\u65b0',
  '\u6b63\u5728\u65bd\u5c55\u4fee\u6539\u9b54\u6cd5\u2728',
  '\u5e94\u7528\u4fee\u6539\u6307\u4ee4\u4e2d\uff0c\u8bf7\u7a0d\u5019',
  '\u6b63\u5728\u7ed9\u6587\u672c\u505a\u4e2aSPA',
  '\u4fee\u6539\u8fdb\u884c\u4e2d\uff0c\u53d8\u8eab\uff01',
  '\u6b63\u5728\u4f18\u5316\u6587\u672c\uff0c\u7cbe\u76ca\u6c42\u7cbe',
  '\u4fee\u6539\u6307\u4ee4\u6267\u884c\u4e2d',
  '\u6b63\u5728\u6253\u78e8\u6587\u672c\uff0c\u8ffd\u6c42\u5b8c\u7f8e',
  '\u5e94\u7528\u4fee\u6539\u4e2d\uff0c\u89c1\u8bc1\u5947\u8ff9',
  '\u6b63\u5728\u6539\u9020\u6587\u672c\uff0c\u8131\u80ce\u6362\u9aa8',
  '\u4fee\u6539\u4e2d\uff0c\u8ba9\u6587\u5b57\u66f4\u7f8e\u4e3d',
  '\u6b63\u5728\u5e94\u7528\u4fee\u6539\uff0c\u5316\u8150\u673d\u4e3a\u795e\u5947',
  '\u4fee\u6539\u6307\u4ee4\u542f\u52a8\uff0c\u6539\u5934\u6362\u9762',
  '\u6b63\u5728\u7cbe\u4fee\u6587\u672c\uff0c\u5320\u5fc3\u72ec\u8fd0',
  '\u5e94\u7528\u4fee\u6539\u4e2d\uff0c\u6587\u672c\u5347\u7ea7ing',
  '\u6b63\u5728\u8c03\u6559\u6587\u672c\uff0c\u7cbe\u96d5\u7ec6\u7422',
  '\u4fee\u6539\u8fdb\u884c\u4e2d\uff0c\u5b8c\u7f8e\u4e3b\u4e49\u53d1\u4f5c',
  '\u6b63\u5728\u5e94\u7528\u4fee\u6539\u6307\u4ee4\uff0c\u624b\u827a\u4eba\u4e0a\u7ebf',
  '\u4fee\u6539\u4e2d\uff0c\u7ed9\u6587\u5b57\u6765\u4e2a\u5927\u53d8\u6837',
  '\u6b63\u5728\u4f18\u5316\u4e2d\uff0c\u8ffd\u6c42\u6781\u81f4',
  '\u5e94\u7528\u4fee\u6539\u6307\u4ee4\uff0c\u6587\u672c\u6539\u9020\u8ba1\u5212\u542f\u52a8',
  '\u4fee\u6539\u4e2d\uff0c\u672cAI\u7684\u5f3a\u8feb\u75c7\u53c8\u72af\u4e86',
  '\u6b63\u5728\u5e94\u7528\u4fee\u6539\uff0c\u8ba9\u6587\u5b57\u66f4\u6709\u7075\u9b42',
  '\u4fee\u6539\u6307\u4ee4\u6267\u884c\u4e2d\uff0c\u7cbe\u76ca\u6c42\u7cbe\u4e0d\u505c\u6b47',
] as const;

const getModifyingDisplayMessage = () =>
  MODIFYING_MESSAGES[Math.floor(Math.random() * MODIFYING_MESSAGES.length)];

const containsAnnotations = (text: string): boolean => /【.*?】|\[.*?\]/.test(text);

const renderAnnotatedText = (text: string) => {
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

const TextModification: React.FC = () => {
  const navigate = useNavigate();
  const { userInfo } = useAuthStore();
  const toast = useToast();
  const {
    inputText,
    loading,
    selectedDirectives,
    modifiedText,
    showAnnotations,
    streaming,
    setInputText,
    setLoading,
    setSelectedDirectives,
    setModifiedText,
    setShowAnnotations,
    setStreaming,
    resetStreamState,
    clear,
  } = useModificationStore();
  const { showProgress, hideProgress, updateProgress } = useGlobalProgressStore();
  const { conversations, toggleExpanded, setCurrentPage } = useAIChatStore();

  const [copyNotification, setCopyNotification] = useState<string | null>(null);
  const [isWaitingForModifiedContent, setIsWaitingForModifiedContent] = useState<boolean>(false);
  const notificationTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const resultRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const pageKey = 'global';

  useEffect(() => {
    setCurrentPage(pageKey);
  }, [setCurrentPage]);

  useEffect(() => {
    if (!userInfo) {
      navigate('/login');
    }
  }, [userInfo, navigate]);

  useEffect(() => {
    return () => {
      if (notificationTimerRef.current) {
        clearTimeout(notificationTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!streaming || !resultRef.current) {
      return;
    }

    resultRef.current.scrollTop = resultRef.current.scrollHeight;
  }, [modifiedText, streaming]);

  const showNotification = (message: string) => {
    if (notificationTimerRef.current) {
      clearTimeout(notificationTimerRef.current);
    }

    setCopyNotification(message);
    notificationTimerRef.current = setTimeout(() => {
      setCopyNotification(null);
    }, 2000);
  };

  const handleApplyModifications = async () => {
    if (!inputText.trim()) {
      toast.error(INPUT_EMPTY_ERROR);
      return;
    }

    if (selectedDirectives.length === 0 && !containsAnnotations(inputText)) {
      toast.error(DIRECTIVE_EMPTY_ERROR);
      return;
    }

    showProgress(RUNNING_PROGRESS, 'modification');
    resetStreamState();
    setLoading(true);
    setStreaming(true);
    setIsWaitingForModifiedContent(true);
    setModifiedText(getModifyingDisplayMessage());

    try {
      let hasReceivedContent = false;
      let finalText = '';

      for await (const chunk of apiClient.refineStream({
        text: inputText,
        directives: selectedDirectives,
      })) {
        if (chunk.type === 'error') {
          throw new Error(chunk.error || DEFAULT_ERROR);
        }

        if (chunk.full_text) {
          hasReceivedContent = true;
          setIsWaitingForModifiedContent(false);
          finalText = chunk.full_text;
          setModifiedText(chunk.full_text);
          continue;
        }

        if (chunk.type === 'chunk' && chunk.text) {
          hasReceivedContent = true;
          setIsWaitingForModifiedContent(false);
          finalText = `${finalText}${chunk.text}`;
          setModifiedText(finalText);
          continue;
        }

        if (chunk.type === 'complete') {
          hasReceivedContent = true;
          setIsWaitingForModifiedContent(false);
          finalText = chunk.text || chunk.full_text || finalText;
          setModifiedText(finalText);
        }
      }

      if (!hasReceivedContent) {
        throw new Error(EMPTY_RESULT_ERROR);
      }

      updateProgress(COMPLETE_PROGRESS);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : DEFAULT_ERROR;
      setIsWaitingForModifiedContent(false);
      setModifiedText('');
      updateProgress(`\u667a\u80fd\u6587\u672c\u4fee\u6539\u5931\u8d25: ${errorMessage}`);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
      setStreaming(false);
      setIsWaitingForModifiedContent(false);
      setTimeout(() => {
        hideProgress();
      }, 1200);
    }
  };

  const handleClear = () => {
    setIsWaitingForModifiedContent(false);
    clear();
  };

  const handleCopyInput = () => {
    if (!inputText) {
      return;
    }

    navigator.clipboard.writeText(inputText).then(
      () => showNotification(COPY_INPUT_SUCCESS),
      (error) => {
        console.error(COPY_FAILED, error);
        showNotification(COPY_FAILED);
      }
    );
  };

  const handleCopyResult = () => {
    if (!modifiedText) {
      return;
    }

    const cleanedText = cleanTextFromMarkdown(modifiedText);
    navigator.clipboard.writeText(cleanedText).then(
      () => showNotification(COPY_RESULT_SUCCESS),
      (error) => {
        console.error(COPY_FAILED, error);
        showNotification(COPY_FAILED);
      }
    );
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
  const directivesTitle =
    selectedDirectives.length > 0
      ? `${SELECTED_DIRECTIVES_PREFIX} (${selectedDirectives.length})`
      : containsAnnotations(inputText)
        ? ANNOTATION_DETECTED_TITLE
        : '';

  return (
    <div className={styles.modificationContainer} ref={containerRef}>
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
                    maxLength={5000}
                    className={styles.inputTextarea}
                  />
                </div>

                <div className={styles.inputFooter}>
                  <div className={styles.buttonRow}>
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
                    <strong>{CAT_HINT_TEXT}</strong>
                    <br />
                    {CAT_HINT_STEP_1}
                    <br />
                    {CAT_HINT_STEP_2}
                    <br />
                    {CAT_HINT_STEP_3}
                  </div>
                </div>
              )}

              <DirectiveSelector
                selectedDirectives={selectedDirectives}
                onDirectivesChange={setSelectedDirectives}
                disabled={loading}
              />

              {(selectedDirectives.length > 0 || containsAnnotations(inputText)) && (
                <Card variant="ghost" padding="medium" className={styles.optionsCard}>
                  <div className={styles.optionsHeader}>
                    <h3 className={styles.optionsTitle}>{OPTIONS_TITLE}</h3>
                    <div className={styles.annotationsToggle}>
                      <label className={styles.toggleLabel}>
                        <input
                          type="checkbox"
                          checked={showAnnotations}
                          onChange={(e) => setShowAnnotations(e.target.checked)}
                        />
                        <span>{SHOW_ANNOTATIONS_LABEL}</span>
                      </label>
                    </div>
                  </div>
                  <div className={styles.selectedDirectives}>
                    <div className={styles.directivesHeader}>
                      <h4 className={styles.directivesTitle}>{directivesTitle}</h4>
                      <Button
                        variant="primary"
                        size="small"
                        onClick={handleApplyModifications}
                        disabled={loading || streaming || !inputText.trim()}
                      >
                        {APPLY_MODIFICATIONS_LABEL}
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
                        <p>{ANNOTATION_DETECTED_TEXT}</p>
                      </div>
                    )}
                  </div>
                </Card>
              )}

              {(streaming || modifiedText) && (
                <Card variant="ghost" padding="medium" className={styles.resultCard}>
                  <div className={styles.resultHeader}>
                    <h3 className={styles.resultTitle}>{RESULT_TITLE}</h3>
                    {!streaming && (
                      <Button variant="ghost" size="small" onClick={handleCopyResult}>
                        {COPY_RESULT_LABEL}
                      </Button>
                    )}
                  </div>
                  <div className={styles.resultContent} ref={resultRef}>
                    {streaming && isWaitingForModifiedContent ? (
                      <div className={styles.loadingPlaceholder}>
                        <span>{modifiedText}</span>
                        <div className={styles.waveDots}>
                          <div className={styles.waveDot} />
                          <div className={styles.waveDot} />
                          <div className={styles.waveDot} />
                        </div>
                      </div>
                    ) : showAnnotations && !streaming ? (
                      <div className={styles.annotatedText}>
                        {renderAnnotatedText(modifiedText)}
                      </div>
                    ) : (
                      <div className={styles.plainText}>{modifiedText}</div>
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

export default TextModification;
