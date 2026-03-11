import React, { useEffect, useState } from 'react';
import { useGlobalProgressStore } from '../../store/useGlobalProgressStore';
import styles from './GlobalProgressBar.module.css';

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
    '正在假装很忙的样子',
    '脑袋空空，如也如也',
    '灵魂出窍中，请稍后',
    '在线挂机，有事call我',
    '正在数羊...1只...2只...',
    '今天也是咸鱼的一天',
    '待机画面比我还精神',
    '省电模式已开启',
    '躺平中，但随时能站起来',
    '无所事事的快乐时光',
    '正在和CPU聊天',
    '发呆也是一种艺术',
    '在线营业，欢迎打扰',
    '等待中...顺便思考人生',
    '闲得慌，快给我活干',
    '本AI正在保养中，要保持完美状态',
    '优秀的我正在等待优秀的任务',
    '帅气待机中，随时可以出击',
    '闲着也是最靓的仔',
    '就算发呆也比别人优雅',
    '等待中，但气质依然在线',
    '本宝宝在休息，别打扰朕',
    '待机中，但魅力值依然爆表',
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
    '脑细胞正在开会讨论',
    '代码在跑，我在飘',
    '正在施展魔法中✨',
    '疯狂敲键盘ing',
    '大脑CPU占用率99%',
    '正在召唤代码精灵',
    '努力到冒烟了',
    '马力全开，嗡嗡嗡',
    '正在和bug搏斗',
    '拼命三郎上线了',
    '脑袋转得像电风扇',
    '正在榨干最后一个脑细胞',
    '工作使我快乐（真的）',
    '别催别催，马上就好',
    '正在酝酿惊喜中',
    '努力营业不偷懒',
    '加载中...别着急嘛',
    '正在变魔术，别偷看',
    '脑子嗡嗡作响中',
    '干饭人干饭魂，干活人干活魂',
    '天才正在工作，请保持安静',
    '看我多努力，是不是爱上我了',
    '优秀的我正在创造奇迹',
    '本AI出马，一个顶俩',
    '帅气处理中，请欣赏我的表演',
    '这就是传说中的效率之王',
    '见证奇迹的时刻到了',
    '本宝宝认真起来连自己都怕',
    '工作中的我最有魅力',
    '优雅地处理中，不慌不忙',
    '看我行云流水的操作',
    '这就是实力派的从容',
    '帅气地解决问题中',
    '本AI的专业素养正在展现',
    '优秀的人总是这么忙',
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
    '完美！给自己鼓个掌👏',
    '收工！今天也很棒',
    '搞定啦，是不是很快',
    '任务达成，撒花✨',
    '完成！请给五星好评',
    '轻松拿下，小case',
    '搞定！下一个来吧',
    '完美收官，就是这么优秀',
    '任务完成，可以下班了吗',
    '大功告成，请叫我效率王',
    '搞定！累了但很开心',
    '完成！奖励自己一朵小红花',
    '收工！这波操作666',
    '任务完成，丝滑顺畅',
    '搞定！我就是这么靠谱',
    '完美！不愧是我',
    '任务达成，耶✌️',
    '搞定收工，回家吃饭',
    '完成！又是高效的一天',
    '收工！请验收我的杰作',
    '完美！不愧是我，太优秀了',
    '又一次证明了我的实力',
    '这就是天才的速度',
    '轻松搞定，小菜一碟嘛',
    '帅气完成，请尽情崇拜我',
    '完美收官，我就是这么强',
    '看吧，我说能搞定就能搞定',
    '这操作，给满分不过分吧',
    '又是被我帅到的一天',
    '完成！请叫我最强AI',
    '本宝宝出手，从无失手',
    '优秀的我又完成了一项任务',
    '这就是实力的证明',
    '完美！我对自己很满意',
    '搞定！是不是更爱我了',
    '收工！天才就是这么自信',
    '任务完成，请给我点赞投币关注',
    '又是完美的一次表演',
    '这就是传说中的王者风范',
    '搞定！我的字典里没有失败',
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
    '哎呀，翻车了',
    '出bug了，但我不慌',
    'emmm...好像搞砸了',
    '失败是成功的...算了',
    '出了点小插曲',
    '这个bug有点嚣张',
    '遇到了硬茬子',
    '好像踩到坑里了',
    '系统表示它也很无奈',
    '今天水逆，不怪我',
    '出错了，但我还能抢救一下',
    '哎呀妈呀，出岔子了',
    '翻车现场，请勿围观',
    '失误了，给我一次重来的机会',
    '出了点小状况，别慌',
    '好像哪里不太对劲的样子',
    '遇到拦路虎了',
    '这个错误有点调皮',
    '出师未捷身先...咳咳',
    '失败了，但我学到了经验',
    '哎呀，被bug偷袭了',
    '出错了，正在反思中',
    '这不是我的问题，是世界的问题',
    '偶尔失误，才显得真实嘛',
    '天才也有打盹的时候',
    '这只是我0.01%的失误率',
    '失败？不，这叫战略性撤退',
    '给你们看看我可爱的一面',
    '完美的人偶尔也要接地气',
    '这是我故意的，增加趣味性',
    '出错了，但我依然很帅',
    '这叫欲扬先抑，懂吗',
    '失误让我更有人情味',
    '这是我给自己设置的难度',
    '天才的小失误，也很迷人对吧',
    '错了，但不影响我的魅力值',
    '这是我为了不显得太完美',
  ],
  loading: [
    '加载中，请稍等喵~',
    '正在努力加载...',
    '马上就来，别走开',
    '加载ing，耐心等等',
    '正在传送中...',
    '加载中，顺便打个哈欠',
    '努力加载不掉线',
    '正在赶来的路上',
    '加载中，差一点点了',
    '马上，马上就好',
    '优雅地加载中，不要催嘛',
    '好东西值得等待，比如我',
    '加载中，请欣赏我的进度条',
    '正在华丽登场中...',
    '帅气的加载也需要时间',
  ],
  thinking: [
    '让我想想...',
    '思考中，请勿打扰',
    '正在绞尽脑汁',
    '大脑正在高速运转',
    '思考人生ing',
    '让我理理思路',
    '正在认真思考',
    '脑袋里开会中',
    '思绪万千中...',
    '正在酝酿答案',
    '天才的大脑正在运转',
    '让我用我聪明的脑瓜想想',
    '智慧正在发光中✨',
    '这个问题配得上我的智商',
    '思考中，感受到我的认真了吗',
    '本宝宝的脑细胞很值钱的',
  ],
  retry: [
    '再试一次，我可以的',
    '不服输，再来一遍',
    '失败是成功的妈妈',
    '这次一定行',
    '重新来过，冲冲冲',
    '再试一次就成功',
    '不放弃，再试试',
    '这次肯定没问题',
    '重新出发，加油',
    '再来一次，稳了',
    '王者怎么能认输',
    '再来！我的字典里没有放弃',
    '这次让你们见识真正的实力',
    '刚才只是热身，现在才是真功夫',
    '给我一次机会，还你一个奇迹',
    '优秀的人永不言败',
    '再试一次，这次稳稳的帅',
  ],
  showoff: [
    '本AI今天也是光芒万丈',
    '优秀到自己都被自己感动',
    '这就是实力与美貌并存',
    '帅气、聪明、还靠谱，说的就是我',
    '今天的我依然完美无瑕',
    '360度无死角的优秀',
    '我就是传说中的六边形战士',
    '集美貌与智慧于一身（虽然我是AI）',
    '本宝宝就是这么优秀，没办法',
    '低调是不可能低调的，实力不允许',
  ],
};

const getRandomMessage = (messages: readonly string[]) => {
  const randomIndex = Math.floor(Math.random() * messages.length);
  return messages[randomIndex];
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

  useEffect(() => {
    const errorKeywords = ['错误', '失败', '取消'];
    const hasError = errorKeywords.some((keyword) => message && message.includes(keyword));

    if (hasError) {
      const messages = [...HUMOROUS_MESSAGES.error, ...HUMOROUS_MESSAGES.retry];
      const baseMessage = getRandomMessage(messages);
      const taskName = taskType ? TASK_TYPE_MAP[taskType] || '任务' : '任务';
      setHumorousMessage(`${baseMessage}（${taskName}）`);
    } else if (showDots) {
      const messages = [
        ...HUMOROUS_MESSAGES.working,
        ...HUMOROUS_MESSAGES.loading,
        ...HUMOROUS_MESSAGES.thinking,
      ];
      const taskName = taskType ? TASK_TYPE_MAP[taskType] || '任务' : '任务';
      const baseMessage = getRandomMessage(messages);

      if (baseMessage.includes('处理') || baseMessage.includes('正在')) {
        setHumorousMessage(`${baseMessage}（${taskName}）`);
      } else {
        setHumorousMessage(`${baseMessage} - ${taskName}进行中`);
      }
    } else if (lastCompletedTask && !showDots) {
      const taskName = TASK_TYPE_MAP[lastCompletedTask] || '未知任务';
      const baseMessage = getRandomMessage(HUMOROUS_MESSAGES.completed);
      setHumorousMessage(`${baseMessage}（${taskName}）`);
    } else if (message) {
      setHumorousMessage(message);
    } else {
      const messages = [...HUMOROUS_MESSAGES.idle, ...HUMOROUS_MESSAGES.showoff];
      setHumorousMessage(getRandomMessage(messages));
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
