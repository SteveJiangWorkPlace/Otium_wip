"""
提示词模板模块（清晰的版本管理）

包含所有AI交互的提示词模板定义，采用清晰的版本管理策略：

版本策略：
1. **production版本**：当前实际使用的生产版本（基于原始完整版本，确保质量和稳定性）
2. **original版本**：最初始完整版本（在注释中备份，用于参考和回滚，快捷批注已移除"灵活表达"）
3. **compact版本**：紧凑版本框架（已注释掉，具体内容已删除，用户可自行填充调试）
4. **ai_optimized版本**：AI优化版本框架（已注释掉，具体内容已删除，用户可自行填充调试）

注意：
1. 所有production版本模板都保持原始完整语义，确保翻译质量和稳定性
2. original版本在注释中完整备份，便于语义追溯和历史参考
3. compact和ai_optimized版本只保留注释框架，具体内容已删除，用户可自行填充调试
4. 快捷批注的production版本基于修改后的原始版本（移除"灵活表达"，修改"符号修正"，更新"人性化处理"）
5. 主要提示词（纠错、翻译、精修）的production和original版本内容相同，确保语义完整性
"""

# =================================================================
# 1. 智能纠错提示词模板
# =================================================================

# =================================================================
# 生产版本（当前使用）
# =================================================================
ERROR_CHECK_PRODUCTION_TEMPLATE = """校对中文文本，检查并直接修改以下文本中的三类错误：错别字、漏字和重复字。
直接修改这三类错误，不要只是标记它们。
不要修改表达方式、语法结构或其他内容。不修改专业术语，不修改写作风格，不修改标点符号（除非明显错误）。

输入文本:
{chinese_text}

输出格式:
- 返回修改后的完整文本
- 对于每处修改，用**双星号**将修改后的内容包围起来，例如"这是一个**正确**的例子"
- 不要添加任何解释或评论，只返回修改后的文本
- 如无错误，直接返回原文"""

# =================================================================
# 原始版本备份（注释形式，用于参考和回滚）
# =================================================================
# ERROR_CHECK_ORIGINAL_TEMPLATE = """校对中文文本，检查并直接修改以下文本中的三类错误：错别字、漏字和重复字。
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
# - 如无错误，直接返回原文"""
# =================================================================

# =================================================================
# 紧凑版本框架（已注释掉，具体内容已删除，用户可自行填充调试）
# =================================================================
# ERROR_CHECK_COMPACT_TEMPLATE = """[compact版本内容，用户可自行填充调试]
# {chinese_text}"""
# =================================================================

# =================================================================
# AI优化版本框架（已注释掉，具体内容已删除，用户可自行填充调试）
# =================================================================
# ERROR_CHECK_AI_OPTIMIZED_TEMPLATE = """[ai_optimized版本内容，用户可自行填充调试]
# {chinese_text}"""
# =================================================================

# =================================================================
# 2. 学术翻译提示词模板
# =================================================================

# =================================================================
# 生产版本（当前使用）
# =================================================================
TRANSLATION_PRODUCTION_TEMPLATE = """You are an expert academic translator specializing in translating Chinese academic papers into English.

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

# =================================================================
# 原始版本备份（注释形式，用于参考和回滚）
# =================================================================
# TRANSLATION_ORIGINAL_TEMPLATE = """You are an expert academic translator specializing in translating Chinese academic papers into English.
#
# **Task:** Translate the Chinese academic text into professional academic English.
#
# **Spelling Convention:** {spelling_rule}
#
# **Input (Chinese Academic Text):**
# {chinese_text}
#
# **TRANSLATION GUIDELINES:**
# 1. **Academic Style**: Maintain formal academic tone appropriate for scholarly publications.
# 2. **Technical Terminology**: Preserve specialized terminology and translate it accurately.
# 3. **Paragraph Structure**: Maintain the original paragraph structure.
# 4. **Citations**: Preserve any citation formats or references in their original form.
# 5. **Natural Translation**: Focus on accuracy and clarity rather than stylistic concerns.
# 6. {sentence_structure_rule}
# 7. **IMPORTANT - Remove Markdown**: Remove all Markdown formatting symbols like asterisks (*), double asterisks (**), underscores (_), etc. from the output. Provide clean text without any Markdown formatting.
# 8. **Punctuation with Quotation Marks**: For general text (not formal citations), always place commas, periods, and other punctuation marks OUTSIDE of quotation marks, not inside. For example, use "example", not "example,". For formal citations, maintain the original citation style's punctuation rules.
# 9. **Names Capitalization**: Always properly capitalize all personal names, organizational names, and proper nouns. Ensure that all names of people, institutions, theories named after people, etc. are correctly capitalized in the English translation.
#
# **Output:**
# Provide ONLY the translated English text without explanations, comments, or any Markdown formatting symbols."""
# =================================================================

# =================================================================
# 紧凑版本框架（已注释掉，具体内容已删除，用户可自行填充调试）
# =================================================================
# TRANSLATION_COMPACT_TEMPLATE = """[compact版本内容，用户可自行填充调试]
#
# **Spelling:** {spelling_rule}
#
# **Text to translate:**
# {chinese_text}
#
# **Rules:** [用户自行填充]"""
# =================================================================

# =================================================================
# AI优化版本框架（已注释掉，具体内容已删除，用户可自行填充调试）
# =================================================================
# TRANSLATION_AI_OPTIMIZED_TEMPLATE = """[ai_optimized版本内容，用户可自行填充调试]
#
# **Spelling:** {spelling_rule}
#
# **Text to translate:**
# {chinese_text}
#
# **Rules:** [用户自行填充]"""
# =================================================================

# TRANSLATION_COMPACT_TEMPLATE = """Translate Chinese academic text to English academic text.
#
# **Spelling:** {spelling_rule}
#
# **Text to translate:**
# {chinese_text}
#
# **Rules:**
# 1. Use formal academic tone
# 2. Preserve technical terms accurately
# 3. Keep original paragraph structure
# 4. Preserve citation formats
# 5. Focus on accuracy and clarity
# 6. {sentence_structure_rule_short}
# 7. Remove all Markdown formatting
# 8. Place punctuation outside quotation marks
# 9. Capitalize proper names correctly
#
# **Output:** Only translated English text without Markdown."""
#
# TRANSLATION_AI_OPTIMIZED_TEMPLATE = """Translate Chinese academic text to professional English academic text.
#
# **Spelling:** {spelling_rule}
#
# **Text to translate:**
# {chinese_text}
#
# **Rules:**
# 1. **Format Rules:**
#    - Remove all markdown formatting
#    - Place punctuation outside quotation marks
#    - Capitalize proper names correctly
# 2. **Style Rules:**
#    - Use formal academic tone
#    - Preserve technical terms accurately
#    - Focus on accuracy and clarity
# 3. **Structure Rules:**
#    - Keep original paragraph structure
#    - Preserve citation formats
#    - {sentence_structure_rule_optimized}
#
# **Output:** Only translated English text without markdown."""

# 句子结构规则定义（生产版本）
SENTENCE_STRUCTURE_RULES_PRODUCTION = {
    "basic": """**Sentence Structure (Basic Rule)**: Strictly avoid using the "comma + verb-ing" structure (e.g., ", revealing trends"). Instead, use relative clauses (e.g., ", which revealed..."), coordination (e.g., "and revealed..."), or start new sentences where appropriate for better flow.""",
    "professional": """**Sentence Structure Variety (Balanced Rule)**: AI models often overuse the "comma + verb-ing" structure (e.g., ", revealing trends"). Do not strictly ban it, but **use it sparingly** to avoid a repetitive "AI tone." Instead, prioritize variety by using relative clauses (e.g., ", which revealed..."), coordination (e.g., "and revealed..."), or starting new sentences where appropriate for better flow."""
}

# =================================================================
# 原始版本备份（注释形式，用于参考和回滚）
# =================================================================
# SENTENCE_STRUCTURE_RULES_ORIGINAL = {
#     "basic": """**Sentence Structure (Basic Rule)**: Strictly avoid using the "comma + verb-ing" structure (e.g., ", revealing trends"). Instead, use relative clauses (e.g., ", which revealed..."), coordination (e.g., "and revealed..."), or start new sentences where appropriate for better flow.""",
#     "professional": """**Sentence Structure Variety (Balanced Rule)**: AI models often overuse the "comma + verb-ing" structure (e.g., ", revealing trends"). Do not strictly ban it, but **use it sparingly** to avoid a repetitive "AI tone." Instead, prioritize variety by using relative clauses (e.g., ", which revealed..."), coordination (e.g., "and revealed..."), or starting new sentences where appropriate for better flow."""
# }
# =================================================================

# =================================================================
# 紧凑版本框架（已注释掉，具体内容已删除，用户可自行填充调试）
# =================================================================
# SENTENCE_STRUCTURE_RULES_COMPACT = {
#     "basic": "[compact版本内容，用户可自行填充调试]",
#     "professional": "[compact版本内容，用户可自行填充调试]"
# }
# =================================================================

# =================================================================
# AI优化版本框架（已注释掉，具体内容已删除，用户可自行填充调试）
# =================================================================
# SENTENCE_STRUCTURE_RULES_AI_OPTIMIZED = {
#     "basic": "[ai_optimized版本内容，用户可自行填充调试]",
#     "professional": "[ai_optimized版本内容，用户可自行填充调试]"
# }
# =================================================================

# 拼写规则定义（生产版本）
SPELLING_RULES_PRODUCTION = {
    "US": "American Spelling (Color, Honor, Analyze)",
    "UK": "British Spelling (Colour, Honour, Analyse)"
}

# =================================================================
# 原始版本备份（注释形式，用于参考和回滚）
# =================================================================
# SPELLING_RULES_ORIGINAL = {
#     "US": "American Spelling (Color, Honor, Analyze)",
#     "UK": "British Spelling (Colour, Honour, Analyse)"
# }
# =================================================================

# =================================================================
# 3. 英文精修提示词模板
# =================================================================

# =================================================================
# 生产版本（当前使用）
# =================================================================
ENGLISH_REFINE_PRODUCTION_TEMPLATE = """{annotation_notice}

You are an expert academic editor specializing in academic papers and scholarly writing.

**CRITICAL INSTRUCTION TYPES:**

**TYPE 1: LOCAL INSTRUCTIONS (in 【】 or [])**
- These are ATTACHED to specific sentences
- ONLY modify the sentence that IMMEDIATELY PRECEDES the instruction marker
- Example: "This is a sentence.【make it more formal】" → ONLY modify "This is a sentence."
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

# =================================================================
# 原始版本备份（注释形式，用于参考和回滚）
# =================================================================
# ENGLISH_REFINE_ORIGINAL_TEMPLATE = """{annotation_notice}
#
# You are an expert academic editor specializing in academic papers and scholarly writing.
#
# **CRITICAL INSTRUCTION TYPES:**
#
# **TYPE 1: LOCAL INSTRUCTIONS (in 【】 or [])**
# - These are ATTACHED to specific sentences
# - ONLY modify the sentence that IMMEDIATELY PRECEDES the instruction marker
# - Example: "This is a sentence.【make it more formal】" → ONLY modify "This is a sentence."
# - NEVER apply these instructions to any other sentence in the document
# - The instruction ONLY affects the ONE sentence or phrase it is directly attached to
#
# **TYPE 2: GLOBAL DIRECTIVES (listed in the section below)**
# - These apply to the ENTIRE document consistently
# - Apply these to ALL sentences throughout the text
#
# **CRITICAL RULE - READ CAREFULLY:**
# When you see "Sentence A.【instruction X】 Sentence B.", the instruction X ONLY applies to Sentence A.
# Sentence B and all other sentences should NOT be affected by instruction X.
#
# {hidden_section}
#
# **CONCRETE EXAMPLES:**
#
# Example 1:
# Input: "The study shows significant results.【use more academic vocabulary】 The data supports this conclusion."
# Correct Output: "The study **demonstrates substantial findings**. The data supports this conclusion."
# Wrong Output: "The study **demonstrates substantial findings**. The data **corroborates this assertion**." ← WRONG! The instruction should NOT affect the second sentence.
#
#
# **PROCESSING STEPS:**
# 1. Read the text sentence by sentence from beginning to end
# 2. For each sentence:
#    - Check if there is a 【】 or [] marker IMMEDIATELY AFTER it (within the same line)
#    - If YES: Apply that specific instruction to THAT SENTENCE ONLY, then move to the next sentence
#    - If NO: Only apply the GLOBAL DIRECTIVES (if any), then move to the next sentence
# 3. After processing all sentences, remove all instruction markers (【】/[]) from the output
# 4. Highlight all modified parts with double asterisks (e.g., **modified text**)
# 5. Ensure smooth transitions and maintain professional academic tone
#
# **OUTPUT REQUIREMENTS:**
# - Highlight modified parts with **double asterisks**
# - Output MUST be in ENGLISH only
# - Maintain original meaning and intent
# - NO explanations, NO comments, NO meta-text
# - ONLY output the refined text itself
#
# Now, please refine the following text, remembering that local instructions ONLY apply to the sentence they are attached to:
# {processed_text}"""
# =================================================================

# =================================================================
# 紧凑版本框架（已注释掉，具体内容已删除，用户可自行填充调试）
# =================================================================
# ENGLISH_REFINE_COMPACT_TEMPLATE = """[compact版本内容，用户可自行填充调试]
# {annotation_notice}
#
# {hidden_section}
#
# {processed_text}"""
# =================================================================

# =================================================================
# AI优化版本框架（已注释掉，具体内容已删除，用户可自行填充调试）
# =================================================================
# ENGLISH_REFINE_AI_OPTIMIZED_TEMPLATE = """[ai_optimized版本内容，用户可自行填充调试]
# {annotation_notice}
#
# {hidden_section}
#
# {processed_text}"""
# =================================================================

# =================================================================
# 4. 快捷批注模板
# =================================================================

# =================================================================
# 生产版本（当前使用 - 基于修改后的原始版本）
# =================================================================
SHORTCUT_ANNOTATIONS_PRODUCTION = {
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

# =================================================================
# 原始版本备份（注释形式，用于参考和回滚 - 已移除"灵活表达"功能）
# =================================================================
# SHORTCUT_ANNOTATIONS_ORIGINAL = {
#     "主语修正": "将所有抽象概念作为主语的句子改写为以人为主语。例如，将'The framework suggests...'改为'Researchers using this framework suggest...'",
#     "句式修正": "查找并修改所有'逗号 + -ing'结构的句子以及同位语句式。例如，将'The data was analyzed, revealing trends'改为'The data was analyzed and revealed trends'或拆分为两个句子, 将'Mr. Wang, our new project manager, will arrive tomorrow'改为'Mr. Wang is our new project manager. He will arrive tomorrow'",
#     "符号修正": "检查所有引号内容，确保逗号和句号放在闭合的引号之外。例如，将'Smith stated that \"this is important,\"'改为'Smith stated that \"this is important\",''",
#     "丰富句式": "识别句子长度过于一致的段落，调整为混合使用短句(5-10词)、中等句(15-20词)和长句(25-30词)",
#     "同义替换": "识别并替换过于学术化或AI风格的词汇，使用更简洁自然的同义词。例如，将'utilize'改为'use'，将'conceptualize'改为'think about'",
#     "去AI词汇": """通过以下规则润色英文文本：
# 严格避免使用副词+形容词以及副词+动词的组合
# 严格避免将动词ing形式作名词用法
# 将 "This [动词]..." 的独立句，改为由 "which" 连接的非限定性定语从句
# 使用分号（;）连接两个语法各自独立、但后者是前者思想的直接延续或解释的句子，以增强逻辑流动性
# 同时严格避免使用以下表达方式和词汇短语：
# 1.    用master或其衍生词代表掌握某项技能的意思
# 2.    主句 + , + -ing形式的伴随状语句式
# 3.    my goal is to
# 4.    hone
# 5.    permit
# 6.    deep comprehension
# 7.    look forward to
# 8.    address
# 9.    command
# 10.    drawn to
# 11.    delve into
# 12.    demonstrate（不要高频出现）
# 13.    draw
# 14.    drawn to
# 15.    privilege
# 16.    testament
# 17.    commitment
# 18.    tenure
# 19.    thereby
# 20.    thereby + doing
# 21.    cultivate
# 22.    Building on this
# 23.    Building on this foundation
# 24.    intend to""",
#     "人性化处理": """Revise the English text to make it sound more like a thoughtful but less confident human wrote it. You will achieve this by performing the following actions on a random selection of targets (do not change everything, aim for a 40-70% replacement rate):
# 1. Reduce Formality and Confidence: Identify strong, confident, or goal-oriented phrases and replace them with more personal, uncertain, or hopeful alternatives.
# •    Find: I will, I plan to, I aim to, my objective is to
# •    Replace with: I hope to, I would like to, I'm thinking about trying to, I want to see if I can, it might be cool to
# •    Find: This will establish, This will demonstrate, This analysis reveals
# •    Replace with: This could help show, Maybe this will point to, I feel like this shows, What I get from this is
# 2. Simplify Academic and Professional Vocabulary: Find standard academic or overly formal words and replace them with simpler, more common or colloquial equivalents.
# •    Find: utilize, employ
# •    Replace with: use, make use of
# •    Find: examine, investigate, analyze
# •    Replace with: look into, check out, figure out, get a handle on
# •    Find: furthermore, moreover, additionally
# •    Replace with: also, on top of that, and another thing is
# •    Find: consequently, therefore, thus
# •    Replace with: so, because of that, which is why
# •    Find: methodology, framework
# •    Replace with: approach, way of doing things, setup, basic idea
# •    Find: necessitates, requires
# •    Replace with: needs, means I have to
# •    Find: a pursuit of this scope
# •    Replace with: doing something this big, this kind of project
# 3. Inject Colloquial Elements:
# •    Introduce conversational filler words like just, really, kind of, sort of.
# •    Use contractions (it is -> it's, I will -> I'll, I would -> I'd).
# •    Occasionally use informal sentence starters like \"The thing is,\" or \"What I'm trying to say is,\".
# Crucial Rule: The final text should be a mixture. It should not be completely informal. The desired effect is that of a person who knows the formal language but whose natural, less certain voice is breaking through. Preserve the core ideas of the original text."""
# }
# =================================================================

# =================================================================
# 紧凑版本框架（已注释掉，具体内容已删除，用户可自行填充调试）
# =================================================================
# SHORTCUT_ANNOTATIONS_COMPACT = {
#     "主语修正": "[compact版本内容，用户可自行填充调试]",
#     "句式修正": "[compact版本内容，用户可自行填充调试]",
#     "符号修正": "[compact版本内容，用户可自行填充调试]",
#     "丰富句式": "[compact版本内容，用户可自行填充调试]",
#     "同义替换": "[compact版本内容，用户可自行填充调试]",
#     "去AI词汇": "[compact版本内容，用户可自行填充调试]",
#     "人性化处理": "[compact版本内容，用户可自行填充调试]"
# }
# =================================================================

# =================================================================
# AI优化版本框架（已注释掉，具体内容已删除，用户可自行填充调试）
# =================================================================
# SHORTCUT_ANNOTATIONS_AI_OPTIMIZED = {
#     "主语修正": "[ai_optimized版本内容，用户可自行填充调试]",
#     "句式修正": "[ai_optimized版本内容，用户可自行填充调试]",
#     "符号修正": "[ai_optimized版本内容，用户可自行填充调试]",
#     "丰富句式": "[ai_optimized版本内容，用户可自行填充调试]",
#     "同义替换": "[ai_optimized版本内容，用户可自行填充调试]",
#     "去AI词汇": "[ai_optimized版本内容，用户可自行填充调试]",
#     "人性化处理": "[ai_optimized版本内容，用户可自行填充调试]"
# }
# =================================================================

# =================================================================
# 模板版本常量
# =================================================================

TEMPLATE_VERSIONS = {
    "production": "production",    # 生产版本（当前实际使用，基于原始版本，确保稳定性）
    "original": "original",        # 原始版本备份（最长，最详细）
    "compact": "compact",          # 紧凑版本框架（具体内容已删除，用户可自行填充调试）
    "ai_optimized": "ai_optimized" # AI优化版本框架（具体内容已删除，用户可自行填充调试）
}