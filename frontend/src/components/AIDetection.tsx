import React, { useState, useEffect, useRef, useCallback } from 'react'
import { Card, Button, Icon } from './ui'
import { AIDetectionResponse } from '../types'
import { apiClient } from '../api/client'
import { cleanTextFromMarkdown } from '../utils/textCleaner'
import styles from './AIDetection.module.css'

interface AIDetectionProps {
  text: string
  onDetectionComplete: (result: AIDetectionResponse) => void
  disabled?: boolean
  autoDetect?: boolean
  result?: AIDetectionResponse | null
  onCopyNotification?: (message: string) => void
}

const AIDetection: React.FC<AIDetectionProps> = ({
  text,
  onDetectionComplete,
  disabled = false,
  autoDetect = false,
  result: externalResult = null,
  onCopyNotification,
}) => {
  const [loading, setLoading] = useState(false)
  const [internalResult, setInternalResult] = useState<AIDetectionResponse | null>(null)
  const hasAutoDetected = useRef(false)

  // 使用外部传入的结果或内部结果
  const result = externalResult !== undefined ? externalResult : internalResult

  const handleDetect = useCallback(async () => {
    if (!text.trim()) {
      alert('请先输入文本')
      return
    }

    setLoading(true)
    try {
      const response = await apiClient.detectAI({ text })

      const result: AIDetectionResponse = {
        is_ai_generated: response.ai_score ? response.ai_score > 0.5 : false,
        confidence: response.ai_score ? Math.abs(response.ai_score - 0.5) * 2 : 0.5,
        details: '检测完成',
        ai_score: response.ai_score || 0,
        full_text: response.full_text || text,
        detailed_scores: response.detailed_scores || [],
      }

      setInternalResult(result)
      onDetectionComplete(result)
      // 成功时不显示提醒
    } catch (error) {
      console.error('AI检测失败:', error)
      let errorMessage = 'AI检测失败，请稍后重试'

      if (error instanceof Error) {
        errorMessage = error.message
      } else if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as any
        const responseData = axiosError.response?.data

        if (responseData) {
          // 尝试从统一错误格式提取消息
          if (typeof responseData.message === 'string' && responseData.message) {
            errorMessage = responseData.message
          } else if (typeof responseData.detail === 'string') {
            errorMessage = responseData.detail
          } else if (typeof responseData.detail === 'object' && responseData.detail?.message) {
            errorMessage = responseData.detail.message
          } else if (responseData.error) {
            errorMessage = responseData.error
          }
        }
      }

      alert(errorMessage)
    } finally {
      setLoading(false)
    }
  }, [text, onDetectionComplete])

  // 当文本变化时重置状态
  useEffect(() => {
    hasAutoDetected.current = false
  }, [text])

  // 当autoDetect从false变为true时触发检测
  const prevAutoDetect = useRef(autoDetect)
  useEffect(() => {
    if (autoDetect && !prevAutoDetect.current && text.trim() && !loading) {
      handleDetect()
    }
    prevAutoDetect.current = autoDetect
  }, [autoDetect, text, loading, handleDetect])

  const getHighlightedText = () => {
    if (!result?.full_text) return { __html: '' }

    let text = result.full_text

    if (result.detailed_scores && Array.isArray(result.detailed_scores)) {
      const highAISentences = result.detailed_scores
        .filter((s) => s.generated_prob * 100 >= 15)
        .sort((a, b) => b.generated_prob - a.generated_prob)
        .map((s) => s.sentence)

      highAISentences.forEach((sentence) => {
        const escaped = sentence.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
        text = text.replace(
          new RegExp(escaped, 'g'),
          `<mark style="background-color: var(--color-black); color: var(--color-white); padding: 2px 4px; border-radius: 4px;">${sentence}</mark>`
        )
      })
    }

    return { __html: text }
  }

  const handleCopyText = () => {
    if (!result?.full_text) return

    // 清理markdown符号后复制
    const cleanedText = cleanTextFromMarkdown(result.full_text)
    navigator.clipboard.writeText(cleanedText).then(
      () => {
        if (onCopyNotification) {
          onCopyNotification('已复制到剪贴板')
        } else {
          alert('已复制到剪贴板')
        }
      },
      () => {
        if (onCopyNotification) {
          onCopyNotification('复制失败，请手动复制')
        } else {
          alert('复制失败，请手动复制')
        }
      }
    )
  }

  // 如果没有检测结果，不显示任何内容
  if (!result) {
    return null
  }

  const aiScore = ((result.ai_score ?? 0) * 100).toFixed(1)
  const scoreNum = parseFloat(aiScore)
  const isHigh = scoreNum >= 20

  return (
    <Card variant="ghost" padding="medium" className={styles.container}>
      <div className={styles.scoreSection}>
            <div className={styles.scoreHeader}>
              <span className={styles.scoreLabel}>全文AI生成概率</span>
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
                  <span>检测到较高的AI生成概率，建议进行人工修改</span>
                </div>
              ) : (
                <div className={styles.successMessage}>
                  <Icon name="check" size="sm" variant="success" />
                  <span>AI生成概率较低，文本质量良好</span>
                </div>
              )}
            </div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)', marginTop: 'var(--spacing-2)', lineHeight: 'var(--line-height-relaxed)' }}>
              温馨提示：
              <br />1. 本检测结果基于ZeroGPT模型，仅供参考，如用于学术用途，建议将最终版本提交Turnitin进行权威检测。
              <br />2. 如果多次修改后AI率仍然较高，请确保提供的初始文本为非AI生成内容。
            </div>
          </div>

          <div className={styles.textSection}>
            <div className={styles.textHeader}>
              <h4 className={styles.textTitle}>检测结果分析</h4>
              <Button
                variant="ghost"
                size="small"
                onClick={handleCopyText}
              >
                复制文本
              </Button>
            </div>

            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)', marginBottom: 'var(--spacing-2)', lineHeight: 'var(--line-height-tight)' }}>
              提示：AI特征≥15%的单个句子已被高亮标出
            </div>
            <div
              className={styles.highlightedText}
              dangerouslySetInnerHTML={getHighlightedText()}
            />

            {result.detailed_scores && result.detailed_scores.length > 0 && (
              <div className={styles.detailedScores}>
                <h5 className={styles.scoresTitle}>详细句子分析</h5>
                <div className={styles.scoresList}>
                  {result.detailed_scores
                    .sort((a, b) => b.generated_prob - a.generated_prob)
                    .slice(0, 5)
                    .map((score, index) => (
                    <div key={index} className={styles.scoreItem}>
                      <div className={styles.sentenceScore}>
                        <span className={styles.sentenceText}>
                          {score.sentence.length > 50
                            ? score.sentence.substring(0, 50) + '...'
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
  )
}

export default AIDetection