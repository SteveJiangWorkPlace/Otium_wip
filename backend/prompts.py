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
from typing import Any

# 导入缓存和监控模块
from prompt_cache import prompt_cache_manager
from prompt_monitor import prompt_performance_monitor

# ==========================================
# 原始提示词函数（原位于 prompts_backup.py）
# ==========================================


def build_error_check_prompt_original(chinese_text: str) -> str:
    """原始智能纠错提示词构建函数"""
    return f"""
校对中文文本，检查并直接修改以下文本中的三类错误：错别字、漏字和重复字。
直接修改这三类错误，不要只是标记它们。
不要修改表达方式、语法结构或其他内容。不修改专业术语，不修改写作风格，不修改标点符号（除非明显错误）。

输入文本:
{chinese_text}

输出格式:
- 返回修改后的完整文本
- 对于每处修改，用**双星号**将修改后的内容包围起来，例如"这是一个**正确**的例子"
- 不要添加任何解释或评论，只返回修改后的文本
- 如无错误，直接返回原文
"""


def build_academic_translate_prompt_original(
    chinese_text: str, style: str = "US", version: str = "professional"
) -> str:
    """原始学术翻译提示词构建函数"""
    spelling_rule = (
        "American Spelling (Color, Honor, Analyze)"
        if style == "US"
        else "British Spelling (Colour, Honour, Analyse)"
    )

    if version == "basic":
        sentence_structure_guideline = """**Sentence Structure (Basic Rule)**: Strictly avoid using the "comma + verb-ing" structure (e.g., ", revealing trends"). Instead, use relative clauses (e.g., ", which revealed..."), coordination (e.g., "and revealed..."), or start new sentences where appropriate for better flow."""
    else:
        sentence_structure_guideline = """**Sentence Structure Variety (Balanced Rule)**: AI models often overuse the "comma + verb-ing" structure (e.g., ", revealing trends"). Do not strictly ban it, but **use it sparingly** to avoid a repetitive "AI tone." Instead, prioritize variety by using relative clauses (e.g., ", which revealed..."), coordination (e.g., "and revealed..."), or starting new sentences where appropriate for better flow."""

    return f"""
    You are an expert academic translator specializing in translating Chinese academic papers into English.

    **Task:** Translate the Chinese academic text into professional academic English.

    **Spelling Convention:** {spelling_rule}

    **Input (Chinese Academic Text):**
    {chinese_text}

    **TRANSLATION GUIDELINES:**
    1. **Academic Style**: Maintain formal academic tone appropriate for scholarly publications.
    2. **Technical Terminology**: Preserve specialized terminology and translate it accurately.
    3. **Paragraph Structure**: Maintain the original paragraph structure.
    4. **Citations**: Preserve any citation formats or references in their original form.
    5. **Natural Translation**: Focus on accuracy and clarity rather than stylistic concerns.
    6. {sentence_structure_guideline}
    7. **IMPORTANT - Remove Markdown**: Remove all Markdown formatting symbols like asterisks (*), double asterisks (**), underscores (_), etc. from the output. Provide clean text without any Markdown formatting.
    8. **Punctuation with Quotation Marks**: For general text (not formal citations), always place commas, periods, and other punctuation marks OUTSIDE of quotation marks, not inside. For example, use "example", not "example,". For formal citations, maintain the original citation style's punctuation rules.
    9. **Names Capitalization**: Always properly capitalize all personal names, organizational names, and proper nouns. Ensure that all names of people, institutions, theories named after people, etc. are correctly capitalized in the English translation.

    **Output:**
    Provide ONLY the translated English text without explanations, comments, or any Markdown formatting symbols.
    """


# 原始批注预处理函数（与 preprocess_annotations 相同）
def preprocess_annotations_original(text: str) -> str:
    """预处理文本中的中文批注，将其转换为AI可理解的指令格式

    处理两种格式的中文批注：
    1. 【批注内容】格式：句子末尾的中文方括号批注
    2. [批注内容]格式：句子末尾的英文方括号批注

    将批注转换为标准格式：[LOCAL INSTRUCTION ONLY FOR THIS SENTENCE: 批注内容]

    Args:
        text: 包含中文批注的文本字符串

    Returns:
        str: 处理后的文本，批注已转换为标准格式

    Raises:
        无: 函数使用正则表达式匹配，不会抛出异常

    Examples:
        >>> preprocess_annotations_original("这是一个句子。【需要翻译】")
        '这是一个句子。[LOCAL INSTRUCTION ONLY FOR THIS SENTENCE: 需要翻译]'
        >>> preprocess_annotations_original("另一个句子。[保持原意]")
        '另一个句子。[LOCAL INSTRUCTION ONLY FOR THIS SENTENCE: 保持原意]'

    Notes:
        - 批注必须紧跟在句子标点（。！？.!?）之后
        - 支持嵌套在引号内的批注处理
        - 函数不会修改文本的其他部分
    """
    # 处理【】格式批注
    processed = text
    for match in re.finditer(r"([^。！？.!?]+[。！？.!?]+)【([^】]*)】", processed):
        sentence = match.group(1)
        annotation = match.group(2)
        full_match = match.group(0)
        replacement = f"{sentence}[LOCAL INSTRUCTION ONLY FOR THIS SENTENCE: {annotation}]"
        processed = processed.replace(full_match, replacement)

    # 处理[]格式批注
    for match in re.finditer(r"([^。！？.!?]+[。！？.!?]+)\[([^\]]*)\]", processed):
        sentence = match.group(1)
        annotation = match.group(2)
        full_match = match.group(0)
        replacement = f"{sentence}[LOCAL INSTRUCTION ONLY FOR THIS SENTENCE: {annotation}]"
        processed = processed.replace(full_match, replacement)

    return processed


def build_english_refine_prompt_original(
    text_with_instructions: str,
    hidden_instructions: str = "",
    annotations: list[dict[str, Any]] | None = None,
) -> str:
    """原始英文精修提示词构建函数"""
    # 使用改进的预处理函数
    processed_text = preprocess_annotations_original(text_with_instructions)

    # 构建句子到批注的映射，用于提示词中的具体示例
    sentence_annotation_examples = ""
    if annotations and len(annotations) > 0:
        examples = []
        for anno in annotations[:3]:  # 最多使用前3个批注作为例子
            sentence = anno["sentence"].strip()
            instruction = anno["content"].strip()
            examples.append(
                f'- 句子 "{sentence}" 有批注 "{instruction}"，只修改这个句子，其他句子保持不变'
            )

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

    return f"""
{annotation_notice}

You are an expert academic editor specializing in academic papers and scholarly writing.

**CRITICAL INSTRUCTION TYPES:**

**TYPE 1: LOCAL INSTRUCTIONS (in 【】 or [])**
- These are ATTACHED to specific sentences
- ONLY modify the sentence that IMMEDIATELY PRECEDES the instruction marker
- Example: "This is a sentence.【make it more formal】" -> ONLY modify "This is a sentence."
- NEVER apply these instructions to any other sentence in the document
- The instruction ONLY affects the ONE sentence or phrase it is directly attached to

**TYPE 2: GLOBAL DIRECTIVES (listed in the section below)**
- These apply to the ENTIRE document consistently
- Apply these to ALL sentences throughout the text

**CRITICAL RULE - READ CAREFULLY:**
When you see "Sentence A.【instruction X】 Sentence B.", the instruction X ONLY applies to Sentence A.
Sentence B and all other sentences should NOT be affected by instruction X.

{hidden_section}

**CONCRETE EXAMPLES:**

Example 1:
Input: "The study shows significant results.【use more academic vocabulary】 The data supports this conclusion."
Correct Output: "The study **demonstrates substantial findings**. The data supports this conclusion."
Wrong Output: "The study **demonstrates substantial findings**. The data **corroborates this assertion**." <- WRONG! The instruction should NOT affect the second sentence.


**PROCESSING STEPS:**
1. Read the text sentence by sentence from beginning to end
2. For each sentence:
   - Check if there is a 【】 or [] marker IMMEDIATELY AFTER it (within the same line)
   - If YES: Apply that specific instruction to THAT SENTENCE ONLY, then move to the next sentence
   - If NO: Only apply the GLOBAL DIRECTIVES (if any), then move to the next sentence
3. After processing all sentences, remove all instruction markers (【】/[]) from the output
4. Highlight all modified parts with double asterisks (e.g., **modified text**)
5. Ensure smooth transitions and maintain professional academic tone

**OUTPUT REQUIREMENTS:**
- Highlight modified parts with **double asterisks**
- Output MUST be in ENGLISH only
- Maintain original meaning and intent
- NO explanations, NO comments, NO meta-text
- ONLY output the refined text itself

Now, please refine the following text, remembering that local instructions ONLY apply to the sentence they are attached to:
{processed_text}
"""


# 原始快捷批注命令（完全一致）
SHORTCUT_ANNOTATIONS_ORIGINAL = {
    "主语修正": "将所有抽象概念作为主语的句子改写为以人为主语。例如，将'The framework suggests...'改为'Researchers using this framework suggest...'",
    "句式修正": "查找并修改所有'逗号 + -ing'结构的句子以及同位语句式。例如，将'The data was analyzed, revealing trends'改为'The data was analyzed and revealed trends'或拆分为两个句子, 将'Mr. Wang, our new project manager, will arrive tomorrow'改为'Mr. Wang is our new project manager. He will arrive tomorrow'",
    "符号修正": "检查所有引号内容，确保逗号和句号放在闭合的引号之外。例如，将'Smith stated that \"this is important,\"'改为'Smith stated that \"this is important\",''",
    "丰富句式": "识别句子长度过于一致的段落，调整为混合使用短句(5-10词)、中等句(15-20词)和长句(25-30词)",
    "同义替换": "识别并替换过于学术化或AI风格的词汇，使用更简洁自然的同义词。例如，将'utilize'改为'use'，将'conceptualize'改为'think about'",
    "去AI词汇": '通过以下规则润色英文文本：\n严格避免使用副词+形容词以及副词+动词的组合\n严格避免将动词ing形式作名词用法\n将 "This [动词]..." 的独立句，改为由 "which" 连接的非限定性定语从句\n使用分号（;）连接两个语法各自独立、但后者是前者思想的直接延续或解释的句子，以增强逻辑流动性\n同时严格避免使用以下表达方式和词汇短语：\n1.    用master或其衍生词代表掌握某项技能的意思\n2.    主句 + , + -ing形式的伴随状语句式\n3.    my goal is to\n4.    hone\n5.    permit\n6.    deep comprehension\n7.    look forward to\n8.    address\n9.    command\n10.    drawn to\n11.    delve into\n12.    demonstrate（不要高频出现）\n13.    draw\n14.    drawn to\n15.    privilege\n16.    testament\n17.    commitment\n18.    tenure\n19.    thereby\n20.    thereby + doing\n21.    cultivate\n22.    Building on this\n23.    Building on this foundation\n24.    intend to',
    "人性化处理": "Revise the English text to make it sound more like a thoughtful but less confident human wrote it. You will achieve this by performing the following actions on a random selection of targets (do not change everything, aim for a 40-70% replacement rate):\n1. Reduce Formality and Confidence: Identify strong, confident, or goal-oriented phrases and replace them with more personal, uncertain, or hopeful alternatives.\n-    Find: I will, I plan to, I aim to, my objective is to\n-    Replace with: I hope to, I would like to, I'm thinking about trying to, I want to see if I can, it might be cool to\n-    Find: This will establish, This will demonstrate, This analysis reveals\n-    Replace with: This could help show, Maybe this will point to, I feel like this shows, What I get from this is\n2. Simplify Academic and Professional Vocabulary: Find standard academic or overly formal words and replace them with simpler, more common or colloquial equivalents.\n-    Find: utilize, employ\n-    Replace with: use, make use of\n-    Find: examine, investigate, analyze\n-    Replace with: look into, check out, figure out, get a handle on\n-    Find: furthermore, moreover, additionally\n-    Replace with: also, on top of that, and another thing is\n-    Find: consequently, therefore, thus\n-    Replace with: so, because of that, which is why\n-    Find: methodology, framework\n-    Replace with: approach, way of doing things, setup, basic idea\n-    Find: necessitates, requires\n-    Replace with: needs, means I have to\n-    Find: a pursuit of this scope\n-    Replace with: doing something this big, this kind of project\n3. Inject Colloquial Elements:\n-    Introduce conversational filler words like just, really, kind of, sort of.\n-    Use contractions (it is -> it's, I will -> I'll, I would -> I'd).\n-    Occasionally use informal sentence starters like \"The thing is,\" or \"What I'm trying to say is,\".\nCrucial Rule: The final text should be a mixture. It should not be completely informal. The desired effect is that of a person who knows the formal language but whose natural, less certain voice is breaking through. Preserve the core ideas of the original text.",
}


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
严格避免使用副词
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
   - Find: utilize, employ -> Replace with: use, make use of
   - Find: examine, investigate, analyze -> Replace with: look into, check out, figure out, get a handle on
   - Find: furthermore, moreover, additionally -> Replace with: also, on top of that, and another thing is
   - Find: consequently, therefore, thus -> Replace with: so, because of that, which is why
   - Find: methodology, framework -> Replace with: approach, way of doing things, setup, basic idea
   - Find: necessitates, requires -> Replace with: needs, means I have to
   - Find: a pursuit of this scope -> Replace with: doing something this big, this kind of project

3. **Inject Conversational Elements**:
   - Use contractions (it is -> it's, I will -> I'll, I would -> I'd)
   - Add filler words: just, really, kind of, sort of
   - Occasionally use informal starters: "The thing is," "What I'm trying to say is,"

The final text should be a natural blend of formal knowledge and a more personal voice, preserving the core ideas of the original. Aim for 40-70% replacement rate, don't change everything.""",
}


# ==========================================
# 智能纠错提示词构建
# ==========================================


def build_error_check_prompt(
    chinese_text: str, template_version: str = DEFAULT_TEMPLATE_VERSION
) -> str:
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
        prompt_length=len(prompt),
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
    use_cache: bool = True,
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
            template_version=template_version,
        )

        if cached_prompt is not None:
            # 类型断言，确保不是None
            assert cached_prompt is not None
            # 记录缓存命中
            prompt_performance_monitor.record_cache_hit(True)

            # 记录性能（缓存命中）
            build_time = time.time() - start_time
            prompt_performance_monitor.record_function_call(
                func_name="build_academic_translate_prompt",
                build_time=build_time,
                prompt_length=len(cached_prompt),
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
            template_version=template_version,
        )

    # 记录性能
    build_time = time.time() - start_time
    prompt_performance_monitor.record_function_call(
        func_name="build_academic_translate_prompt",
        build_time=build_time,
        prompt_length=len(prompt),
    )

    return prompt


# ==========================================
# 批注预处理函数
# ==========================================


# ==========================================
# 英文精修提示词构建
# ==========================================


def build_english_refine_prompt(
    text_with_instructions: str,
    hidden_instructions: str = "",
    annotations: list[dict[str, Any]] | None = None,
    template_version: str = ENGLISH_REFINE_TEMPLATE_VERSION,
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

    # 根据模板版本选择模板
    # 生产版本和原始版本都使用原始函数
    if template_version in ["original", "production"]:
        # 原始版本/生产版本 - 直接调用原始函数
        prompt = build_english_refine_prompt_original(
            text_with_instructions=text_with_instructions,
            hidden_instructions=hidden_instructions,
            annotations=annotations,
        )
    else:
        # 其他版本（compact或ai_optimized）不再支持，回退到原始版本
        # 注意：压缩版本模板已移除，只保留生产版本
        prompt = build_english_refine_prompt_original(
            text_with_instructions=text_with_instructions,
            hidden_instructions=hidden_instructions,
            annotations=annotations,
        )

    # 记录性能
    build_time = time.time() - start_time
    prompt_performance_monitor.record_function_call(
        func_name="build_english_refine_prompt",
        build_time=build_time,
        prompt_length=len(prompt),
    )

    return prompt


# ==========================================
# 快捷批注命令
# ==========================================


def get_shortcut_annotations(
    version: str = DEFAULT_ANNOTATIONS_VERSION,
) -> dict[str, str]:
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


def get_prompt_stats() -> dict[str, Any]:
    """
    获取提示词构建统计信息

    Returns:
        统计信息字典
    """
    return prompt_performance_monitor.get_report()


def get_cache_stats() -> dict[str, Any]:
    """
    获取缓存统计信息

    Returns:
        缓存统计信息字典
    """
    return prompt_cache_manager.get_stats()


def clear_prompt_cache() -> None:
    """清空提示词缓存管理器中的所有缓存条目

    调用prompt_cache_manager的clear()方法，移除所有缓存的提示词构建结果。
    用于开发调试或需要强制刷新缓存的场景。

    Returns:
        None: 函数无返回值，直接修改缓存管理器状态

    Raises:
        无: 函数内部处理所有异常，不会向外抛出

    Examples:
        >>> clear_prompt_cache()
        # 缓存已清空，后续提示词构建将重新生成

    Notes:
        - 清空缓存会立即生效，但不会影响已发出的API请求
        - 生产环境中慎用，可能导致短时间内性能下降
        - 可通过API端点 /api/debug/prompt-cache/clear 调用此功能
    """
    prompt_cache_manager.clear()


def reset_prompt_monitor() -> None:
    """重置提示词性能监控器的所有统计数据

    调用prompt_performance_monitor的reset_metrics()方法，将监控器计数器归零。
    用于开发调试或需要重新开始统计的场景。

    Returns:
        None: 函数无返回值，直接修改监控器状态

    Raises:
        无: 函数内部处理所有异常，不会向外抛出

    Examples:
        >>> reset_prompt_monitor()
        # 性能监控器已重置，所有统计从零开始

    Notes:
        - 重置会清除以下统计数据：构建次数、总构建时间、缓存命中率等
        - 生产环境中慎用，会丢失历史性能数据
        - 可通过API端点 /api/debug/prompt-metrics 查看监控数据
    """
    prompt_performance_monitor.reset_metrics()


# ==========================================
# 测试函数（开发使用）
# ==========================================


def test_prompt_build_performance() -> dict[str, Any]:
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
            "length": len(error_check_prompt),
        },
        "translation_no_cache": {
            "time_ms": round(translation_time * 1000, 2),
            "length": len(translation_prompt),
        },
        "translation_with_cache": {
            "time_ms": round(translation_time_cached * 1000, 2),
            "length": len(translation_prompt_cached),
        },
        "cache_stats": prompt_cache_manager.get_stats(),
        "performance_stats": prompt_performance_monitor.get_report(),
    }

    return results
