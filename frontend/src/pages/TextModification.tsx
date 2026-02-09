import React, { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/useAuthStore'
import { useModificationStore } from '../store/useModificationStore'
import { useAIChatStore } from '../store/useAIChatStore'
import { apiClient } from '../api/client'
import { cleanTextFromMarkdown } from '../utils/textCleaner'
import Card from '../components/ui/Card/Card'
import Textarea from '../components/ui/Textarea/Textarea'
import Button from '../components/ui/Button/Button'
import { useToast } from '../components/ui/Toast'
import DirectiveSelector from '../components/DirectiveSelector'
import AIChatPanel from '../components/AIChatPanel/AIChatPanel'
import styles from './TextModification.module.css'

const TextModification: React.FC = () => {
  const navigate = useNavigate()
  const { userInfo } = useAuthStore()

  const {
    inputText,
    loading,
    selectedDirectives,
    modifiedText,
    showAnnotations,
    setInputText,
    setLoading,
    setSelectedDirectives,
    setModifiedText,
    setShowAnnotations,
    clear
  } = useModificationStore()

  const toast = useToast()

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

  useEffect(() => {
    if (!userInfo) {
      navigate('/login')
    }
  }, [userInfo, navigate])

  const handleApplyModifications = async () => {
    if (!inputText.trim()) {
      toast.error('请先输入文本')
      return
    }

    // 允许执行的条件：选择了指令 或 文本包含批注
    if (selectedDirectives.length === 0 && !containsAnnotations(inputText)) {
      toast.error('请至少选择一个修改指令或在文本中添加【】或[]格式的局部批注')
      return
    }

    setLoading(true)
    try {
      // 调用API应用选定的指令进行文本修改
      const response = await apiClient.refineText({
        text: inputText,
        directives: selectedDirectives
      })

      if (response.success) {
        setModifiedText(response.text)
        toast.success('文本修改完成！')
      }
    } catch (error) {
      let errorMessage = '文本修改失败，请稍后重试'
      if (error instanceof Error) {
        errorMessage = error.message
      } else if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as any
        errorMessage = axiosError.response?.data?.detail || errorMessage
      }
      toast.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => {
    clear()
  }

  const handleCopyInput = () => {
    if (inputText) {
      navigator.clipboard.writeText(inputText)
      toast.success('已复制输入文本到剪贴板')
    }
  }

  const handleCopyResult = () => {
    if (modifiedText) {
      // 清理markdown符号后复制
      const cleanedText = cleanTextFromMarkdown(modifiedText)
      navigator.clipboard.writeText(cleanedText)
      toast.success('已复制修改结果到剪贴板')
    }
  }

  // 检测文本是否包含【】或[]批注
  const containsAnnotations = (text: string): boolean => {
    return /【.*?】|\[.*?\]/.test(text)
  }

  const renderAnnotatedText = (text: string) => {
    // 处理**text**格式的粗体标记（如果后端未清理）
    let highlightedText = text.replace(
      /\*\*(.*?)\*\*/g,
      '<mark style="background-color: var(--color-black); color: var(--color-white); padding: 2px 4px; border-radius: 4px;">$1</mark>'
    )
    // 处理<b>text</b>格式的HTML粗体标签（后端已清理markdown）
    highlightedText = highlightedText.replace(
      /<b>(.*?)<\/b>/g,
      '<mark style="background-color: var(--color-black); color: var(--color-white); padding: 2px 4px; border-radius: 4px;">$1</mark>'
    )
    // 保持<i>text</i>斜体标签不变
    return { __html: highlightedText }
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

  return (
    <div className={styles.modificationContainer} ref={containerRef}>
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
                  <h2 className={styles.cardTitle}>输入待修改文本</h2>
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
                    placeholder="请输入待修改的文本..."
                    rows={16}
                    resize="vertical"
                    fullWidth
                    maxLength={2000}
                  />
                  {/* 字符计数显示已移除 */}
                </div>

                <div className={styles.inputFooter}>
                  <div className={styles.buttonRow}>
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
              </Card>

              {/* 指令选择器 */}
              <DirectiveSelector
                selectedDirectives={selectedDirectives}
                onDirectivesChange={setSelectedDirectives}
                disabled={loading}
              />

              {/* 修改选项 */}
              {(selectedDirectives.length > 0 || containsAnnotations(inputText)) && (
                <Card variant="ghost" padding="medium" className={styles.optionsCard}>
                  <div className={styles.optionsHeader}>
                    <h3 className={styles.optionsTitle}>修改选项</h3>
                    <div className={styles.annotationsToggle}>
                      <label className={styles.toggleLabel}>
                        <input
                          type="checkbox"
                          checked={showAnnotations}
                          onChange={(e) => setShowAnnotations(e.target.checked)}
                        />
                        <span>显示【】批注</span>
                      </label>
                    </div>
                  </div>
                  <div className={styles.selectedDirectives}>
                    <div className={styles.directivesHeader}>
                      <h4 className={styles.directivesTitle}>
                        {selectedDirectives.length > 0
                          ? `已选指令 (${selectedDirectives.length})`
                          : containsAnnotations(inputText)
                            ? "检测到局部批注"
                            : ""}
                      </h4>
                      <Button
                        variant="primary"
                        size="small"
                        onClick={handleApplyModifications}
                        loading={loading}
                        disabled={loading || !inputText.trim()}
                      >
                        应用修改
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
                        <p>检测到文本中包含【】或[]格式的局部批注指令</p>
                      </div>
                    )}
                  </div>
                </Card>
              )}

              {/* 修改结果展示 */}
              {modifiedText && (
                <Card variant="ghost" padding="medium" className={styles.resultCard}>
                  <div className={styles.resultHeader}>
                    <h3 className={styles.resultTitle}>修改结果</h3>
                    <Button
                      variant="ghost"
                      size="small"
                      onClick={handleCopyResult}
                    >
                      复制结果
                    </Button>
                  </div>
                  <div className={styles.resultContent}>
                    {showAnnotations ? (
                      <div
                        className={styles.annotatedText}
                        dangerouslySetInnerHTML={renderAnnotatedText(modifiedText)}
                      />
                    ) : (
                      <div className={styles.plainText}>
                        {modifiedText}
                      </div>
                    )}
                  </div>
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

export default TextModification