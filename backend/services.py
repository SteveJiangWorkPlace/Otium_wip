"""
API服务模块

包含与外部API交互的服务函数，如Gemini和GPTZero。
"""

import ast
import json
import logging
import time
import re
import hashlib
from typing import Dict, Any, Optional, List

import google.genai
import google.genai.errors
import requests

from exceptions import GeminiAPIError, GPTZeroAPIError, RateLimitError
from utils import TextValidator


# ==========================================
# Gemini API 服务
# ==========================================

def generate_gemini_content_with_fallback(prompt: str, api_key: Optional[str] = None,
                                         primary_model: str = "gemini-2.5-pro",
                                         fallback_model: str = "gemini-3-pro-preview") -> Dict[str, Any]:
    """带容错的 Gemini 内容生成

    Args:
        prompt: 提示词文本
        api_key: Gemini API密钥，如果为None则使用环境变量
        primary_model: 主要模型名称
        fallback_model: 备用模型名称

    Returns:
        包含结果的字典，格式：{"success": bool, "text": str, "model_used": str, "error": str, "error_type": str}
    """
    logging.info(f"尝试使用主要模型 {primary_model} 生成内容")

    # 安全设置 - 使用 google.genai 的类型
    safety_settings = [
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_NONE"
        }
    ]

    def _try_model(model_name: str) -> Dict[str, Any]:
        max_retries = 3
        retry_delay = 2  # 秒

        for attempt in range(max_retries):
            try:
                # 只使用传入的API密钥，不再使用环境变量
                current_api_key = api_key
                if not current_api_key:
                    raise GeminiAPIError("未提供 Gemini API Key，请在侧边栏输入", "missing_key")

                # 调试日志：记录API密钥信息（不记录完整密钥）
                key_prefix = current_api_key[:8] if len(current_api_key) > 8 else current_api_key[:len(current_api_key)]
                logging.info(f"使用请求头中的Gemini API密钥，前缀: {key_prefix}...")

                # 创建客户端
                client = google.genai.Client(api_key=current_api_key)

                # 准备配置（包括安全设置）
                config = {
                    "safety_settings": safety_settings
                }

                # 生成内容
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config
                )

                # 提取响应文本
                # 注意：response 结构可能不同，需要检查
                text = ""
                if hasattr(response, 'text'):
                    text = response.text
                elif hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            text = candidate.content.parts[0].text
                        elif hasattr(candidate.content, 'text'):
                            text = candidate.content.text

                return {"success": True, "text": text, "model_used": model_name}

            except Exception as e:
                # 获取原始错误消息
                error_raw = str(e)
                error_msg = error_raw.lower()

                # 尝试解析JSON或Python字典格式的错误信息
                error_json = None
                try:
                    # 尝试从错误消息中提取字典/JSON
                    # 查找可能的字典结构开始
                    json_start = error_raw.find('{')
                    if json_start != -1:
                        json_str = error_raw[json_start:]
                        # 首先尝试使用ast.literal_eval解析Python字典（支持单引号）
                        try:
                            error_json = ast.literal_eval(json_str)
                        except:
                            # 如果失败，尝试json.loads（需要双引号）
                            # 将单引号替换为双引号
                            json_str_fixed = json_str.replace("'", '"')
                            error_json = json.loads(json_str_fixed)
                except:
                    pass  # 如果解析失败，继续使用原始错误消息

                # 服务不可用错误
                if "service unavailable" in error_msg or "503" in error_msg or "unavailable" in error_msg:
                    logging.error(f"模型 {model_name} - 服务不可用: {str(e)}")
                    raise GeminiAPIError(f"Google API服务暂时不可用，请稍后再试", "service_unavailable")

                # 超时错误（包括 DeadlineExceeded 和 requests Timeout）
                elif "timeout" in error_msg or "deadline" in error_msg or "timed out" in error_msg:
                    logging.error(f"模型 {model_name} - 请求超时 (尝试 {attempt+1}/{max_retries}): {str(e)}")
                    if attempt < max_retries - 1:
                        logging.info(f"等待 {retry_delay} 秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    raise GeminiAPIError("请求超时（默认60秒），请检查网络连接", "timeout")

                # 网络连接错误
                elif "connect" in error_msg or "socket" in error_msg or "network" in error_msg or "connection" in error_msg:
                    logging.error(f"模型 {model_name} - 网络连接错误 (尝试 {attempt+1}/{max_retries}): {str(e)}")
                    if attempt < max_retries - 1:
                        logging.info(f"等待 {retry_delay} 秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    error_message = "无法连接到Google API服务。"
                    error_message += "\n可能的原因："
                    error_message += "\n1. 网络连接问题 - 请检查您的互联网连接"
                    error_message += "\n2. 防火墙或网络设置 - 如果您在中国，可能需要VPN才能访问Google服务"
                    error_message += "\n3. Google服务暂时不可用 - 请稍后再试"
                    error_message += "\n\n解决方案："
                    error_message += "\n• 检查网络连接是否正常"
                    error_message += "\n• 如果使用VPN，请确保VPN连接稳定"
                    raise GeminiAPIError(error_message, "network_error")

                # API配额错误
                elif "quota" in error_msg or "resource_exhausted" in error_msg:
                    logging.error(f"模型 {model_name} - API 配额已用尽: {str(e)}")
                    raise GeminiAPIError("API 配额已用尽，请稍后再试", "quota")

                # 速率限制
                elif "429" in error_msg or "rate_limit" in error_msg or "too many requests" in error_msg:
                    logging.error(f"模型 {model_name} - 速率限制: {str(e)}")
                    raise RateLimitError("请求过于频繁，请稍后再试")

                # API密钥无效
                elif "invalid" in error_msg or "api_key" in error_msg or "permission" in error_msg or "unauthorized" in error_msg:
                    logging.error(f"模型 {model_name} - API Key 无效: {str(e)}")
                    raise GeminiAPIError("API Key 无效或已过期，请检查配置", "invalid_key")

                # 区域限制错误
                elif (error_json and
                      (error_json.get('error', {}).get('status') == 'FAILED_PRECONDITION' or
                       'user location is not supported' in str(error_json).lower() or
                       'location is not supported' in str(error_json).lower())) or \
                     "failed_precondition" in error_msg or \
                     "user location is not supported" in error_msg or \
                     "location is not supported" in error_msg:
                    logging.error(f"模型 {model_name} - 区域限制: {str(e)}")
                    error_message = "Google Gemini API 在您所在的区域不可用。\n"
                    error_message += "可能的原因：\n"
                    error_message += "1. 您所在的地区（如中国大陆）可能无法直接访问Google服务\n"
                    error_message += "2. 网络环境限制\n\n"
                    error_message += "解决方案：\n"
                    error_message += "• 使用VPN连接到支持Google服务的地区\n"
                    error_message += "• 检查网络连接和代理设置\n"
                    error_message += "• 联系网络管理员确认是否允许访问Google API"
                    raise GeminiAPIError(error_message, "region_restricted")

                # 其他API错误
                elif "api" in error_msg or "google" in error_msg or "genai" in error_msg:
                    logging.error(f"模型 {model_name} - API 错误: {str(e)}")
                    raise GeminiAPIError(f"API 错误: {str(e)}", "api_error")

                # 未知错误
                else:
                    logging.error(f"模型 {model_name} - 未知错误: {str(e)}", exc_info=True)
                    raise GeminiAPIError(f"未知错误: {str(e)}", "unknown")

        # 如果所有重试都失败（理论上不应该到达这里）
        raise GeminiAPIError(f"所有 {max_retries} 次重试均失败", "all_retries_failed")

    # 尝试主要模型
    try:
        return _try_model(primary_model)

    except GeminiAPIError as e:
        if e.error_type in ["blocked", "invalid_key", "region_restricted"]:
            return {"success": False, "error": e.message, "error_type": e.error_type}

        logging.warning(f"主要模型 {primary_model} 失败，尝试备用模型 {fallback_model}")

        try:
            return _try_model(fallback_model)
        except GeminiAPIError as fallback_error:
            return {"success": False, "error": fallback_error.message, "error_type": fallback_error.error_type}
        except Exception as fallback_error:
            logging.error(f"备用模型也失败: {str(fallback_error)}", exc_info=True)
            return {"success": False, "error": "所有模型尝试均失败，请稍后再试", "error_type": "all_failed"}

    except RateLimitError as e:
        return {"success": False, "error": str(e), "error_type": "rate_limit"}

    except Exception as e:
        logging.error(f"未知错误: {str(e)}", exc_info=True)
        return {"success": False, "error": "系统错误，请稍后再试", "error_type": "unknown"}


# ==========================================
# GPTZero API 服务
# ==========================================

def check_gptzero(text: str, api_key: str) -> Dict[str, Any]:
    """使用GPTZero检测AI内容

    Args:
        text: 要检测的文本
        api_key: GPTZero API密钥

    Returns:
        包含检测结果的字典
    """
    is_valid, message = TextValidator.validate_for_gptzero(text)
    if not is_valid:
        if "过长" in message:
            text = text[:TextValidator.GPTZERO_MAX_CHARS]
            logging.warning("文本已截断至GPTZero API限制")
        else:
            return {"success": False, "message": message}

    url = "https://api.gptzero.me/v2/predict/text"
    headers = {
        "x-api-key": api_key,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = {"document": text}

    max_retries = 3
    retry_count = 0
    current_delay = 2

    while retry_count < max_retries:
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()

            if "documents" in result:
                if isinstance(result["documents"], dict):
                    doc = result["documents"]
                elif isinstance(result["documents"], list) and len(result["documents"]) > 0:
                    doc = result["documents"][0]
                else:
                    return {"success": False, "message": "未知的API响应格式"}

                return {
                    "ai_score": doc.get("completely_generated_prob", 0),
                    "success": True,
                    "message": "检测成功",
                    "detailed_scores": doc.get("sentences", []),
                    "full_text": text
                }
            else:
                return {"success": False, "message": "API返回了未知格式的数据"}

        except requests.exceptions.Timeout:
            retry_count += 1
            if retry_count >= max_retries:
                logging.error("GPTZero API请求超时，已达到最大重试次数")
                return {"success": False, "message": "检测请求超时，请稍后再试"}
            logging.warning(f"GPTZero API超时，{current_delay}秒后重试 ({retry_count}/{max_retries})")
            time.sleep(current_delay)
            current_delay *= 2

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            if status_code == 401:
                return {"success": False, "message": "API Key 无效或已过期"}
            elif status_code == 429:
                return {"success": False, "message": "请求过于频繁，请稍后再试"}
            else:
                return {"success": False, "message": f"API 请求失败（状态码 {status_code}）"}

        except Exception as e:
            logging.error(f"GPTZero API调用异常: {str(e)}", exc_info=True)
            return {"success": False, "message": "系统错误，请稍后再试"}

    return {"success": False, "message": "检测失败，已达到最大重试次数"}


# ==========================================
# 辅助函数（与缓存相关）
# ==========================================

def generate_safe_hash_for_cache(text: str, key: str) -> str:
    """生成安全的哈希值，用于缓存键

    Args:
        text: 文本内容
        key: 额外的键（如操作类型）

    Returns:
        哈希字符串
    """
    text_hash = hashlib.sha256(str(text).encode()).hexdigest()[:20]
    key_hash = hashlib.sha256(str(key).encode()).hexdigest()[:10]
    return f"{text_hash}_{key_hash}"


def contains_annotation_marker(text: str) -> bool:
    """检测文本是否包含【】或[]形式的批注标记

    Args:
        text: 文本内容

    Returns:
        是否包含批注标记
    """
    return ('【' in text and '】' in text) or ('[' in text and ']' in text)


def extract_annotations_with_context(text: str) -> list:
    """提取文本中的所有批注及其所属句子

    Args:
        text: 文本内容

    Returns:
        批注列表，每个批注包含类型、句子、内容、位置等信息
    """
    annotations = []

    # 匹配格式：任何以句号、感叹号或问号结尾的文本，后面紧跟【】批注
    for match in re.finditer(r'([^。！？.!?]+[。！？.!?]+)【([^】]*)】', text):
        sentence = match.group(1)
        annotation_content = match.group(2)
        annotations.append({
            'type': '【】',
            'sentence': sentence,
            'content': annotation_content,
            'start': match.start(),
            'end': match.end(),
            'full_match': match.group(0)
        })

    # 同样处理方括号格式
    for match in re.finditer(r'([^。！？.!?]+[。！？.!?]+)\[([^\]]*)\]', text):
        sentence = match.group(1)
        annotation_content = match.group(2)
        annotations.append({
            'type': '[]',
            'sentence': sentence,
            'content': annotation_content,
            'start': match.start(),
            'end': match.end(),
            'full_match': match.group(0)
        })

    # 记录详细日志
    if annotations:
        logging.info(f"提取到 {len(annotations)} 个批注:")
        for i, anno in enumerate(annotations):
            logging.info(f"批注 {i+1}: 句子='{anno['sentence']}', 内容='{anno['content']}'")

    return annotations


# ==========================================
# AI聊天服务
# ==========================================

# 初始系统提示（隐形）
AI_SYSTEM_PROMPT = """你是一个在教育、科技、社会研究等领域的信息搜集专家。
我将和你探讨学术问题，你需要：
1. 提供准确、真实的信息
2. 标注信息源，确保信息可信
3. 保持专业、严谨的学术态度
4. 对于不确定的信息，明确说明不确定性
5. 以清晰、有条理的方式组织信息

请用中文回复，除非问题本身是英文的。
"""


def clean_markdown(text: str) -> str:
    """清理markdown符号，将粗体/斜体转换为HTML标签，移除其他标记"""
    if not text:
        return text

    import re

    # 第一步：处理列表标记 - 先于其他处理，因为列表标记可能包含其他格式
    lines = text.split('\n')
    processed_lines = []
    for line in lines:
        # 匹配无序列表标记 (-, *, +)
        unordered_match = re.match(r'^[\s]*([-*+])\s+(.*)', line)
        if unordered_match:
            # 处理列表项内部可能的格式
            list_content = unordered_match.group(2)
            # 临时标记，稍后处理内部格式
            processed_lines.append(f'• {list_content}')
            continue

        # 匹配有序列表标记 (1., 2., 等)
        ordered_match = re.match(r'^[\s]*(\d+)\.\s+(.*)', line)
        if ordered_match:
            list_content = ordered_match.group(2)
            # 临时标记，稍后处理内部格式
            processed_lines.append(f'{ordered_match.group(1)}. {list_content}')
            continue

        # 匹配任务列表标记 (- [x] 或 - [ ])
        task_match = re.match(r'^[\s]*[-*+]\s*\[(x| )\]\s+(.*)', line)
        if task_match:
            list_content = task_match.group(2)
            checkbox = '☑' if task_match.group(1) == 'x' else '☐'
            processed_lines.append(f'{checkbox} {list_content}')
            continue

        processed_lines.append(line)

    text = '\n'.join(processed_lines)

    # 第二步：转换粗体标记 (**text** 或 __text__) 为 <b>text</b>
    # 使用非贪婪匹配，避免跨行匹配
    text = re.sub(r'\*\*([^\*\n]+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__([^_\n]+?)__', r'<b>\1</b>', text)

    # 第三步：转换斜体标记 (*text* 或 _text_) 为 <i>text</i>
    # 注意：避免匹配乘号或星号用法
    # 使用更严格的匹配：前后有空白或标点的斜体
    text = re.sub(r'(^|\s|\()\*([^\*\n]+?)\*($|\s|\)|\.|,|;|:)', r'\1<i>\2</i>\3', text)
    text = re.sub(r'(^|\s|\()_([^_\n]+?)_($|\s|\)|\.|,|;|:)', r'\1<i>\2</i>\3', text)

    # 第四步：移除其他markdown标记
    # 移除标题标记 (# ## ###) - 只移除标记，保留文本
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # 移除代码块标记 (``` ```)
    text = re.sub(r'```[a-z]*\n', '', text)
    text = re.sub(r'```', '', text)

    # 移除行内代码标记 (`) - 只移除标记，保留文本
    text = re.sub(r'`([^`]+)`', r'\1', text)

    # 移除链接标记 ([text](url)) - 保留文本部分
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # 移除图片标记 (![alt](url)) - 保留alt文本
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)

    # 移除引用标记 (>) - 只移除标记，保留文本
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)

    # 第五步：清理残留的markdown符号
    # 再次处理可能漏掉的粗体和斜体（使用更宽松的匹配）
    # 处理**text**格式的粗体（可能包含换行）
    text = re.sub(r'\*\*([^\*]+?)\*\*', r'<b>\1</b>', text, flags=re.DOTALL)
    # 处理__text__格式的粗体
    text = re.sub(r'__([^_]+?)__', r'<b>\1</b>', text, flags=re.DOTALL)
    # 处理*text*格式的斜体
    text = re.sub(r'\*([^\*]+?)\*', r'<i>\1</i>', text, flags=re.DOTALL)
    # 处理_text_格式的斜体
    text = re.sub(r'_([^_]+?)_', r'<i>\1</i>', text, flags=re.DOTALL)

    # 第六步：移除所有残留的markdown符号
    # 移除可能残留的单个*、_、~、^等markdown符号
    # 但保留可能作为标点或特殊字符使用的符号
    # 1. 移除行首或行尾的单个markdown符号
    text = re.sub(r'^\s*[\*_~^`]\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s*[\*_~^`]\s*$', '', text, flags=re.MULTILINE)
    # 2. 移除被空白包围的单个markdown符号
    text = re.sub(r'\s+[\*_~^`]\s+', ' ', text)
    # 3. 移除连续的markdown符号（如 *** 或 ___）
    text = re.sub(r'[\*_~^`]{2,}', '', text)

    # 第六步：清理空白和格式
    # 合并多个空白
    text = re.sub(r'[ \t]+', ' ', text)
    # 合并多个换行
    text = re.sub(r'\n{3,}', '\n\n', text)
    # 移除不必要的缩进：移除所有行首空白（包括空格和制表符）
    # 但保留列表项的前缀（• 或 数字.）
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # 移除行首空白
        line = line.lstrip()
        cleaned_lines.append(line)
    text = '\n'.join(cleaned_lines)

    # 第七步：确保HTML标签正确闭合
    # 简单检查<b>和<i>标签配对
    # 这里不进行复杂的HTML解析，只是基本处理

    return text.strip()


def chat_with_gemini(messages: List[Dict[str, str]], api_key: Optional[str] = None) -> Dict[str, Any]:
    """与Gemini进行对话

    Args:
        messages: 消息列表，格式 [{"role": "user", "content": "..."}, ...]
        api_key: Gemini API密钥，如果为None则从环境变量获取

    Returns:
        包含结果的字典，格式：{"success": bool, "text": str, "model_used": str, "error": str}
    """
    # 构建包含系统提示的消息
    full_messages = [{"role": "system", "content": AI_SYSTEM_PROMPT}] + messages

    # 将消息格式化为适合Gemini的prompt
    prompt = ""
    for msg in full_messages:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            prompt += f"系统指令：{content}\n\n"
        elif role == "user":
            prompt += f"用户：{content}\n\n"
        elif role == "assistant":
            prompt += f"助手：{content}\n\n"

    prompt += "助手："

    # 使用现有generate_gemini_content_with_fallback函数
    result = generate_gemini_content_with_fallback(
        prompt=prompt,
        api_key=api_key,
        primary_model="gemini-3-pro-preview",
        fallback_model="gemini-2.5-pro"
    )

    # 清理AI回复中的markdown符号
    if result.get("success") and result.get("text"):
        result["text"] = clean_markdown(result["text"])

    return result