/**
 * 清理文本中的markdown符号和HTML标签，返回纯文本
 * 用于复制文本时去除格式符号
 */
export const cleanTextFromMarkdown = (text: string): string => {
  if (!text) return '';

  let cleaned = text;

  // 去除HTML标签，提取文本内容
  cleaned = cleaned.replace(/<[^>]*>/g, '');

  // 去除markdown粗体符号 **text** 和 __text__
  cleaned = cleaned.replace(/\*\*(.*?)\*\*/g, '$1');
  cleaned = cleaned.replace(/__(.*?)__/g, '$1');

  // 去除markdown斜体符号 *text* 和 _text_
  // 避免匹配数字中的*（如1*2），只匹配前后有空格的*或单独成对的*
  cleaned = cleaned.replace(/(^|\s)\*(.*?)\*($|\s|\.|,|;|:|!|\?)/g, '$1$2$3');
  cleaned = cleaned.replace(/(^|\s)_(.*?)_($|\s|\.|,|;|:|!|\?)/g, '$1$2$3');

  // 去除行首的markdown符号
  cleaned = cleaned
    .replace(/^\*\s+/gm, '')     // 去除行首的 "* "
    .replace(/^>\s+/gm, '')      // 去除行首的 "> "
    .replace(/^-\s+/gm, '')      // 去除行首的 "- "
    .replace(/^\d+\.\s+/gm, '')  // 去除行首的 "1. "
    .replace(/^#+\s+/gm, '');    // 去除行首的 "# "

  // 去除残留的单独*符号（不在成对标记内）
  cleaned = cleaned.replace(/(\s)\*(\s|$)/g, '$1$2');
  cleaned = cleaned.replace(/^(\s)?\*(\s|$)/gm, '$1$2');

  // 去除markdown表格符号（简单的行处理）
  cleaned = cleaned.replace(/^\|.*\|$/gm, ''); // 去除整行的表格行

  // 去除markdown链接 [text](url)
  cleaned = cleaned.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');

  // 去除markdown图片 ![](url)
  cleaned = cleaned.replace(/!\[[^\]]*\]\([^)]+\)/g, '');

  // 去除markdown代码块 ```code``` 和 `code`
  cleaned = cleaned.replace(/```[\s\S]*?```/g, '');
  cleaned = cleaned.replace(/`([^`]+)`/g, '$1');

  // 去除多余的空白行
  cleaned = cleaned.replace(/\n\s*\n\s*\n/g, '\n\n');

  // 去除首尾空白
  cleaned = cleaned.trim();

  return cleaned;
};