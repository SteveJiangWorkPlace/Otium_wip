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
from typing import Any, Callable, Dict, Generator, Optional
from urllib.parse import urlparse

import google.genai
import google.genai._api_client as genai_api_client
import google.genai.errors
import requests
from google.genai.types import HttpOptions

from config import settings
from exceptions import GeminiAPIError, RateLimitError
from utils import TextValidator
from prompts import build_literature_research_prompt

# ==========================================
# Gemini API 服务
# ==========================================


def _build_gemini_requests_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = settings.GEMINI_USE_SYSTEM_PROXY

    if settings.GEMINI_PROXY_URL:
        session.proxies.update(
            {
                "http": settings.GEMINI_PROXY_URL,
                "https": settings.GEMINI_PROXY_URL,
            }
        )

    return session


def _build_direct_requests_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = settings.GEMINI_USE_SYSTEM_PROXY
    if settings.GEMINI_PROXY_URL:
        session.proxies.update(
            {
                "http": settings.GEMINI_PROXY_URL,
                "https": settings.GEMINI_PROXY_URL,
            }
        )
    return session


def _request_gemini(method: str, url: str, **kwargs):
    session = _build_gemini_requests_session()
    return session.request(method=method, url=url, **kwargs)


def _request_direct(method: str, url: str, **kwargs):
    session = _build_direct_requests_session()
    return session.request(method=method, url=url, **kwargs)


def _describe_gemini_network_mode() -> str:
    if settings.GEMINI_PROXY_URL:
        return "explicit_proxy"
    if settings.GEMINI_USE_SYSTEM_PROXY:
        return "system_proxy"
    return "direct"


def _patch_google_genai_transport() -> None:
    if getattr(genai_api_client.ApiClient, "_otium_proxy_patched", False):
        return

    def _patched_request_unauthorized(self, http_request, stream: bool = False):
        data = None
        if http_request.data:
            if not isinstance(http_request.data, bytes):
                data = json.dumps(http_request.data)
            else:
                data = http_request.data

        http_session = _build_gemini_requests_session()
        response = http_session.request(
            method=http_request.method,
            url=http_request.url,
            headers=http_request.headers,
            data=data,
            timeout=http_request.timeout,
            stream=stream,
        )
        genai_api_client.errors.APIError.raise_for_response(response)
        return genai_api_client.HttpResponse(
            response.headers, response if stream else [response.text]
        )

    def _patched_download_file_request(self, http_request):
        data = None
        if http_request.data:
            if not isinstance(http_request.data, bytes):
                data = json.dumps(http_request.data, cls=genai_api_client.RequestJsonEncoder)
            else:
                data = http_request.data

        http_session = _build_gemini_requests_session()
        response = http_session.request(
            method=http_request.method,
            url=http_request.url,
            headers=http_request.headers,
            data=data,
            timeout=http_request.timeout,
            stream=False,
        )
        genai_api_client.errors.APIError.raise_for_response(response)
        return genai_api_client.HttpResponse(response.headers, byte_stream=[response.content])

    genai_api_client.ApiClient._request_unauthorized = _patched_request_unauthorized
    genai_api_client.ApiClient._download_file_request = _patched_download_file_request
    genai_api_client.ApiClient._otium_proxy_patched = True

    logging.info("Gemini transport mode: %s", _describe_gemini_network_mode())


_patch_google_genai_transport()


def _collect_gemini_response_debug(response: Any) -> dict[str, Any]:
    debug: dict[str, Any] = {
        "has_text_attr": hasattr(response, "text"),
        "text_length": len(getattr(response, "text", "") or ""),
        "candidate_count": 0,
        "finish_reason": None,
        "parts_count": 0,
        "first_part_length": 0,
    }

    candidates = getattr(response, "candidates", None) or []
    debug["candidate_count"] = len(candidates)
    if not candidates:
        return debug

    candidate = candidates[0]
    finish_reason = getattr(candidate, "finish_reason", None)
    if finish_reason is not None:
        debug["finish_reason"] = str(finish_reason)

    content = getattr(candidate, "content", None)
    parts = getattr(content, "parts", None) or []
    debug["parts_count"] = len(parts)
    if parts:
        first_part_text = getattr(parts[0], "text", "") or ""
        debug["first_part_length"] = len(first_part_text)

    return debug


def _extract_text_from_genai_content(content: Any) -> str:
    if not content:
        return ""

    parts = getattr(content, "parts", None) or []
    if parts:
        texts = [(getattr(part, "text", "") or "") for part in parts]
        return "".join(texts)

    return getattr(content, "text", "") or ""


def _extract_text_from_genai_response(response: Any) -> str:
    text = getattr(response, "text", "") or ""
    if text:
        return text

    candidates = getattr(response, "candidates", None) or []
    if not candidates:
        return ""

    candidate = candidates[0]
    return _extract_text_from_genai_content(getattr(candidate, "content", None))


def _extract_text_from_gemini_json(result: dict[str, Any]) -> str:
    candidates = result.get("candidates") or []
    if not candidates:
        return ""

    content = candidates[0].get("content") or {}
    parts = content.get("parts") or []
    texts = [(part.get("text") or "") for part in parts if isinstance(part, dict)]
    return "".join(texts)


def generate_gemini_content_with_fallback(
    prompt: str,
    api_key: str | None = None,
    primary_model: str = "gemini-2.5-flash",
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
    logging.info("Attempting content generation with primary model %s", primary_model)

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
                    raise GeminiAPIError(
                        "Gemini API key is missing. Provide it in the request or set GEMINI_API_KEY.",
                        "missing_key",
                    )

                key_prefix = (
                    current_api_key[:8]
                    if len(current_api_key) > 8
                    else current_api_key[: len(current_api_key)]
                )
                logging.info(
                    "_try_model start: model=%s attempt=%s/%s api_key_source=%s prefix=%s...",
                    model_name,
                    attempt + 1,
                    max_retries,
                    key_source,
                    key_prefix,
                )

                # 调试日志：记录API密钥信息（不记录完整密钥）
                key_prefix = (
                    current_api_key[:8]
                    if len(current_api_key) > 8
                    else current_api_key[: len(current_api_key)]
                )
                logging.info("Using Gemini API key from %s with prefix %s...", key_source, key_prefix)
                logging.info("Trying Gemini model: %s", model_name)

                logging.info("Gemini client network mode: %s", _describe_gemini_network_mode())

                # 创建客户端
                # 设置timeout值（180000 = 180秒/3分钟读取超时）
                # timeout值除以1000得到实际的读取超时秒数
                http_opts = HttpOptions(timeout=180000)
                client = google.genai.Client(api_key=current_api_key, http_options=http_opts)

                # 准备配置（包括安全设置）
                config = {"safety_settings": safety_settings}

                # 生成内容
                logging.info("Calling Gemini API: model=%s prompt_length=%s", model_name, len(prompt))
                response = client.models.generate_content(
                    model=model_name, contents=prompt, config=config
                )
                logging.info("Gemini API call succeeded: model=%s", model_name)
                logging.warning(
                    "gemini_non_stream_debug model=%s meta=%s",
                    model_name,
                    _collect_gemini_response_debug(response),
                )

                # 提取响应文本
                # 注意：response 结构可能不同，需要检查
                text = _extract_text_from_genai_response(response)

                return {"success": True, "text": text, "model_used": model_name}

            except Exception as e:
                # 获取原始错误消息
                error_raw = str(e)
                error_msg = error_raw.lower()
                logging.error("Raw Gemini API exception: %s", error_raw)
                logging.error("Gemini exception type: %s", type(e).__name__)

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
                    logging.error("Model %s service unavailable: %s", model_name, str(e))
                    raise GeminiAPIError(
                        "Google API service is temporarily unavailable. Please try again later.",
                        "service_unavailable",
                    ) from e

                # 超时错误（包括 DeadlineExceeded 和 requests Timeout）
                elif "timeout" in error_msg or "deadline" in error_msg or "timed out" in error_msg:
                    logging.error(
                        "Model %s request timed out (attempt %s/%s): %s",
                        model_name,
                        attempt + 1,
                        max_retries,
                        str(e),
                    )
                    if attempt < max_retries - 1:
                        logging.info("Retrying in %s seconds...", retry_delay)
                        time.sleep(retry_delay)
                        continue
                    raise GeminiAPIError(
                        "Request timed out after the default 180-second limit. Check network connectivity.",
                        "timeout",
                    ) from e

                # 网络连接错误
                elif (
                    "connect" in error_msg
                    or "socket" in error_msg
                    or "network" in error_msg
                    or "connection" in error_msg
                ):
                    logging.error(
                        "Model %s network error (attempt %s/%s): %s",
                        model_name,
                        attempt + 1,
                        max_retries,
                        str(e),
                    )
                    if attempt < max_retries - 1:
                        logging.info("Retrying in %s seconds...", retry_delay)
                        time.sleep(retry_delay)
                        continue
                    error_message = "Unable to connect to Google API service."
                    error_message += "\nPossible causes:"
                    error_message += "\n1. Network connectivity issue."
                    error_message += "\n2. Firewall, VPN, or local proxy configuration issue."
                    error_message += "\n3. Google service temporarily unavailable."
                    error_message += "\n\nSuggested actions:"
                    error_message += "\n- Verify the internet connection."
                    error_message += "\n- Verify the VPN or proxy connection."
                    raise GeminiAPIError(error_message, "network_error") from e

                # API配额错误
                elif "quota" in error_msg or "resource_exhausted" in error_msg:
                    logging.error("Model %s quota exhausted: %s", model_name, str(e))
                    raise GeminiAPIError("API quota exhausted. Please try again later.", "quota") from e

                # 速率限制
                elif (
                    "429" in error_msg
                    or "rate_limit" in error_msg
                    or "too many requests" in error_msg
                ):
                    logging.error("Model %s rate limited: %s", model_name, str(e))
                    raise RateLimitError("Too many requests. Please try again later.") from e

                # API密钥无效
                elif (
                    "invalid" in error_msg
                    or "api_key" in error_msg
                    or "permission" in error_msg
                    or "unauthorized" in error_msg
                ):
                    logging.error("Model %s invalid API key: %s", model_name, str(e))
                    logging.error("Full exception type: %s", type(e))
                    logging.error("Full exception details: %r", e)
                    if error_json:
                        logging.error("Parsed error JSON: %s", error_json)
                    raise GeminiAPIError("API key is invalid or expired. Check configuration.", "invalid_key") from e

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
                    logging.error("Model %s region restricted: %s", model_name, str(e))
                    error_message = "Google Gemini API is not available in the current region.\n"
                    error_message += "Suggested actions:\n"
                    error_message += "- Use a network path that supports Google services.\n"
                    error_message += "- Check VPN and proxy settings.\n"
                    error_message += "- Confirm that outbound access to Google API is allowed."
                    raise GeminiAPIError(error_message, "region_restricted") from e

                # 其他API错误
                elif "api" in error_msg or "google" in error_msg or "genai" in error_msg:
                    logging.error("Model %s API error: %s", model_name, str(e))
                    raise GeminiAPIError(f"API error: {str(e)}", "api_error") from e

                # 未知错误
                else:
                    logging.error("Model %s unknown error: %s", model_name, str(e), exc_info=True)
                    raise GeminiAPIError(f"Unknown error: {str(e)}", "unknown") from e

        # 如果所有重试都失败（理论上不应该到达这里）
        raise GeminiAPIError(f"All {max_retries} retry attempts failed", "all_retries_failed")

    # 尝试主要模型
    try:
        return _try_model(primary_model)

    except GeminiAPIError as e:
        logging.warning("Primary model %s failed with error_type=%s", primary_model, e.error_type)

        # 如果是网络连接错误，直接尝试requests备选方案，而不是备用模型
        if e.error_type == "network_error":
            logging.warning("Network error detected; trying requests fallback directly...")
            try:
                result = generate_gemini_with_requests(
                    prompt=prompt, api_key=api_key, model=primary_model
                )
                if result.get("success"):
                    logging.info("Requests fallback succeeded: model=%s", primary_model)
                    return result
                else:
                    # 主要模型失败，尝试备用模型
                    logging.warning("Requests primary model failed; trying fallback model %s", fallback_model)
                    result = generate_gemini_with_requests(
                        prompt=prompt, api_key=api_key, model=fallback_model
                    )
                    return result
            except Exception as requests_exception:
                logging.error("Requests fallback also failed: %s", str(requests_exception), exc_info=True)
                return {
                    "success": False,
                    "error": f"All attempts failed: {e.message}",
                    "error_type": e.error_type,
                }

        # 如果不是网络错误，尝试备用模型
        logging.warning("Trying fallback model %s", fallback_model)
        try:
            return _try_model(fallback_model)
        except GeminiAPIError as fallback_error:
            logging.warning(
                "Fallback model also failed with error_type=%s; trying requests fallback...",
                fallback_error.error_type,
            )

            # 尝试使用requests备选方案
            try:
                # 先尝试主要模型
                result = generate_gemini_with_requests(
                    prompt=prompt, api_key=api_key, model=primary_model
                )

                if result.get("success"):
                    logging.info("Requests fallback succeeded: model=%s", primary_model)
                    return result
                else:
                    # 主要模型失败，尝试备用模型
                    logging.warning("Requests primary model failed; trying fallback model %s", fallback_model)
                    result = generate_gemini_with_requests(
                        prompt=prompt, api_key=api_key, model=fallback_model
                    )
                    return result

            except Exception as requests_exception:
                logging.error("Requests fallback also failed: %s", str(requests_exception), exc_info=True)
                return {
                    "success": False,
                    "error": f"All attempts failed: {fallback_error.message}",
                    "error_type": fallback_error.error_type,
                }
        except Exception as fallback_error:
            logging.error("Fallback model also failed: %s", str(fallback_error), exc_info=True)
            logging.warning("Trying requests fallback...")

            # 尝试使用requests备选方案
            try:
                # 先尝试主要模型
                result = generate_gemini_with_requests(
                    prompt=prompt, api_key=api_key, model=primary_model
                )

                if result.get("success"):
                    logging.info("Requests fallback succeeded: model=%s", primary_model)
                    return result
                else:
                    # 主要模型失败，尝试备用模型
                    logging.warning("Requests primary model failed; trying fallback model %s", fallback_model)
                    result = generate_gemini_with_requests(
                        prompt=prompt, api_key=api_key, model=fallback_model
                    )
                    return result

            except Exception as requests_exception:
                logging.error("Requests fallback also failed: %s", str(requests_exception), exc_info=True)
                return {
                    "success": False,
                    "error": "All attempts failed. Please try again later.",
                    "error_type": "all_failed",
                }

    except RateLimitError as e:
        logging.warning("Rate limit error detected; trying requests fallback...")

        # 尝试使用requests备选方案
        try:
            # 先尝试主要模型
            result = generate_gemini_with_requests(
                prompt=prompt, api_key=api_key, model=primary_model
            )

            if result.get("success"):
                logging.info("Requests fallback succeeded: model=%s", primary_model)
                return result
            else:
                # 主要模型失败，尝试备用模型
                logging.warning("Requests primary model failed; trying fallback model %s", fallback_model)
                result = generate_gemini_with_requests(
                    prompt=prompt, api_key=api_key, model=fallback_model
                )
                return result

        except Exception as requests_exception:
            logging.error("Requests fallback also failed: %s", str(requests_exception), exc_info=True)
            return {"success": False, "error": str(e), "error_type": "rate_limit"}

    except Exception as e:
        logging.error("Unknown Gemini generation error: %s", str(e), exc_info=True)

        # 当google.genai库失败时，尝试使用requests备选方案
        logging.warning("google.genai call failed; trying requests fallback...")

        try:
            # 先尝试主要模型
            result = generate_gemini_with_requests(
                prompt=prompt, api_key=api_key, model=primary_model
            )

            if result.get("success"):
                logging.info("Requests fallback succeeded: model=%s", primary_model)
                return result
            else:
                # 主要模型失败，尝试备用模型
                logging.warning("Requests primary model failed; trying fallback model %s", fallback_model)
                result = generate_gemini_with_requests(
                    prompt=prompt, api_key=api_key, model=fallback_model
                )
                return result

        except Exception as fallback_exception:
            logging.error("Requests fallback also failed: %s", str(fallback_exception), exc_info=True)
            return {
                "success": False,
                "error": f"All attempts failed: {str(e)}",
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
        "Starting Gemini stream generation: primary_model=%s fallback_model=%s prompt_length=%s",
        primary_model,
        fallback_model,
        len(prompt),
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
            raise GeminiAPIError("Gemini API key is missing.", "missing_key")

        # 创建客户端
        # 设置timeout值（180000 = 180秒/3分钟读取超时）
        # timeout值除以1000得到实际的读取超时秒数
        http_opts = HttpOptions(timeout=180000)
        logging.info("Gemini stream network mode: %s", _describe_gemini_network_mode())
        client = google.genai.Client(api_key=current_api_key, http_options=http_opts)

        # 准备配置
        config = {"safety_settings": safety_settings}

        # 尝试主模型
        current_model = primary_model
        models_tried = []

        # 尝试使用主模型
        try:
            logging.info("Calling Gemini streaming API: model=%s", current_model)
            response_stream = client.models.generate_content_stream(
                model=current_model, contents=prompt, config=config
            )
            models_tried.append(current_model)
        except Exception as primary_error:
            logging.warning("Primary streaming model %s failed: %s", primary_model, str(primary_error))

            # 检查是否有备用模型
            if fallback_model and fallback_model != primary_model:
                logging.info("Switching to fallback streaming model: %s", fallback_model)
                current_model = fallback_model
                try:
                    response_stream = client.models.generate_content_stream(
                        model=current_model, contents=prompt, config=config
                    )
                    models_tried.append(current_model)
                    logging.info("Fallback streaming model succeeded: %s", fallback_model)
                except Exception as fallback_error:
                    logging.error("Fallback streaming model %s also failed: %s", fallback_model, str(fallback_error))
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
                    "Streaming generation timed out after %s seconds; chunks=%s sentences=%s",
                    timeout_seconds,
                    chunk_count,
                    len(sentences),
                )
                yield {
                    "type": "error",
                    "error": f"Streaming generation timed out after {timeout_seconds} seconds",
                    "error_type": "timeout",
                }
                return  # 流式翻译超时，结束生成器
            chunk_debug = _collect_gemini_response_debug(chunk)
            logging.warning(
                "gemini_stream_chunk_debug index=%s meta=%s",
                chunk_count,
                chunk_debug,
            )

            chunk_text = _extract_text_from_genai_response(chunk)

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
                            "Sentence detection loop exceeded the safety limit (%s). buffer_length=%s preview=%r",
                            max_iterations,
                            len(buffer),
                            buffer[:50],
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
        logging.info("Streaming translation completed with %s sentences", len(sentences))
        logging.info(
            "translate_stream_summary: reason=%s, chunks=%s, chars=%s, sentences=%s, elapsed=%.2fs",
            stream_end_reason,
            chunk_count,
            len(full_response),
            len(sentences),
            time.time() - start_time,
        )
        logging.warning(
            "gemini_stream_final_debug model=%s chars=%s chunks=%s stream_end_reason=%s",
            current_model,
            len(full_response),
            chunk_count,
            stream_end_reason,
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
        logging.error("Streaming translation error: %s", str(e), exc_info=True)

        # 尝试获取错误类型
        error_msg = str(e).lower()

        if "service unavailable" in error_msg or "503" in error_msg:
            error_type = "service_unavailable"
            error_message = "Google API service is temporarily unavailable. Please try again later."
        elif "timeout" in error_msg or "deadline" in error_msg:
            error_type = "timeout"
            error_message = "Request timed out. Check network connectivity."
        elif "network" in error_msg or "connection" in error_msg:
            error_type = "network_error"
            error_message = "Unable to connect to Google API service. Check network connectivity."
        elif "quota" in error_msg or "resource_exhausted" in error_msg:
            error_type = "quota"
            error_message = "API quota exhausted. Please try again later."
        elif "429" in error_msg or "rate_limit" in error_msg:
            error_type = "rate_limit"
            error_message = "Too many requests. Please try again later."
        elif "invalid" in error_msg or "api_key" in error_msg or "permission" in error_msg:
            error_type = "invalid_key"
            error_message = "API key is invalid or expired. Check configuration."
        else:
            error_type = "unknown"
            error_message = f"System error: {str(e)}"

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
            logging.warning("Input text was truncated to the GPTZero API limit")
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
            response = _request_direct("POST", url, headers=headers, json=payload, timeout=180)
            response.raise_for_status()
            result = response.json()

            if "documents" in result:
                if isinstance(result["documents"], dict):
                    doc = result["documents"]
                elif isinstance(result["documents"], list) and len(result["documents"]) > 0:
                    doc = result["documents"][0]
                else:
                    return {"success": False, "message": "Unknown API response format"}

                return {
                    "ai_score": doc.get("completely_generated_prob", 0),
                    "success": True,
                    "message": "",
                    "detailed_scores": doc.get("sentences", []),
                    "full_text": text,
                }
            else:
                return {"success": False, "message": "API returned data in an unknown format"}

        except requests.exceptions.Timeout:
            retry_count += 1
            if retry_count >= max_retries:
                logging.error("GPTZero API request timed out after reaching max retries")
                return {"success": False, "message": "Detection request timed out. Please try again later."}
            logging.warning(
                f"GPTZero API timeout; retrying in {current_delay} seconds ({retry_count}/{max_retries})"
            )
            time.sleep(current_delay)
            current_delay *= 2

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            if status_code == 401:
                return {"success": False, "message": "API key is invalid or expired"}
            elif status_code == 429:
                return {"success": False, "message": "Too many requests. Please try again later."}
            else:
                return {
                    "success": False,
                    "message": f"API request failed (status code {status_code})",
                }

        except Exception as e:
            logging.error("GPTZero API exception: %s", str(e), exc_info=True)
            return {"success": False, "message": "System error. Please try again later."}

    return {"success": False, "message": "Detection failed after reaching max retries"}


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
        logging.info("Extracted %s annotations", len(annotations))
        for i, anno in enumerate(annotations):
            logging.info(
                "Annotation %s: sentence=%r content=%r",
                i + 1,
                anno["sentence"],
                anno["content"],
            )

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
                logging.info("clean_markdown: position %s: U+%04X", i, ord(c))
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

        logging.info("Gemini requests fallback uses direct connection")

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

        logging.info(
            "Calling Gemini API via requests: model=%s prompt_length=%s",
            model,
            len(prompt),
        )
        response = _request_gemini("POST", url, headers=headers, json=payload, timeout=180)

        if response.status_code == 200:
            result = response.json()
            if "candidates" in result and result["candidates"]:
                text = _extract_text_from_gemini_json(result)
                logging.info(
                    "Requests Gemini API call succeeded: model=%s response_length=%s",
                    model,
                    len(text),
                )
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


def build_gemini_chat_prompt(messages: list[dict[str, str]]) -> str:
    """将聊天消息转换为 Gemini 可用的 prompt。"""
    full_messages = [{"role": "system", "content": AI_SYSTEM_PROMPT}] + messages
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

    return prompt + "助手："


def _extract_manus_documents(payload: Any) -> list[dict[str, str]]:
    """Extract downloadable document links from Manus task payload."""
    url_keys = {
        "url",
        "download_url",
        "downloadUrl",
        "file_url",
        "fileUrl",
        "signed_url",
        "signedUrl",
        "public_url",
        "publicUrl",
        "remote_url",
        "remoteUrl",
        "web_url",
        "webUrl",
        "link",
        "href",
    }
    name_keys = {"name", "filename", "file_name", "fileName", "title", "document_name", "documentName"}
    container_keys = {
        "documents",
        "files",
        "artifacts",
        "attachments",
        "resources",
        "outputs",
        "result",
        "data",
    }
    document_type_keys = {"type", "content_type", "mime_type"}

    documents: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    def normalize_url(value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            return ""
        if trimmed.startswith("//"):
            return f"https:{trimmed}"
        if trimmed.startswith("/"):
            return f"https://api.manus.ai{trimmed}"
        return trimmed

    def is_http_url(value: str) -> bool:
        try:
            parsed = urlparse(value)
            return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
        except Exception:
            return False

    def extract_document_urls_from_text(text: str) -> list[str]:
        if not text:
            return []
        url_pattern = re.compile(r"https?://[^\s<>\"]+")
        markdown_pattern = re.compile(r"\[[^\]]+\]\((https?://[^)\s]+)\)")
        candidates: list[str] = []
        candidates.extend(markdown_pattern.findall(text))
        candidates.extend(url_pattern.findall(text))
        doc_exts = (".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xlsx", ".csv", ".txt", ".md", ".zip")
        result: list[str] = []
        for url in candidates:
            normalized = normalize_url(url).rstrip(".,;:!?)\"'")
            lowered = normalized.lower()
            if any(lowered.endswith(ext) or f"{ext}?" in lowered for ext in doc_exts):
                result.append(normalized)
        return result

    def to_document(entry: dict[str, Any], source: str) -> dict[str, str] | None:
        url_value: str | None = None
        for key in url_keys:
            candidate = entry.get(key)
            if isinstance(candidate, str):
                normalized_candidate = normalize_url(candidate)
                if is_http_url(normalized_candidate):
                    url_value = normalized_candidate
                    break

        if not url_value:
            for key in ("path", "file_path", "download_path"):
                candidate = entry.get(key)
                if isinstance(candidate, str):
                    normalized_candidate = normalize_url(candidate)
                    if is_http_url(normalized_candidate):
                        url_value = normalized_candidate
                        break

        if not url_value:
            text_candidates: list[str] = []
            for key in ("text", "message", "description", "content", "raw"):
                value = entry.get(key)
                if isinstance(value, str) and value.strip():
                    text_candidates.extend(extract_document_urls_from_text(value))
            if text_candidates:
                url_value = text_candidates[0]

        if url_value:
            url_value = normalize_url(url_value)

        if not url_value or not is_http_url(url_value) or url_value in seen_urls:
            return None

        lowered_url = url_value.lower()
        parsed_url = urlparse(url_value)
        file_ext = parsed_url.path.rsplit(".", 1)[-1].lower() if "." in parsed_url.path else ""
        has_name_signal = any(
            isinstance(entry.get(key), str) and entry.get(key, "").strip() for key in name_keys
        )
        has_type_signal = entry.get("type") in {"output_file", "file", "document", "artifact"}
        has_source_signal = source in container_keys
        has_file_ext_signal = file_ext in {
            "pdf",
            "doc",
            "docx",
            "ppt",
            "pptx",
            "xlsx",
            "csv",
            "md",
            "txt",
            "zip",
        }
        has_keyword_signal = any(
            keyword in lowered_url for keyword in ("download", "file", "artifact", "document", "report")
        )
        if not (
            has_name_signal
            or has_type_signal
            or has_source_signal
            or has_file_ext_signal
            or has_keyword_signal
        ):
            return None

        name_value = ""
        for key in name_keys:
            candidate = entry.get(key)
            if isinstance(candidate, str) and candidate.strip():
                name_value = candidate.strip()
                break

        if not name_value:
            parsed = urlparse(url_value)
            name_value = parsed.path.rsplit("/", 1)[-1] or "下载文档"

        doc_type = ""
        for key in document_type_keys:
            candidate = entry.get(key)
            if isinstance(candidate, str) and candidate.strip():
                doc_type = candidate.strip()
                break

        seen_urls.add(url_value)
        result = {"name": name_value, "url": url_value, "source": source}
        if doc_type:
            result["type"] = doc_type
        return result

    def walk(node: Any, source: str = "manus_output") -> None:
        if isinstance(node, dict):
            if node.get("type") in {"output_file", "file", "document", "artifact"}:
                doc = to_document(node, source)
                if doc:
                    documents.append(doc)

            if any(key in node for key in url_keys):
                doc = to_document(node, source)
                if doc:
                    documents.append(doc)

            for key, value in node.items():
                next_source = key if key in container_keys else source
                walk(value, next_source)
            return

        if isinstance(node, list):
            for item in node:
                walk(item, source)
            return

        if isinstance(node, str):
            text_urls = extract_document_urls_from_text(node)
            for idx, text_url in enumerate(text_urls):
                if text_url in seen_urls:
                    continue
                seen_urls.add(text_url)
                documents.append({"name": f"文档 {len(documents) + 1 + idx}", "url": text_url, "source": source})

    walk(payload)
    return documents


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
            "documents": [],
        }

    # 根据生成文献综述选项构建最终prompt（仅当提示词未构建时）
    if not prompt_already_built:
        # 使用新的提示词模板系统
        final_prompt = build_literature_research_prompt(
            prompt=prompt,
            generate_literature_review=generate_literature_review,
            use_cache=True,  # 启用缓存提高性能
        )
        logging.info(
            "Built literature research prompt with template system: generate_literature_review=%s",
            generate_literature_review,
        )
        logging.info("Literature research prompt build completed: length=%s chars", len(final_prompt))

        prompt = final_prompt
    else:
        logging.info("Prompt already built; skipping prompt construction")
    logging.info("Starting Manus API chat: prompt_length=%s chars", len(prompt))
    logging.info("Prompt preview: %r...", prompt[:100])

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
            "Manus timeout config: post_timeout=%ss max_poll_attempts=200 poll_timeout=300s pending_timeout=1200s",
            timeout,
        )
        response = _request_direct("POST", url, json=data, headers=headers, timeout=timeout)
        response.raise_for_status()

        task_data = response.json()
        logging.info("Manus API response status: %s", response.status_code)
        logging.info("Manus task created successfully: %s", task_data.get("task_id", "unknown"))

        # 调用进度回调（任务创建成功）
        if progress_callback:
            progress_callback(5, "Task created; waiting for Manus processing", {"task_id": task_data.get("task_id")})

        task_id = task_data.get("task_id")
        if not task_id:
            error_msg = "Manus API response did not include task_id"
            logging.error(f"{error_msg}: {repr(task_data)}")
            return {
                "success": False,
                "text": "",
                "error": error_msg,
                "error_type": "api_error",
                "documents": [],
            }

        # 轮询任务状态直到完成
        # 优先使用API返回的task_url，如果没有则构建默认URL
        task_url = task_data.get("task_url")
        if task_url:
            task_status_url = task_url
            logging.info("Using task URL from API response: %s", task_url)
        else:
            task_status_url = f"https://api.manus.ai/v1/tasks/{task_id}"
            logging.info("Using constructed task status URL: %s", task_status_url)
        max_poll_attempts = 200  # 最多尝试200次（10分钟，每3秒一次），避免Render负载均衡器超时
        poll_interval = 3  # 每3秒轮询一次，保持连接活跃

        # 存储收集到的assistant文本和步骤信息
        all_assistant_texts = []
        all_steps = []  # 存储所有收集到的步骤信息
        all_documents: list[dict[str, str]] = []
        initial_documents = _extract_manus_documents(task_data)
        if initial_documents:
            all_documents.extend(initial_documents)
            logging.info("Captured %s document links from task creation response", len(initial_documents))
        last_status = None
        pending_with_content_start_time = None  # 跟踪待处理状态但有内容的开始时间

        # 调用进度回调（开始轮询）
        if progress_callback:
            progress_callback(10, "Starting task status polling", {"max_poll_attempts": max_poll_attempts, "poll_interval": poll_interval})

        for attempt in range(max_poll_attempts):
            logging.info(
                "Polling task status: attempt %s/%s task_id=%s",
                attempt + 1,
                max_poll_attempts,
                task_id,
            )

            # 更新轮询进度 (10% - 90%)
            if progress_callback:
                # 从10%开始，逐步增加到90%
                progress_percentage = 10 + int((attempt / max_poll_attempts) * 80)
                progress_callback(
                    progress_percentage,
                    f"Polling task status ({attempt + 1}/{max_poll_attempts})",
                    {"attempt": attempt + 1, "total_attempts": max_poll_attempts},
                )

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
                            status_response = _request_direct(
                                "GET", url, headers=headers, timeout=current_timeout
                            )
                            if status_response.status_code == 200:
                                # 成功获取
                                status_data = status_response.json()
                                logging.info("Fetched task status successfully: url=%s retry=%s", url, retry)
                                break
                            else:
                                logging.info(
                                    "Task status URL returned status %s: %s (retry=%s)",
                                    status_response.status_code,
                                    url,
                                    retry,
                                )
                                if retry < max_retries - 1:
                                    time.sleep(2)  # 重试前等待2秒
                                continue
                        except requests.exceptions.Timeout as e:
                            last_exception = e
                            logging.warning(
                                "Task status URL timeout %s: %s (retry=%s timeout=%ss)",
                                type(e).__name__,
                                url,
                                retry,
                                current_timeout,
                            )
                            if retry < max_retries - 1:
                                time.sleep(2)  # 重试前等待2秒
                            continue
                        except requests.exceptions.RequestException as e:
                            last_exception = e
                            logging.info(
                                "Task status URL request exception %s: %s (retry=%s)",
                                type(e).__name__,
                                url,
                                retry,
                            )
                            if retry < max_retries - 1:
                                time.sleep(2)  # 重试前等待2秒
                            continue
                    if status_data is not None:
                        break

                if status_data is None:
                    if last_exception:
                        raise last_exception
                    else:
                        raise requests.exceptions.HTTPError("Unable to fetch task status; all URL attempts failed")

                status = status_data.get("status", "unknown")
                current_documents = _extract_manus_documents(status_data)
                if current_documents:
                    existing_urls = {doc["url"] for doc in all_documents}
                    for doc in current_documents:
                        if doc["url"] not in existing_urls:
                            all_documents.append(doc)
                            existing_urls.add(doc["url"])
                logging.info("Manus task status: %s", status)

                # 如果状态发生变化，重置计时器
                if status != last_status:
                    # 当状态从pending/running/processing变为其他状态时，重置pending计时器
                    if last_status in ["pending", "running", "processing"] and status not in ["pending", "running", "processing"]:
                        pending_with_content_start_time = None
                        logging.info("Task status changed from %s to %s; resetting pending timer", last_status, status)
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
                                        logging.info("Detected Manus step: %s...", cleaned_text[:100])

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
                        result_text = "The task completed but did not return a reply body."

                    # 应用clean_markdown清理文本，确保与普通对话格式一致
                    # 注释掉clean_markdown，因为Manus API已返回纯文本，清理可能导致格式问题
                    # result_text = clean_markdown(result_text)

                    logging.info("Manus API chat succeeded: text_length=%s chars", len(result_text))
                    # 记录响应体字节大小（UTF-8编码）
                    byte_size = len(result_text.encode('utf-8'))
                    logging.info("Manus API response byte size: %s bytes (%.2f KB)", byte_size, byte_size / 1024)
                    # 调试：记录前200个字符
                    if result_text:
                        preview = result_text[:200].replace('\n', ' ')
                        logging.info("Manus API text preview: %s", preview)

                    # 计算总处理时间
                    total_time = time.time() - start_time
                    logging.info("Manus API total processing time: %.2fs polls=%s", total_time, attempt + 1)

                    # 处理结果文本：转换URL为可点击链接，规范化段落间距
                    if result_text:
                        # 转换URL为Markdown链接格式
                        result_text = convert_urls_to_markdown(result_text)
                        logging.info("Text length after URL conversion: %s chars", len(result_text))

                        # 规范化段落间距，确保不超过一个空行
                        result_text = normalize_paragraph_spacing(result_text, max_empty_lines=1)
                        logging.info("Text length after paragraph normalization: %s chars", len(result_text))

                    if not all_documents:
                        logging.warning(
                            "Manus task completed without document links: task_id=%s, status_keys=%s",
                            task_id,
                            list(status_data.keys()) if isinstance(status_data, dict) else [],
                        )

                    return {
                        "success": True,
                        "text": result_text,
                        "documents": all_documents,
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
                    logging.info("Task status is %s; waiting for completion", status)
                    # 如果有内容，记录进度但不返回
                    if assistant_texts:
                        logging.info(
                            "Collected %s new content blocks while task status=%s",
                            len(assistant_texts),
                            status,
                        )
                    # 重置pending计时器（因为不再使用超时返回逻辑）
                    pending_with_content_start_time = None

                # 等待下一次轮询
                time.sleep(poll_interval)

            except requests.exceptions.Timeout as e:
                # 状态查询超时异常，这通常是网络问题或API响应慢
                # 不立即返回内容，而是继续轮询，除非达到重试次数限制
                logging.warning("Task status query timed out: %s; continuing to poll", str(e))
                # 记录超时但继续尝试
                time.sleep(poll_interval)
                continue
            except Exception as e:
                logging.error("Task status polling exception %s: %s", type(e).__name__, str(e), exc_info=True)
                # 根据用户要求：即使发生异常，如果任务未完成，也不返回内容
                # 记录异常但继续轮询，让系统有更多机会完成任务
                logging.warning("Polling exception occurred before completion; continuing to poll...")
                # 继续轮询，不返回任何内容
                time.sleep(poll_interval)
                continue

        # 如果达到最大轮询次数
        timeout_msg = (
            f"Task polling timed out after {max_poll_attempts} attempts "
            f"({max_poll_attempts * poll_interval} seconds); task did not complete"
        )
        logging.error(timeout_msg)
        # 计算总处理时间
        total_time = time.time() - start_time
        logging.error("Manus API timed out: total_time=%.2fs polls=%s", total_time, max_poll_attempts)
        # 根据用户要求：即使有部分内容，如果任务未完成，也不返回内容
        # 始终返回错误，表示任务未能在预期时间内完成
        return {
            "success": False,
            "text": "",
            "steps": all_steps,  # 返回已收集到的步骤信息供调试
            "documents": all_documents,
            "error": timeout_msg,
            "error_type": "timeout",
            "model_used": "manus-1.6",
        }

    except Exception as e:
        error_msg = f"Manus API chat exception: {type(e).__name__}: {str(e)}"
        logging.error(error_msg, exc_info=True)
        # 计算总处理时间
        total_time = time.time() - start_time
        logging.error("Manus API exception total_time=%.2fs", total_time)
        return {
            "success": False,
            "text": "",
            "steps": [],  # 异常时没有收集到步骤
            "documents": [],
            "error": error_msg,
            "error_type": "unknown",
            "model_used": "",
        }


def chat_with_manus_stream(
    prompt: str,
    api_key: str | None = None,
    generate_literature_review: bool = False,
    prompt_already_built: bool = False,
) -> Generator[dict[str, Any], None, None]:
    """以增量事件形式返回 Manus 调研进度与文本。"""
    from config import settings

    if api_key is None:
        api_key = settings.MANUS_API_KEY

    if not api_key:
        yield {
            "type": "error",
            "error": "MANUS_API_KEY is not configured",
            "model_used": "manus-1.6",
        }
        return

    if not prompt_already_built:
        prompt = build_literature_research_prompt(
            prompt=prompt,
            generate_literature_review=generate_literature_review,
            use_cache=True,
        )

    logging.info("Starting Manus streaming chat: prompt_length=%s", len(prompt))
    start_time = time.time()
    url = "https://api.manus.ai/v1/tasks"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "API_KEY": api_key,
    }
    data = {"prompt": prompt, "model": "manus-1.6"}

    try:
        response = _request_direct("POST", url, json=data, headers=headers, timeout=1200)
        response.raise_for_status()

        task_data = response.json()
        task_id = task_data.get("task_id")
        if not task_id:
            yield {
                "type": "error",
                "error": "Manus API响应中没有task_id字段",
                "model_used": "manus-1.6",
            }
            return

        yield {
            "type": "step",
            "step": "任务已创建，正在等待 Manus 开始处理",
            "model_used": "manus-1.6",
        }

        task_url = task_data.get("task_url")
        max_poll_attempts = 200
        poll_interval = 3
        all_assistant_texts: list[str] = []
        all_steps: list[str] = []
        all_documents: list[dict[str, str]] = []
        initial_documents = _extract_manus_documents(task_data)
        if initial_documents:
            all_documents.extend(initial_documents)

        last_status = None
        last_emitted_text = ""

        for attempt in range(max_poll_attempts):
            possible_urls = []
            if task_url:
                possible_urls.append(task_url)
            possible_urls.append(f"https://api.manus.ai/v1/tasks/{task_id}")
            possible_urls.append(f"https://api.manus.ai/v1/task/{task_id}")
            possible_urls.append(f"https://api.manus.ai/v1/tasks/{task_id}/output")
            possible_urls.append(f"https://api.manus.ai/v1/tasks/{task_id}/result")

            status_data = None
            last_exception = None

            for candidate_url in possible_urls:
                for retry in range(3):
                    try:
                        current_timeout = 180 if retry == 2 else 120
                        status_response = _request_direct(
                            "GET", candidate_url, headers=headers, timeout=current_timeout
                        )
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            break
                        if retry < 2:
                            time.sleep(2)
                    except requests.exceptions.RequestException as exc:
                        last_exception = exc
                        if retry < 2:
                            time.sleep(2)
                if status_data is not None:
                    break

            if status_data is None:
                if last_exception:
                    raise last_exception
                raise requests.exceptions.HTTPError("无法获取任务状态，所有URL尝试失败")

            status = status_data.get("status", "unknown")
            if status != last_status:
                yield {
                    "type": "step",
                    "step": f"当前状态：{status}",
                    "steps": list(all_steps),
                    "model_used": "manus-1.6",
                }
                last_status = status

            current_documents = _extract_manus_documents(status_data)
            if current_documents:
                existing_urls = {doc["url"] for doc in all_documents}
                for doc in current_documents:
                    if doc["url"] not in existing_urls:
                        all_documents.append(doc)
                        existing_urls.add(doc["url"])

            assistant_texts: list[str] = []
            current_steps: list[str] = []
            output = status_data.get("output", [])
            for item in output:
                if item.get("role") != "assistant" or not item.get("content"):
                    continue

                for content_item in item.get("content", []):
                    content_type = content_item.get("type")
                    text = content_item.get("text")
                    if not text or not text.strip():
                        continue

                    cleaned_text = text.strip()
                    if content_type == "output_text":
                        assistant_texts.append(cleaned_text)

                    if (
                        "搜索" in cleaned_text
                        or "访问" in cleaned_text
                        or "保存" in cleaned_text
                        or content_type in ["step", "query", "action", "operation"]
                    ) and cleaned_text not in current_steps:
                        current_steps.append(cleaned_text)

            for text in assistant_texts:
                if text not in all_assistant_texts:
                    all_assistant_texts.append(text)

            for step in current_steps:
                if step not in all_steps:
                    all_steps.append(step)
                    yield {
                        "type": "step",
                        "step": step,
                        "steps": list(all_steps),
                        "model_used": "manus-1.6",
                    }

            combined_text = "\n\n".join(all_assistant_texts)
            if combined_text:
                combined_text = convert_urls_to_markdown(combined_text)
                combined_text = normalize_paragraph_spacing(combined_text, max_empty_lines=1)
                if combined_text != last_emitted_text:
                    yield {
                        "type": "replace",
                        "text": combined_text,
                        "full_text": combined_text,
                        "steps": list(all_steps),
                        "documents": list(all_documents),
                        "model_used": "manus-1.6",
                    }
                    last_emitted_text = combined_text

            if status in ["completed", "succeeded", "finished"]:
                final_text = combined_text or "对话已完成，但没有生成具体的回复内容。"
                logging.info(
                    "Manus 流式对话完成，耗时 %.2f 秒，轮询次数 %s",
                    time.time() - start_time,
                    attempt + 1,
                )
                yield {
                    "type": "complete",
                    "text": final_text,
                    "full_text": final_text,
                    "steps": list(all_steps),
                    "documents": list(all_documents),
                    "model_used": "manus-1.6",
                }
                return

            if status in ["pending", "running", "processing"]:
                time.sleep(poll_interval)
                continue

            time.sleep(poll_interval)

        yield {
            "type": "error",
            "error": f"任务轮询超时（{max_poll_attempts}次尝试，{max_poll_attempts * poll_interval}秒），任务仍未完成",
            "steps": list(all_steps),
            "documents": list(all_documents),
            "model_used": "manus-1.6",
        }
    except Exception as exc:
        logging.error(
            "Manus streaming chat exception %s: %s",
            type(exc).__name__,
            str(exc),
            exc_info=True,
        )
        yield {
            "type": "error",
            "error": f"Manus API对话异常: {type(exc).__name__}: {str(exc)}",
            "model_used": "manus-1.6",
        }
