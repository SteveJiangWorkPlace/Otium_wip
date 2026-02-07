import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/useAuthStore'
import { useCorrectionStore } from '../store/useCorrectionStore'
import { apiClient } from '../api/client'
import { Card, Textarea, Button } from '../components'
import styles from './TextCorrection.module.css'

const TextCorrection: React.FC = () => {
  const navigate = useNavigate()
  const { userInfo } = useAuthStore()

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
    clear
  } = useCorrectionStore()

  // 加载步骤对应的提示消息
  const loadingStepMessages = {
    error_checking: '正在进行智能纠错...正在检查错别字、漏字和重复字，请稍候',
  }

  useEffect(() => {
    if (!userInfo) {
      navigate('/login')
    }
  }, [userInfo, navigate])

  const handleErrorCheck = async () => {
    if (!inputText.trim()) {
      alert('请先输入文本')
      return
    }

    setLoading(true)
    setLoadingStep('error_checking')
    try {
      const response = await apiClient.checkText({
        text: inputText,
        operation: 'error_check'
      })

      if (response.success) {
        setResultText(response.text)
        setEditableText(response.text)
        alert('智能纠错完成！')
      }
    } catch (error) {
      let errorMessage = '处理失败，请稍后重试'
      if (error instanceof Error) {
        errorMessage = error.message
      } else if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as any
        errorMessage = axiosError.response?.data?.detail || errorMessage
      }
      alert(errorMessage)
    } finally {
      setLoading(false)
      setLoadingStep(null)
    }
  }

  const handleClear = () => {
    clear()
  }

  const handleCopyInput = () => {
    if (inputText) {
      navigator.clipboard.writeText(inputText)
      alert('已复制输入文本到剪贴板')
    }
  }

  const handleCopyResult = () => {
    if (resultText) {
      navigator.clipboard.writeText(resultText)
      alert('已复制到剪贴板')
    }
  }

  const renderHighlightedText = (text: string) => {
    const highlightedText = text.replace(
      /\*\*(.*?)\*\*/g,
      '<mark style="background-color: var(--color-black); color: var(--color-white); font-weight: bold; padding: 2px 4px; border-radius: 4px;">$1</mark>'
    )
    return { __html: highlightedText }
  }

  return (
    <div className={styles.correctionContainer}>
      <div className={styles.content}>
        {/* 输入区域 */}
        <Card variant="elevated" padding="medium" className={styles.inputCard}>
          <div className={styles.inputHeader}>
            <h2 className={styles.cardTitle}>输入中文文本</h2>
          </div>

          <div className={styles.textareaWrapper}>
            <Textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="请输入中文文本..."
              rows={16}
              resize="vertical"
              fullWidth
              maxLength={2000}
            />
            <div className={styles.charCount}>
              {inputText.length} / 2000
            </div>
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
                <Button
                  variant="ghost"
                  size="small"
                  onClick={handleClear}
                  disabled={loading}
                >
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

          {loading && loadingStep && (
            <div className={styles.loadingMessage}>
              <div className={styles.loadingSpinner} />
              <span>{loadingStepMessages[loadingStep]}</span>
            </div>
          )}
        </Card>

        {/* 结果显示 */}
        {resultText && (
          <Card variant="elevated" padding="medium" className={styles.resultCard}>
            <div className={styles.resultHeader}>
              <h3 className={styles.resultTitle}>纠错结果</h3>
              <Button
                variant="ghost"
                size="small"
                onClick={handleCopyResult}
              >
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
  )
}

export default TextCorrection