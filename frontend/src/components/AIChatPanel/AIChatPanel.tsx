import React, { useRef, useEffect, useState } from 'react';
import {
  useAIChatStore,
  type AIChatMessage as StoreAIChatMessage,
} from '../../store/useAIChatStore';
import { apiClient } from '../../api/client';
import type { AIChatMessage as ApiAIChatMessage } from '../../types';
import { BackgroundTaskStatus } from '../../types';
import Button from '../ui/Button/Button';
import Textarea from '../ui/Textarea/Textarea';
// import { Switch } from 'antd';
import styles from './AIChatPanel.module.css';

interface AIChatPanelProps {
  pageKey: string;
  className?: string;
}

const AIChatPanel: React.FC<AIChatPanelProps> = ({ pageKey, className = '' }) => {
  const {
    conversations,
    toggleExpanded,
    addMessage,
    setInputText,
    setLoading,
    literatureResearchMode,
    toggleLiteratureResearchMode,
    generateLiteratureReview,
    toggleGenerateLiteratureReview,
  } = useAIChatStore();

  const [processingStep, setProcessingStep] = useState<number>(0);
  const [manusSteps, setManusSteps] = useState<string[]>([]);
  const [currentManusStep, setCurrentManusStep] = useState<number>(0);
  // 进度相关状态已移除，根据简化需求只保留基本轮询机制
  const [pollingAbortController, setPollingAbortController] = useState<AbortController | null>(
    null
  );

  const conversation = conversations[pageKey] || {
    isExpanded: false,
    messages: [],
    inputText: '',
    loading: false,
    sessionId: null,
    splitPosition: 30,
  };

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // 从localStorage获取最新的文献调研结果（暂时未使用）
  // const getLatestLiteratureResearch = (): string => {
  //   try {
  //     const storageKey = 'literature-research-storage';
  //     const stored = localStorage.getItem(storageKey);
  //     if (!stored) {
  //       return '';
  //     }
  //     const data = JSON.parse(stored);
  //     // 获取resultText字段
  //     const resultText = data?.state?.resultText || '';
  //     return resultText;
  //   } catch (error) {
  //     console.error('获取文献调研结果失败:', error);
  //     return '';
  //   }
  // };

  // 滚动到底部
  const scrollToBottom = () => {
    // 使用requestAnimationFrame确保在浏览器重绘后执行
    requestAnimationFrame(() => {
      if (messagesContainerRef.current) {
        // 使用scrollTop确保滚动到底部
        messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
      } else {
        // 备用方案
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }
    });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation.messages]);

  // AI完成响应后滚动到底部
  useEffect(() => {
    // 当loading从true变为false时滚动（AI响应完成）
    if (!conversation.loading && conversation.messages.length > 0) {
      // 稍微延迟确保DOM更新
      const timer = setTimeout(() => {
        scrollToBottom();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [conversation.loading, conversation.messages.length]);

  // AI处理步骤文本 - 根据文献调研模式动态调整
  // 文献调研模式：简化显示，只有等待信息
  // 普通模式：保持原有处理步骤
  const processingSteps = literatureResearchMode
    ? ['文献调研可能需要较长时间，请耐心等待...'] // 简化版本，只有一个步骤
    : ['正在处理您的请求...'];

  // 处理AI思考状态的步骤显示
  useEffect(() => {
    let stepInterval: NodeJS.Timeout | null = null;

    if (conversation.loading) {
      // 启动步骤轮换
      setProcessingStep(0);
      stepInterval = setInterval(() => {
        setProcessingStep((prev) => (prev + 1) % processingSteps.length);
      }, 2000); // 每2秒切换到下一步骤
    } else {
      // 停止轮换，重置步骤
      setProcessingStep(0);
    }

    return () => {
      if (stepInterval) {
        clearInterval(stepInterval);
      }
    };
  }, [conversation.loading, processingSteps.length]);

  // 处理Manus步骤进度显示
  useEffect(() => {
    let stepInterval: NodeJS.Timeout | null = null;

    if (conversation.loading && manusSteps.length > 0) {
      // 文献调研模式下显示Manus步骤进度
      stepInterval = setInterval(() => {
        setCurrentManusStep((prev) => {
          // 如果已经是最后一个步骤，重置到第一个步骤（循环显示）
          if (prev >= manusSteps.length) {
            return 1;
          }
          return prev + 1;
        });
      }, 5000); // 每5秒切换到下一步骤
    } else {
      // 停止轮换，重置步骤
      if (currentManusStep > 0) {
        setCurrentManusStep(0);
      }
    }

    return () => {
      if (stepInterval) {
        clearInterval(stepInterval);
      }
    };
  }, [conversation.loading, manusSteps.length, currentManusStep]);

  // 清理后台任务轮询
  useEffect(() => {
    return () => {
      if (pollingAbortController) {
        pollingAbortController.abort();
        setPollingAbortController(null);
      }
    };
  }, [pollingAbortController]);

  // 清理markdown符号但保留必要格式 - 统一处理所有模式
  const cleanMarkdown = (html: string): string => {
    // 辅助函数：计算字符串的视觉长度（将制表符视为4个空格）
    const visualLength = (str: string): number => {
      let length = 0;
      for (let i = 0; i < str.length; i++) {
        if (str[i] === '\t') {
          // 制表符：移动到下一个制表位（假设制表符大小为4）
          length += 4 - (length % 4);
        } else {
          length++;
        }
      }
      return length;
    };

    // 辅助函数：将制表符转换为空格（用于对齐）
    const convertTabsToSpaces = (str: string): string => {
      let result = '';
      let column = 0;
      for (let i = 0; i < str.length; i++) {
        if (str[i] === '\t') {
          const spacesNeeded = 4 - (column % 4);
          result += ' '.repeat(spacesNeeded);
          column += spacesNeeded;
        } else {
          result += str[i];
          column++;
        }
      }
      return result;
    };

    // 先转换markdown格式为HTML
    let cleaned = html;

    // 第一步：处理代码块（```language\ncode\n```）
    // 使用占位符保存代码块，避免内部内容被其他规则处理
    const codeBlockPlaceholders: string[] = [];
    cleaned = cleaned.replace(/```(\w*)\n([\s\S]*?)```/g, (match, language, code) => {
      // 清理代码前后的空白
      const cleanedCode = code.trim();
      // 为语言添加CSS类
      const langClass = language ? ` language-${language}` : '';
      // 创建占位符
      const placeholder = `___CODE_BLOCK_${codeBlockPlaceholders.length}___`;
      // 保存最终HTML
      codeBlockPlaceholders.push(
        `<pre><code class="ai-code-block${langClass}">${cleanedCode}</code></pre>`
      );
      return placeholder;
    });

    // 第二步：处理markdown表格
    cleaned = cleaned.replace(
      /\n(\|[^\n]+\|\s*\n)(\|[-\s:|]+\|.*\|\s*\n)((?:\|[^\n]+\|\s*\n)+)/g,
      (match, headerLine, separatorLine, dataLines) => {
        try {
          // 解析表头行 - 移除首尾的|，然后按|分割
          const headerCells = headerLine
            .trim()
            .slice(1, -1)
            .split('|')
            .map((cell: string) => cell.trim());

          // 解析数据行
          const rowLines = dataLines
            .trim()
            .split('\n')
            .filter((line: string) => line.trim() !== '');
          const rows = rowLines.map((line: string) =>
            line
              .trim()
              .slice(1, -1)
              .split('|')
              .map((cell: string) => cell.trim())
          );

          // 构建HTML表格
          let tableHtml = '<div class="ai-table-container"><table class="ai-table"><thead><tr>';
          headerCells.forEach((cell: string) => {
            tableHtml += `<th>${cell}</th>`;
          });
          tableHtml += '</tr></thead><tbody>';
          rows.forEach((row: string[]) => {
            tableHtml += '<tr>';
            row.forEach((cell: string) => {
              tableHtml += `<td>${cell}</td>`;
            });
            tableHtml += '</tr>';
          });
          tableHtml += '</tbody></table></div>';
          return tableHtml;
        } catch (error) {
          console.warn('Markdown表格转换失败:', error);
          return match; // 转换失败时返回原内容
        }
      }
    );

    // 第三步：转换粗体 **文本** 为 <strong>文本</strong>
    cleaned = cleaned.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // 第四步：转换斜体 *文本* 为 <em>文本</em>
    // 匹配 *文本* 但不在数字中间（如 1*2），前后有空格或标点符号
    cleaned = cleaned.replace(
      /(^|[^\w*])\*(?![\s*])([^*\n]+?)(?<![\s*])\*($|[^\w*])/g,
      '$1<em>$2</em>$3'
    );

    // 第五步：处理标题
    cleaned = cleaned.replace(/^###\s+(.+)$/gm, '<h3>$1</h3>');
    cleaned = cleaned.replace(/^##\s+(.+)$/gm, '<h2>$1</h2>');
    cleaned = cleaned.replace(/^#\s+(.+)$/gm, '<h1>$1</h1>');

    // 保留行首的markdown符号（列表和标题），因为项目符号或编号列表是允许的
    // 注意：这里不再去除行首的 "* ", "- ", "1. ", "# " 等符号

    // 第六步：处理链接：[文本](链接)
    cleaned = cleaned.replace(
      /\[([^\]]+?)\]\(([^)]+?)\)/g,
      '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
    );

    // 第七步：处理内联代码：`代码`
    cleaned = cleaned.replace(/`([^`\n]+?)`/g, '<code>$1</code>');

    // 第八步：处理markdown列表（不生成HTML列表结构，直接处理每一行）
    // 用户要求：不采用有序列表编号形式，直接保留原始文本格式
    const linesForList = cleaned.split('\n');
    const processedLines: string[] = [];

    for (let i = 0; i < linesForList.length; i++) {
      let line = linesForList[i];

      // 检查是否是列表项
      // 无序列表：*、-、+开头，后面跟空格 - 转换为•符号
      // 有序列表：数字.或)开头，如1.、2.、1)、2)等 - 保持原样
      const unorderedMatch = line.match(/^(\s*)([*\-+])\s+(.*)$/);
      const orderedMatch = line.match(/^(\s*)(\d+[.)])\s+(.*)$/);

      if (unorderedMatch || orderedMatch) {
        const match = unorderedMatch || orderedMatch;
        if (!match) continue;

        const [, indent, marker, content] = match;

        // 收集多行列表项内容
        let itemContent = content;
        let j = i + 1;
        while (j < linesForList.length) {
          const nextLine = linesForList[j];
          // 检查下一行是否是同一列表项的延续（以空格开头，但不是新的列表项）
          if (nextLine.match(/^\s+\S/) && !nextLine.match(/^\s*([*\-+]|\d+[.)])\s+/)) {
            // 第一行文本起始位置在 indent + marker + ' ' 之后
            const markerLength = marker.length;
            const firstLineTextStart = visualLength(indent) + markerLength + 1; // 从0开始的视觉位置

            // 计算第二行的前导空格数（视觉长度）
            const leadingSpacesMatch = nextLine.match(/^(\s*)/);
            const nextLineIndentStr = leadingSpacesMatch ? leadingSpacesMatch[1] : '';

            // 获取第二行文本内容（去除前导空格）
            const nextLineText = nextLine.substring(nextLineIndentStr.length);

            // 悬挂缩进：第二行必须对齐到第一行文本开始位置
            // 强制对齐到第一行文本起始位置，忽略第二行原有的缩进
            const targetIndent = firstLineTextStart;

            // 基础缩进已经提供了 visualLength(indent) 的缩进
            // 需要额外添加的缩进量
            const additionalSpacesNeeded = targetIndent - visualLength(indent);

            // 构建对齐的行：使用转换后的缩进（制表符转空格）确保精确对齐
            const baseIndentSpaces = convertTabsToSpaces(indent);
            const alignedLine =
              baseIndentSpaces + ' '.repeat(additionalSpacesNeeded) + nextLineText;
            itemContent += '\n' + alignedLine;
            j++;
            i++; // 跳过已处理的行
          } else {
            break;
          }
        }

        // 对于无序列表，将符号替换为•
        if (unorderedMatch) {
          // 保持缩进，替换符号为•，统一使用空格缩进
          const baseIndentSpaces = convertTabsToSpaces(indent);
          line = baseIndentSpaces + '• ' + itemContent;
        } else {
          // 有序列表保持原样，统一使用空格缩进
          const baseIndentSpaces = convertTabsToSpaces(indent);
          line = baseIndentSpaces + marker + ' ' + itemContent;
        }
      }

      processedLines.push(line);
    }

    // 重新组合行
    cleaned = processedLines.join('\n');

    // 第九步：为现有的HTML表格添加样式（如果AI直接返回了HTML表格）
    cleaned = cleaned.replace(
      /<table>/g,
      '<div class="ai-table-container"><table class="ai-table">'
    );
    cleaned = cleaned.replace(/<\/table>/g, '</table></div>');

    // 第十步：处理换行符
    // 先分割成行，然后处理
    const lines = cleaned.split('\n');
    const processedLinesForNewlines: string[] = [];
    let previousWasEmpty = false;

    for (let index = 0; index < lines.length; index++) {
      const line = lines[index];
      const isCodeBlock = line.startsWith('___CODE_BLOCK_') && line.endsWith('___');

      if (isCodeBlock) {
        // 代码块占位符，直接添加
        processedLinesForNewlines.push(line);
        previousWasEmpty = false;
      } else if (line.trim() === '') {
        // 空行：如果是第一个空行且不是最后一行，添加换行符\n
        if (!previousWasEmpty && index < lines.length - 1) {
          processedLinesForNewlines.push('');
          previousWasEmpty = true;
        }
        // 如果是连续空行，跳过不添加额外的换行符
      } else {
        // 非空行，添加行内容
        processedLinesForNewlines.push(line);
        previousWasEmpty = false;
      }
    }

    // 用换行符连接，使用white-space: pre-wrap显示
    cleaned = processedLinesForNewlines.join('\n');

    // 第十一步：恢复代码块占位符
    codeBlockPlaceholders.forEach((html, index) => {
      const placeholder = `___CODE_BLOCK_${index}___`;
      cleaned = cleaned.replace(placeholder, html);
    });

    // 第十二步：规范化段落间距，确保不超过一个空行
    const linesForSpacing = cleaned.split('\n');
    const normalizedLines: string[] = [];
    let emptyLineCount = 0;

    for (const line of linesForSpacing) {
      if (line.trim() === '') {
        emptyLineCount++;
        if (emptyLineCount <= 1) {
          normalizedLines.push(line);
        }
        // 如果emptyLineCount > 1，跳过这个额外的空行
      } else {
        emptyLineCount = 0;
        normalizedLines.push(line);
      }
    }

    cleaned = normalizedLines.join('\n');

    // 第十三步：最终清理，确保不超过两个连续换行符（一个空行）
    cleaned = cleaned.replace(/\n{3,}/g, '\n\n');

    // 保留HTML标签，其它markdown符号已处理
    return cleaned;
  };

  const handleSendMessage = async () => {
    const text = conversation.inputText.trim();
    if (!text || conversation.loading) return;

    // 重置Manus步骤状态
    setManusSteps([]);
    setCurrentManusStep(0);
    // 进度相关状态已移除，不再需要重置

    // 如果之前有轮询，取消它
    if (pollingAbortController) {
      pollingAbortController.abort();
      setPollingAbortController(null);
    }

    // 添加用户消息
    const userMessage: StoreAIChatMessage = {
      role: 'user',
      content: text,
      timestamp: Date.now(),
    };
    addMessage(pageKey, userMessage);
    scrollToBottom();
    setInputText(pageKey, '');
    setLoading(pageKey, true);

    try {
      // 构建消息列表（转换为API格式），过滤掉空内容的消息
      const messages: ApiAIChatMessage[] = conversation.messages
        .map((msg) => ({
          role: msg.role,
          content: msg.content,
        }))
        .filter((msg) => msg.content && msg.content.trim().length > 0);

      // 添加当前用户消息（API格式）
      messages.push({
        role: userMessage.role,
        content: userMessage.content,
      });

      // 直接调用聊天API，由后端决定是否使用后台任务
      const response = await apiClient.chat({
        messages,
        session_id: conversation.sessionId || undefined,
        literature_research_mode: literatureResearchMode, // 传递文献调研模式状态
        generate_literature_review: generateLiteratureReview, // 传递生成文献综述选项
      });

      // 检查响应是否包含后台任务ID（表示任务已提交到后台处理）
      if (response.success && response.task_id) {
        // 这是后台任务响应，需要轮询任务状态
        // 使用非空断言，因为我们已经检查了response.task_id存在
        const taskId = response.task_id as number;

        // 创建AbortController用于取消轮询
        const abortController = new AbortController();
        setPollingAbortController(abortController);

        // 轮询任务结果
        try {
          const task = await apiClient.pollTaskResult(taskId, {
            interval: 1000, // 初始1秒间隔
            maxAttempts: 180, // 限制最大轮询次数，避免极端情况下长时间等待
            maxElapsedMs: 12 * 60 * 1000, // 最多轮询12分钟
            onProgress: (task) => {
              // 保留轮询机制但不更新进度信息（根据简化需求）
              // 只保留最基本的状态更新，确保轮询继续工作

              // 如果有步骤信息，更新Manus步骤（保留基本逻辑）
              if (task.result_data?.steps && Array.isArray(task.result_data.steps)) {
                setManusSteps(task.result_data.steps);
                // 设置当前步骤为最新
                if (task.result_data.steps.length > 0) {
                  setCurrentManusStep(task.result_data.steps.length);
                }
              }
            },
            signal: abortController.signal,
          });

          // 任务完成，处理结果
          if (task.status === BackgroundTaskStatus.COMPLETED && task.result_data) {
            const resultData = task.result_data;

            // 如果有Manus步骤信息，更新状态
            if (resultData.steps && resultData.steps.length > 0) {
              setManusSteps(resultData.steps);
              if (currentManusStep === 0 && resultData.steps.length > 0) {
                setCurrentManusStep(resultData.steps.length);
              }
            }

            // 添加AI回复
            const aiMessage: StoreAIChatMessage = {
              role: 'assistant',
              content: resultData.text || resultData.result || '任务完成',
              timestamp: Date.now(),
            };
            addMessage(pageKey, aiMessage);
          } else if (task.status === BackgroundTaskStatus.FAILED) {
            throw new Error(task.error_message || '任务处理失败');
          }
        } catch (pollingError: any) {
          if (pollingError.message === '轮询被取消') {
            console.log('轮询已取消');
            return;
          }
          throw pollingError;
        } finally {
          setPollingAbortController(null);
        }
      } else if (response.success) {
        // 这是同步响应，直接显示结果
        // 如果有Manus步骤信息，更新状态
        if (response.steps && response.steps.length > 0) {
          setManusSteps(response.steps);
          // 如果当前没有步骤进度，设置第一个步骤
          if (currentManusStep === 0 && response.steps.length > 0) {
            setCurrentManusStep(1);
          }
        }

        // 添加AI回复
        const aiMessage: StoreAIChatMessage = {
          role: 'assistant',
          content: response.text,
          timestamp: Date.now(),
        };
        addMessage(pageKey, aiMessage);
      } else {
        // 显示错误消息
        const errorMessage: StoreAIChatMessage = {
          role: 'assistant',
          content: `错误: ${response.error || '未知错误'}`,
          timestamp: Date.now(),
        };
        addMessage(pageKey, errorMessage);
      }
    } catch (error: any) {
      console.error('聊天请求失败:', error);
      const errorMessage: StoreAIChatMessage = {
        role: 'assistant',
        content: `请求失败: ${error.message || '网络错误'}`,
        timestamp: Date.now(),
      };
      addMessage(pageKey, errorMessage);
    } finally {
      setLoading(pageKey, false);
      // 重置Manus步骤状态
      setManusSteps([]);
      setCurrentManusStep(0);
      // 进度相关状态已移除，不再需要重置
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (!conversation.isExpanded) {
    return (
      <div className={`${styles.collapsedPanel} ${className}`}>
        <div className={styles.collapsedHeader}>
          <h3 className={styles.collapsedTitle}>Otium</h3>
          <Button
            variant="ghost"
            size="small"
            onClick={() => toggleExpanded(pageKey)}
            className={styles.expandButton}
          >
            展开
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={`${styles.panel} ${className}`} ref={containerRef}>
      {/* 面板头部 - 文献调研模式开关 */}
      <div className={styles.header}>
        <div className={styles.modeSwitch}>
          <span className={styles.modeLabel}>文献调研模式</span>
          <div
            onClick={() => toggleLiteratureResearchMode()}
            className={`${styles.appleSwitch} ${literatureResearchMode ? styles.appleSwitchActive : ''}`}
            title={literatureResearchMode ? '关闭文献调研模式' : '开启文献调研模式'}
            role="switch"
            aria-checked={literatureResearchMode}
          >
            <div className={styles.appleSwitchThumb}></div>
          </div>
        </div>
        {literatureResearchMode && (
          <div className={styles.literatureReviewOption}>
            <span className={styles.modeLabel}>生成文献综述</span>
            <div
              onClick={() => toggleGenerateLiteratureReview()}
              className={`${styles.appleSwitch} ${generateLiteratureReview ? styles.appleSwitchActive : ''}`}
              title={generateLiteratureReview ? '关闭生成文献综述' : '开启生成文献综述'}
              role="switch"
              aria-checked={generateLiteratureReview}
            >
              <div className={styles.appleSwitchThumb}></div>
            </div>
          </div>
        )}
      </div>

      {/* 消息列表 */}
      <div className={styles.messagesContainer} ref={messagesContainerRef}>
        {conversation.messages.length === 0 ? (
          <div className={styles.emptyState}>
            <h4 className={styles.emptyTitle}>我能为你做什么？</h4>
          </div>
        ) : (
          <div className={styles.messagesList}>
            {conversation.messages.map((message, index) => (
              <div
                key={index}
                className={`${styles.message} ${
                  message.role === 'user' ? styles.userMessage : styles.assistantMessage
                }`}
              >
                {message.role === 'assistant' && (
                  <div className={styles.messageHeader}>
                    <img src="/logopic.svg" alt="Otium" className={styles.messageIcon} />
                    <span className={styles.messageRole}>Otium</span>
                  </div>
                )}
                {message.role === 'assistant' ? (
                  <div
                    className={styles.messageContent}
                    dangerouslySetInnerHTML={{ __html: cleanMarkdown(message.content) }}
                  />
                ) : (
                  <div className={styles.messageContent}>{message.content}</div>
                )}
              </div>
            ))}
            {conversation.loading && (
              <div className={`${styles.message} ${styles.assistantMessage}`}>
                <div className={styles.messageHeader}>
                  <img src="/logopic.svg" alt="Otium" className={styles.messageIcon} />
                  <span className={styles.messageRole}>Otium</span>
                </div>
                <div className={styles.messageContent}>
                  {/* 统一使用普通对话的加载动画格式 */}
                  <div className={styles.processingStepsContainer}>
                    <div className={styles.processingStepContent}>
                      {processingSteps[processingStep]}
                    </div>
                    <div className={styles.typingIndicator}>
                      <span>.</span>
                      <span>.</span>
                      <span>.</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* 输入区域 */}
      <div className={styles.inputContainer}>
        <div className={styles.inputActions}>
          <div style={{ position: 'relative', width: '100%' }}>
            <Textarea
              value={conversation.inputText}
              onChange={(e) => setInputText(pageKey, e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                literatureResearchMode
                  ? '输入文献调研需求，如：主题、时间跨度、文献篇数等具体要求'
                  : '输入您的问题...'
              }
              rows={4}
              resize="vertical"
              disabled={conversation.loading}
              className={styles.textarea}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIChatPanel;
