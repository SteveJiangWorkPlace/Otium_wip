"""
提示词模板模块

包含所有AI交互的提示词模板定义，分为两个版本：
1. 原始完整版本：在注释中完整备份原始提示词，供参考和回滚
2. 优化版本：经过语种优化和压缩的提示词模板

注意：所有模板都包含原始提示词的完整备份注释，确保语义可追溯。
"""

# =================================================================
# 1. 智能纠错提示词模板
# =================================================================

# =================================================================
# 原始提示词备份（完整保留）
# =================================================================
# 原始版本（241字符）：
# 校对中文文本，检查并直接修改以下文本中的三类错误：错别字、漏字和重复字。
# 直接修改这三类错误，不要只是标记它们。
# 不要修改表达方式、语法结构或其他内容。不修改专业术语，不修改写作风格，不修改标点符号（除非明显错误）。
#
# 输入文本:
# {chinese_text}
#
# 输出格式:
# - 返回修改后的完整文本
# - 对于每处修改，用**双星号**将修改后的内容包围起来，例如"这是一个**正确**的例子"
# - 不要添加任何解释或评论，只返回修改后的文本
# - 如无错误，直接返回原文
# =================================================================

ERROR_CHECK_COMPACT_TEMPLATE = """检查并修改中文文本中的错误：错别字、漏字和重复字。

直接修改错误，不要只是标记。
只修改这三类错误，其他内容保持不变。

输入文本:
{chinese_text}

输出要求:
- 返回修改后的完整文本
- 修改处用**双星号**包围
- 无错误则返回原文
- 不添加解释或评论"""

ERROR_CHECK_AI_OPTIMIZED_TEMPLATE = """检查并修改中文文本中的三类错误：错别字、漏字、重复字。

直接修改错误，不要只是标记。
只修改这三类错误，其他内容保持不变。

输入文本:
{chinese_text}

输出:
- 修改后的完整文本
- 修改处用**标出
- 无错误则返回原文
- 无解释"""

# =================================================================
# 2. 学术翻译提示词模板
# =================================================================

# =================================================================
# 原始提示词备份（完整保留）
# =================================================================
# 原始版本（2136字符）：
# 完整提示词包含9条详细指导原则，见 prompts.py 中的 build_academic_translate_prompt 函数
# 主要包含：
# 1. 学术风格：保持正式的学术语气
# 2. 技术术语：准确保留专业术语
# 3. 段落结构：保持原始段落结构
# 4. 引用格式：保留原始引用格式
# 5. 自然翻译：注重准确性和清晰度
# 6. 句子结构指导原则（基本版或专业版）
# 7. 移除Markdown：删除所有Markdown格式符号
# 8. 引号标点：将标点放在引号外
# 9. 名称大写：正确大写专有名词
# =================================================================

TRANSLATION_BASE_TEMPLATE = """You are an expert academic translator specializing in translating Chinese academic papers into English.

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
6. {sentence_structure_rule}
7. **IMPORTANT - Remove Markdown**: Remove all Markdown formatting symbols like asterisks (*), double asterisks (**), underscores (_), etc. from the output. Provide clean text without any Markdown formatting.
8. **Punctuation with Quotation Marks**: For general text (not formal citations), always place commas, periods, and other punctuation marks OUTSIDE of quotation marks, not inside. For example, use "example", not "example,". For formal citations, maintain the original citation style's punctuation rules.
9. **Names Capitalization**: Always properly capitalize all personal names, organizational names, and proper nouns. Ensure that all names of people, institutions, theories named after people, etc. are correctly capitalized in the English translation.

**Output:**
Provide ONLY the translated English text without explanations, comments, or any Markdown formatting symbols."""

TRANSLATION_COMPACT_TEMPLATE = """Translate Chinese academic text to English academic text.

**Spelling:** {spelling_rule}

**Text to translate:**
{chinese_text}

**Rules:**
1. Use formal academic tone
2. Preserve technical terms accurately
3. Keep original paragraph structure
4. Preserve citation formats
5. Focus on accuracy and clarity
6. {sentence_structure_rule_short}
7. Remove all Markdown formatting
8. Place punctuation outside quotation marks
9. Capitalize proper names correctly

**Output:** Only translated English text without Markdown."""

TRANSLATION_AI_OPTIMIZED_TEMPLATE = """Translate Chinese academic text to professional English academic text.

**Spelling:** {spelling_rule}

**Text to translate:**
{chinese_text}

**Rules:**
1. **Format Rules:**
   - Remove all markdown formatting
   - Place punctuation outside quotation marks
   - Capitalize proper names correctly
2. **Style Rules:**
   - Use formal academic tone
   - Preserve technical terms accurately
   - Focus on accuracy and clarity
3. **Structure Rules:**
   - Keep original paragraph structure
   - Preserve citation formats
   - {sentence_structure_rule_optimized}

**Output:** Only translated English text without markdown."""

# 句子结构规则定义
SENTENCE_STRUCTURE_RULES = {
    "basic": """**Sentence Structure (Basic Rule)**: Strictly avoid using the "comma + verb-ing" structure (e.g., ", revealing trends"). Instead, use relative clauses (e.g., ", which revealed..."), coordination (e.g., "and revealed..."), or start new sentences where appropriate for better flow.""",
    "professional": """**Sentence Structure Variety (Balanced Rule)**: AI models often overuse the "comma + verb-ing" structure (e.g., ", revealing trends"). Do not strictly ban it, but **use it sparingly** to avoid a repetitive "AI tone." Instead, prioritize variety by using relative clauses (e.g., ", which revealed..."), coordination (e.g., "and revealed..."), or starting new sentences where appropriate for better flow."""
}

SENTENCE_STRUCTURE_RULES_SHORT = {
    "basic": "Strictly Avoid 'comma + verb-ing' structures. Use relative clauses or start new sentences.",
    "professional": "Use 'comma + verb-ing' sparingly to avoid AI tone. Prefer relative clauses."
}

SENTENCE_STRUCTURE_RULES_OPTIMIZED = {
    "basic": "Avoid 'comma + -ing' structures. Use relative clauses or new sentences.",
    "professional": "Use 'comma + -ing' structures sparingly. Prefer relative clauses for variety."
}

# 拼写规则定义
SPELLING_RULES = {
    "US": "American Spelling (Color, Honor, Analyze)",
    "UK": "British Spelling (Colour, Honour, Analyse)"
}

# =================================================================
# 3. 英文精修提示词模板
# =================================================================

# =================================================================
# 原始提示词备份（完整保留）
# =================================================================
# 原始版本（3153字符）：
# 完整提示词包含复杂的局部批注处理规则、全局指令和详细示例
# 主要强调：局部批注（【】或[]）只修改前面的句子，不影响其他句子
# 包含CRITICAL INSTRUCTION TYPES说明、具体示例和处理步骤
# =================================================================

ENGLISH_REFINE_BASE_TEMPLATE = """{annotation_notice}

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
{processed_text}"""

ENGLISH_REFINE_COMPACT_TEMPLATE = """{annotation_notice}

You are an expert academic editor.

**Instruction Types:**
1. **Local Instructions** (in 【】or []):
   - Apply ONLY to the preceding sentence
   - Example: "Text A.【instruction】 Text B." → Modify A only, keep B unchanged
2. **Global Directives**: Apply to entire document

**Critical Rule:**
Local instructions do NOT affect other sentences.

{hidden_section}

**Processing Steps:**
1. Read text sentence by sentence
2. For each sentence:
   - Apply local instruction if present
   - Apply global directives
3. Remove instruction markers
4. Highlight changes with **
5. Output refined text only

**Output:**
- Refined English text with changes highlighted
- No explanations or comments
{processed_text}"""

ENGLISH_REFINE_AI_OPTIMIZED_TEMPLATE = """Edit English academic text following instructions.

**Instruction Types:**
1. **Local Instructions** (in 【】or []):
   - Apply ONLY to the preceding sentence
   - Example: "Text A.【instruction】 Text B." → Modify A only, keep B unchanged
2. **Global Directives**: Apply to entire document

**Critical Rule:**
Local instructions do NOT affect other sentences.

{hidden_section}

**Processing Steps:**
1. Read text sentence by sentence
2. For each sentence:
   - Apply local instruction if present
   - Apply global directives
3. Remove instruction markers
4. Highlight changes with **
5. Output refined text only

**Output:**
- Refined English text with changes highlighted
- No explanations or comments
{processed_text}"""

# =================================================================
# 4. 快捷批注模板
# =================================================================

# =================================================================
# 原始快捷批注备份（完整保留）
# =================================================================
# 包含8个批注命令，其中最长的"人性化处理"2154字符，"去AI词汇"632字符
# 具体内容见 prompts.py 中的 SHORTCUT_ANNOTATIONS 字典
# =================================================================

SHORTCUT_ANNOTATIONS_COMPACT = {
    "主语修正": "将抽象概念主语改为人为主语（如'The framework suggests'→'Researchers using this framework suggest'）",
    "句式修正": "修改'逗号 + -ing'结构和同位语句式（拆分为更自然的句子）",
    "符号修正": "确保标点符号在引号外，同时用分号连接两个关系紧密的独立从句",
    "丰富句式": "混合使用不同长度的句子（短、中、长句）",
    "同义替换": "替换过于学术化的词汇为更自然的表达",
    "去AI词汇": "避免AI写作常用词汇和句式（详细规则列表简化）",
    "人性化处理": "Revise the text to sound more like a thoughtful but less confident human by selectively modifying 40-70% of the content. This involves softening strong, goal-oriented phrases into more personal and uncertain alternatives (e.g., \"I will\" becomes \"I hope to\"), simplifying formal vocabulary to common equivalents (e.g., \"utilize\" to \"use,\" \"consequently\" to \"so\"), and injecting conversational elements like contractions (it's, I'd) and fillers (kind of, just). The final text should be a natural blend of formal knowledge and a more personal voice, preserving the core ideas of the original."
}

SHORTCUT_ANNOTATIONS_AI_OPTIMIZED = {
    "主语修正": "将抽象主语改为人为主语",
    "句式修正": "修改'逗号+-ing'和同位语句式",
    "符号修正": "标点在引号外，同时用分号连接独立从句",
    "丰富句式": "混合使用不同长度句子",
    "同义替换": "替换学术化词汇为更自然表达",
    "去AI词汇": "避免AI常用词汇和句式",
    "人性化处理": "Revise the text to sound more like a thoughtful but less confident human by selectively modifying 40-70% of the content. This involves softening strong, goal-oriented phrases into more personal and uncertain alternatives (e.g., \"I will\" becomes \"I hope to\"), simplifying formal vocabulary to common equivalents (e.g., \"utilize\" to \"use,\" \"consequently\" to \"so\"), and injecting conversational elements like contractions (it's, I'd) and fillers (kind of, just). The final text should be a natural blend of formal knowledge and a more personal voice, preserving the core ideas of the original."
}

# 混合版本：大部分使用优化内容，但"去AI词汇"和"人性化处理"使用原始完整内容
SHORTCUT_ANNOTATIONS_HYBRID_COMPACT = {
    "主语修正": "将抽象概念主语改为人为主语（如'The framework suggests'→'Researchers using this framework suggest'）",
    "句式修正": "修改'逗号 + -ing'结构和同位语句式（拆分为更自然的句子）",
    "符号修正": "确保标点符号在引号外，同时用分号连接两个关系紧密的独立从句",
    "丰富句式": "混合使用不同长度的句子（短、中、长句）",
    "同义替换": "替换过于学术化的词汇为更自然的表达",
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
    "人性化处理": """Revise the text to sound more like a thoughtful but less confident human by selectively modifying 40-70% of the content. This involves softening strong, goal-oriented phrases into more personal and uncertain alternatives (e.g., "I will" becomes "I hope to"), simplifying formal vocabulary to common equivalents (e.g., "utilize" to "use," "consequently" to "so"), and injecting conversational elements like contractions (it's, I'd) and fillers (kind of, just). The final text should be a natural blend of formal knowledge and a more personal voice, preserving the core ideas of the original."""
}

SHORTCUT_ANNOTATIONS_HYBRID_AI_OPTIMIZED = {
    "主语修正": "将抽象主语改为人为主语",
    "句式修正": "修改'逗号+-ing'和同位语句式",
    "符号修正": "标点在引号外，同时用分号连接独立从句",
    "丰富句式": "混合使用不同长度句子",
    "同义替换": "替换学术化词汇为更自然表达",
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
    "人性化处理": """Revise the text to sound more like a thoughtful but less confident human by selectively modifying 40-70% of the content. This involves softening strong, goal-oriented phrases into more personal and uncertain alternatives (e.g., "I will" becomes "I hope to"), simplifying formal vocabulary to common equivalents (e.g., "utilize" to "use," "consequently" to "so"), and injecting conversational elements like contractions (it's, I'd) and fillers (kind of, just). The final text should be a natural blend of formal knowledge and a more personal voice, preserving the core ideas of the original."""
}

# =================================================================
# 模板版本常量
# =================================================================

TEMPLATE_VERSIONS = {
    "original": "original",      # 原始版本（最长，最详细）
    "compact": "compact",        # 紧凑版本（中等压缩）
    "ai_optimized": "ai_optimized"  # AI优化版本（最简，AI最易理解）
}