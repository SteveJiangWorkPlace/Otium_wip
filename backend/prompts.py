"""
Prompt构建模块（优化版本）

包含所有用于AI模型交互的prompt构建函数和快捷批注命令。
此版本集成了模板系统、缓存机制和性能监控。

主要优化：
1. 模板化：静态内容提取为常量模板，减少字符串拼接开销
2. 缓存：提示词缓存，相似文本复用构建结果
3. 监控：性能监控，记录构建时间、缓存命中率等指标
4. 多版本：支持原始、紧凑、AI优化三种模板版本
"""

import re
import time
from typing import List, Dict, Any, Optional

# 导入新模块
try:
    # 相对导入（当作为包的一部分时）
    from .prompt_templates import (
        # 纠错模板
        ERROR_CHECK_COMPACT_TEMPLATE,
        ERROR_CHECK_AI_OPTIMIZED_TEMPLATE,

        # 翻译模板
        TRANSLATION_BASE_TEMPLATE,
        TRANSLATION_COMPACT_TEMPLATE,
        TRANSLATION_AI_OPTIMIZED_TEMPLATE,
        SENTENCE_STRUCTURE_RULES,
        SENTENCE_STRUCTURE_RULES_SHORT,
        SENTENCE_STRUCTURE_RULES_OPTIMIZED,
        SPELLING_RULES,

        # 英文精修模板
        ENGLISH_REFINE_BASE_TEMPLATE,
        ENGLISH_REFINE_COMPACT_TEMPLATE,
        ENGLISH_REFINE_AI_OPTIMIZED_TEMPLATE,

        # 快捷批注模板
        SHORTCUT_ANNOTATIONS_COMPACT,
        SHORTCUT_ANNOTATIONS_AI_OPTIMIZED,
        SHORTCUT_ANNOTATIONS_HYBRID_COMPACT,
        SHORTCUT_ANNOTATIONS_HYBRID_AI_OPTIMIZED,

        # 版本常量
        TEMPLATE_VERSIONS
    )

    from .prompt_cache import prompt_cache_manager
    from .prompt_monitor import prompt_performance_monitor
except ImportError:
    # 绝对导入（当直接运行时）
    from prompt_templates import (
        ERROR_CHECK_COMPACT_TEMPLATE,
        ERROR_CHECK_AI_OPTIMIZED_TEMPLATE,
        TRANSLATION_BASE_TEMPLATE,
        TRANSLATION_COMPACT_TEMPLATE,
        TRANSLATION_AI_OPTIMIZED_TEMPLATE,
        SENTENCE_STRUCTURE_RULES,
        SENTENCE_STRUCTURE_RULES_SHORT,
        SENTENCE_STRUCTURE_RULES_OPTIMIZED,
        SPELLING_RULES,
        ENGLISH_REFINE_BASE_TEMPLATE,
        ENGLISH_REFINE_COMPACT_TEMPLATE,
        ENGLISH_REFINE_AI_OPTIMIZED_TEMPLATE,
        SHORTCUT_ANNOTATIONS_COMPACT,
        SHORTCUT_ANNOTATIONS_AI_OPTIMIZED,
        SHORTCUT_ANNOTATIONS_HYBRID_COMPACT,
        SHORTCUT_ANNOTATIONS_HYBRID_AI_OPTIMIZED,
        TEMPLATE_VERSIONS
    )

    from prompt_cache import prompt_cache_manager
    from prompt_monitor import prompt_performance_monitor


# ==========================================
# 配置常量
# ==========================================

# 默认模板版本
# 用户指定配置：
# 1. 智能纠错：使用compact版本
# 2. 学术翻译：使用ai_optimized版本，但句子结构规则使用compact版本（SENTENCE_STRUCTURE_RULES_SHORT）
# 3. 英文精修：使用ai_optimized版本
DEFAULT_TEMPLATE_VERSION = "compact"  # 智能纠错默认使用compact版本
TRANSLATION_TEMPLATE_VERSION = "ai_optimized"  # 学术翻译使用ai_optimized版本
ENGLISH_REFINE_TEMPLATE_VERSION = "ai_optimized"  # 英文精修使用ai_optimized版本

# 默认快捷批注版本
# "compact": 大部分使用紧凑版本，"去AI词汇"和"人性化处理"保留原始完整内容（根据用户要求）
# "original_compact": 纯紧凑版本（无混合，仅用于测试对比）
DEFAULT_ANNOTATIONS_VERSION = "compact"


# ==========================================
# 智能纠错提示词构建
# ==========================================

def build_error_check_prompt(chinese_text: str, template_version: str = DEFAULT_TEMPLATE_VERSION) -> str:
    """
    构建用于智能纠错的提示词（优化版本）

    Args:
        chinese_text: 中文文本
        template_version: 模板版本 ("original", "compact", "ai_optimized")

    Returns:
        构建好的提示词
    """
    # 记录开始时间
    start_time = time.time()

    # 选择模板
    if template_version == "ai_optimized":
        template = ERROR_CHECK_AI_OPTIMIZED_TEMPLATE
    else:  # 默认使用compact版本
        template = ERROR_CHECK_COMPACT_TEMPLATE

    # 构建提示词
    prompt = template.format(chinese_text=chinese_text)

    # 记录性能
    build_time = time.time() - start_time
    prompt_performance_monitor.record_function_call(
        func_name="build_error_check_prompt",
        build_time=build_time,
        prompt_length=len(prompt)
    )

    return prompt


# ==========================================
# 学术翻译提示词构建
# ==========================================

def build_academic_translate_prompt(
    chinese_text: str,
    style: str = "US",
    version: str = "professional",
    template_version: str = TRANSLATION_TEMPLATE_VERSION,
    use_cache: bool = True
) -> str:
    """
    构建翻译提示词（优化版本）

    Args:
        chinese_text: 中文文本
        style: 拼写风格 ("US", "UK")
        version: 版本 ("basic", "professional")
        template_version: 模板版本 ("original", "compact", "ai_optimized")
        use_cache: 是否使用缓存

    Returns:
        构建好的提示词
    """
    # 记录开始时间
    start_time = time.time()

    # 缓存检查
    if use_cache:
        cached_prompt = prompt_cache_manager.get(
            text=chinese_text,
            style=style,
            version=version,
            template_version=template_version
        )

        if cached_prompt is not None:
            # 记录缓存命中
            prompt_performance_monitor.record_cache_hit(True)

            # 记录性能（缓存命中）
            build_time = time.time() - start_time
            prompt_performance_monitor.record_function_call(
                func_name="build_academic_translate_prompt",
                build_time=build_time,
                prompt_length=len(cached_prompt)
            )

            return cached_prompt

    # 记录缓存未命中
    prompt_performance_monitor.record_cache_hit(False)

    # 根据模板版本选择规则
    if template_version == "original":
        # 原始版本
        template = TRANSLATION_BASE_TEMPLATE
        sentence_rule_dict = SENTENCE_STRUCTURE_RULES
        rule_param_name = "sentence_structure_rule"
    elif template_version == "ai_optimized":
        # AI优化版本（使用AI优化模板，但句子结构规则使用compact版本，根据用户要求）
        template = TRANSLATION_AI_OPTIMIZED_TEMPLATE
        sentence_rule_dict = SENTENCE_STRUCTURE_RULES_SHORT  # 使用compact版本的规则
        rule_param_name = "sentence_structure_rule_optimized"  # AI优化模板使用这个参数名
    else:
        # 紧凑版本
        template = TRANSLATION_COMPACT_TEMPLATE
        sentence_rule_dict = SENTENCE_STRUCTURE_RULES_SHORT
        rule_param_name = "sentence_structure_rule_short"

    # 获取拼写规则
    spelling_rule = SPELLING_RULES.get(style, SPELLING_RULES["US"])

    # 获取句子结构规则
    sentence_structure_rule = sentence_rule_dict.get(version, sentence_rule_dict.get("professional"))

    # 构建提示词
    prompt = template.format(
        spelling_rule=spelling_rule,
        chinese_text=chinese_text,
        **{rule_param_name: sentence_structure_rule}
    )

    # 缓存结果
    if use_cache:
        prompt_cache_manager.set(
            text=chinese_text,
            style=style,
            version=version,
            prompt=prompt,
            template_version=template_version
        )

    # 记录性能
    build_time = time.time() - start_time
    prompt_performance_monitor.record_function_call(
        func_name="build_academic_translate_prompt",
        build_time=build_time,
        prompt_length=len(prompt)
    )

    return prompt


# ==========================================
# 批注预处理函数
# ==========================================

def preprocess_annotations(text: str) -> str:
    """
    将【】批注转换为更明确的格式，确保只与前面的句子关联

    Args:
        text: 包含批注的文本

    Returns:
        处理后的文本
    """
    # 处理【】格式批注
    processed = text
    for match in re.finditer(r'([^。！？.!?]+[。！？.!?]+)【([^】]*)】', processed):
        sentence = match.group(1)
        annotation = match.group(2)
        full_match = match.group(0)
        replacement = f"{sentence}[LOCAL INSTRUCTION ONLY FOR THIS SENTENCE: {annotation}]"
        processed = processed.replace(full_match, replacement)

    # 处理[]格式批注
    for match in re.finditer(r'([^。！？.!?]+[。！？.!?]+)\[([^\]]*)\]', processed):
        sentence = match.group(1)
        annotation = match.group(2)
        full_match = match.group(0)
        replacement = f"{sentence}[LOCAL INSTRUCTION ONLY FOR THIS SENTENCE: {annotation}]"
        processed = processed.replace(full_match, replacement)

    return processed


# ==========================================
# 英文精修提示词构建
# ==========================================

def build_english_refine_prompt(
    text_with_instructions: str,
    hidden_instructions: str = "",
    annotations: Optional[List[Dict[str, Any]]] = None,
    template_version: str = ENGLISH_REFINE_TEMPLATE_VERSION
) -> str:
    """
    构建英文精修提示词（优化版本）

    Args:
        text_with_instructions: 包含批注的文本
        hidden_instructions: 隐藏的全局指令
        annotations: 批注列表
        template_version: 模板版本 ("original", "compact", "ai_optimized")

    Returns:
        构建好的提示词
    """
    # 记录开始时间
    start_time = time.time()

    # 预处理文本
    processed_text = preprocess_annotations(text_with_instructions)

    # 构建句子到批注的映射，用于提示词中的具体示例
    sentence_annotation_examples = ""
    if annotations and len(annotations) > 0:
        examples = []
        for i, anno in enumerate(annotations[:3]):  # 最多使用前3个批注作为例子
            sentence = anno['sentence'].strip()
            instruction = anno['content'].strip()
            examples.append(f"- 句子 \"{sentence}\" 有批注 \"{instruction}\"，只修改这个句子，其他句子保持不变")

        if examples:
            sentence_annotation_examples = "本文中的具体批注例子:\n" + "\n".join(examples)

    # 增强批注提示部分
    annotation_notice = ""
    if annotations and len(annotations) > 0:
        annotation_notice = f"""
**CRITICAL INSTRUCTION - LOCAL ANNOTATIONS DETECTED**

This text contains {len(annotations)} local instruction(s) marked with 【】 or [].

EXTREMELY IMPORTANT RULE:
- Each annotation MUST ONLY modify the SINGLE sentence it is attached to
- Other sentences MUST remain COMPLETELY UNCHANGED unless affected by global directives
- This is a HARD CONSTRAINT that cannot be violated under any circumstances

{sentence_annotation_examples}
"""

    hidden_section = ""
    if hidden_instructions:
        hidden_section = f"""
**GLOBAL DIRECTIVES (APPLY TO ENTIRE DOCUMENT):**

The following directives should be applied consistently throughout the ENTIRE document:

{hidden_instructions}
"""

    # 根据模板版本选择模板
    if template_version == "original":
        template = ENGLISH_REFINE_BASE_TEMPLATE
    elif template_version == "ai_optimized":
        template = ENGLISH_REFINE_AI_OPTIMIZED_TEMPLATE
    else:  # compact
        template = ENGLISH_REFINE_COMPACT_TEMPLATE

    # 构建提示词
    prompt = template.format(
        annotation_notice=annotation_notice,
        hidden_section=hidden_section,
        processed_text=processed_text
    )

    # 记录性能
    build_time = time.time() - start_time
    prompt_performance_monitor.record_function_call(
        func_name="build_english_refine_prompt",
        build_time=build_time,
        prompt_length=len(prompt)
    )

    return prompt


# ==========================================
# 快捷批注命令
# ==========================================

def get_shortcut_annotations(version: str = DEFAULT_ANNOTATIONS_VERSION) -> Dict[str, str]:
    """
    获取快捷批注命令（混合版本：大部分优化，"去AI词汇"和"人性化处理"保留原始完整内容）

    Args:
        version: 批注版本 ("compact", "ai_optimized", "original_compact", "original_ai")

    Returns:
        快捷批注字典
    """
    # 根据用户要求，"去AI词汇"和"人性化处理"必须保留原始完整内容
    # 因此默认使用混合版本
    if version == "ai_optimized":
        # AI优化版本，但关键批注使用原始完整内容
        return SHORTCUT_ANNOTATIONS_HYBRID_AI_OPTIMIZED.copy()
    elif version == "original_ai":
        # 纯AI优化版本（无混合，仅用于测试对比）
        return SHORTCUT_ANNOTATIONS_AI_OPTIMIZED.copy()
    elif version == "original_compact":
        # 纯紧凑版本（无混合，仅用于测试对比）
        return SHORTCUT_ANNOTATIONS_COMPACT.copy()
    else:  # compact 或默认
        # 紧凑版本，但关键批注使用原始完整内容
        return SHORTCUT_ANNOTATIONS_HYBRID_COMPACT.copy()


# 向后兼容：导出默认的快捷批注
SHORTCUT_ANNOTATIONS = get_shortcut_annotations(DEFAULT_ANNOTATIONS_VERSION)


# ==========================================
# 工具函数
# ==========================================

def get_prompt_stats() -> Dict[str, Any]:
    """
    获取提示词构建统计信息

    Returns:
        统计信息字典
    """
    return prompt_performance_monitor.get_report()


def get_cache_stats() -> Dict[str, Any]:
    """
    获取缓存统计信息

    Returns:
        缓存统计信息字典
    """
    return prompt_cache_manager.get_stats()


def clear_prompt_cache() -> None:
    """清空提示词缓存"""
    prompt_cache_manager.clear()


def reset_prompt_monitor() -> None:
    """重置性能监控器"""
    prompt_performance_monitor.reset_metrics()


# ==========================================
# 测试函数（开发使用）
# ==========================================

def test_prompt_build_performance() -> Dict[str, Any]:
    """
    测试提示词构建性能

    Returns:
        性能测试结果
    """
    test_text = "这是一个测试文本，用于测试提示词构建的性能。This is a test text for testing prompt building performance."

    results = {}

    # 测试纠错提示词
    start_time = time.time()
    error_check_prompt = build_error_check_prompt(test_text)
    error_check_time = time.time() - start_time

    # 测试翻译提示词（无缓存）
    start_time = time.time()
    translation_prompt = build_academic_translate_prompt(test_text, use_cache=False)
    translation_time = time.time() - start_time

    # 测试翻译提示词（有缓存）
    start_time = time.time()
    translation_prompt_cached = build_academic_translate_prompt(test_text, use_cache=True)
    translation_time_cached = time.time() - start_time

    results = {
        "error_check": {
            "time_ms": round(error_check_time * 1000, 2),
            "length": len(error_check_prompt)
        },
        "translation_no_cache": {
            "time_ms": round(translation_time * 1000, 2),
            "length": len(translation_prompt)
        },
        "translation_with_cache": {
            "time_ms": round(translation_time_cached * 1000, 2),
            "length": len(translation_prompt_cached)
        },
        "cache_stats": prompt_cache_manager.get_stats(),
        "performance_stats": prompt_performance_monitor.get_report()
    }

    return results