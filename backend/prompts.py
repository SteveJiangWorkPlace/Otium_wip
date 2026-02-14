"""
Prompt构建模块（生产版本）

包含所有用于AI模型交互的prompt构建函数和快捷批注命令。
此版本集成了模板系统、缓存机制和性能监控，使用稳定的原始提示词版本作为生产版本。

主要特性：
1. 生产稳定性：使用原始完整提示词版本作为生产版本，确保翻译质量和语义完整性
2. 缓存机制：提示词缓存，相似文本复用构建结果
3. 性能监控：性能监控，记录构建时间、缓存命中率等指标
4. 可扩展架构：保留多版本模板架构（production/original/compact/ai_optimized），便于未来优化
5. 修改后的快捷批注：production版本基于原始版本，但进行用户指定的修改

版本管理策略：
- production: 生产版本（基于原始完整版本，快捷批注进行特定修改）
- original: 原始版本备份（最初始版本，快捷批注已移除"灵活表达"）
- compact: 紧凑版本框架（具体内容已删除，用户可自行填充调试）
- ai_optimized: AI优化版本框架（具体内容已删除，用户可自行填充调试）

注意：所有主要提示词（纠错、翻译、精修）的production和original版本内容相同，确保语义完整性。
"""

import re
import time
from typing import List, Dict, Any, Optional

# 导入原始函数（从备份文件）
try:
    # 相对导入（当作为包的一部分时）
    from .prompts_backup import (
        SHORTCUT_ANNOTATIONS_ORIGINAL,
        build_error_check_prompt_original,
        build_academic_translate_prompt_original,
        build_english_refine_prompt_original
    )
    from .prompt_cache import prompt_cache_manager
    from .prompt_monitor import prompt_performance_monitor
except ImportError:
    # 绝对导入（当直接运行时）
    from prompts_backup import (
        SHORTCUT_ANNOTATIONS_ORIGINAL,
        build_error_check_prompt_original,
        build_academic_translate_prompt_original,
        build_english_refine_prompt_original
    )
    from prompt_cache import prompt_cache_manager
    from prompt_monitor import prompt_performance_monitor


# ==========================================
# 配置常量
# ==========================================

# 生产环境模板版本（稳定版本）
# 根据用户最终要求：使用原始提示词版本作为生产版本，确保质量和稳定性
PRODUCTION_TEMPLATE_VERSION = "production"  # 生产版本（基于原始版本）
DEFAULT_TEMPLATE_VERSION = PRODUCTION_TEMPLATE_VERSION  # 智能纠错使用生产版本
TRANSLATION_TEMPLATE_VERSION = PRODUCTION_TEMPLATE_VERSION  # 学术翻译使用生产版本
ENGLISH_REFINE_TEMPLATE_VERSION = PRODUCTION_TEMPLATE_VERSION  # 英文精修使用生产版本

# 默认快捷批注版本
# "production": 生产版本（基于修改后的原始版本，移除"灵活表达"，修改"符号修正"，更新"人性化处理"）
# "original": 原始版本（从prompts_backup.py导入，已移除"灵活表达"）
DEFAULT_ANNOTATIONS_VERSION = "production"

# 生产版本快捷批注命令（production版本）
# 基于原始版本，但进行用户指定的修改（移除"灵活表达"，修改"符号修正"，更新"人性化处理"）
SHORTCUT_ANNOTATIONS_MODIFIED = {
    "主语修正": "将所有抽象概念作为主语的句子改写为以人为主语。例如，将'The framework suggests...'改为'Researchers using this framework suggest...'",
    "句式修正": "查找并修改所有'逗号 + -ing'结构的句子以及同位语句式。例如，将'The data was analyzed, revealing trends'改为'The data was analyzed and revealed trends'或拆分为两个句子, 将'Mr. Wang, our new project manager, will arrive tomorrow'改为'Mr. Wang is our new project manager. He will arrive tomorrow'",
    "符号修正": "确保标点符号在引号外，同时用分号连接两个关系紧密的独立从句",
    "丰富句式": "识别句子长度过于一致的段落，调整为混合使用短句(5-10词)、中等句(15-20词)和长句(25-30词)",
    "同义替换": "识别并替换过于学术化或AI风格的词汇，使用更简洁自然的同义词。例如，将'utilize'改为'use'，将'conceptualize'改为'think about'",
    "去AI词汇": """通过以下规则润色英文文本：
严格避免使用副词+形容词以及副词+动词的组合
严格避免将动词ing形式作名词用法
将 "This [动词]..." 的独立句，改为由 "which" 连接的非限定性定语从句
使用分号（;）连接两个语法各自独立、但后者是前者思想的直接延续或解释的句子，以增强逻辑流动性
同时严格避免使用以下表达方式和词汇短语：
1.    用master或其衍生词代表掌握某项技能的意思
2.    主句 + , + -ing形式的伴随状语句式
3.    my goal is to
4.    hone
5.    permit
6.    deep comprehension
7.    look forward to
8.    address
9.    command
10.    drawn to
11.    delve into
12.    demonstrate（不要高频出现）
13.    draw
14.    drawn to
15.    privilege
16.    testament
17.    commitment
18.    tenure
19.    thereby
20.    thereby + doing
21.    cultivate
22.    Building on this
23.    Building on this foundation
24.    intend to""",
    "人性化处理": """Revise the text to sound more like a thoughtful but less confident human by selectively modifying 40-70% of the content.

1. **Reduce Formality and Confidence**:
   - Find: I will, I plan to, I aim to, my objective is to
   - Replace with: I hope to, I would like to, I'm thinking about trying to, I want to see if I can, it might be cool to
   - Find: This will establish, This will demonstrate, This analysis reveals
   - Replace with: This could help show, Maybe this will point to, I feel like this shows, What I get from this is

2. **Simplify Academic Vocabulary**:
   - Find: utilize, employ → Replace with: use, make use of
   - Find: examine, investigate, analyze → Replace with: look into, check out, figure out, get a handle on
   - Find: furthermore, moreover, additionally → Replace with: also, on top of that, and another thing is
   - Find: consequently, therefore, thus → Replace with: so, because of that, which is why
   - Find: methodology, framework → Replace with: approach, way of doing things, setup, basic idea
   - Find: necessitates, requires → Replace with: needs, means I have to
   - Find: a pursuit of this scope → Replace with: doing something this big, this kind of project

3. **Inject Conversational Elements**:
   - Use contractions (it is → it's, I will → I'll, I would → I'd)
   - Add filler words: just, really, kind of, sort of
   - Occasionally use informal starters: "The thing is," "What I'm trying to say is,"

The final text should be a natural blend of formal knowledge and a more personal voice, preserving the core ideas of the original. Aim for 40-70% replacement rate, don't change everything."""
}


# ==========================================
# 智能纠错提示词构建
# ==========================================

def build_error_check_prompt(chinese_text: str, template_version: str = DEFAULT_TEMPLATE_VERSION) -> str:
    """
    构建用于智能纠错的提示词（生产版本）

    Args:
        chinese_text: 中文文本
        template_version: 模板版本 ("production", "original") - 其他版本已不再支持

    Returns:
        构建好的提示词
    """
    # 记录开始时间
    start_time = time.time()

    # 生产版本和原始版本都使用原始完整版本（内容相同）
    prompt = build_error_check_prompt_original(chinese_text)

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
    构建翻译提示词（生产版本）

    Args:
        chinese_text: 中文文本
        style: 拼写风格 ("US", "UK")
        version: 版本 ("basic", "professional")
        template_version: 模板版本 ("production", "original") - 其他版本已不再支持
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
    # 生产版本和原始版本都使用原始函数
    if template_version in ["original", "production"]:
        # 原始版本/生产版本 - 直接调用原始函数
        prompt = build_academic_translate_prompt_original(chinese_text, style, version)
    else:
        # 其他版本（compact或ai_optimized）不再支持，回退到原始版本
        # 注意：压缩版本模板已移除，只保留生产版本
        prompt = build_academic_translate_prompt_original(chinese_text, style, version)

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
    构建英文精修提示词（生产版本）

    Args:
        text_with_instructions: 包含批注的文本
        hidden_instructions: 隐藏的全局指令
        annotations: 批注列表
        template_version: 模板版本 ("production", "original") - 其他版本已不再支持

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
    # 生产版本和原始版本都使用原始函数
    if template_version in ["original", "production"]:
        # 原始版本/生产版本 - 直接调用原始函数
        prompt = build_english_refine_prompt_original(
            text_with_instructions=text_with_instructions,
            hidden_instructions=hidden_instructions,
            annotations=annotations
        )
    else:
        # 其他版本（compact或ai_optimized）不再支持，回退到原始版本
        # 注意：压缩版本模板已移除，只保留生产版本
        prompt = build_english_refine_prompt_original(
            text_with_instructions=text_with_instructions,
            hidden_instructions=hidden_instructions,
            annotations=annotations
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
    获取快捷批注命令

    Args:
        version: 批注版本 ("production", "original", "original_modified")
        - "production": 生产版本（基于修改后的原始版本，移除"灵活表达"，修改"符号修正"，更新"人性化处理"）
        - "original": 原始版本（已移除"灵活表达"）
        - "original_modified": 向后兼容别名，等同于"production"

    Returns:
        快捷批注字典
    """
    if version == "original":
        # 完全原始版本（已移除"灵活表达"）
        return SHORTCUT_ANNOTATIONS_ORIGINAL.copy()
    elif version in ["production", "original_modified"]:
        # 生产版本/修改后的版本
        return SHORTCUT_ANNOTATIONS_MODIFIED.copy()
    else:
        # 默认返回生产版本
        return SHORTCUT_ANNOTATIONS_MODIFIED.copy()


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