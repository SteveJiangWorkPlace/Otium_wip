import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/useAuthStore'
import { apiClient } from '../api/client'
import { cleanTextFromMarkdown } from '../utils/textCleaner'
import { Card, Textarea, Button } from '../components'
import DirectiveSelector from '../components/DirectiveSelector'
import AIDetection from '../components/AIDetection'
import ResultDisplay from '../components/ResultDisplay'
import { AIDetectionResponse } from '../types'
import styles from './Home.module.css'

const Home: React.FC = () => {
  const navigate = useNavigate()
  const { userInfo } = useAuthStore()

  const [inputText, setInputText] = useState('')
  const [version, setVersion] = useState<'professional' | 'basic'>('professional')
  const [loading, setLoading] = useState(false)
  const [loadingStep, setLoadingStep] = useState<'translating' | 'ai_detecting' | 'refining' | 'error_checking' | null>(null)
  const [resultType, setResultType] = useState<'error_check' | 'translation' | null>(null)
  const [resultText, setResultText] = useState('')
  const [editableText, setEditableText] = useState('')
  const [selectedDirectives, setSelectedDirectives] = useState<string[]>([])
  const [refinedText, setRefinedText] = useState('')
  const [aiDetectionResult, setAiDetectionResult] = useState<AIDetectionResponse | null>(null)

  // 加载步骤对应的提示消息
  const loadingStepMessages = {
    translating: '正在翻译...请耐心等待，这可能需要几秒钟到一分钟时间',
    ai_detecting: '正在检测AI内容...正在分析文本特征，请稍候',
    refining: '正在执行翻译批注修改...正在根据指令优化文本，请稍候',
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
        operation: 'error_check',
        version: version
      })

      if (response.success) {
        setResultType('error_check')
        setResultText(response.text)
        setEditableText('')
        setRefinedText('')
        setAiDetectionResult(null)
        // 成功时不显示提醒
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

  const handleTranslation = async (type: 'us' | 'uk') => {
    if (!inputText.trim()) {
      alert('请先输入文本')
      return
    }

    setLoading(true)
    setLoadingStep('translating')
    try {
      const response = await apiClient.checkText({
        text: inputText,
        operation: type === 'us' ? 'translate_us' : 'translate_uk',
        version: version
      })

      if (response.success) {
        setResultType('translation')
        setResultText(response.text)
        setEditableText(response.text)
        setRefinedText('')
        setAiDetectionResult(null)
        // 成功时不显示提醒
      }
    } catch (error) {
      let errorMessage = '翻译失败，请稍后重试'
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
    setInputText('')
    setResultType(null)
    setResultText('')
    setEditableText('')
    setRefinedText('')
    setAiDetectionResult(null)
  }

  const handleCopyInput = () => {
    if (inputText) {
      navigator.clipboard.writeText(inputText)
      alert('已复制输入文本到剪贴板')
    }
  }

  const handleCopyResult = () => {
    if (resultText) {
      // 清理markdown符号后复制
      const cleanedText = cleanTextFromMarkdown(resultText)
      navigator.clipboard.writeText(cleanedText)
      alert('已复制到剪贴板')
    }
  }

  return (
    <div className={styles.homeContainer}>
      <div className={styles.content}>
        {/* 输入区域 */}
        <Card variant="elevated" padding="medium" className={styles.inputCard}>
          <div className={styles.inputHeader}>
            <h2 className={styles.cardTitle}>输入中文文本</h2>
            <div className={styles.versionSection}>
              <div className={styles.versionInfo}>
                <span className={styles.versionLabel}>请选择翻译版本</span>
                <div className={styles.versionButtons}>
                  <Button
                    variant={version === 'professional' ? 'primary' : 'ghost'}
                    size="small"
                    onClick={() => setVersion('professional')}
                    disabled={loading}
                  >
                    专业版
                  </Button>
                  <Button
                    variant={version === 'basic' ? 'primary' : 'ghost'}
                    size="small"
                    onClick={() => setVersion('basic')}
                    disabled={loading}
                  >
                    基础版
                  </Button>
                </div>
                <button
                  className={styles.versionHelp}
                  title="专业版：使用完整指令集进行深度优化\n基础版：使用基础指令进行快速处理"
                >
                  ?
                </button>
              </div>
            </div>
          </div>

          <div className={styles.textareaWrapper}>
            <Textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="请输入中文文本..."
              rows={8}
              resize="vertical"
              fullWidth
              maxLength={1000}
            />
            <div className={styles.charCount}>
              {inputText.length} / 1000
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
                <Button
                  variant="secondary"
                  size="small"
                  onClick={() => handleTranslation('us')}
                  loading={loading && loadingStep === 'translating'}
                  disabled={loading}
                >
                  美式翻译
                </Button>
                <Button
                  variant="secondary"
                  size="small"
                  onClick={() => handleTranslation('uk')}
                  loading={loading && loadingStep === 'translating'}
                  disabled={loading}
                >
                  英式翻译
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


        {/* 指令选择器 */}
        {resultType === 'translation' && (
          <DirectiveSelector
            selectedDirectives={selectedDirectives}
            onDirectivesChange={setSelectedDirectives}
            disabled={loading}
          />
        )}

        {/* AI检测 */}
        {resultType === 'translation' && (
          <AIDetection
            text={editableText}
            onDetectionComplete={setAiDetectionResult}
            disabled={loading}
          />
        )}

        {/* 结果显示 */}
        {resultType && (
          <ResultDisplay
            resultType={resultType}
            resultText={resultText}
            editableText={editableText}
            onEditableTextChange={setEditableText}
            refinedText={refinedText}
            aiDetectionResult={aiDetectionResult}
            selectedDirectives={selectedDirectives}
            onCopy={handleCopyResult}
          />
        )}
      </div>
    </div>
  )
}

export default Home