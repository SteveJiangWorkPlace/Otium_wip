import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/useAuthStore'
import { useModificationStore } from '../store/useModificationStore'
import { apiClient } from '../api/client'
import { Card, Textarea, Button, useToast } from '../components'
import DirectiveSelector from '../components/DirectiveSelector'
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
      navigator.clipboard.writeText(modifiedText)
      toast.success('已复制修改结果到剪贴板')
    }
  }

  // 检测文本是否包含【】或[]批注
  const containsAnnotations = (text: string): boolean => {
    return /【.*?】|\[.*?\]/.test(text)
  }

  const renderAnnotatedText = (text: string) => {
    // 使用**标记高亮修改部分，参考智能纠错格式
    const highlightedText = text.replace(
      /\*\*(.*?)\*\*/g,
      '<mark style="background-color: var(--color-black); color: var(--color-white); padding: 2px 4px; border-radius: 4px;">$1</mark>'
    )
    return { __html: highlightedText }
  }

  return (
    <div className={styles.modificationContainer}>
      <div className={styles.content}>
        {/* 输入区域 */}
        <Card variant="elevated" padding="medium" className={styles.inputCard}>
          <div className={styles.inputHeader}>
            <h2 className={styles.cardTitle}>输入待修改文本</h2>
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
            <div className={styles.charCount}>
              {inputText.length} / 2000
            </div>
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
          <Card variant="elevated" padding="medium" className={styles.optionsCard}>
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
          <Card variant="elevated" padding="medium" className={styles.resultCard}>
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
  )
}

export default TextModification