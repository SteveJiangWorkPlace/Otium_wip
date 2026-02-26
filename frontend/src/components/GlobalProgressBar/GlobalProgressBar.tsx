import React, { useEffect, useState } from 'react';
import { useGlobalProgressStore } from '../../store/useGlobalProgressStore';
import styles from './GlobalProgressBar.module.css';

// 幽默文案库（放在组件外部避免重复创建）
// 任务类型映射
const TASK_TYPE_MAP: Record<string, string> = {
  correction: '智能纠错',
  translation: '文本翻译',
  'ai-detection': 'AI检测',
  modification: '文本修改',
  general: '通用任务',
};

const HUMOROUS_MESSAGES = {
  idle: [
    '大脑待机中...zzz',
    '等待指令，随时待命',
    '闲置模式启动',
    '喝杯咖啡，等我一下',
    '摸鱼时间到',
    '待机中，勿扰模式',
    '空闲状态，等待召唤',
    '我在，但我在发呆',
    '休息一下，马上回来',
    '宇宙和平，无事发生',
  ],
  working: [
    'Otium正在疯狂思考',
    '正在处理，请稍安勿躁',
    '努力工作中，不要催',
    'CPU转速飙升中',
    '算法正在燃烧脑细胞',
    '努力生成优质内容',
    '智能处理中，请耐心等待',
    '正在为你加班加点',
    '努力工作的Otium',
    '计算中，请勿断电',
  ],
  completed: [
    '任务完成，收工！',
    '搞定！可以夸夸我了',
    '处理完毕，请验收',
    '大功告成，完美！',
    '任务搞定，打个卡',
    '圆满完成，请指示',
    '处理结束，请查收',
    '搞定收工，真简单',
    '任务完成，轻轻松松',
    '处理完毕，毫无压力',
  ],
  error: [
    '哎呀，出了点小状况',
    '任务失败，但不是我笨',
    '遇到点麻烦，需要支援',
    '好像哪里不对劲',
    '出了点小差错',
    '这个任务有点调皮',
    '遇到了未知的敌人',
    '程序说它今天心情不好',
    '需要一点魔法修复',
    '遇到了小小的挑战',
  ],
};

const GlobalProgressBar: React.FC = () => {
  const { isVisible, message, showDots, taskType, lastCompletedTask } = useGlobalProgressStore();
  const [dotIndex, setDotIndex] = useState(0);
  const [humorousMessage, setHumorousMessage] = useState<string>('');
  const [completionTime, setCompletionTime] = useState<number | null>(null);

  // 点号动画效果
  useEffect(() => {
    if (!showDots) {
      setDotIndex(0);
      return;
    }

    const interval = setInterval(() => {
      setDotIndex((prev) => (prev + 1) % 4); // 0, 1, 2, 3
    }, 500);

    return () => clearInterval(interval);
  }, [showDots]);

  // 处理完成状态超时（15分钟后切换为空闲状态）
  useEffect(() => {
    // 完成状态条件：有最后完成的任务且没有点号动画（任务已完成）
    if (lastCompletedTask && !showDots) {
      // 任务刚完成，记录完成时间
      setCompletionTime((prevTime) => {
        // 如果还没有设置完成时间，则设置当前时间
        if (!prevTime) {
          return Date.now();
        }
        // 如果已经有完成时间，保持不变
        return prevTime;
      });
    } else {
      // 有新的任务或清除状态，重置完成时间
      setCompletionTime(null);
    }
  }, [lastCompletedTask, showDots]);

  // 检查15分钟超时
  useEffect(() => {
    if (completionTime) {
      const timeoutId = setTimeout(
        () => {
          // 15分钟（900000毫秒）后清除最后完成的任务状态
          const elapsed = Date.now() - completionTime;
          if (elapsed >= 15 * 60 * 1000) {
            setCompletionTime(null);
            // 清除最后完成的任务状态，让组件显示空闲状态
            useGlobalProgressStore.getState().clearProgress();
          }
        },
        15 * 60 * 1000
      );

      return () => clearTimeout(timeoutId);
    }
  }, [completionTime]);

  // 根据状态更新幽默文案
  useEffect(() => {
    // 优先级1: 错误状态（最高优先级）
    const errorKeywords = ['错误', '失败', '取消'];
    const hasError = errorKeywords.some((keyword) => message && message.includes(keyword));

    if (hasError) {
      // 错误状态 - 使用幽默文案
      const messages = HUMOROUS_MESSAGES.error;
      const randomIndex = Math.floor(Math.random() * messages.length);

      // 添加任务类型信息
      const taskName = taskType ? TASK_TYPE_MAP[taskType] || '任务' : '任务';
      const baseMessage = messages[randomIndex];
      setHumorousMessage(`${baseMessage}（${taskName}）`);
    }
    // 优先级2: 运行中状态（showDots为true）
    else if (showDots) {
      // 运行中状态 - 使用幽默文案
      const messages = HUMOROUS_MESSAGES.working;
      const randomIndex = Math.floor(Math.random() * messages.length);

      // 添加任务类型信息
      const taskName = taskType ? TASK_TYPE_MAP[taskType] || '任务' : '任务';
      const baseMessage = messages[randomIndex];

      if (baseMessage.includes('处理') || baseMessage.includes('正在')) {
        setHumorousMessage(`${baseMessage}（${taskName}）`);
      } else {
        setHumorousMessage(`${baseMessage} - ${taskName}进行中`);
      }
    }
    // 优先级3: 完成状态（有最后完成的任务且没有点号动画）
    else if (lastCompletedTask && !showDots) {
      // 完成状态 - 只显示简单直白的任务完成消息，不使用幽默文案
      const taskName = TASK_TYPE_MAP[lastCompletedTask] || '未知任务';
      setHumorousMessage(`${taskName}已完成`);
    }
    // 优先级4: 其他状态，使用原始消息
    else if (message) {
      setHumorousMessage(message);
    }
    // 优先级5: 空闲状态
    else {
      const messages = HUMOROUS_MESSAGES.idle;
      const randomIndex = Math.floor(Math.random() * messages.length);
      setHumorousMessage(messages[randomIndex]);
    }
  }, [isVisible, message, showDots, taskType, lastCompletedTask]);

  const getDots = () => {
    return '.'.repeat(dotIndex);
  };

  // 确定当前显示的图标路径
  const getCurrentIconPath = () => {
    // 首先检查错误状态（优先级最高）
    const errorKeywords = ['错误', '失败', '取消'];
    const hasError = errorKeywords.some((keyword) => message && message.includes(keyword));

    if (hasError) {
      // 错误状态 - 显示休息图标
      return '/rest.svg';
    } else if (showDots) {
      // 运行中状态
      return '/working.svg';
    } else if (lastCompletedTask && !showDots) {
      // 完成状态
      return '/complete.svg';
    } else {
      // 空闲状态
      return '/rest.svg';
    }
  };

  // 检查是否为错误状态
  const errorKeywords = ['错误', '失败', '取消'];
  const isErrorState = errorKeywords.some((keyword) => message && message.includes(keyword));

  const currentIconPath = getCurrentIconPath();

  // 图标加载错误处理
  const [iconError, setIconError] = useState(false);

  // 当图标路径变化时重置错误状态
  useEffect(() => {
    setIconError(false);
  }, [currentIconPath]);

  const handleIconError = () => {
    console.error(`图标加载失败: ${currentIconPath}`);
    setIconError(true);
  };

  return (
    <div className={styles.progressBarContainer}>
      {/* 图标容器 */}
      <div className={styles.iconContainer}>
        {iconError ? (
          <div className={styles.fallbackIcon}>
            <span className={styles.fallbackText}>!</span>
          </div>
        ) : (
          <img
            src={currentIconPath}
            alt="状态图标"
            className={`${styles.statusIcon} ${isErrorState ? styles.error : ''}`}
            onError={handleIconError}
            loading="eager"
          />
        )}
      </div>

      {/* 进度条内容 */}
      <div className={styles.progressBarContent}>
        <div className={styles.progressMessage}>
          {humorousMessage}
          {showDots && <span className={styles.dots}>{getDots()}</span>}
        </div>
      </div>
    </div>
  );
};

export default GlobalProgressBar;
