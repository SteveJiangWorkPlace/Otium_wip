"""
API服务模块

包含与外部API交互的服务函数，如Gemini和GPTZero。
"""

import ast
import hashlib
import json
import logging
import re
import time
from collections.abc import AsyncGenerator
from typing import Any, Callable, Dict, Optional

import google.genai
import google.genai.errors
import requests
from google.genai.types import HttpOptions

from exceptions import GeminiAPIError, RateLimitError
from utils import TextValidator
from prompts import build_literature_research_prompt

# ==========================================
# Gemini API 服务
# ==========================================


def generate_gemini_content_with_fallback(
    prompt: str,
    api_key: str | None = None,
    primary_model: str = "gemini-2.5-flash",  # 文本相关功能使用flash作为主要模型
    fallback_model: str = "gemini-2.5-pro",
) -> dict[str, Any]:
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
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    def _try_model(model_name: str) -> dict[str, Any]:
        max_retries = 3
        retry_delay = 2  # 秒

        for attempt in range(max_retries):
            try:
                # 使用传入的API密钥，如果为空则尝试从环境变量获取
                current_api_key = api_key
                key_source = "传入参数"

                if not current_api_key:
                    # 尝试从环境变量获取
                    from config import settings
                    current_api_key = settings.GEMINI_API_KEY
                    key_source = "环境变量"

                if not current_api_key:
                    raise GeminiAPIError("未提供 Gemini API Key，请在侧边栏输入或设置GEMINI_API_KEY环境变量", "missing_key")

                key_prefix = (
                    current_api_key[:8]
                    if len(current_api_key) > 8
                    else current_api_key[: len(current_api_key)]
                )
                logging.info(
                    f"_try_model: 开始尝试模型 {model_name}, 尝试 {attempt + 1}/{max_retries}, API密钥来源: {key_source}, 前缀: {key_prefix}..."
                )

                # 调试日志：记录API密钥信息（不记录完整密钥）
                key_prefix = (
                    current_api_key[:8]
                    if len(current_api_key) > 8
                    else current_api_key[: len(current_api_key)]
                )
                logging.info(f"使用{key_source}的Gemini API密钥，前缀: {key_prefix}...")
                logging.info(f"尝试使用模型: {model_name}")

                logging.info("使用系统代理设置连接")

                # 创建客户端
                # 设置timeout值（180000 = 180秒/3分钟读取超时）
                # timeout值除以1000得到实际的读取超时秒数
                http_opts = HttpOptions(timeout=180000)
                client = google.genai.Client(api_key=current_api_key, http_options=http_opts)

                # 准备配置（包括安全设置）
                config = {"safety_settings": safety_settings}

                # 生成内容
                logging.info(f"调用Gemini API: 模型={model_name}, prompt长度={len(prompt)}")
                response = client.models.generate_content(
                    model=model_name, contents=prompt, config=config
                )
                logging.info(f"Gemini API调用成功: 模型={model_name}")

                # 提取响应文本
                # 注意：response 结构可能不同，需要检查
                text = ""
                if hasattr(response, "text"):
                    text = response.text
                elif hasattr(response, "candidates") and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, "content") and candidate.content:
                        if hasattr(candidate.content, "parts") and candidate.content.parts:
                            text = candidate.content.parts[0].text
                        elif hasattr(candidate.content, "text"):
                            text = candidate.content.text

                return {"success": True, "text": text, "model_used": model_name}

            except Exception as e:
                # 获取原始错误消息
                error_raw = str(e)
                error_msg = error_raw.lower()
                logging.error(f"Gemini API异常原始错误: {error_raw}")
                logging.error(f"异常类型: {type(e).__name__}")

                # 尝试解析JSON或Python字典格式的错误信息
                error_json = None
                try:
                    # 尝试从错误消息中提取字典/JSON
                    # 查找可能的字典结构开始
                    json_start = error_raw.find("{")
                    if json_start != -1:
                        json_str = error_raw[json_start:]
                        # 首先尝试使用ast.literal_eval解析Python字典（支持单引号）
                        try:
                            error_json = ast.literal_eval(json_str)
                        except Exception:
                            # 如果失败，尝试json.loads（需要双引号）
                            # 将单引号替换为双引号
                            json_str_fixed = json_str.replace("'", '"')
                            error_json = json.loads(json_str_fixed)
                except Exception:
                    pass  # 如果解析失败，继续使用原始错误消息

                # 服务不可用错误
                if (
                    "service unavailable" in error_msg
                    or "503" in error_msg
                    or "unavailable" in error_msg
                ):
                    logging.error(f"模型 {model_name} - 服务不可用: {str(e)}")
                    raise GeminiAPIError(
                        "Google API服务暂时不可用，请稍后再试", "service_unavailable"
                    ) from e

                # 超时错误（包括 DeadlineExceeded 和 requests Timeout）
                elif "timeout" in error_msg or "deadline" in error_msg or "timed out" in error_msg:
                    logging.error(
                        f"模型 {model_name} - 请求超时 (尝试 {attempt + 1}/{max_retries}): {str(e)}"
                    )
                    if attempt < max_retries - 1:
                        logging.info(f"等待 {retry_delay} 秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    raise GeminiAPIError(
                        "请求超时（默认180秒/3分钟），请检查网络连接", "timeout"
                    ) from e

                # 网络连接错误
                elif (
                    "connect" in error_msg
                    or "socket" in error_msg
                    or "network" in error_msg
                    or "connection" in error_msg
                ):
                    logging.error(
                        f"模型 {model_name} - 网络连接错误 (尝试 {attempt + 1}/{max_retries}): {str(e)}"
                    )
                    if attempt < max_retries - 1:
                        logging.info(f"等待 {retry_delay} 秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    error_message = "无法连接到Google API服务。"
                    error_message += "\n可能的原因："
                    error_message += "\n1. 网络连接问题 - 请检查您的互联网连接"
                    error_message += (
                        "\n2. 防火墙或网络设置 - 如果您在中国，可能需要VPN才能访问Google服务"
                    )
                    error_message += "\n3. Google服务暂时不可用 - 请稍后再试"
                    error_message += "\n\n解决方案："
                    error_message += "\n- 检查网络连接是否正常"
                    error_message += "\n- 如果使用VPN，请确保VPN连接稳定"
                    raise GeminiAPIError(error_message, "network_error") from e

                # API配额错误
                elif "quota" in error_msg or "resource_exhausted" in error_msg:
                    logging.error(f"模型 {model_name} - API 配额已用尽: {str(e)}")
                    raise GeminiAPIError("API 配额已用尽，请稍后再试", "quota") from e

                # 速率限制
                elif (
                    "429" in error_msg
                    or "rate_limit" in error_msg
                    or "too many requests" in error_msg
                ):
                    logging.error(f"模型 {model_name} - 速率限制: {str(e)}")
                    raise RateLimitError("请求过于频繁，请稍后再试") from e

                # API密钥无效
                elif (
                    "invalid" in error_msg
                    or "api_key" in error_msg
                    or "permission" in error_msg
                    or "unauthorized" in error_msg
                ):
                    logging.error(f"模型 {model_name} - API Key 无效: {str(e)}")
                    # 记录完整的错误类型和详细信息用于调试
                    logging.error(f"完整错误类型: {type(e)}")
                    logging.error(f"完整错误详细信息: {repr(e)}")
                    if error_json:
                        logging.error(f"解析后的错误JSON: {error_json}")
                    raise GeminiAPIError("API Key 无效或已过期，请检查配置", "invalid_key") from e

                # 区域限制错误
                elif (
                    (
                        error_json
                        and (
                            error_json.get("error", {}).get("status") == "FAILED_PRECONDITION"
                            or "user location is not supported" in str(error_json).lower()
                            or "location is not supported" in str(error_json).lower()
                        )
                    )
                    or "failed_precondition" in error_msg
                    or "user location is not supported" in error_msg
                    or "location is not supported" in error_msg
                ):
                    logging.error(f"模型 {model_name} - 区域限制: {str(e)}")
                    error_message = "Google Gemini API 在您所在的区域不可用。\n"
                    error_message += "可能的原因：\n"
                    error_message += "1. 您所在的地区（如中国大陆）可能无法直接访问Google服务\n"
                    error_message += "2. 网络环境限制\n\n"
                    error_message += "解决方案：\n"
                    error_message += "- 使用VPN连接到支持Google服务的地区\n"
                    error_message += "- 检查网络连接和代理设置\n"
                    error_message += "- 联系网络管理员确认是否允许访问Google API"
                    raise GeminiAPIError(error_message, "region_restricted") from e

                # 其他API错误
                elif "api" in error_msg or "google" in error_msg or "genai" in error_msg:
                    logging.error(f"模型 {model_name} - API 错误: {str(e)}")
                    raise GeminiAPIError(f"API 错误: {str(e)}", "api_error") from e

                # 未知错误
                else:
                    logging.error(f"模型 {model_name} - 未知错误: {str(e)}", exc_info=True)
                    raise GeminiAPIError(f"未知错误: {str(e)}", "unknown") from e

        # 如果所有重试都失败（理论上不应该到达这里）
        raise GeminiAPIError(f"所有 {max_retries} 次重试均失败", "all_retries_failed")

    # 尝试主要模型
    try:
        return _try_model(primary_model)

    except GeminiAPIError as e:
        logging.warning(f"主要模型 {primary_model} 失败，错误类型: {e.error_type}")

        # 如果是网络连接错误，直接尝试requests备选方案，而不是备用模型
        if e.error_type == "network_error":
            logging.warning("网络连接错误，直接尝试requests备选方案...")
            try:
                result = generate_gemini_with_requests(
                    prompt=prompt, api_key=api_key, model=primary_model
                )
                if result.get("success"):
                    logging.info(f"requests备选方案成功: 模型={primary_model}")
                    return result
                else:
                    # 主要模型失败，尝试备用模型
                    logging.warning(f"requests主要模型失败，尝试备用模型: {fallback_model}")
                    result = generate_gemini_with_requests(
                        prompt=prompt, api_key=api_key, model=fallback_model
                    )
                    return result
            except Exception as requests_exception:
                logging.error(f"requests备选方案也失败: {str(requests_exception)}", exc_info=True)
                return {
                    "success": False,
                    "error": f"所有尝试均失败: {e.message}",
                    "error_type": e.error_type,
                }

        # 如果不是网络错误，尝试备用模型
        logging.warning(f"尝试备用模型 {fallback_model}")
        try:
            return _try_model(fallback_model)
        except GeminiAPIError as fallback_error:
            logging.warning(
                f"备用模型也失败，错误类型: {fallback_error.error_type}, 尝试requests备选方案..."
            )

            # 尝试使用requests备选方案
            try:
                # 先尝试主要模型
                result = generate_gemini_with_requests(
                    prompt=prompt, api_key=api_key, model=primary_model
                )

                if result.get("success"):
                    logging.info(f"requests备选方案成功: 模型={primary_model}")
                    return result
                else:
                    # 主要模型失败，尝试备用模型
                    logging.warning(f"requests主要模型失败，尝试备用模型: {fallback_model}")
                    result = generate_gemini_with_requests(
                        prompt=prompt, api_key=api_key, model=fallback_model
                    )
                    return result

            except Exception as requests_exception:
                logging.error(f"requests备选方案也失败: {str(requests_exception)}", exc_info=True)
                return {
                    "success": False,
                    "error": f"所有尝试均失败: {fallback_error.message}",
                    "error_type": fallback_error.error_type,
                }
        except Exception as fallback_error:
            logging.error(f"备用模型也失败: {str(fallback_error)}", exc_info=True)
            logging.warning("尝试requests备选方案...")

            # 尝试使用requests备选方案
            try:
                # 先尝试主要模型
                result = generate_gemini_with_requests(
                    prompt=prompt, api_key=api_key, model=primary_model
                )

                if result.get("success"):
                    logging.info(f"requests备选方案成功: 模型={primary_model}")
                    return result
                else:
                    # 主要模型失败，尝试备用模型
                    logging.warning(f"requests主要模型失败，尝试备用模型: {fallback_model}")
                    result = generate_gemini_with_requests(
                        prompt=prompt, api_key=api_key, model=fallback_model
                    )
                    return result

            except Exception as requests_exception:
                logging.error(f"requests备选方案也失败: {str(requests_exception)}", exc_info=True)
                return {
                    "success": False,
                    "error": "所有尝试均失败，请稍后再试",
                    "error_type": "all_failed",
                }

    except RateLimitError as e:
        logging.warning("速率限制错误，尝试requests备选方案...")

        # 尝试使用requests备选方案
        try:
            # 先尝试主要模型
            result = generate_gemini_with_requests(
                prompt=prompt, api_key=api_key, model=primary_model
            )

            if result.get("success"):
                logging.info(f"requests备选方案成功: 模型={primary_model}")
                return result
            else:
                # 主要模型失败，尝试备用模型
                logging.warning(f"requests主要模型失败，尝试备用模型: {fallback_model}")
                result = generate_gemini_with_requests(
                    prompt=prompt, api_key=api_key, model=fallback_model
                )
                return result

        except Exception as requests_exception:
            logging.error(f"requests备选方案也失败: {str(requests_exception)}", exc_info=True)
            return {"success": False, "error": str(e), "error_type": "rate_limit"}

    except Exception as e:
        logging.error(f"未知错误: {str(e)}", exc_info=True)

        # 当google.genai库失败时，尝试使用requests备选方案
        logging.warning("google.genai库调用失败，尝试使用requests备选方案...")

        try:
            # 先尝试主要模型
            result = generate_gemini_with_requests(
                prompt=prompt, api_key=api_key, model=primary_model
            )

            if result.get("success"):
                logging.info(f"requests备选方案成功: 模型={primary_model}")
                return result
            else:
                # 主要模型失败，尝试备用模型
                logging.warning(f"requests主要模型失败，尝试备用模型: {fallback_model}")
                result = generate_gemini_with_requests(
                    prompt=prompt, api_key=api_key, model=fallback_model
                )
                return result

        except Exception as fallback_exception:
            logging.error(f"requests备选方案也失败: {str(fallback_exception)}", exc_info=True)
            return {
                "success": False,
                "error": f"所有尝试均失败: {str(e)}",
                "error_type": "all_failed",
            }


# ==========================================
# 流式翻译服务
# ==========================================


def split_into_sentences(text: str) -> list[str]:
    """将文本分割成句子

    Args:
        text: 输入文本

    Returns:
        句子列表
    """
    import re

    # 使用中文和英文标点分割句子
    # 匹配中文标点：。！？和英文标点：. ! ?
    # 保留分割符号在句子中
    sentences = re.split(r"(?<=[。！？.!?])\s*", text.strip())

    # 过滤空句子
    sentences = [s.strip() for s in sentences if s.strip()]

    return sentences


async def generate_gemini_content_stream(
    prompt: str,
    api_key: str | None = None,
    primary_model: str = "gemini-2.5-flash",
    fallback_model: str | None = "gemini-2.5-pro",
) -> AsyncGenerator[dict[str, Any], None]:
    """流式生成 Gemini 内容，支持主备模型切换

    Args:
        prompt: 提示词文本
        api_key: Gemini API密钥，如果为None则使用环境变量
        primary_model: 主要模型名称
        fallback_model: 备用模型名称，如果为None则不使用备用模型

    Yields:
        包含流式结果的字典，格式：{"type": "chunk"|"sentence"|"complete", "text": str, "index": int, "total": int, "error": str}
    """

    logging.info(
        f"开始流式翻译，主模型: {primary_model}, 备用模型: {fallback_model}, prompt长度: {len(prompt)}"
    )

    # 安全设置
    safety_settings = [
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    try:
        # 检查API密钥
        current_api_key = api_key
        if not current_api_key:
            raise GeminiAPIError("未提供 Gemini API Key，请在侧边栏输入", "missing_key")

        # 创建客户端
        # 设置timeout值（180000 = 180秒/3分钟读取超时）
        # timeout值除以1000得到实际的读取超时秒数
        http_opts = HttpOptions(timeout=180000)
        client = google.genai.Client(api_key=current_api_key, http_options=http_opts)

        # 准备配置
        config = {"safety_settings": safety_settings}

        # 尝试主模型
        current_model = primary_model
        models_tried = []

        # 尝试使用主模型
        try:
            logging.info(f"调用Gemini流式API: 模型={current_model}")
            response_stream = client.models.generate_content_stream(
                model=current_model, contents=prompt, config=config
            )
            models_tried.append(current_model)
        except Exception as primary_error:
            logging.warning(f"主模型 {primary_model} 调用失败: {str(primary_error)}")

            # 检查是否有备用模型
            if fallback_model and fallback_model != primary_model:
                logging.info(f"尝试切换到备用模型: {fallback_model}")
                current_model = fallback_model
                try:
                    response_stream = client.models.generate_content_stream(
                        model=current_model, contents=prompt, config=config
                    )
                    models_tried.append(current_model)
                    logging.info(f"备用模型 {fallback_model} 调用成功")
                except Exception as fallback_error:
                    logging.error(f"备用模型 {fallback_model} 也调用失败: {str(fallback_error)}")
                    # 重新抛出主模型的错误，让外部异常处理处理
                    raise primary_error from fallback_error
            else:
                # 没有备用模型或备用模型与主模型相同，直接抛出错误
                raise primary_error

        # 流式处理缓冲区
        full_response = ""
        buffer = ""
        sentences: list[str] = []
        sentence_index = 0

        # 用于检测句子边界的正则表达式
        # 匹配中文标点：。！？和英文标点：. ! ?
        import re

        sentence_end_pattern = re.compile(r"[。！？.!?]")

        # 处理流式响应
        start_time = time.time()
        timeout_seconds = 180  # 与前端超时保持一致（3分钟）
        chunk_count = 0
        stream_end_reason = "natural_completion"

        for chunk in response_stream:
            # 超时检查
            chunk_count += 1
            if time.time() - start_time > timeout_seconds:
                stream_end_reason = "timeout"
                logging.error(
                    f"流式翻译超时: {timeout_seconds}秒内未完成, "
                    f"已处理{chunk_count}个chunk, 已生成{len(sentences)}个句子"
                )
                yield {
                    "type": "error",
                    "error": f"流式翻译超时: {timeout_seconds}秒内未完成",
                    "error_type": "timeout",
                }
                return  # 流式翻译超时，结束生成器
            if hasattr(chunk, "text"):
                chunk_text = chunk.text
            elif hasattr(chunk, "candidates") and chunk.candidates:
                candidate = chunk.candidates[0]
                if hasattr(candidate, "content") and candidate.content:
                    if hasattr(candidate.content, "parts") and candidate.content.parts:
                        chunk_text = candidate.content.parts[0].text
                    elif hasattr(candidate.content, "text"):
                        chunk_text = candidate.content.text
                else:
                    chunk_text = ""
            else:
                chunk_text = ""

            if chunk_text:
                full_response += chunk_text
                buffer += chunk_text

                # 返回块级数据
                yield {
                    "type": "chunk",
                    "text": chunk_text,
                    "full_text": full_response,
                    "chunk_index": len(full_response) - len(chunk_text),
                }

                # 检测缓冲区中是否有完整的句子
                # 添加循环安全机制，防止无限循环
                max_iterations = len(buffer) * 2  # 安全上限
                iteration_count = 0

                while True:
                    iteration_count += 1
                    if iteration_count > max_iterations:
                        logging.warning(
                            f"句子检测循环超过安全上限({max_iterations})，强制退出。"
                            f"buffer长度: {len(buffer)}, 内容前50字符: {repr(buffer[:50])}"
                        )
                        break

                    # 查找句子结束位置
                    match = sentence_end_pattern.search(buffer)
                    if not match:
                        break

                    # 找到句子结束位置
                    end_pos = match.end()
                    # 提取句子（包括结束标点）
                    sentence = buffer[:end_pos].strip()
                    if sentence:
                        sentences.append(sentence)

                        # 返回句子级数据
                        yield {
                            "type": "sentence",
                            "text": sentence,
                            "index": sentence_index,
                            "total": sentence_index + 1,  # 暂时设置为当前句子数，最终会更新
                            "full_text": full_response,
                        }
                        sentence_index += 1

                        # 从缓冲区中移除已处理的句子
                        buffer = buffer[end_pos:].lstrip()
                    else:
                        # 如果没有有效句子内容，移动位置
                        buffer = buffer[end_pos:].lstrip()

        # 处理缓冲区中剩余的内容（可能是一个不完整的句子）
        if buffer.strip():
            # 将剩余内容作为一个句子
            sentences.append(buffer.strip())
            yield {
                "type": "sentence",
                "text": buffer.strip(),
                "index": sentence_index,
                "total": sentence_index + 1,
                "full_text": full_response,
            }
            sentence_index += 1

        # 更新所有已发送句子的总数
        # 重新发送更新后的句子信息（可选，但前端可能不需要）
        # 或者直接发送完成信号
        logging.info(f"翻译完成，共 {len(sentences)} 个句子")
        logging.info(
            "translate_stream_summary: reason=%s, chunks=%s, chars=%s, sentences=%s, elapsed=%.2fs",
            stream_end_reason,
            chunk_count,
            len(full_response),
            len(sentences),
            time.time() - start_time,
        )

        # 返回完成信号
        yield {
            "type": "complete",
            "text": full_response,
            "total_sentences": len(sentences),
            "model_used": current_model,
            "models_tried": models_tried,
        }

    except Exception as e:
        logging.error(f"流式翻译错误: {str(e)}", exc_info=True)

        # 尝试获取错误类型
        error_msg = str(e).lower()

        if "service unavailable" in error_msg or "503" in error_msg:
            error_type = "service_unavailable"
            error_message = "Google API服务暂时不可用，请稍后再试"
        elif "timeout" in error_msg or "deadline" in error_msg:
            error_type = "timeout"
            error_message = "请求超时，请检查网络连接"
        elif "network" in error_msg or "connection" in error_msg:
            error_type = "network_error"
            error_message = "无法连接到Google API服务，请检查网络连接"
        elif "quota" in error_msg or "resource_exhausted" in error_msg:
            error_type = "quota"
            error_message = "API 配额已用尽，请稍后再试"
        elif "429" in error_msg or "rate_limit" in error_msg:
            error_type = "rate_limit"
            error_message = "请求过于频繁，请稍后再试"
        elif "invalid" in error_msg or "api_key" in error_msg or "permission" in error_msg:
            error_type = "invalid_key"
            error_message = "API Key 无效或已过期，请检查配置"
        else:
            error_type = "unknown"
            error_message = f"系统错误: {str(e)}"

        yield {"type": "error", "error": error_message, "error_type": error_type}


# ==========================================
# GPTZero API 服务
# ==========================================


def check_gptzero(text: str, api_key: str) -> dict[str, Any]:
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
            text = text[: TextValidator.GPTZERO_MAX_CHARS]
            logging.warning("文本已截断至GPTZero API限制")
        else:
            return {"success": False, "message": message}

    url = "https://api.gptzero.me/v2/predict/text"
    headers = {
        "x-api-key": api_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    payload = {"document": text}

    max_retries = 3
    retry_count = 0
    current_delay = 2

    while retry_count < max_retries:
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=180)
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
                    "message": "",
                    "detailed_scores": doc.get("sentences", []),
                    "full_text": text,
                }
            else:
                return {"success": False, "message": "API返回了未知格式的数据"}

        except requests.exceptions.Timeout:
            retry_count += 1
            if retry_count >= max_retries:
                logging.error("GPTZero API请求超时，已达到最大重试次数")
                return {"success": False, "message": "检测请求超时，请稍后再试"}
            logging.warning(
                f"GPTZero API超时，{current_delay}秒后重试 ({retry_count}/{max_retries})"
            )
            time.sleep(current_delay)
            current_delay *= 2

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            if status_code == 401:
                return {"success": False, "message": "API Key 无效或已过期"}
            elif status_code == 429:
                return {"success": False, "message": "请求过于频繁，请稍后再试"}
            else:
                return {
                    "success": False,
                    "message": f"API 请求失败（状态码 {status_code}）",
                }

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
    return ("【" in text and "】" in text) or ("[" in text and "]" in text)


def extract_annotations_with_context(text: str) -> list:
    """提取文本中的所有批注及其所属句子

    Args:
        text: 文本内容

    Returns:
        批注列表，每个批注包含类型、句子、内容、位置等信息
    """
    annotations = []

    # 匹配格式：任何以句号、感叹号或问号结尾的文本，后面紧跟【】批注
    for match in re.finditer(r"([^。！？.!?]+[。！？.!?]+)【([^】]*)】", text):
        sentence = match.group(1)
        annotation_content = match.group(2)
        annotations.append(
            {
                "type": "【】",
                "sentence": sentence,
                "content": annotation_content,
                "start": match.start(),
                "end": match.end(),
                "full_match": match.group(0),
            }
        )

    # 同样处理方括号格式
    for match in re.finditer(r"([^。！？.!?]+[。！？.!?]+)\[([^\]]*)\]", text):
        sentence = match.group(1)
        annotation_content = match.group(2)
        annotations.append(
            {
                "type": "[]",
                "sentence": sentence,
                "content": annotation_content,
                "start": match.start(),
                "end": match.end(),
                "full_match": match.group(0),
            }
        )

    # 记录详细日志
    if annotations:
        logging.info(f"提取到 {len(annotations)} 个批注:")
        for i, anno in enumerate(annotations):
            logging.info(f"批注 {i + 1}: 句子='{anno['sentence']}', 内容='{anno['content']}'")

    return annotations


# ==========================================
# AI聊天服务
# ==========================================

# 初始系统提示（隐形）
AI_SYSTEM_PROMPT = """你是一个在教育、科技、社会研究、电影、传媒等领域的信息搜集专家。
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

    # 调试：检查输入文本中是否包含Unicode字符
    import logging

    non_ascii_count = sum(1 for c in text if ord(c) > 127)
    if non_ascii_count > 0:
        logging.info(
            f"clean_markdown: 输入文本包含 {non_ascii_count} 个非ASCII字符，长度: {len(text)}"
        )
        # 查找具体的Unicode字符（只记录前3个）
        found = 0
        for i, c in enumerate(text[:500]):  # 只检查前500个字符
            if ord(c) > 127:
                logging.info(f"clean_markdown: 位置 {i}: U+{ord(c):04X}")
                found += 1
                if found >= 3:
                    break

    import re

    # 第一步：处理列表标记 - 先于其他处理，因为列表标记可能包含其他格式
    lines = text.split("\n")
    processed_lines = []
    for line in lines:
        # 匹配无序列表标记 (-, *, +)
        unordered_match = re.match(r"^[\s]*([-*+])\s+(.*)", line)
        if unordered_match:
            # 处理列表项内部可能的格式
            list_content = unordered_match.group(2)
            # 临时标记，稍后处理内部格式
            processed_lines.append(f"- {list_content}")
            continue

        # 匹配有序列表标记 (1., 2., 等)
        ordered_match = re.match(r"^[\s]*(\d+)\.\s+(.*)", line)
        if ordered_match:
            list_content = ordered_match.group(2)
            # 临时标记，稍后处理内部格式
            processed_lines.append(f"{ordered_match.group(1)}. {list_content}")
            continue

        # 匹配任务列表标记 (- [x] 或 - [ ])
        task_match = re.match(r"^[\s]*[-*+]\s*\[(x| )\]\s+(.*)", line)
        if task_match:
            list_content = task_match.group(2)
            checkbox = "[x]" if task_match.group(1) == "x" else "[ ]"
            processed_lines.append(f"{checkbox} {list_content}")
            continue

        processed_lines.append(line)

    text = "\n".join(processed_lines)

    # 第二步：转换粗体标记 (**text** 或 __text__) 为 <b>text</b>
    # 使用非贪婪匹配，避免跨行匹配
    text = re.sub(r"\*\*([^\*\n]+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__([^_\n]+?)__", r"<b>\1</b>", text)

    # 第三步：转换斜体标记 (*text* 或 _text_) 为 <i>text</i>
    # 注意：避免匹配乘号或星号用法
    # 使用更严格的匹配：前后有空白或标点的斜体
    text = re.sub(r"(^|\s|\()\*([^\*\n]+?)\*($|\s|\)|\.|,|;|:)", r"\1<i>\2</i>\3", text)
    text = re.sub(r"(^|\s|\()_([^_\n]+?)_($|\s|\)|\.|,|;|:)", r"\1<i>\2</i>\3", text)

    # 第四步：移除其他markdown标记
    # 移除标题标记 (# ## ###) - 只移除标记，保留文本
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

    # 移除代码块标记 (``` ```)
    text = re.sub(r"```[a-z]*\n", "", text)
    text = re.sub(r"```", "", text)

    # 移除行内代码标记 (`) - 只移除标记，保留文本
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # 移除链接标记 ([text](url)) - 保留文本部分
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # 移除图片标记 (![alt](url)) - 保留alt文本
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)

    # 移除引用标记 (>) - 只移除标记，保留文本
    text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)

    # 第五步：清理残留的markdown符号
    # 再次处理可能漏掉的粗体和斜体（使用更宽松的匹配）
    # 处理**text**格式的粗体（可能包含换行）
    text = re.sub(r"\*\*([^\*]+?)\*\*", r"<b>\1</b>", text, flags=re.DOTALL)
    # 处理__text__格式的粗体
    text = re.sub(r"__([^_]+?)__", r"<b>\1</b>", text, flags=re.DOTALL)
    # 处理*text*格式的斜体
    text = re.sub(r"\*([^\*]+?)\*", r"<i>\1</i>", text, flags=re.DOTALL)
    # 处理_text_格式的斜体
    text = re.sub(r"_([^_]+?)_", r"<i>\1</i>", text, flags=re.DOTALL)

    # 第六步：移除所有残留的markdown符号
    # 移除可能残留的单个*、_、~、^等markdown符号
    # 但保留可能作为标点或特殊字符使用的符号
    # 1. 移除行首或行尾的单个markdown符号
    text = re.sub(r"^\s*[\*_~^`]\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*[\*_~^`]\s*$", "", text, flags=re.MULTILINE)
    # 2. 移除被空白包围的单个markdown符号
    text = re.sub(r"\s+[\*_~^`]\s+", " ", text)
    # 3. 移除连续的markdown符号（如 *** 或 ___）
    text = re.sub(r"[\*_~^`]{2,}", "", text)

    # 第六步：清理空白和格式
    # 合并多个空白
    text = re.sub(r"[ \t]+", " ", text)
    # 合并多个换行
    text = re.sub(r"\n{3,}", "\n\n", text)
    # 移除不必要的缩进：移除所有行首空白（包括空格和制表符）
    # 但保留列表项的前缀（- 或 数字.）
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        # 移除行首空白
        line = line.lstrip()
        cleaned_lines.append(line)
    text = "\n".join(cleaned_lines)

    # 第七步：移除表情符号和其他Unicode字符，避免GBK编码问题
    # 移除常见的表情符号范围
    emoji_pattern = re.compile(
        "["
        "\U0001f600-\U0001f64f"  # 表情符号
        "\U0001f300-\U0001f5ff"  # 符号和象形文字
        "\U0001f680-\U0001f6ff"  # 交通和地图符号
        "\U0001f700-\U0001f77f"  # 字母符号
        "\U0001f780-\U0001f7ff"  # 几何图形扩展
        "\U0001f800-\U0001f8ff"  # 补充箭头-C
        "\U0001f900-\U0001f9ff"  # 补充符号和象形文字
        "\U0001fa00-\U0001fa6f"  # 棋类符号
        "\U0001fa70-\U0001faff"  # 符号和象形文字扩展-A
        "\U00002702-\U000027b0"  # 杂项符号
        "\U000024c2-\U0001f251"  # 封闭字符
        "]",
        flags=re.UNICODE,
    )
    text = emoji_pattern.sub("", text)

    # 第八步：确保HTML标签正确闭合
    # 简单检查<b>和<i>标签配对
    # 这里不进行复杂的HTML解析，只是基本处理

    # 第九步：确保文本是GBK兼容的，避免Windows控制台编码错误
    # 移除所有GBK无法编码的字符
    try:
        # 尝试将文本编码为GBK，忽略无法编码的字符
        text = text.encode("gbk", errors="ignore").decode("gbk")
    except (UnicodeEncodeError, UnicodeDecodeError):
        # 如果GBK编解码失败，回退到ASCII
        text = text.encode("ascii", errors="ignore").decode("ascii")

    return text.strip()


def convert_urls_to_markdown(text: str) -> str:
    """将纯文本中的URL转换为Markdown链接格式

    Args:
        text: 包含URL的纯文本

    Returns:
        转换后的文本，URL被转换为[标题](URL)格式
    """
    import re

    if not text:
        return text

    # 常见的URL模式
    # 匹配http/https/ftp协议，包括常见的学术网站
    url_pattern = re.compile(
        r'(https?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+|'  # 基础URL
        r'https?://(?:www\.)?arxiv\.org/[^\s]+|'  # arXiv
        r'https?://(?:www\.)?doi\.org/[^\s]+|'  # DOI
        r'https?://(?:www\.)?ncbi\.nlm\.nih\.gov/[^\s]+|'  # PubMed/NCBI
        r'https?://(?:www\.)?ieee\.org/[^\s]+|'  # IEEE
        r'https?://(?:www\.)?acm\.org/[^\s]+|'  # ACM
        r'https?://(?:www\.)?springer\.com/[^\s]+|'  # Springer
        r'https?://(?:www\.)?elsevier\.com/[^\s]+|'  # Elsevier
        r'https?://(?:www\.)?wiley\.com/[^\s]+|'  # Wiley
        r'https?://(?:www\.)?tandfonline\.com/[^\s]+|'  # Taylor & Francis
        r'https?://(?:www\.)?sciencedirect\.com/[^\s]+|'  # ScienceDirect
        r'https?://(?:www\.)?researchgate\.net/[^\s]+|'  # ResearchGate
        r'https?://(?:www\.)?scholar\.google\.com/[^\s]+|'  # Google Scholar
        r'https?://(?:www\.)?semanticscholar\.org/[^\s]+)'  # Semantic Scholar
    )

    def replace_url(match):
        """替换URL为Markdown链接格式的回调函数

        Args:
            match: re.Match对象，包含匹配的URL

        Returns:
            str: Markdown格式的链接 [标题](URL)
        """
        url = match.group(0)
        # 移除末尾的标点符号（句号、逗号、括号等）
        while url and url[-1] in '.,;:!?)\'"<>':
            url = url[:-1]

        # 尝试从URL中提取有意义的标题
        title = url

        # 如果是arXiv链接，尝试提取论文ID
        if 'arxiv.org' in url:
            # 匹配arXiv ID格式：arXiv:YYMM.NNNNN 或 arXiv:YYMM.NNNNNvN
            arxiv_match = re.search(r'arxiv\.org/(?:abs/|pdf/)?(\d+\.\d+(?:v\d+)?)', url, re.IGNORECASE)
            if arxiv_match:
                title = f"arXiv:{arxiv_match.group(1)}"

        # 如果是DOI链接
        elif 'doi.org' in url:
            doi_match = re.search(r'doi\.org/(.+)', url)
            if doi_match:
                title = f"DOI:{doi_match.group(1)[:50]}"

        # 如果是PubMed链接
        elif 'pubmed.ncbi.nlm.nih.gov' in url:
            pm_match = re.search(r'pubmed\.ncbi\.nlm\.nih\.gov/(\d+)', url)
            if pm_match:
                title = f"PubMed ID:{pm_match.group(1)}"

        # 如果是其他学术链接，尝试提取最后一部分作为标题
        else:
            # 移除协议和域名部分
            clean_url = re.sub(r'^https?://(?:www\.)?', '', url)
            # 取最后一部分，最多40个字符
            parts = clean_url.split('/')
            if len(parts) > 1:
                last_part = parts[-1]
                # 移除查询参数
                last_part = last_part.split('?')[0]
                # 解码URL编码字符
                import urllib.parse
                last_part = urllib.parse.unquote(last_part)
                if len(last_part) > 40:
                    title = f"...{last_part[-40:]}"
                else:
                    title = last_part if last_part else clean_url[:50]
            else:
                title = clean_url[:50]

        # 返回Markdown格式链接
        return f"[{title}]({url})"

    # 查找所有URL并替换
    def process_text_segment(segment):
        """处理文本片段，将URL转换为Markdown链接

        Args:
            segment (str): 文本片段

        Returns:
            str: 处理后的文本片段
        """
        # 如果已经是Markdown链接格式，跳过
        if re.search(r'\[.*?\]\(https?://[^)]+\)', segment):
            return segment

        # 替换URL
        return url_pattern.sub(replace_url, segment)

    # 分割文本为段落，避免在HTML标签或已有Markdown中替换
    lines = text.split('\n')
    processed_lines = []

    for line in lines:
        # 分割行，避免在代码块或特殊格式中替换
        # 简单实现：直接处理整行
        processed_lines.append(process_text_segment(line))

    return '\n'.join(processed_lines)


def normalize_paragraph_spacing(text: str, max_empty_lines: int = 1) -> str:
    """规范化段落间距，确保不超过指定数量的空行

    Args:
        text: 输入文本
        max_empty_lines: 允许的最大连续空行数（默认1）

    Returns:
        处理后的文本
    """
    import re

    if not text:
        return text

    # 分割为行
    lines = text.split('\n')
    processed_lines = []
    empty_count = 0

    for line in lines:
        if line.strip() == '':
            empty_count += 1
            if empty_count <= max_empty_lines:
                processed_lines.append(line)
        else:
            empty_count = 0
            processed_lines.append(line)

    return '\n'.join(processed_lines)


def generate_gemini_with_requests(
    prompt: str,
    api_key: str | None = None,
    model: str = "gemini-2.5-flash",
) -> dict[str, Any]:
    """使用requests库直接调用Gemini API（备选方案）

    Args:
        prompt: 提示词文本
        api_key: Gemini API密钥，如果为None则使用环境变量
        model: 模型名称

    Returns:
        包含结果的字典，格式：{"success": bool, "text": str, "model_used": str, "error": str, "error_type": str}
    """
    try:
        # 获取API密钥
        current_api_key = api_key
        if not current_api_key:
            from config import settings

            current_api_key = settings.GEMINI_API_KEY

        if not current_api_key:
            return {
                "success": False,
                "text": "",
                "model_used": model,
                "error": "未提供 Gemini API Key",
                "error_type": "missing_key",
            }

        logging.info("使用系统代理设置连接")

        # Gemini API端点
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={current_api_key}"

        # 请求头
        headers = {"Content-Type": "application/json"}

        # 请求体
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE",
                },
            ],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 1,
                "topP": 1,
                "maxOutputTokens": 8192,  # 增加最大输出token数
            },
        }

        logging.info(f"使用requests调用Gemini API: 模型={model}, prompt长度={len(prompt)}")
        response = requests.post(url, headers=headers, json=payload, timeout=180)

        if response.status_code == 200:
            result = response.json()
            if "candidates" in result and result["candidates"]:
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                logging.info(f"requests调用Gemini API成功: 模型={model}, 响应长度={len(text)}")
                return {
                    "success": True,
                    "text": text,
                    "model_used": model,
                    "error": "",
                    "error_type": "",
                }
            else:
                error_msg = f"响应格式异常: {result}"
                logging.error(error_msg)
                return {
                    "success": False,
                    "text": "",
                    "model_used": model,
                    "error": error_msg,
                    "error_type": "api_error",
                }
        else:
            error_msg = f"API错误: {response.status_code} - {repr(response.text[:200])}"
            logging.error(error_msg)
            return {
                "success": False,
                "text": "",
                "model_used": model,
                "error": error_msg,
                "error_type": "api_error",
            }

    except requests.exceptions.Timeout:
        error_msg = "请求超时 (300秒)"
        logging.error(error_msg)
        return {
            "success": False,
            "text": "",
            "model_used": model,
            "error": error_msg,
            "error_type": "timeout",
        }

    except Exception as e:
        error_msg = f"请求异常: {type(e).__name__}: {str(e)}"
        logging.error(error_msg, exc_info=True)
        return {
            "success": False,
            "text": "",
            "model_used": model,
            "error": error_msg,
            "error_type": "unknown",
        }


def chat_with_gemini(messages: list[dict[str, str]], api_key: str | None = None) -> dict[str, Any]:
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
        primary_model="gemini-2.5-flash",
        fallback_model="gemini-2.5-pro",
    )

    # 注意：不再清理AI回复中的markdown符号，由前端统一处理格式
    # 保留原始markdown格式，让前端cleanMarkdown函数处理
    # if result.get("success") and result.get("text"):
    #     result["text"] = clean_markdown(result["text"])

    return result


def chat_with_manus(
    prompt: str,
    api_key: str | None = None,
    generate_literature_review: bool = False,
    prompt_already_built: bool = False,
    progress_callback: Optional[Callable[[int, str, Optional[Dict[str, Any]]], None]] = None,
) -> dict[str, Any]:
    """使用Manus API进行通用对话

    Args:
        prompt: 用户输入的prompt/query
        api_key: Manus API密钥，如果为None则使用环境变量
        generate_literature_review: 是否生成文献综述，默认False
        prompt_already_built: 提示词是否已经构建完成，默认False
        progress_callback: 可选的进度回调函数，格式为 (progress_percentage: int, step_description: str, step_details: Optional[Dict]) -> None

    Returns:
        包含结果的字典，格式：{"success": bool, "text": str, "error": str, "error_type": str}
    """
    from config import settings

    # 使用提供的API密钥或环境变量中的密钥
    if api_key is None:
        api_key = settings.MANUS_API_KEY

    if not api_key:
        error_msg = "MANUS_API_KEY 未配置"
        logging.error(error_msg)
        return {
            "success": False,
            "text": "",
            "error": error_msg,
            "error_type": "config_error",
            "model_used": "",
            "steps": [],
        }

    # 根据生成文献综述选项构建最终prompt（仅当提示词未构建时）
    if not prompt_already_built:
        # 使用新的提示词模板系统
        final_prompt = build_literature_research_prompt(
            prompt=prompt,
            generate_literature_review=generate_literature_review,
            use_cache=True,  # 启用缓存提高性能
        )
        logging.info(f"使用提示词模板系统构建文献调研提示词: generate_literature_review={generate_literature_review}")
        logging.info(f"提示词模板构建完成，长度: {len(final_prompt)} 字符")

        prompt = final_prompt
    else:
        logging.info("提示词已构建，跳过构建步骤")
    logging.info(f"开始Manus API对话，prompt长度: {len(prompt)} 字符")
    logging.info(f"prompt预览: {repr(prompt[:100])}...")

    # 记录开始时间用于计算总处理时间
    start_time = time.time()

    # Manus API调用
    url = "https://api.manus.ai/v1/tasks"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "API_KEY": api_key,
    }
    data = {"prompt": prompt, "model": "manus-1.6"}

    try:
        # 设置超时（对话可能需要较长时间，匹配Render的1800秒超时）
        timeout = 1200  # 20分钟超时，匹配Gunicorn的1800秒超时
        logging.info(
            f"Manus API超时设置: POST请求超时={timeout}秒, 最大轮询次数=200次(10分钟), 轮询超时=300秒, pending状态超时=1200秒"
        )
        response = requests.post(url, json=data, headers=headers, timeout=timeout)
        response.raise_for_status()

        task_data = response.json()
        logging.info(f"Manus API响应状态码: {response.status_code}")
        logging.info(f"任务创建成功: {task_data.get('task_id', 'unknown')}")

        # 调用进度回调（任务创建成功）
        if progress_callback:
            progress_callback(5, "任务已创建，正在等待Manus API处理", {"task_id": task_data.get("task_id")})

        task_id = task_data.get("task_id")
        if not task_id:
            error_msg = "Manus API响应中没有task_id字段"
            logging.error(f"{error_msg}: {repr(task_data)}")
            return {
                "success": False,
                "text": "",
                "error": error_msg,
                "error_type": "api_error",
            }

        # 轮询任务状态直到完成
        # 优先使用API返回的task_url，如果没有则构建默认URL
        task_url = task_data.get("task_url")
        if task_url:
            task_status_url = task_url
            logging.info(f"使用API返回的任务URL: {task_url}")
        else:
            task_status_url = f"https://api.manus.ai/v1/tasks/{task_id}"
            logging.info(f"使用构建的任务状态URL: {task_status_url}")
        max_poll_attempts = 200  # 最多尝试200次（10分钟，每3秒一次），避免Render负载均衡器超时
        poll_interval = 3  # 每3秒轮询一次，保持连接活跃

        # 存储收集到的assistant文本和步骤信息
        all_assistant_texts = []
        all_steps = []  # 存储所有收集到的步骤信息
        last_status = None
        pending_with_content_start_time = None  # 跟踪待处理状态但有内容的开始时间

        # 调用进度回调（开始轮询）
        if progress_callback:
            progress_callback(10, "开始轮询任务状态", {"max_poll_attempts": max_poll_attempts, "poll_interval": poll_interval})

        for attempt in range(max_poll_attempts):
            logging.info(f"轮询任务状态，尝试 {attempt + 1}/{max_poll_attempts}，任务ID: {task_id}")

            # 更新轮询进度 (10% - 90%)
            if progress_callback:
                # 从10%开始，逐步增加到90%
                progress_percentage = 10 + int((attempt / max_poll_attempts) * 80)
                progress_callback(progress_percentage, f"轮询任务状态 ({attempt + 1}/{max_poll_attempts})", {"attempt": attempt + 1, "total_attempts": max_poll_attempts})

            try:
                # 尝试可能的URL获取任务状态
                possible_urls = []
                if task_url:
                    possible_urls.append(task_url)
                possible_urls.append(f"https://api.manus.ai/v1/tasks/{task_id}")
                possible_urls.append(f"https://api.manus.ai/v1/task/{task_id}")  # 单数形式
                possible_urls.append(f"https://api.manus.ai/v1/tasks/{task_id}/output")
                possible_urls.append(f"https://api.manus.ai/v1/tasks/{task_id}/result")

                status_response = None
                status_data = None
                last_exception = None

                for url in possible_urls:
                    max_retries = 3
                    for retry in range(max_retries):
                        try:
                            # 增加状态查询超时时间，从60秒增加到120秒，避免网络波动导致的假性超时
                            # 最后一次重试使用更长的超时时间
                            current_timeout = 180 if retry == max_retries - 1 else 120
                            status_response = requests.get(url, headers=headers, timeout=current_timeout)
                            if status_response.status_code == 200:
                                # 成功获取
                                status_data = status_response.json()
                                logging.info(f"使用URL获取任务状态成功: {url} (重试{retry})")
                                break
                            else:
                                logging.info(f"URL返回状态码 {status_response.status_code}: {url} (重试{retry})")
                                if retry < max_retries - 1:
                                    time.sleep(2)  # 重试前等待2秒
                                continue
                        except requests.exceptions.Timeout as e:
                            last_exception = e
                            logging.warning(f"URL请求超时 {type(e).__name__}: {url} (重试{retry}, 超时{current_timeout}秒)")
                            if retry < max_retries - 1:
                                time.sleep(2)  # 重试前等待2秒
                            continue
                        except requests.exceptions.RequestException as e:
                            last_exception = e
                            logging.info(f"URL请求异常 {type(e).__name__}: {url} (重试{retry})")
                            if retry < max_retries - 1:
                                time.sleep(2)  # 重试前等待2秒
                            continue
                    if status_data is not None:
                        break

                if status_data is None:
                    if last_exception:
                        raise last_exception
                    else:
                        raise requests.exceptions.HTTPError("无法获取任务状态，所有URL尝试失败")

                status = status_data.get("status", "unknown")
                logging.info(f"任务状态: {status}")

                # 如果状态发生变化，重置计时器
                if status != last_status:
                    # 当状态从pending/running/processing变为其他状态时，重置pending计时器
                    if last_status in ["pending", "running", "processing"] and status not in ["pending", "running", "processing"]:
                        pending_with_content_start_time = None
                        logging.info(f"状态从{last_status}变为{status}，重置pending计时器")
                    last_status = status

                # 收集所有assistant消息的文本和步骤信息
                assistant_texts = []
                current_steps = []
                output = status_data.get("output", [])
                for item in output:
                    if item.get("role") == "assistant" and item.get("content"):
                        for content_item in item.get("content", []):
                            content_type = content_item.get("type")
                            text = content_item.get("text")

                            if content_type == "output_text" and text and text.strip():
                                cleaned_text = text.strip()
                                assistant_texts.append(cleaned_text)

                                # 尝试识别步骤信息
                                # 检查是否包含"搜索"、"访问"、"保存"等关键词
                                # 检查content_type是否为step/query/action等
                                if ("搜索" in cleaned_text or
                                    "访问" in cleaned_text or
                                    "保存" in cleaned_text or
                                    content_type in ["step", "query", "action", "operation"]):
                                    if cleaned_text not in current_steps:
                                        current_steps.append(cleaned_text)
                                        logging.info(f"识别到Manus步骤: {cleaned_text[:100]}...")

                # 更新所有收集到的文本（去重）
                for text in assistant_texts:
                    if text not in all_assistant_texts:
                        all_assistant_texts.append(text)

                # 更新所有收集到的步骤（去重）
                for step in current_steps:
                    if step not in all_steps:
                        all_steps.append(step)

                # 如果任务完成，返回结果
                if status in ["completed", "succeeded", "finished"]:
                    result_text = "\n\n".join(all_assistant_texts)
                    if not result_text:
                        result_text = "对话已完成，但没有生成具体的回复内容。"

                    # 应用clean_markdown清理文本，确保与普通对话格式一致
                    # 注释掉clean_markdown，因为Manus API已返回纯文本，清理可能导致格式问题
                    # result_text = clean_markdown(result_text)

                    logging.info(f"Manus API对话成功，文本长度: {len(result_text)} 字符")
                    # 记录响应体字节大小（UTF-8编码）
                    byte_size = len(result_text.encode('utf-8'))
                    logging.info(f"Manus API响应体字节大小: {byte_size} 字节 ({byte_size/1024:.2f} KB)")
                    # 调试：记录前200个字符
                    if result_text:
                        preview = result_text[:200].replace('\n', ' ')
                        logging.info(f"Manus API返回文本预览: {preview}")

                    # 计算总处理时间
                    total_time = time.time() - start_time
                    logging.info(f"Manus API总处理时间: {total_time:.2f}秒, 轮询次数: {attempt + 1}次")

                    # 处理结果文本：转换URL为可点击链接，规范化段落间距
                    if result_text:
                        # 转换URL为Markdown链接格式
                        result_text = convert_urls_to_markdown(result_text)
                        logging.info(f"URL转换后文本长度: {len(result_text)} 字符")

                        # 规范化段落间距，确保不超过一个空行
                        result_text = normalize_paragraph_spacing(result_text, max_empty_lines=1)
                        logging.info(f"段落规范化后文本长度: {len(result_text)} 字符")

                    return {
                        "success": True,
                        "text": result_text,
                        "steps": all_steps,  # 返回收集到的步骤信息
                        "error": "",
                        "error_type": "",
                        "model_used": "manus-1.6",
                    }

                # 如果状态为pending/running/processing，继续等待直到完成
                # 用户要求：只在completed/succeeded/finished时才输出结果
                # 移除pending状态超时返回逻辑，让Manus有足够时间完成复杂调研
                if status in ["pending", "running", "processing"]:
                    # 简单记录状态，不设置超时返回
                    logging.info(f"任务状态为{status}，继续等待完成...")
                    # 如果有内容，记录进度但不返回
                    if assistant_texts:
                        logging.info(f"任务状态{status}下已收集到{len(assistant_texts)}条新内容")
                    # 重置pending计时器（因为不再使用超时返回逻辑）
                    pending_with_content_start_time = None

                # 等待下一次轮询
                time.sleep(poll_interval)

            except requests.exceptions.Timeout as e:
                # 状态查询超时异常，这通常是网络问题或API响应慢
                # 不立即返回内容，而是继续轮询，除非达到重试次数限制
                logging.warning(f"状态查询超时: {str(e)}，继续轮询")
                # 记录超时但继续尝试
                time.sleep(poll_interval)
                continue
            except Exception as e:
                logging.error(f"轮询任务状态异常: {type(e).__name__}: {str(e)}", exc_info=True)
                # 根据用户要求：即使发生异常，如果任务未完成，也不返回内容
                # 记录异常但继续轮询，让系统有更多机会完成任务
                logging.warning(f"轮询异常，但任务未完成，继续尝试轮询...")
                # 继续轮询，不返回任何内容
                time.sleep(poll_interval)
                continue

        # 如果达到最大轮询次数
        timeout_msg = f"任务轮询超时（{max_poll_attempts}次尝试，{max_poll_attempts * poll_interval}秒），任务仍未完成"
        logging.error(timeout_msg)
        # 计算总处理时间
        total_time = time.time() - start_time
        logging.error(f"Manus API超时，总处理时间: {total_time:.2f}秒, 轮询次数: {max_poll_attempts}次")
        # 根据用户要求：即使有部分内容，如果任务未完成，也不返回内容
        # 始终返回错误，表示任务未能在预期时间内完成
        return {
            "success": False,
            "text": "",
            "steps": all_steps,  # 返回已收集到的步骤信息供调试
            "error": timeout_msg,
            "error_type": "timeout",
            "model_used": "manus-1.6",
        }

    except Exception as e:
        error_msg = f"Manus API对话异常: {type(e).__name__}: {str(e)}"
        logging.error(error_msg, exc_info=True)
        # 计算总处理时间
        total_time = time.time() - start_time
        logging.error(f"Manus API异常，总处理时间: {total_time:.2f}秒")
        return {
            "success": False,
            "text": "",
            "steps": [],  # 异常时没有收集到步骤
            "error": error_msg,
            "error_type": "unknown",
            "model_used": "",
        }
