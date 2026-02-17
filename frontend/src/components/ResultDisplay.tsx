import React from 'react';
import { Card, Button, Icon, Textarea } from './ui';
import { AIDetectionResponse } from '../types';
import styles from './ResultDisplay.module.css';

interface ResultDisplayProps {
  resultType: 'error_check' | 'translation';
  resultText: string;
  editableText: string;
  onEditableTextChange: (text: string) => void;
  refinedText: string;
  aiDetectionResult: AIDetectionResponse | null;
  selectedDirectives: string[];
  onCopy?: () => void;
}

const ResultDisplay: React.FC<ResultDisplayProps> = ({
  resultType,
  resultText,
  editableText,
  onEditableTextChange,
  refinedText,
  aiDetectionResult,
  selectedDirectives,
  onCopy,
}) => {
  const getTitle = () => {
    switch (resultType) {
      case 'error_check':
        return '智能纠错结果';
      case 'translation':
        return '翻译结果';
      default:
        return '处理结果';
    }
  };

  const getHintText = () => {
    switch (resultType) {
      case 'error_check':
        return '已检查错别字、漏字和重复字，请查看修改建议';
      case 'translation':
        return '翻译完成，您可以编辑文本或应用修改指令';
      default:
        return '';
    }
  };

  const renderHighlightedText = (text: string) => {
    const highlightedText = text.replace(
      /\*\*(.*?)\*\*/g,
      '<mark style="background-color: var(--color-black); color: var(--color-white); padding: 2px 4px; border-radius: 4px;">$1</mark>'
    );
    return { __html: highlightedText };
  };

  const handleRefine = () => {
    // 这里应该调用API应用选定的指令进行文本优化
    alert('文本优化功能暂未实现');
  };

  return (
    <Card variant="elevated" padding="medium" className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>{getTitle()}</h3>
      </div>

      <div className={styles.hint}>
        <span>{getHintText()}</span>
      </div>

      {/* 原始结果展示 */}
      <div className={styles.resultSection}>
        <div className={styles.sectionHeader}>
          <h4 className={styles.sectionTitle}>原始结果</h4>
          {onCopy && (
            <div className={styles.sectionActions}>
              <Button variant="ghost" size="small" onClick={onCopy}>
                复制
              </Button>
            </div>
          )}
        </div>
        <div
          className={styles.highlightedText}
          dangerouslySetInnerHTML={renderHighlightedText(resultText)}
        />
      </div>

      {/* 可编辑区域（仅翻译结果） */}
      {resultType === 'translation' && (
        <div className={styles.editableSection}>
          <div className={styles.sectionHeader}>
            <h4 className={styles.sectionTitle}>可编辑文本</h4>
            <div className={styles.sectionActions}>
              <Button variant="ghost" size="small" onClick={() => onEditableTextChange(resultText)}>
                重置
              </Button>
            </div>
          </div>
          <Textarea
            value={editableText}
            onChange={(e) => onEditableTextChange(e.target.value)}
            rows={6}
            resize="vertical"
            fullWidth
            className={styles.editableTextarea}
          />
        </div>
      )}

      {/* 指令应用区域 */}
      {resultType === 'translation' && selectedDirectives.length > 0 && (
        <div className={styles.directivesSection}>
          <div className={styles.sectionHeader}>
            <h4 className={styles.sectionTitle}>应用修改指令</h4>
            <Button
              variant="primary"
              size="small"
              onClick={handleRefine}
              disabled={!editableText.trim()}
            >
              应用指令 ({selectedDirectives.length})
            </Button>
          </div>
          <div className={styles.directivesList}>
            {selectedDirectives.map((directive) => (
              <div key={directive} className={styles.directiveTag}>
                <Icon name="check" size="xs" variant="success" />
                <span>{directive}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 优化结果展示 */}
      {refinedText && (
        <div className={styles.refinedSection}>
          <h4 className={styles.sectionTitle}>优化结果</h4>
          <div className={styles.refinedText}>{refinedText}</div>
        </div>
      )}

      {/* AI检测结果 */}
      {aiDetectionResult && (
        <div className={styles.aiDetectionSection}>
          <h4 className={styles.sectionTitle}>AI检测结果</h4>
          <div className={styles.aiScore}>
            <span className={styles.aiScoreLabel}>AI生成概率：</span>
            <span className={styles.aiScoreValue}>
              {((aiDetectionResult.ai_score ?? 0) * 100).toFixed(1)}%
            </span>
          </div>
          {aiDetectionResult.detailed_scores && (
            <div className={styles.aiDetails}>
              <h5 className={styles.aiDetailsTitle}>高AI概率句子：</h5>
              <ul className={styles.aiSentences}>
                {aiDetectionResult.detailed_scores
                  .filter((s) => s.generated_prob * 100 >= 15)
                  .slice(0, 3)
                  .map((score, index) => (
                    <li key={index} className={styles.aiSentence}>
                      <Icon name="warning" size="xs" variant="warning" />
                      <span>{score.sentence}</span>
                    </li>
                  ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </Card>
  );
};

export default ResultDisplay;
