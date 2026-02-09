import React, { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/useAuthStore'
import { useTranslationStore } from '../store/useTranslationStore'
import { useAIChatStore } from '../store/useAIChatStore'
import { apiClient } from '../api/client'
import { cleanTextFromMarkdown } from '../utils/textCleaner'
import Card from '../components/ui/Card/Card'
import Textarea from '../components/ui/Textarea/Textarea'
import Button from '../components/ui/Button/Button'
import AIChatPanel from '../components/AIChatPanel/AIChatPanel'
import styles from './TextTranslation.module.css'

const TextTranslation: React.FC = () => {
  const navigate = useNavigate()
  const { userInfo, updateUserInfo } = useAuthStore()

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
    clear
  } = useTranslationStore()

  // AI聊天状态
  const {
    conversations,
    toggleExpanded,
    setCurrentPage,
  } = useAIChatStore()
  const containerRef = useRef<HTMLDivElement>(null)
  const pageKey = 'global'

  // 初始化当前页面
  useEffect(() => {
    setCurrentPage(pageKey)
  }, [setCurrentPage])

  // 加载步骤对应的提示消息
  const loadingStepMessages = {
    translating: '正在翻译...请耐心等待，这可能需要几秒钟到一分钟时间',
  }

  useEffect(() => {
    if (!userInfo) {
      navigate('/login')
    }
  }, [userInfo, navigate])

  const handleTranslation = async () => {
    if (!inputText.trim()) {
      alert('请先输入文本')
      return
    }

    setLoading(true)
    setLoadingStep('translating')
    try {
      const response = await apiClient.checkText({
        text: inputText,
        operation: englishType === 'us' ? 'translate_us' : 'translate_uk',
        version: version
      })

      if (response.success) {
        setTranslatedText(response.text)
        setEditableText(response.text)
        alert(`${englishType === 'us' ? '美式' : '英式'}翻译完成！`)

        // 翻译成功后，获取最新的用户信息以更新剩余次数
        try {
          const updatedUserInfo = await apiClient.getCurrentUser()
          updateUserInfo(updatedUserInfo)
          console.log('用户信息已更新')
        } catch (error) {
          console.warn('获取更新后的用户信息失败:', error)
          // 不再需要处理剩余次数，现在只使用每日限制
        }
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
    clear()
  }

  const handleCopyInput = () => {
    if (inputText) {
      navigator.clipboard.writeText(inputText)
      alert('已复制输入文本到剪贴板')
    }
  }

  const handleCopyResult = () => {
    if (translatedText) {
      // 清理markdown符号后复制
      const cleanedText = cleanTextFromMarkdown(translatedText)
      navigator.clipboard.writeText(cleanedText)
      alert('已复制到剪贴板')
    }
  }


  const conversation = conversations[pageKey] || {
    isExpanded: false,
    messages: [],
    inputText: '',
    loading: false,
    sessionId: null,
    splitPosition: 70,
  }

  const workspaceWidth = conversation.isExpanded ? 72.5 : 100

  const handleEditText = (text: string) => {
    setEditableText(text)
  }

  return (
    <div className={styles.translationContainer} ref={containerRef}>
      <div className={styles.pageContainer}>
        {/* 工作区 */}
        <div
          className={styles.workspaceContainer}
          style={{ width: `${workspaceWidth}%` }}
        >
          <div className={styles.workspaceHeader}>
            {/* 标题已移除，AI按钮已移到输入区域 */}
          </div>

          <div className={styles.workspaceContent}>
            <div className={styles.content}>
              {/* 输入区域 */}
              <Card variant="ghost" padding="medium" className={styles.inputCard}>
                <div className={styles.inputHeader}>
                  <h2 className={styles.cardTitle}>输入中文文本</h2>
                  <div className={styles.versionSection}>
                    <div className={styles.selectionGroup}>
                      <div className={styles.selectionItem}>
                        <div className={styles.selectionLabel}>
                          <button
                            className={styles.versionHelp}
                            title="专业版：允许适当使用伴随状语从句以增强表达专业性&#13;&#10;基础版：严格避免使用AI句式以降低AI率"
                          >
                            !
                          </button>
                          <span>翻译版本</span>
                        </div>
                        <div className={styles.selectionButtons}>
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
                      </div>
                      <div className={styles.selectionItem}>
                        <div className={styles.selectionLabel}>
                          <span>英语体系</span>
                        </div>
                        <div className={styles.selectionButtons}>
                          <Button
                            variant={englishType === 'us' ? 'primary' : 'ghost'}
                            size="small"
                            onClick={() => setEnglishType('us')}
                            disabled={loading}
                          >
                            美式
                          </Button>
                          <Button
                            variant={englishType === 'uk' ? 'primary' : 'ghost'}
                            size="small"
                            onClick={() => setEnglishType('uk')}
                            disabled={loading}
                          >
                            英式
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div
                    className={styles.aiToggleButton}
                    onClick={() => toggleExpanded(pageKey)}
                    title={conversation.isExpanded ? '隐藏AI助手' : '显示AI助手'}
                  >
                    <img
                      src="/google-gemini.svg"
                      alt="AI助手"
                      className={styles.aiToggleIcon}
                    />
                  </div>
                </div>

                <div className={styles.textareaWrapper}>
                  <Textarea
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder="请输入中文文本..."
                    rows={16}
                    resize="vertical"
                    fullWidth
                    maxLength={5000}
                  />
                  {/* 字符计数已隐藏 */}
                  {/* <div className={styles.charCount}>
                    {inputText.length} / 5000
                  </div> */}
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
                        开始翻译
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

              {/* 翻译结果显示 */}
              {translatedText && (
                <Card variant="ghost" padding="medium" className={styles.resultCard}>
                  <div className={styles.resultHeader}>
                    <h3 className={styles.resultTitle}>
                      {englishType === 'us' ? '美式' : '英式'}翻译结果
                    </h3>
                    <Button
                      variant="ghost"
                      size="small"
                      onClick={handleCopyResult}
                    >
                      复制结果
                    </Button>
                  </div>
                  <Textarea
                    value={editableText}
                    onChange={(e) => handleEditText(e.target.value)}
                    placeholder="翻译结果..."
                    rows={16}
                    resize="vertical"
                    fullWidth
                    className={styles.resultTextarea}
                  />
                </Card>
              )}
            </div>
          </div>
        </div>

        {/* AI面板 */}
        {conversation.isExpanded && (
          <div className={styles.aiPanelContainer} style={{ width: '27.5%' }}>
            <AIChatPanel pageKey={pageKey} />
          </div>
        )}
      </div>
    </div>
  )
}

export default TextTranslation