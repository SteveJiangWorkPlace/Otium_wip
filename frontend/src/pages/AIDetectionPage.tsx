import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/useAuthStore'
import { useDetectionStore } from '../store/useDetectionStore'
import { Card, Textarea, Button } from '../components'
import AIDetection from '../components/AIDetection'
import { AIDetectionResponse } from '../types'
import styles from './AIDetectionPage.module.css'

const AIDetectionPage: React.FC = () => {
  const navigate = useNavigate()
  const { userInfo } = useAuthStore()

  const {
    inputText,
    detectionResult,
    shouldDetect,
    setInputText,
    setDetectionResult,
    setShouldDetect,
    clear
  } = useDetectionStore()

  useEffect(() => {
    if (!userInfo) {
      navigate('/login')
    }
  }, [userInfo, navigate])

  // 当输入文本变化时重置检测状态
  useEffect(() => {
    setShouldDetect(false)
    // 如果输入文本不为空且与保存结果的文本不匹配，清除保存的结果
    if (detectionResult && inputText.trim() && inputText.trim() !== detectionResult.full_text) {
      setDetectionResult(null)
    }
  }, [inputText, detectionResult, setShouldDetect, setDetectionResult])

  const handleClear = () => {
    clear()
  }

  const handleCopyInput = () => {
    if (inputText) {
      navigator.clipboard.writeText(inputText)
      alert('已复制输入文本到剪贴板')
    }
  }

  const handleDetectionComplete = (result: AIDetectionResponse) => {
    setDetectionResult(result)
  }

  return (
    <div className={styles.detectionContainer}>
      <div className={styles.content}>
        {/* 输入区域 */}
        <Card variant="elevated" padding="medium" className={styles.inputCard}>
          <div className={styles.inputHeader}>
            <h2 className={styles.cardTitle}>输入待检测文本</h2>
          </div>

          <div className={styles.textareaWrapper}>
            <Textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="请输入待检测的文本..."
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
                  onClick={() => {
                    if (!inputText.trim()) {
                      alert('请先输入文本')
                      return
                    }
                    setShouldDetect(true)
                  }}
                  disabled={!inputText.trim()}
                >
                  开始检测
                </Button>
              </div>
              <div className={styles.rightButtonGroup}>
                <Button
                  variant="ghost"
                  size="small"
                  onClick={handleClear}
                >
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
            text={inputText.trim() ? inputText : (detectionResult?.full_text || '')}
            onDetectionComplete={handleDetectionComplete}
            autoDetect={shouldDetect}
            result={detectionResult}
          />
        )}

      </div>
    </div>
  )
}

export default AIDetectionPage