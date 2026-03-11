import React, { useState, useEffect, useRef, useCallback } from 'react';
import { AIDetectionResponse } from '../types';
import { apiClient } from '../api/client';
import { cleanTextFromMarkdown, renderMarkdownAsHtml } from '../utils/textCleaner';
import Card from './ui/Card/Card';
import Button from './ui/Button/Button';
import Icon from './ui/Icon/Icon';
import styles from './AIDetection.module.css';

interface AIDetectionProps {
  text: string;
  onDetectionComplete: (result: AIDetectionResponse) => void;
  disabled?: boolean;
  autoDetect?: boolean;
  result?: AIDetectionResponse | null;
  onCopyNotification?: (message: string) => void;
}

const EMPTY_TEXT_ALERT = '\u8bf7\u5148\u8f93\u5165\u6587\u672c';
const DETECT_DONE = '\u68c0\u6d4b\u5b8c\u6210';
const DETECT_FAILED = 'AI \u68c0\u6d4b\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5';
const COPY_SUCCESS = '\u5df2\u590d\u5236\u5230\u526a\u8d34\u677f';
const COPY_FAILED = '\u590d\u5236\u5931\u8d25\uff0c\u8bf7\u624b\u52a8\u590d\u5236';
const SCORE_LABEL = '\u5168\u6587 AI \u751f\u6210\u6982\u7387';
const HIGH_SCORE_HINT =
  '\u68c0\u6d4b\u5230\u8f83\u9ad8\u7684 AI \u751f\u6210\u6982\u7387\uff0c\u5efa\u8bae\u8fdb\u884c\u4eba\u5de5\u4fee\u6539';
const LOW_SCORE_HINT =
  'AI \u751f\u6210\u6982\u7387\u8f83\u4f4e\uff0c\u6587\u672c\u8d28\u91cf\u826f\u597d';
const WARM_TIP = '\u6e29\u99a8\u63d0\u793a\uff1a';
const WARM_TIP_1 =
  '1. \u672c\u68c0\u6d4b\u7ed3\u679c\u57fa\u4e8e ZeroGPT \u6a21\u578b\uff0c\u4ec5\u4f9b\u53c2\u8003\uff0c\u5982\u7528\u4e8e\u5b66\u672f\u7528\u9014\uff0c\u5efa\u8bae\u5c06\u6700\u7ec8\u7248\u672c\u63d0\u4ea4 Turnitin \u8fdb\u884c\u6743\u5a01\u68c0\u6d4b\u3002';
const WARM_TIP_2 =
  '2. \u5982\u679c\u591a\u6b21\u4fee\u6539\u540e AI \u7387\u4ecd\u7136\u8f83\u9ad8\uff0c\u8bf7\u786e\u4fdd\u63d0\u4f9b\u7684\u521d\u59cb\u6587\u672c\u4e3a\u975e AI \u751f\u6210\u5185\u5bb9\u3002';
const ANALYSIS_TITLE = '\u68c0\u6d4b\u7ed3\u679c\u5206\u6790';
const COPY_TEXT_LABEL = '\u590d\u5236\u6587\u672c';
const HIGHLIGHT_HINT =
  '\u63d0\u793a\uff1aAI \u7279\u5f81\u226515%\u7684\u5355\u4e2a\u53e5\u5b50\u5df2\u88ab\u9ad8\u4eae\u6807\u51fa';
const DETAILED_TITLE = '\u8be6\u7ec6\u53e5\u5b50\u5206\u6790';

const AIDetection: React.FC<AIDetectionProps> = ({
  text,
  onDetectionComplete,
  disabled = false,
  autoDetect = false,
  result: externalResult = null,
  onCopyNotification,
}) => {
  const [loading, setLoading] = useState(false);
  const [internalResult, setInternalResult] = useState<AIDetectionResponse | null>(null);
  const hasAutoDetected = useRef(false);

  const result = externalResult !== undefined ? externalResult : internalResult;

  const handleDetect = useCallback(async () => {
    if (!text.trim()) {
      alert(EMPTY_TEXT_ALERT);
      return;
    }

    setLoading(true);
    try {
      const response = await apiClient.detectAI({ text });
      const nextResult: AIDetectionResponse = {
        is_ai_generated: response.ai_score ? response.ai_score > 0.5 : false,
        confidence: response.ai_score ? Math.abs(response.ai_score - 0.5) * 2 : 0.5,
        details: DETECT_DONE,
        ai_score: response.ai_score || 0,
        full_text: response.full_text || text,
        detailed_scores: response.detailed_scores || [],
      };

      setInternalResult(nextResult);
      onDetectionComplete(nextResult);
    } catch (error) {
      console.error('AI detection failed:', error);
      let errorMessage = DETECT_FAILED;

      if (error instanceof Error) {
        errorMessage = error.message;
      } else if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as any;
        const responseData = axiosError.response?.data;

        if (responseData) {
          if (typeof responseData.message === 'string' && responseData.message) {
            errorMessage = responseData.message;
          } else if (typeof responseData.detail === 'string') {
            errorMessage = responseData.detail;
          } else if (typeof responseData.detail === 'object' && responseData.detail?.message) {
            errorMessage = responseData.detail.message;
          } else if (responseData.error) {
            errorMessage = responseData.error;
          }
        }
      }

      alert(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [text, onDetectionComplete]);

  useEffect(() => {
    hasAutoDetected.current = false;
  }, [text]);

  const prevAutoDetect = useRef(autoDetect);
  useEffect(() => {
    if (autoDetect && !prevAutoDetect.current && text.trim() && !loading) {
      handleDetect();
    }
    prevAutoDetect.current = autoDetect;
  }, [autoDetect, text, loading, handleDetect]);

  const getHighlightedText = () => {
    if (!result?.full_text) {
      return { __html: '' };
    }

    let htmlText = renderMarkdownAsHtml(result.full_text);
    if (result.detailed_scores && Array.isArray(result.detailed_scores)) {
      const highAISentences = result.detailed_scores
        .filter((item) => item.generated_prob * 100 >= 15)
        .sort((a, b) => b.generated_prob - a.generated_prob)
        .map((item) => item.sentence);

      highAISentences.forEach((sentence) => {
        const htmlSentence = renderMarkdownAsHtml(sentence);
        const escaped = htmlSentence.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        htmlText = htmlText.replace(
          new RegExp(escaped, 'g'),
          `<mark style="background-color: var(--color-black); color: var(--color-white); padding: 2px 4px; border-radius: 4px;">${htmlSentence}</mark>`
        );
      });
    }

    return { __html: htmlText };
  };

  const handleCopyText = () => {
    if (!result?.full_text) {
      return;
    }

    const cleanedText = cleanTextFromMarkdown(result.full_text);
    navigator.clipboard.writeText(cleanedText).then(
      () => {
        if (onCopyNotification) {
          onCopyNotification(COPY_SUCCESS);
        } else {
          alert(COPY_SUCCESS);
        }
      },
      () => {
        if (onCopyNotification) {
          onCopyNotification(COPY_FAILED);
        } else {
          alert(COPY_FAILED);
        }
      }
    );
  };

  if (!result) {
    return null;
  }

  const aiScore = ((result.ai_score ?? 0) * 100).toFixed(1);
  const scoreNum = parseFloat(aiScore);
  const isHigh = scoreNum >= 20;

  return (
    <Card variant="ghost" padding="medium" className={styles.container}>
      <div className={styles.scoreSection}>
        <div className={styles.scoreHeader}>
          <span className={styles.scoreLabel}>{SCORE_LABEL}</span>
          <span className={`${styles.scoreValue} ${isHigh ? styles.highScore : ''}`}>
            {aiScore}%
          </span>
        </div>

        <div className={styles.progressBar}>
          <div
            className={`${styles.progressFill} ${isHigh ? styles.highProgress : ''}`}
            style={{ width: `${Math.min(scoreNum, 100)}%` }}
          />
        </div>

        <div className={styles.scoreDescription}>
          {isHigh ? (
            <div className={styles.warningMessage}>
              <Icon name="warning" size="sm" variant="warning" />
              <span>{HIGH_SCORE_HINT}</span>
            </div>
          ) : (
            <div className={styles.successMessage}>
              <Icon name="check" size="sm" variant="success" />
              <span>{LOW_SCORE_HINT}</span>
            </div>
          )}
        </div>

        <div
          style={{
            fontSize: 'var(--font-size-xs)',
            color: 'var(--color-text-secondary)',
            marginTop: 'var(--spacing-2)',
            lineHeight: 'var(--line-height-relaxed)',
          }}
        >
          {WARM_TIP}
          <br />
          {WARM_TIP_1}
          <br />
          {WARM_TIP_2}
        </div>
      </div>

      <div className={styles.textSection}>
        <div className={styles.textHeader}>
          <h4 className={styles.textTitle}>{ANALYSIS_TITLE}</h4>
          <Button
            variant="ghost"
            size="small"
            onClick={handleCopyText}
            disabled={disabled || loading}
          >
            {COPY_TEXT_LABEL}
          </Button>
        </div>

        <div
          style={{
            fontSize: 'var(--font-size-base)',
            color: 'var(--color-text-secondary)',
            marginBottom: 'var(--spacing-2)',
            lineHeight: 'var(--line-height-relaxed)',
          }}
        >
          {HIGHLIGHT_HINT}
        </div>
        <div className={styles.highlightedText} dangerouslySetInnerHTML={getHighlightedText()} />

        {result.detailed_scores && result.detailed_scores.length > 0 && (
          <div className={styles.detailedScores}>
            <h5 className={styles.scoresTitle}>{DETAILED_TITLE}</h5>
            <div className={styles.scoresList}>
              {result.detailed_scores
                .sort((a, b) => b.generated_prob - a.generated_prob)
                .slice(0, 5)
                .map((score, index) => (
                  <div key={index} className={styles.scoreItem}>
                    <div className={styles.sentenceScore}>
                      <span className={styles.sentenceText}>
                        {score.sentence.length > 50
                          ? `${score.sentence.substring(0, 50)}...`
                          : score.sentence}
                      </span>
                      <span className={styles.sentenceProbability}>
                        {(score.generated_prob * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className={styles.sentenceProgress}>
                      <div
                        className={styles.sentenceProgressFill}
                        style={{ width: `${Math.min(score.generated_prob * 100, 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

export default AIDetection;
