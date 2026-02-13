"""
Prompt构建模块

包含所有用于AI模型交互的prompt构建函数和快捷批注命令。
"""

import re
from typing import List, Dict, Any, Optional


# ==========================================
# Prompt构建函数
# ==========================================

def build_error_check_prompt(chinese_text: str) -> str:
    """构建用于智能纠错的提示词"""
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


def build_academic_translate_prompt(chinese_text: str, style: str = "US", version: str = "professional") -> str:
    """构建翻译提示词"""
    spelling_rule = "American Spelling (Color, Honor, Analyze)" if style == "US" else "British Spelling (Colour, Honour, Analyse)"

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


def preprocess_annotations(text: str) -> str:
    """将【】批注转换为更明确的格式，确保只与前面的句子关联"""
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


def build_english_refine_prompt(
    text_with_instructions: str,
    hidden_instructions: str = "",
    annotations: Optional[List[Dict[str, Any]]] = None
) -> str:
    """构建英文精修提示词，强化局部批注的限制性"""
    # 使用改进的预处理函数
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

    return f"""
{annotation_notice}

You are an expert academic editor specializing in academic papers and scholarly writing.

**CRITICAL INSTRUCTION TYPES:**

**TYPE 1: LOCAL INSTRUCTIONS (in 【】 or [])**
- These are ATTACHED to specific sentences
- ONLY modify the sentence that IMMEDIATELY PRECEDES the instruction marker
- Example: "This is a sentence.【make it more formal】" → ONLY modify "This is a sentence."
- NEVER apply these instructions to any other sentence in the document
- The instruction ONLY affects the ONE sentence or phrase it is directly attached to
- All other sentences MUST remain COMPLETELY UNCHANGED

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
Wrong Output: "The study **demonstrates substantial findings**. The data **corroborates this assertion**." ← WRONG! The instruction should NOT affect the second sentence.


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


# ==========================================
# 快捷批注命令（与原代码完全一致）
# ==========================================

SHORTCUT_ANNOTATIONS = {
    "主语修正": "将所有抽象概念作为主语的句子改写为以人为主语。例如，将'The framework suggests...'改为'Researchers using this framework suggest...'",
    "句式修正": "查找并修改所有'逗号 + -ing'结构的句子以及同位语句式。例如，将'The data was analyzed, revealing trends'改为'The data was analyzed and revealed trends'或拆分为两个句子, 将'Mr. Wang, our new project manager, will arrive tomorrow'改为'Mr. Wang is our new project manager. He will arrive tomorrow'",
    "符号修正": "检查所有引号内容，确保逗号和句号放在闭合的引号之外。例如，将'Smith stated that \"this is important,\"'改为'Smith stated that \"this is important\",''",
    "丰富句式": "识别句子长度过于一致的段落，调整为混合使用短句(5-10词)、中等句(15-20词)和长句(25-30词)",
    "灵活表达": "在适当位置添加破折号、分号，或将某些句子改为以'And'、'But'、'However'开头，以增加文本的自然流动性",
    "同义替换": "识别并替换过于学术化或AI风格的词汇，使用更简洁自然的同义词。例如，将'utilize'改为'use'，将'conceptualize'改为'think about'",
    "去AI词汇": "通过以下规则润色英文文本：\n严格避免使用副词+形容词以及副词+动词的组合\n严格避免将动词ing形式作名词用法\n将 \"This [动词]...\" 的独立句，改为由 \"which\" 连接的非限定性定语从句\n使用分号（;）连接两个语法各自独立、但后者是前者思想的直接延续或解释的句子，以增强逻辑流动性\n同时严格避免使用以下表达方式和词汇短语：\n1.    用master或其衍生词代表掌握某项技能的意思\n2.    主句 + , + -ing形式的伴随状语句式\n3.    my goal is to\n4.    hone\n5.    permit\n6.    deep comprehension\n7.    look forward to\n8.    address\n9.    command\n10.    drawn to\n11.    delve into\n12.    demonstrate（不要高频出现）\n13.    draw\n14.    drawn to\n15.    privilege\n16.    testament\n17.    commitment\n18.    tenure\n19.    thereby\n20.    thereby + doing\n21.    cultivate\n22.    Building on this\n23.    Building on this foundation\n24.    intend to",
    "人性化处理": "Revise the English text to make it sound more like a thoughtful but less confident human wrote it. You will achieve this by performing the following actions on a random selection of targets (do not change everything, aim for a 40-70% replacement rate):\n1. Reduce Formality and Confidence: Identify strong, confident, or goal-oriented phrases and replace them with more personal, uncertain, or hopeful alternatives.\n•    Find: I will, I plan to, I aim to, my objective is to\n•    Replace with: I hope to, I would like to, I'm thinking about trying to, I want to see if I can, it might be cool to\n•    Find: This will establish, This will demonstrate, This analysis reveals\n•    Replace with: This could help show, Maybe this will point to, I feel like this shows, What I get from this is\n2. Simplify Academic and Professional Vocabulary: Find standard academic or overly formal words and replace them with simpler, more common or colloquial equivalents.\n•    Find: utilize, employ\n•    Replace with: use, make use of\n•    Find: examine, investigate, analyze\n•    Replace with: look into, check out, figure out, get a handle on\n•    Find: furthermore, moreover, additionally\n•    Replace with: also, on top of that, and another thing is\n•    Find: consequently, therefore, thus\n•    Replace with: so, because of that, which is why\n•    Find: methodology, framework\n•    Replace with: approach, way of doing things, setup, basic idea\n•    Find: necessitates, requires\n•    Replace with: needs, means I have to\n•    Find: a pursuit of this scope\n•    Replace with: doing something this big, this kind of project\n3. Inject Colloquial Elements:\n•    Introduce conversational filler words like just, really, kind of, sort of.\n•    Use contractions (it is -> it's, I will -> I'll, I would -> I'd).\n•    Occasionally use informal sentence starters like \"The thing is,\" or \"What I'm trying to say is,\".\nCrucial Rule: The final text should be a mixture. It should not be completely informal. The desired effect is that of a person who knows the formal language but whose natural, less certain voice is breaking through. Preserve the core ideas of the original text."
}