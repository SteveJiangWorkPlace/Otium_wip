import React, { useRef, useEffect, useState, useCallback } from 'react';
import {
  useAIChatStore,
  type AIChatMessage as StoreAIChatMessage,
} from '../../store/useAIChatStore';
import { useAuthStore } from '../../store/useAuthStore';
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

interface ManusDocumentLink {
  name?: string;
  url?: string;
  source?: string;
  type?: string;
}

const LITERATURE_RESEARCH_USER_WHITELIST = new Set(['admin', 'dog', 'cat']);
const THINKING_PLACEHOLDER = '正在思考…';

const AIChatPanel: React.FC<AIChatPanelProps> = ({ pageKey, className = '' }) => {
  const {
    conversations,
    toggleExpanded,
    addMessage,
    updateMessage,
    setInputText,
    setLoading,
    setActiveTaskId,
    clearConversation,
    literatureResearchMode,
    toggleLiteratureResearchMode,
    generateLiteratureReview,
    toggleGenerateLiteratureReview,
  } = useAIChatStore();
  const username = useAuthStore((state) => state.userInfo?.username ?? '');
  const canUseLiteratureResearch = LITERATURE_RESEARCH_USER_WHITELIST.has(username.toLowerCase());
  const isLiteratureResearchEnabled = canUseLiteratureResearch && literatureResearchMode;
  const isGenerateLiteratureReviewEnabled = canUseLiteratureResearch && generateLiteratureReview;
  const [manusSteps, setManusSteps] = useState<string[]>([]);
  const [currentManusStep, setCurrentManusStep] = useState<number>(0);
  // 进度相关状态已移除，根据简化需求只保留基本轮询机制
  const [pollingAbortController, setPollingAbortController] = useState<AbortController | null>(
    null
  );
  const [streamAbortController, setStreamAbortController] = useState<AbortController | null>(null);

  const conversation = conversations[pageKey] || {
    isExpanded: false,
    messages: [],
    inputText: '',
    loading: false,
    activeTaskId: null,
    sessionId: null,
    splitPosition: 30,
  };

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  const formatAssistantContentWithDocuments = useCallback(
    (text: string, documents?: ManusDocumentLink[]): string => {
      const baseText = (text || '').trim();
      const validDocuments = Array.isArray(documents)
        ? documents.filter((doc): doc is ManusDocumentLink & { url: string } =>
            Boolean(doc && typeof doc.url === 'string' && doc.url.trim().length > 0)
          )
        : [];

      const inferredDocuments: ManusDocumentLink[] = [];
      const docUrlRegex = /https?:\/\/[^\s<>)"\]]+/g;
      const markdownDocRegex = /\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g;
      const docExtRegex = /\.(pdf|doc|docx|ppt|pptx|xlsx|csv|txt|md|zip)(\?|$)/i;

      let markdownMatch: RegExpExecArray | null = null;
      while ((markdownMatch = markdownDocRegex.exec(baseText)) !== null) {
        const name = (markdownMatch[1] || '').trim();
        const url = (markdownMatch[2] || '').trim();
        if (docExtRegex.test(url)) {
          inferredDocuments.push({ name, url, source: 'text_markdown' });
        }
      }

      const plainUrls = baseText.match(docUrlRegex) || [];
      plainUrls.forEach((url) => {
        const cleanedUrl = url.replace(/[.,;:!?)"']+$/g, '');
        if (docExtRegex.test(cleanedUrl)) {
          inferredDocuments.push({ url: cleanedUrl, source: 'text_plain' });
        }
      });

      const mergedDocuments = [...validDocuments, ...inferredDocuments];
      const uniqueByUrl = new Map<string, ManusDocumentLink & { url: string }>();
      mergedDocuments.forEach((doc) => {
        if (!doc || typeof doc.url !== 'string') return;
        const normalizedUrl = doc.url.trim();
        if (!normalizedUrl) return;
        if (!uniqueByUrl.has(normalizedUrl)) {
          uniqueByUrl.set(normalizedUrl, { ...doc, url: normalizedUrl });
        }
      });
      const allDocuments = Array.from(uniqueByUrl.values());

      if (allDocuments.length === 0) {
        return baseText || '任务完成';
      }

      const documentLines = allDocuments.map((doc, index) => {
        const safeName = (doc.name || '').trim() || `文档 ${index + 1}`;
        return `- [${safeName}](${doc.url})`;
      });

      const documentsSection = `**可下载文档**\n${documentLines.join('\n')}`;
      return baseText ? `${baseText}\n\n${documentsSection}` : documentsSection;
    },
    []
  );

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
      if (streamAbortController) {
        streamAbortController.abort();
        setStreamAbortController(null);
      }
    };
  }, [pollingAbortController, streamAbortController]);

  const pollBackgroundTask = async (taskId: number, abortController: AbortController) => {
    return apiClient.pollTaskResult(taskId, {
      interval: 1000,
      maxAttempts: 180,
      maxElapsedMs: 12 * 60 * 1000,
      onProgress: (task) => {
        if (task.result_data?.steps && Array.isArray(task.result_data.steps)) {
          setManusSteps(task.result_data.steps);
          if (task.result_data.steps.length > 0) {
            setCurrentManusStep(task.result_data.steps.length);
          }
        }
      },
      signal: abortController.signal,
    });
  };

  const applyCompletedTaskResult = useCallback(
    (task: any) => {
      if (task.status === BackgroundTaskStatus.COMPLETED && task.result_data) {
        const resultData = task.result_data;

        if (resultData.steps && resultData.steps.length > 0) {
          setManusSteps(resultData.steps);
          if (currentManusStep === 0 && resultData.steps.length > 0) {
            setCurrentManusStep(resultData.steps.length);
          }
        }

        const aiMessage: StoreAIChatMessage = {
          role: 'assistant',
          content: formatAssistantContentWithDocuments(
            resultData.text || resultData.result || '',
            resultData.documents
          ),
          timestamp: Date.now(),
        };
        addMessage(pageKey, aiMessage);
        return;
      }

      if (task.status === BackgroundTaskStatus.COMPLETED) {
        throw new Error('任务已完成，但未返回可显示的结果内容');
      }

      if (task.status === BackgroundTaskStatus.FAILED) {
        throw new Error(task.error_message || '任务处理失败');
      }
    },
    [addMessage, currentManusStep, formatAssistantContentWithDocuments, pageKey]
  );

  // 续轮询：组件重新挂载后，自动接续未完成的文献调研任务
  useEffect(() => {
    if (!conversation.loading || !conversation.activeTaskId || pollingAbortController) {
      return;
    }

    const resumeAbortController = new AbortController();
    setPollingAbortController(resumeAbortController);

    (async () => {
      try {
        const task = await pollBackgroundTask(
          conversation.activeTaskId as number,
          resumeAbortController
        );
        applyCompletedTaskResult(task);
        setActiveTaskId(pageKey, null);
        setLoading(pageKey, false);
        setManusSteps([]);
        setCurrentManusStep(0);
      } catch (pollingError: any) {
        if (pollingError?.message === '轮询被取消') {
          return;
        }
        const errorMessage: StoreAIChatMessage = {
          role: 'assistant',
          content: `请求失败: ${pollingError?.message || '网络错误'}`,
          timestamp: Date.now(),
        };
        addMessage(pageKey, errorMessage);
        setActiveTaskId(pageKey, null);
        setLoading(pageKey, false);
        setManusSteps([]);
        setCurrentManusStep(0);
      } finally {
        setPollingAbortController(null);
      }
    })();
  }, [
    addMessage,
    applyCompletedTaskResult,
    conversation.activeTaskId,
    conversation.loading,
    currentManusStep,
    pageKey,
    pollingAbortController,
    setActiveTaskId,
    setLoading,
  ]);

  // 清理markdown符号但保留必要格式 - 统一处理所有模式
  const cleanMarkdown = (html: string): string => {
    const escapeHtml = (value: string): string =>
      value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');

    const sanitizeUrl = (url: string): string => {
      const trimmed = url.trim();
      if (trimmed.startsWith('/')) {
        return trimmed;
      }

      try {
        const parsed = new URL(trimmed);
        if (
          parsed.protocol === 'http:' ||
          parsed.protocol === 'https:' ||
          parsed.protocol === 'mailto:'
        ) {
          return parsed.toString();
        }
      } catch (error) {
        return '#';
      }

      return '#';
    };
    // 先转换markdown格式为HTML
    let cleaned = escapeHtml(html);

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
    cleaned = cleaned.replace(/\[([^\]]+?)\]\(([^)]+?)\)/g, (_match, label, url) => {
      const safeUrl = sanitizeUrl(url);
      return `<a href="${safeUrl}" target="_blank" rel="noopener noreferrer">${label}</a>`;
    });

    // 第七步：处理内联代码：`代码`
    cleaned = cleaned.replace(/`([^`\n]+?)`/g, '<code>$1</code>');

    // 第八步：处理 markdown 列表，转换为 HTML 列表以修正悬挂缩进
    const linesForList = cleaned.split('\n');
    const processedLines: string[] = [];
    const unorderedListPattern = /^\s*[*\-+]\s+(.*)$/;
    const orderedListPattern = /^\s*\d+[.)]\s+(.*)$/;
    const isListContinuationLine = (line: string): boolean =>
      /^\s+\S/.test(line) && !unorderedListPattern.test(line) && !orderedListPattern.test(line);

    for (let i = 0; i < linesForList.length; i++) {
      const line = linesForList[i];
      const unorderedMatch = line.match(unorderedListPattern);
      const orderedMatch = line.match(orderedListPattern);

      if (!unorderedMatch && !orderedMatch) {
        processedLines.push(line);
        continue;
      }

      const isOrderedList = Boolean(orderedMatch);
      const currentPattern = isOrderedList ? orderedListPattern : unorderedListPattern;
      const listItems: string[] = [];

      while (i < linesForList.length) {
        const currentLine = linesForList[i];
        const currentMatch = currentLine.match(currentPattern);
        if (!currentMatch) {
          break;
        }

        let itemContent = currentMatch[1].trim();
        i++;

        while (i < linesForList.length) {
          const nextLine = linesForList[i];
          if (nextLine.trim() === '') {
            i++;
            continue;
          }

          if (isListContinuationLine(nextLine)) {
            itemContent += `<br />${nextLine.trim()}`;
            i++;
            continue;
          }

          break;
        }

        listItems.push(`<li>${itemContent}</li>`);

        if (i >= linesForList.length) {
          break;
        }

        if (!linesForList[i].match(currentPattern)) {
          break;
        }
      }

      i--;
      processedLines.push(
        isOrderedList
          ? `<ol class="ai-list ai-ordered-list">${listItems.join('')}</ol>`
          : `<ul class="ai-list ai-unordered-list">${listItems.join('')}</ul>`
      );
    }

    cleaned = processedLines.join('\n');

    // 第九步：为现有的HTML表格添加样式（如果AI直接返回了HTML表格）
    cleaned = cleaned.replace(
      /<table>/g,
      '<div class="ai-table-container"><table class="ai-table">'
    );
    cleaned = cleaned.replace(/<\/table>/g, '</table></div>');

    // 第十步：处理换行符，压缩空行
    const lines = cleaned.split('\n');
    const processedLinesForNewlines: string[] = [];

    for (let index = 0; index < lines.length; index++) {
      const line = lines[index];
      const isCodeBlock = line.startsWith('___CODE_BLOCK_') && line.endsWith('___');

      if (isCodeBlock) {
        processedLinesForNewlines.push(line);
      } else if (line.trim() === '') {
        continue;
      } else {
        processedLinesForNewlines.push(line);
      }
    }

    cleaned = processedLinesForNewlines.join('\n');

    // 第十一步：恢复代码块占位符
    codeBlockPlaceholders.forEach((html, index) => {
      const placeholder = `___CODE_BLOCK_${index}___`;
      cleaned = cleaned.replace(placeholder, html);
    });

    // 第十二步：进一步压缩段落间距，不保留额外空行
    const linesForSpacing = cleaned.split('\n');
    const normalizedLines: string[] = [];

    for (const line of linesForSpacing) {
      if (line.trim() !== '') {
        normalizedLines.push(line);
      }
    }

    cleaned = normalizedLines.join('\n');

    // 第十三步：最终清理，最多保留单个换行
    cleaned = cleaned.replace(/\n{2,}/g, '\n');

    // 保留HTML标签，其它markdown符号已处理
    return cleaned;
  };

  const handleSendMessage = async () => {
    const text = conversation.inputText.trim();
    if (!text || conversation.loading) return;

    // 重置Manus步骤状态
    setManusSteps([]);
    setCurrentManusStep(0);

    // 如果之前有轮询，取消它
    if (pollingAbortController) {
      pollingAbortController.abort();
      setPollingAbortController(null);
      setActiveTaskId(pageKey, null);
    }
    if (streamAbortController) {
      streamAbortController.abort();
      setStreamAbortController(null);
    }

    // 添加用户消息
    const userMessage: StoreAIChatMessage = {
      role: 'user',
      content: text,
      timestamp: Date.now(),
    };
    const assistantMessageId = `assistant-${Date.now().toString(36)}-${Math.random()
      .toString(36)
      .slice(2, 10)}`;
    const assistantMessage: StoreAIChatMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: THINKING_PLACEHOLDER,
      timestamp: Date.now(),
    };
    addMessage(pageKey, userMessage);
    addMessage(pageKey, assistantMessage);
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

      const abortController = new AbortController();
      setStreamAbortController(abortController);
      let streamCompleted = false;

      for await (const chunk of apiClient.chatStream(
        {
          messages,
          session_id: conversation.sessionId || undefined,
          literature_research_mode: isLiteratureResearchEnabled, // 传递文献调研模式状态
          generate_literature_review: isGenerateLiteratureReviewEnabled, // 传递生成文献综述选项
        },
        { signal: abortController.signal }
      )) {
        if (chunk.type === 'step') {
          setManusSteps((prev) => {
            const nextSteps = chunk.steps && chunk.steps.length > 0 ? chunk.steps : prev;
            if (chunk.step && !nextSteps.includes(chunk.step)) {
              return [...nextSteps, chunk.step];
            }
            return nextSteps;
          });
          continue;
        }

        if (chunk.type === 'delta' && chunk.text) {
          updateMessage(pageKey, assistantMessageId, (message) => ({
            ...message,
            content:
              message.content === THINKING_PLACEHOLDER
                ? chunk.text || ''
                : `${message.content}${chunk.text || ''}`,
          }));
          continue;
        }

        if (chunk.type === 'replace') {
          updateMessage(pageKey, assistantMessageId, (message) => ({
            ...message,
            content: chunk.text || chunk.full_text || '',
          }));
          continue;
        }

        if (chunk.type === 'complete') {
          updateMessage(pageKey, assistantMessageId, (message) => ({
            ...message,
            content: formatAssistantContentWithDocuments(
              chunk.text || chunk.full_text || '',
              chunk.documents
            ),
          }));
          streamCompleted = true;
          continue;
        }

        if (chunk.type === 'error') {
          updateMessage(pageKey, assistantMessageId, (message) => ({
            ...message,
            content: `请求失败: ${chunk.error || '网络错误'}`,
          }));
          streamCompleted = true;
        }
      }

      if (!streamCompleted) {
        updateMessage(pageKey, assistantMessageId, (message) => ({
          ...message,
          content: message.content || '已完成响应，但未返回可显示内容。',
        }));
      }
    } catch (error: any) {
      if (error?.name === 'AbortError') {
        return;
      }

      console.error('聊天请求失败:', error);
      updateMessage(pageKey, assistantMessageId, (message) => ({
        ...message,
        content: `请求失败: ${error.message || '网络错误'}`,
      }));
      setActiveTaskId(pageKey, null);
    } finally {
      setStreamAbortController(null);
      setLoading(pageKey, false);
      setActiveTaskId(pageKey, null);
      // 重置Manus步骤状态
      setManusSteps([]);
      setCurrentManusStep(0);
    }
  };

  const handleClearConversation = () => {
    if (pollingAbortController) {
      pollingAbortController.abort();
      setPollingAbortController(null);
    }
    if (streamAbortController) {
      streamAbortController.abort();
      setStreamAbortController(null);
    }
    clearConversation(pageKey);
    setManusSteps([]);
    setCurrentManusStep(0);
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
        <div className={styles.headerLeft}>
          {canUseLiteratureResearch && (
            <div className={styles.modeSwitch}>
              <span className={styles.modeLabel}>文献调研模式</span>
              <div
                onClick={() => toggleLiteratureResearchMode()}
                className={`${styles.appleSwitch} ${
                  isLiteratureResearchEnabled ? styles.appleSwitchActive : ''
                }`}
                title={isLiteratureResearchEnabled ? '关闭文献调研模式' : '开启文献调研模式'}
                role="switch"
                aria-checked={isLiteratureResearchEnabled}
              >
                <div className={styles.appleSwitchThumb}></div>
              </div>
            </div>
          )}
          {isLiteratureResearchEnabled && (
            <div className={styles.literatureReviewOption}>
              <span className={styles.modeLabel}>生成文献综述</span>
              <div
                onClick={() => toggleGenerateLiteratureReview()}
                className={`${styles.appleSwitch} ${
                  isGenerateLiteratureReviewEnabled ? styles.appleSwitchActive : ''
                }`}
                title={isGenerateLiteratureReviewEnabled ? '关闭生成文献综述' : '开启生成文献综述'}
                role="switch"
                aria-checked={isGenerateLiteratureReviewEnabled}
              >
                <div className={styles.appleSwitchThumb}></div>
              </div>
            </div>
          )}
        </div>
        <div className={styles.headerRight}>
          <Button
            variant="ghost"
            size="small"
            onClick={handleClearConversation}
            className={styles.clearButton}
            disabled={conversation.loading || conversation.messages.length === 0}
            title="清空当前对话消息"
          >
            清空对话
          </Button>
        </div>
      </div>

      {/* 消息列表 */}
      <div className={styles.messagesContainer} ref={messagesContainerRef}>
        {conversation.messages.length === 0 ? (
          <div className={styles.emptyState}>
            <h4 className={styles.emptyTitle}>我能为你做什么？</h4>
          </div>
        ) : (
          <div className={styles.messagesList}>
            {conversation.messages.map((message, index) =>
              (() => {
                const isStreamingMessage =
                  conversation.loading &&
                  message.role === 'assistant' &&
                  index === conversation.messages.length - 1;

                return (
                  <div
                    key={message.id || `${message.timestamp}-${message.role}-${index}`}
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
                      <div className={styles.messageContent}>
                        <span
                          dangerouslySetInnerHTML={{ __html: cleanMarkdown(message.content) }}
                        />
                        {isStreamingMessage && <span className={styles.streamCursor} />}
                      </div>
                    ) : (
                      <div className={styles.messageContent}>{message.content}</div>
                    )}
                  </div>
                );
              })()
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
                isLiteratureResearchEnabled
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
