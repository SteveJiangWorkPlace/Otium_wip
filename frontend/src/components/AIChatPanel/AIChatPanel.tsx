import React, { useRef, useEffect } from 'react';
import { useAIChatStore, type AIChatMessage as StoreAIChatMessage } from '../../store/useAIChatStore';
import { apiClient } from '../../api/client';
import type { AIChatMessage as ApiAIChatMessage } from '../../types';
import Button from '../ui/Button/Button';
import Textarea from '../ui/Textarea/Textarea';
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
  } = useAIChatStore();

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


  // 清理markdown符号但保留必要格式
  const cleanMarkdown = (html: string): string => {
    // 先转换markdown格式为HTML
    let cleaned = html;

    // 首先处理markdown表格
    cleaned = cleaned.replace(/\n(\|[^\n]+\|\s*\n)(\|[-\s:|]+\|.*\|\s*\n)((?:\|[^\n]+\|\s*\n)+)/g, (match, headerLine, separatorLine, dataLines) => {
      try {
        // 解析表头行 - 移除首尾的|，然后按|分割
        const headerCells = headerLine.trim().slice(1, -1).split('|').map((cell: string) => cell.trim());

        // 解析数据行
        const rowLines = dataLines.trim().split('\n').filter((line: string) => line.trim() !== '');
        const rows = rowLines.map((line: string) =>
          line.trim().slice(1, -1).split('|').map((cell: string) => cell.trim())
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
    });

    // 转换 **文本** 为 <strong>文本</strong>
    cleaned = cleaned.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // 转换 *文本* 为 <em>文本</em>（但避免匹配行首的*）
    // 只匹配前后有空格或标点的*，避免匹配数字中的*（如1*2）
    cleaned = cleaned.replace(/(^|\s)\*(.*?)\*($|\s|\.|,|;|:|!|\?)/g, '$1<em>$2</em>$3');

    // 去除行首的markdown符号
    cleaned = cleaned
      .replace(/^\*\s+/gm, '') // 去除行首的 "* "
      .replace(/^>\s+/gm, '') // 去除行首的 "> "
      .replace(/^-\s+/gm, '') // 去除行首的 "- "
      .replace(/^\d+\.\s+/gm, '') // 去除行首的 "1. "
      .replace(/^#+\s+/gm, ''); // 去除行首的 "# "

    // 去除残留的单独*符号（不在HTML标签内）
    // 匹配前后有空格的单独*，且不是<em>或<strong>标签的一部分
    cleaned = cleaned.replace(/(\s)\*(\s|$)/g, '$1$2');
    cleaned = cleaned.replace(/^(\s)?\*(\s|$)/gm, '$1$2');

    // 为现有的HTML表格添加样式（如果AI直接返回了HTML表格）
    cleaned = cleaned.replace(/<table>/g, '<div class="ai-table-container"><table class="ai-table">');
    cleaned = cleaned.replace(/<\/table>/g, '</table></div>');

    // 保留HTML标签，其它markdown符号已处理
    return cleaned;
  };

  const handleSendMessage = async () => {
    const text = conversation.inputText.trim();
    if (!text || conversation.loading) return;

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
      // 构建消息列表（转换为API格式）
      const messages: ApiAIChatMessage[] = conversation.messages.map(msg => ({
        role: msg.role,
        content: msg.content,
      }));

      // 添加当前用户消息（API格式）
      messages.push({
        role: userMessage.role,
        content: userMessage.content,
      });

      // 调用API
      const response = await apiClient.chat({
        messages,
        session_id: conversation.sessionId || undefined,
      });

      if (response.success) {
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
          <h3 className={styles.collapsedTitle}>Otium AI助手</h3>
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
      {/* 面板头部 - 已移除所有按钮，仅保留细线边框 */}
      <div className={styles.header}></div>

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
                <div className={styles.messageHeader}>
                  <span className={styles.messageRole}>
                    {message.role === 'user' ? '爱学习的孩子' : 'Otium'}
                  </span>
                </div>
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
                  <span className={styles.messageRole}>Otium</span>
                </div>
                <div className={styles.messageContent}>
                  <div className={styles.typingIndicator}>
                    <span>.</span>
                    <span>.</span>
                    <span>.</span>
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
          {/* AI状态栏 */}
          <div className={styles.aiStatusBar}></div>
          <div style={{ position: 'relative', width: '100%' }}>
            <Textarea
              value={conversation.inputText}
              onChange={(e) => setInputText(pageKey, e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入您的问题..."
              rows={3}
              resize="vertical"
              disabled={conversation.loading}
              className={styles.textarea}
            />
            <button
              className={styles.sendButton}
              onClick={handleSendMessage}
              disabled={!conversation.inputText.trim() || conversation.loading}
              title="发送"
            >
              <div className={styles.sendArrow}>↑</div>
            </button>
          </div>
        </div>
      </div>

    </div>
  );
};

export default AIChatPanel;