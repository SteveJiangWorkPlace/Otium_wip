import React from 'react'
import { Card, Button } from './ui'
import styles from './DirectiveSelector.module.css'

interface DirectiveSelectorProps {
  selectedDirectives: string[]
  onDirectivesChange: (directives: string[]) => void
  disabled?: boolean
}

const DIRECTIVES = [
  '主语修正',
  '句式修正',
  '符号修正',
  '丰富句式',
  '灵活表达',
  '去AI词汇',
]

const DIRECTIVE_INFO = {
  '主语修正': '修正主语结构以降低AI率',
  '句式修正': '修正特定句式以降低AI率',
  '符号修正': '确保引号规范使用',
  '丰富句式': '混合使用不同长度的句子',
  '灵活表达': '灵活使用标点和更自然的句子开头',
  '去AI词汇': '识别并替换AI高频词汇和短语',
}

const DirectiveSelector: React.FC<DirectiveSelectorProps> = ({
  selectedDirectives,
  onDirectivesChange,
  disabled = false,
}) => {
  const handleToggle = (directive: string) => {
    if (selectedDirectives.includes(directive)) {
      onDirectivesChange(selectedDirectives.filter((d) => d !== directive))
    } else {
      onDirectivesChange([...selectedDirectives, directive])
    }
  }

  const handleClearAll = () => {
    onDirectivesChange([])
  }

  const handleAIThreeAxes = () => {
    const threeAxes = ['主语修正', '句式修正', '符号修正']
    onDirectivesChange(threeAxes)
  }

  return (
    <Card variant="ghost" padding="medium" className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>文本修改指令选择</h3>
        <div className={styles.selectedCount}>
          已选择 {selectedDirectives.length} / {DIRECTIVES.length} 个指令
        </div>
      </div>

      <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', marginBottom: 'var(--spacing-3)', lineHeight: 'var(--line-height-relaxed)' }}>
        您可以使用【】在文本中添加局部批注进行精准修改，也可以选择以下快捷指令进行全文修改。快捷指令适用于整篇文本，初次修改建议仅选择"去AI三板斧"。如果AI率仍不达标，可尝试选择其他指令继续优化。
      </div>

      <div className={styles.actions}>
        <Button
          variant="ghost"
          size="small"
          onClick={handleAIThreeAxes}
          disabled={disabled}
        >
          去AI三板斧
        </Button>
        <Button
          variant="ghost"
          size="small"
          onClick={handleClearAll}
          disabled={disabled}
        >
          清空
        </Button>
      </div>

      <div className={styles.directivesGrid}>
        {DIRECTIVES.map((directive) => {
          const isSelected = selectedDirectives.includes(directive)
          return (
            <div
              key={directive}
              className={`${styles.directiveItem} ${isSelected ? styles.selected : ''}`}
              onClick={() => !disabled && handleToggle(directive)}
            >
              <div className={styles.directiveContent}>
                <div className={styles.directiveHeader}>
                  <span className={styles.directiveName}>{directive}</span>
                </div>
                <div className={styles.directiveInfo}>
                  {DIRECTIVE_INFO[directive as keyof typeof DIRECTIVE_INFO]}
                </div>
              </div>
            </div>
          )
        })}
      </div>

    </Card>
  )
}

export default DirectiveSelector