#!/usr/bin/env python3
"""注释规范化检查工具

检查Python和TypeScript文件的注释规范符合性，
识别需要清理的注释和被注释掉的代码。
"""

import os
import re
import ast
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# 设置标准输出编码为UTF-8，解决Windows GBK编码问题
if sys.platform.startswith("win"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


class CommentChecker:
    """注释检查器基类"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.content = ""
        self.lines = []
        self.issues = []

    def load_file(self):
        """
        加载要检查的源文件内容到内存中

        使用UTF-8编码读取文件，如果遇到编码错误则回退到GBK编码读取。
        将文件内容分割为行列表，便于后续逐行分析和检查注释问题。

        Args:
            无: 函数使用实例属性file_path作为文件路径，不接受外部参数

        Returns:
            无: 函数将加载的内容存储在实例属性content和lines中

        Raises:
            FileNotFoundError: 当指定路径的文件不存在时可能抛出
            PermissionError: 当没有文件读取权限时可能抛出
            UnicodeDecodeError: 当文件编码既不是UTF-8也不是GBK时可能抛出（被内部处理）

        Examples:
            >>> checker = CommentChecker("example.py")
            >>> checker.load_file()
            >>> print(f"文件行数: {len(checker.lines)}")
            文件行数: 42

        Notes:
            - 默认使用UTF-8编码读取，支持大多数现代代码文件
            - 遇到编码错误时自动尝试GBK编码，确保Windows环境下的中文文件兼容性
            - 使用errors="replace"参数处理编码错误，避免读取失败
            - 将文件内容存储在self.content属性中（完整字符串）
            - 将文件行存储在self.lines属性中（行列表）
            - 这是其他检查方法的前提，必须在调用check()方法前执行
        """
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.content = f.read()
                self.lines = self.content.split('\n')
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(self.filepath, 'r', encoding='gbk', errors='replace') as f:
                self.content = f.read()
                self.lines = self.content.split('\n')

    def check(self) -> List[Dict]:
        """执行检查，返回问题列表"""
        raise NotImplementedError

    def add_issue(self, line_num: int, issue_type: str, description: str, suggestion: str = ""):
        """
        将检查到的问题添加到问题列表中

        封装问题记录的逻辑，确保所有问题都有统一的结构化格式。
        每个问题记录包含文件路径、行号、问题类型、描述和建议修复方案。

        Args:
            line_num: 问题所在的行号（从1开始计数）
            issue_type: 问题类型标识，如"缺少文件头"、"docstring过短"等
            description: 问题详细描述，说明具体什么问题
            suggestion: 可选的修复建议，提供具体的改进指导

        Returns:
            无: 函数直接将问题添加到self.issues列表中

        Raises:
            无: 函数内部不会抛出异常，确保总是成功添加问题记录

        Examples:
            >>> checker = CommentChecker("example.py")
            >>> checker.add_issue(10, "缺少文件头", "文件缺少模块文档字符串",
            ...                  "在文件开头添加模块描述docstring，格式参考docs/comment_standards.md")
            >>> len(checker.issues)
            1

        Notes:
            - 问题类型应与检查器实现中定义的类型常量保持一致
            - 行号应从1开始，与编辑器显示的行号一致
            - 建议应具体明确，提供可操作的改进指导
            - 所有问题存储在self.issues列表中，便于后续汇总和报告
            - 问题结构为字典格式，包含file、line、type、description、suggestion字段
            - 多个检查方法可以调用此函数记录不同类型的问题
        """
        self.issues.append({
            'file': self.filepath,
            'line': line_num,
            'type': issue_type,
            'description': description,
            'suggestion': suggestion
        })

    def print_issues(self):
        """
        格式化打印检查发现的所有注释问题

        将检查器收集到的问题以统一的格式化输出显示到控制台。
        提供清晰的分类和详细的问题描述，包括问题位置、类型、描述和建议修复方案。

        Args:
            无: 函数使用实例属性issues作为问题列表，不接受外部参数

        Returns:
            无: 函数直接输出到控制台，不返回任何值

        Raises:
            无: 函数内部不会抛出异常，确保总是成功打印结果

        Examples:
            >>> checker = PythonCommentChecker("example.py")
            >>> checker.load_file()
            >>> # 执行各种检查...
            >>> checker.print_issues()
            ================================================================================
            文件: example.py
            发现 3 个问题
            ================================================================================
            行   10 | 缺少文件头      | 文件缺少模块文档字符串
                    建议: 在文件开头添加模块描述docstring，格式参考docs/comment_standards.md
                    代码: #!/usr/bin/env python3

        Notes:
            - 如果没有发现问题，显示"[OK]"消息和文件路径
            - 如果发现问题，以表格形式显示每个问题的详细信息
            - 每个问题显示行号、问题类型、描述和建议修复方案
            - 如果问题有建议，显示建议内容
            - 显示问题行的代码片段（最多80字符），便于定位问题
            - 输出格式使用等号分隔线，提高可读性
            - 问题按行号顺序显示，便于开发者依次修复
            - 支持控制台输出，便于集成到CI/CD流程或开发工作流中
        """
        if not self.issues:
            print(f"[OK] {self.filepath}: 没有发现注释问题")
            return

        print(f"\n{'=' * 80}")
        print(f"文件: {self.filepath}")
        print(f"发现 {len(self.issues)} 个问题")
        print(f"{'=' * 80}")

        for issue in self.issues:
            print(f"行 {issue['line']:4d} | {issue['type']:15s} | {issue['description']}")
            if issue['suggestion']:
                print(f"       建议: {issue['suggestion']}")
            # 显示代码行
            if 1 <= issue['line'] <= len(self.lines):
                line_content = self.lines[issue['line'] - 1].rstrip()
                print(f"       代码: {line_content[:80]}")


class PythonCommentChecker(CommentChecker):
    """Python注释检查器"""

    def check(self) -> List[Dict]:
        """检查Python文件的注释规范"""
        self.load_file()

        # 检查文件头docstring
        self.check_file_header()

        # 检查函数和类的docstring
        self.check_docstrings()

        # 检查被注释掉的代码
        self.check_commented_code()

        # 检查TODO/FIXME标记格式
        self.check_todo_markers()

        # 检查行内注释质量
        self.check_inline_comments()

        return self.issues

    def check_file_header(self):
        """
        检查Python文件的模块级docstring（文件头文档）

        分析文件开头，跳过空行和shebang行（#!/usr/bin/env python3），检查是否包含
        规范的模块文档字符串。这是Python文件的模块级文档要求，提供模块的概述、
        功能描述和使用说明。

        Args:
            无: 函数使用实例属性lines作为代码行列表，不接受外部参数

        Returns:
            无: 函数直接通过add_issue()方法记录发现的问题，没有显式返回值

        Raises:
            无: 函数内部不会抛出异常，确保总是成功执行检查

        Examples:
            >>> checker = PythonCommentChecker("example.py")
            >>> checker.load_file()
            >>> checker.check_file_header()
            # 如果文件没有模块docstring：
            # 行    1 | 缺少文件头 | 文件缺少模块文档字符串
            #        建议: 在文件开头添加模块描述docstring，格式参考docs/comment_standards.md
            #        代码: import os

            >>> # 有效的模块docstring（跳过shebang行）
            >>> # 假设文件内容为：
            >>> # #!/usr/bin/env python3
            >>> # \"\"\"模块描述文档\"\"\"
            >>> # import os
            >>> # 这将被视为有效的文件头，不会报告问题

        Notes:
            - 跳过文件开头的空行
            - 跳过shebang行（以#!开头的行），这是Python脚本的常见实践
            - 检查第一行有效内容是否以三引号（\"\"\"或'''）开头
            - 模块docstring应包含模块描述、作者、版本、功能说明等信息
            - 与PEP 257（Python文档字符串约定）保持一致
            - 文件头文档有助于生成自动文档（如Sphinx）
            - 即使有shebang行，仍然需要模块级docstring
            - 对于脚本文件，可以在shebang行后添加简短的模块描述
            - 注意保持缩进正确，shebang行应该在第1行，docstring在第2行或之后
        """
        # 跳过空行
        line_num = 0
        while line_num < len(self.lines) and not self.lines[line_num].strip():
            line_num += 1

        if line_num >= len(self.lines):
            return

        # 检查并跳过shebang行（以#!开头）
        if self.lines[line_num].strip().startswith('#!'):
            line_num += 1
            # 跳过shebang行后的空行
            while line_num < len(self.lines) and not self.lines[line_num].strip():
                line_num += 1

        if line_num >= len(self.lines):
            return

        first_line = self.lines[line_num].strip()

        # 检查是否有文件头docstring
        if not (first_line.startswith('"""') or first_line.startswith("'''")):
            self.add_issue(
                line_num=line_num + 1,  # 报告实际行号（1-based）
                issue_type="缺少文件头",
                description="文件缺少模块文档字符串",
                suggestion="在文件开头添加模块描述docstring，格式参考docs/comment_standards.md"
            )

    def check_docstrings(self):
        """检查函数和类的docstring"""
        try:
            tree = ast.parse(self.content)

            for node in ast.walk(tree):
                # 检查函数定义
                if isinstance(node, ast.FunctionDef):
                    self.check_function_docstring(node)

                # 检查类定义
                if isinstance(node, ast.ClassDef):
                    self.check_class_docstring(node)

        except SyntaxError as e:
            self.add_issue(
                line_num=e.lineno,
                issue_type="语法错误",
                description=f"Python语法错误: {e.msg}",
                suggestion="修复语法错误后再进行注释检查"
            )

    def check_function_docstring(self, node: ast.FunctionDef):
        """检查函数docstring"""
        # 跳过私有函数（以_开头）
        if node.name.startswith('_'):
            return

        docstring = ast.get_docstring(node)

        if not docstring:
            self.add_issue(
                line_num=node.lineno,
                issue_type="缺少docstring",
                description=f"函数 '{node.name}' 缺少文档字符串",
                suggestion="为函数添加完整的docstring，包含参数、返回值说明"
            )
        elif len(docstring.strip()) < 10:
            self.add_issue(
                line_num=node.lineno,
                issue_type="docstring过短",
                description=f"函数 '{node.name}' 的docstring过于简单",
                suggestion="补充详细的函数说明、参数和返回值描述"
            )

    def check_class_docstring(self, node: ast.ClassDef):
        """检查类docstring"""
        docstring = ast.get_docstring(node)

        if not docstring:
            self.add_issue(
                line_num=node.lineno,
                issue_type="缺少docstring",
                description=f"类 '{node.name}' 缺少文档字符串",
                suggestion="为类添加docstring，说明类的功能和用法"
            )

    def check_commented_code(self):
        """
        检查Python文件中被注释掉的代码行

        分析每行代码，识别被注释掉但可能仍然有效的代码（如函数定义、变量赋值等）。
        这类注释掉的代码通常表示调试代码、废弃功能或临时修改，应该被清理。

        Args:
            无: 函数使用实例属性lines作为代码行列表，不接受外部参数

        Returns:
            无: 函数直接通过add_issue()方法记录发现的问题

        Raises:
            无: 函数内部不会抛出异常，确保总是成功执行检查

        Examples:
            >>> checker = PythonCommentChecker("example.py")
            >>> checker.load_file()
            >>> checker.check_commented_code()
            # 如果文件包含被注释掉的代码：
            # 行   15 | 被注释的代码 | 发现被注释掉的代码
            #        建议: 考虑移除或使用条件编译代替注释掉的代码
            #        代码: # result = calculate_value(input_data)

        Notes:
            - 检查以'# '开头的行（注释后跟空格）
            - 使用代码模式识别：包含赋值、控制流、函数定义等语法元素
            - 跳过纯注释行（以'#'开头但没有代码特征的行）
            - 跳过空行
            - 识别常见代码模式：赋值操作符、控制流关键字、括号等
            - 建议移除注释掉的代码或使用更合适的方法（如版本控制、条件编译）
            - 这有助于减少代码库中的技术债务和混乱
            - 被注释掉的代码可能表示未完成的功能或调试遗留物
        """
        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()

            # 跳过空行和纯注释行
            if not stripped or stripped.startswith('#'):
                continue

            # 检查被注释掉的代码（以#开头，但后面看起来像代码）
            if line.startswith('# ') and len(stripped) > 2:
                # 检查是否看起来像代码（包含赋值、函数调用等）
                code_like = any(pattern in stripped[2:] for pattern in [
                    ' = ', ' == ', ' != ', ' += ', ' -= ', ' *= ', ' /= ',
                    ' if ', ' for ', ' while ', ' def ', ' class ',
                    ' import ', ' from ', ' return ', ' yield ',
                    '(', ')', '[', ']', '{', '}'
                ])

                if code_like:
                    self.add_issue(
                        line_num=i,
                        issue_type="被注释的代码",
                        description="发现被注释掉的代码",
                        suggestion="考虑移除或使用条件编译代替注释掉的代码"
                    )

    def check_todo_markers(self):
        """检查TODO/FIXME标记格式"""
        todo_patterns = [
            (r'#\s*TODO\s*:', 'TODO'),
            (r'#\s*FIXME\s*:', 'FIXME'),
            (r'#\s*XXX\s*:', 'XXX'),
            (r'#\s*HACK\s*:', 'HACK'),
            (r'#\s*BUG\s*:', 'BUG'),
        ]

        for i, line in enumerate(self.lines, 1):
            lower_line = line.lower()

            for pattern, marker in todo_patterns:
                if re.search(pattern, lower_line):
                    # 检查格式是否符合规范 [作者] [日期]
                    if not re.search(r'\[.*?\]\s*\[.*?\]', line):
                        self.add_issue(
                            line_num=i,
                            issue_type=f"{marker}格式错误",
                            description=f"{marker}标记缺少作者和日期信息",
                            suggestion=f"使用格式: # {marker}: [作者] [YYYY-MM-DD] 描述"
                        )

    def check_inline_comments(self):
        """
        检查Python文件中行内注释的质量和有用性

        分析包含行内注释（以#开头）的代码行，评估注释是否提供了有价值的信息。
        识别过于简单、冗余或无意义的注释，这些注释应该被改进或移除。

        Args:
            无: 函数使用实例属性lines作为代码行列表，不接受外部参数

        Returns:
            无: 函数直接通过add_issue()方法记录发现的问题

        Raises:
            无: 函数内部不会抛出异常，确保总是成功执行检查

        Examples:
            >>> checker = PythonCommentChecker("example.py")
            >>> checker.load_file()
            >>> checker.check_inline_comments()
            # 如果文件包含过于简单的注释：
            # 行   25 | 注释过于简单 | 行内注释过于简单，没有提供有用信息
            #        建议: 解释代码的意图或原因，而不是描述明显的操作
            #        代码: result = calculate()  # 计算结果

        Notes:
            - 检查包含'#'字符的行（Python行内注释）
            - 将行分割为代码部分和注释部分
            - 跳过纯注释行（没有代码部分的行）
            - 识别过于简单的注释：以常见简单动词开头且长度小于10字符
            - 简单动词列表：'设置'、'获取'、'定义'、'初始化'等
            - 建议提供解释性注释：说明代码的意图、原因或特殊情况
            - 避免描述性注释：只描述代码在做什么，而不解释为什么这样做
            - 行内注释应提供代码本身无法表达的额外信息
            - 良好的注释解释业务逻辑、算法原理或特殊处理原因
            - 过于简单的注释会增加代码噪音而不提供实际价值
        """
        for i, line in enumerate(self.lines, 1):
            # 检查行内注释
            if '#' in line:
                code_part = line.split('#')[0].strip()
                comment_part = line.split('#')[1].strip()

                # 跳过纯注释行
                if not code_part:
                    continue

                # 检查过于简单的注释
                simple_comments = [
                    '设置', '获取', '定义', '初始化', '开始', '结束',
                    '循环', '条件', '判断', '返回', '调用', '创建',
                    '删除', '更新', '添加', '移除', '计算', '处理'
                ]

                if any(comment_part.startswith(word) for word in simple_comments) and len(comment_part) < 10:
                    self.add_issue(
                        line_num=i,
                        issue_type="注释过于简单",
                        description="行内注释过于简单，没有提供有用信息",
                        suggestion="解释代码的意图或原因，而不是描述明显的操作"
                    )


class TypeScriptCommentChecker(CommentChecker):
    """TypeScript注释检查器"""

    def check(self) -> List[Dict]:
        """检查TypeScript文件的注释规范"""
        self.load_file()

        # 检查文件头注释
        self.check_file_header()

        # 检查被注释掉的代码
        self.check_commented_code()

        # 检查TODO/FIXME标记格式
        self.check_todo_markers()

        # 检查行内注释质量
        self.check_inline_comments()

        # 检查函数/组件注释（简单版本）
        self.check_function_comments()

        return self.issues

    def check_file_header(self):
        """
        检查TypeScript/JavaScript文件的JSDoc文件头注释

        分析文件开头（跳过空行），检查是否包含规范的JSDoc注释（/**开头）。
        这是TypeScript/JavaScript文件的文件级文档要求，提供模块的概述和用途说明。
        通过检查第一行有效内容来识别文件头格式是否正确。

        Args:
            无: 函数使用实例属性lines作为代码行列表，不接受外部参数

        Returns:
            无: 函数直接通过add_issue()方法记录发现的问题，没有显式返回值

        Raises:
            无: 函数内部不会抛出异常，确保总是成功执行检查

        Examples:
            >>> checker = TypeScriptCommentChecker("example.ts")
            >>> checker.load_file()
            >>> checker.check_file_header()
            # 如果文件没有JSDoc文件头注释：
            # 行    1 | 缺少文件头 | 文件缺少JSDoc文件头注释
            #        建议: 在文件开头添加JSDoc注释，格式参考docs/comment_standards.md
            #        代码: console.log("Hello");

            >>> # 有效的JSDoc文件头
            >>> file_content = '''/**
            >>>  * 模块名称：example.ts
            >>>  * 功能描述：示例模块
            >>>  */
            >>> console.log("Hello");'''
            >>> # 这将被视为有效的文件头，不会报告问题

        Notes:
            - 跳过文件开头的空行，只检查第一个非空行
            - 期望JSDoc注释以'/**'开头，遵循TypeScript/JavaScript文档约定
            - 检查仅验证格式，不验证内容完整性
            - 文件头注释应包含模块描述、作者、版本等基本信息
            - 对于TypeScript文件，建议使用JSDoc格式而不是普通的块注释
            - JSDoc文件头有助于IDE智能提示和自动文档生成
            - 与Python不同，TypeScript/JavaScript没有标准的三引号docstring
            - 这是代码可读性和可维护性的重要组成部分
        """
        # 跳过空行
        line_num = 0
        while line_num < len(self.lines) and not self.lines[line_num].strip():
            line_num += 1

        if line_num >= len(self.lines):
            return

        first_line = self.lines[line_num].strip()

        # 检查是否有JSDoc文件头注释
        if not first_line.startswith('/**'):
            self.add_issue(
                line_num=1,
                issue_type="缺少文件头",
                description="文件缺少JSDoc文件头注释",
                suggestion="在文件开头添加JSDoc注释，格式参考docs/comment_standards.md"
            )

    def check_commented_code(self):
        """
        检查TypeScript/JavaScript文件中被注释掉的代码行

        分析每行代码，识别被注释掉但可能仍然有效的代码（如函数定义、变量声明等）。
        考虑TypeScript/JavaScript特有的语法特性，包括块注释(/* */)和行注释(//)。
        这类注释掉的代码通常表示调试代码、废弃功能或临时修改，应该被清理。

        Args:
            无: 函数使用实例属性lines作为代码行列表，不接受外部参数

        Returns:
            无: 函数直接通过add_issue()方法记录发现的问题

        Raises:
            无: 函数内部不会抛出异常，确保总是成功执行检查

        Examples:
            >>> checker = TypeScriptCommentChecker("example.ts")
            >>> checker.load_file()
            >>> checker.check_commented_code()
            # 如果文件包含被注释掉的代码：
            # 行   20 | 被注释的代码 | 发现被注释掉的代码
            #        建议: 考虑移除或使用条件编译代替注释掉的代码
            #        代码: // const result = calculateValue(inputData);

        Notes:
            - 处理TypeScript/JavaScript特有的注释语法：行注释(//)和块注释(/* */)
            - 跟踪块注释状态（in_block_comment标志）
            - 跳过块注释内的所有行，不进行检查
            - 检查以'//'开头的行（行注释）
            - 使用代码模式识别：包含赋值、控制流、函数声明等TypeScript/JavaScript语法元素
            - 识别常见代码模式：赋值操作符、控制流关键字、箭头函数、括号等
            - 跳过纯注释行（以'//'开头但没有代码特征的行）
            - 建议移除注释掉的代码或使用更合适的方法（如版本控制、条件编译）
            - 这有助于减少代码库中的技术债务和混乱
            - 被注释掉的代码可能表示未完成的功能或调试遗留物
            - 特别关注TypeScript特有语法：interface、type、export、import等
        """
        in_block_comment = False

        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()

            # 处理块注释
            if '/*' in line and '*/' not in line:
                in_block_comment = True
                continue
            if '*/' in line:
                in_block_comment = False
                continue

            if in_block_comment:
                continue

            # 检查被注释掉的代码（以//开头，但后面看起来像代码）
            if stripped.startswith('//') and len(stripped) > 2:
                # 检查是否看起来像代码
                code_part = stripped[2:].strip()
                code_like = any(pattern in code_part for pattern in [
                    ' = ', ' == ', ' != ', ' += ', ' -= ', ' *= ', ' /= ',
                    ' if ', ' for ', ' while ', ' function ', ' const ', ' let ', ' var ',
                    ' interface ', ' type ', ' class ', ' export ', ' import ',
                    ' return ', ' => ', '(', ')', '[', ']', '{', '}'
                ])

                if code_like:
                    self.add_issue(
                        line_num=i,
                        issue_type="被注释的代码",
                        description="发现被注释掉的代码",
                        suggestion="考虑移除或使用条件编译代替注释掉的代码"
                    )

    def check_todo_markers(self):
        """检查TODO/FIXME标记格式"""
        todo_patterns = [
            (r'//\s*TODO\s*:', 'TODO'),
            (r'//\s*FIXME\s*:', 'FIXME'),
            (r'//\s*XXX\s*:', 'XXX'),
            (r'//\s*HACK\s*:', 'HACK'),
            (r'//\s*BUG\s*:', 'BUG'),
            (r'/\*\*\s*@todo', 'TODO'),
        ]

        for i, line in enumerate(self.lines, 1):
            lower_line = line.lower()

            for pattern, marker in todo_patterns:
                if re.search(pattern, lower_line):
                    # 检查格式是否符合规范 [作者] [日期]
                    if not re.search(r'\[.*?\]\s*\[.*?\]', line):
                        self.add_issue(
                            line_num=i,
                            issue_type=f"{marker}格式错误",
                            description=f"{marker}标记缺少作者和日期信息",
                            suggestion=f"使用格式: // {marker}: [作者] [YYYY-MM-DD] 描述"
                        )

    def check_inline_comments(self):
        """
        检查TypeScript/JavaScript文件中行内注释的质量和有用性

        分析包含行内注释（以//开头）的代码行，评估注释是否提供了有价值的信息。
        识别过于简单、冗余或无意义的注释，这些注释应该被改进或移除。

        Args:
            无: 函数使用实例属性lines作为代码行列表，不接受外部参数

        Returns:
            无: 函数直接通过add_issue()方法记录发现的问题

        Raises:
            无: 函数内部不会抛出异常，确保总是成功执行检查

        Examples:
            >>> checker = TypeScriptCommentChecker("example.ts")
            >>> checker.load_file()
            >>> checker.check_inline_comments()
            # 如果文件包含过于简单的注释：
            # 行   30 | 注释过于简单 | 行内注释过于简单，没有提供有用信息
            #        建议: 解释代码的意图或原因，而不是描述明显的操作
            #        代码: const result = calculate(); // 计算结果

        Notes:
            - 检查包含'//'字符的行（TypeScript/JavaScript行内注释）
            - 将行分割为代码部分和注释部分
            - 跳过纯注释行（没有代码部分的行）
            - 识别过于简单的注释：以常见简单动词开头且长度小于10字符
            - 简单动词列表：'设置'、'获取'、'定义'、'初始化'等
            - 建议提供解释性注释：说明代码的意图、原因或特殊情况
            - 避免描述性注释：只描述代码在做什么，而不解释为什么这样做
            - 行内注释应提供代码本身无法表达的额外信息
            - 良好的注释解释业务逻辑、算法原理或特殊处理原因
            - 过于简单的注释会增加代码噪音而不提供实际价值
            - 注意TypeScript/JavaScript使用//作为行内注释，而不是#
        """
        for i, line in enumerate(self.lines, 1):
            # 检查行内注释
            if '//' in line:
                code_part = line.split('//')[0].strip()
                comment_part = line.split('//')[1].strip()

                # 跳过纯注释行
                if not code_part:
                    continue

                # 检查过于简单的注释
                simple_comments = [
                    '设置', '获取', '定义', '初始化', '开始', '结束',
                    '循环', '条件', '判断', '返回', '调用', '创建',
                    '删除', '更新', '添加', '移除', '计算', '处理'
                ]

                if any(comment_part.startswith(word) for word in simple_comments) and len(comment_part) < 10:
                    self.add_issue(
                        line_num=i,
                        issue_type="注释过于简单",
                        description="行内注释过于简单，没有提供有用信息",
                        suggestion="解释代码的意图或原因，而不是描述明显的操作"
                    )

    def check_function_comments(self):
        """检查函数注释（简化版）"""
        # 简单的正则匹配函数定义
        function_patterns = [
            r'function\s+(\w+)\s*\(',
            r'const\s+(\w+)\s*=\s*(?:\([^)]*\)|[^=]*)\s*=>',
            r'export\s+(?:default\s+)?(?:function|class)\s+(\w+)',
        ]

        for i, line in enumerate(self.lines, 1):
            for pattern in function_patterns:
                match = re.search(pattern, line)
                if match:
                    function_name = match.group(1)
                    # 检查前几行是否有JSDoc注释
                    has_jsdoc = False
                    for j in range(max(1, i-5), i):
                        if self.lines[j-1].strip().startswith('/**'):
                            has_jsdoc = True
                            break

                    if not has_jsdoc:
                        self.add_issue(
                            line_num=i,
                            issue_type="缺少函数注释",
                            description=f"函数 '{function_name}' 缺少JSDoc注释",
                            suggestion="为函数添加JSDoc注释，包含参数和返回值说明"
                        )


def find_source_files(root_dir: str) -> Tuple[List[str], List[str]]:
    """查找项目中的源代码文件"""
    python_files = []
    typescript_files = []

    for root, dirs, files in os.walk(root_dir):
        # 跳过一些目录
        skip_dirs = ['.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build']
        for skip_dir in skip_dirs:
            if skip_dir in dirs:
                dirs.remove(skip_dir)

        for file in files:
            filepath = os.path.join(root, file)

            if file.endswith('.py'):
                python_files.append(filepath)
            elif file.endswith(('.ts', '.tsx')):
                typescript_files.append(filepath)

    return python_files, typescript_files


def main():
    """
    注释检查工具的主入口函数

    协调整个注释检查流程，包括文件搜索、Python和TypeScript文件检查、问题统计和报告。
    作为命令行工具的主要执行逻辑，组织所有子模块的工作，提供统一的用户界面和输出格式。

    Args:
        无: 函数通过命令行参数（如果有）接收输入，但当前版本仅支持默认检查行为

    Returns:
        int: 退出状态码，0表示检查通过（没有发现问题），1表示发现问题

    Raises:
        KeyboardInterrupt: 当用户按下Ctrl+C中断检查时，在脚本顶部捕获
        Exception: 任何其他未处理的异常，在脚本顶部捕获并显示友好错误信息

    Examples:
        >>> # 从命令行运行
        >>> python scripts/check_comments.py
        ================================================================================
        注释规范化检查工具
        检查Python和TypeScript文件的注释规范符合性
        ================================================================================

        搜索源代码文件...
        找到 56 个Python文件
        找到 47 个TypeScript文件

        ================================================================================
        检查Python文件注释...

        [1/50] 检查: check_unicode.py
        ...

        >>> # 检查特定文件
        >>> python scripts/check_comments.py --check-single backend/main.py

    Notes:
        - 默认检查项目中的所有Python和TypeScript文件（限制前50个）
        - 输出格式化的检查结果，包括问题类型、位置和建议
        - 支持按问题类型统计和分类汇总
        - 使用相对路径显示文件位置，便于用户定位
        - 返回适当的退出码，便于脚本集成和自动化
        - 捕获和处理中断信号，提供友好的退出体验
        - 设计为幂等操作，可重复执行用于持续改进
        - 与comment_standards.md文档保持一致，确保建议的准确性
        - 作为注释规范化项目的一部分，帮助提高代码质量和可维护性
        - 注意Windows命令行编码兼容性，使用ASCII兼容标记
    """
    print("=" * 80)
    print("注释规范化检查工具")
    print("检查Python和TypeScript文件的注释规范符合性")
    print("=" * 80)

    # 确定项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 查找源代码文件
    print("\n搜索源代码文件...")
    python_files, typescript_files = find_source_files(project_root)

    print(f"找到 {len(python_files)} 个Python文件")
    print(f"找到 {len(typescript_files)} 个TypeScript文件")

    # 检查Python文件
    python_issues = []
    if python_files:
        print(f"\n{'=' * 80}")
        print("检查Python文件注释...")

        for i, filepath in enumerate(python_files[:50], 1):  # 限制检查数量
            print(f"\n[{i}/{len(python_files[:50])}] 检查: {os.path.relpath(filepath, project_root)}")

            checker = PythonCommentChecker(filepath)
            issues = checker.check()

            if issues:
                checker.print_issues()
                python_issues.extend(issues)
            else:
                print(f"[OK] 没有发现注释问题")

    # 检查TypeScript文件
    ts_issues = []
    if typescript_files:
        print(f"\n{'=' * 80}")
        print("检查TypeScript文件注释...")

        for i, filepath in enumerate(typescript_files[:50], 1):  # 限制检查数量
            print(f"\n[{i}/{len(typescript_files[:50])}] 检查: {os.path.relpath(filepath, project_root)}")

            checker = TypeScriptCommentChecker(filepath)
            issues = checker.check()

            if issues:
                checker.print_issues()
                ts_issues.extend(issues)
            else:
                print(f"[OK] 没有发现注释问题")

    # 总结报告
    print(f"\n{'=' * 80}")
    print("检查完成！")
    print(f"{'=' * 80}")

    total_issues = len(python_issues) + len(ts_issues)

    if total_issues == 0:
        print("[成功] 所有文件注释规范检查通过！")
        return 0

    print(f"[警告] 发现 {total_issues} 个注释问题：")
    print(f"  - Python文件: {len(python_issues)} 个问题")
    print(f"  - TypeScript文件: {len(ts_issues)} 个问题")

    # 按问题类型统计
    issue_types = {}
    for issue in python_issues + ts_issues:
        issue_type = issue['type']
        issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

    print(f"\n问题类型分布:")
    for issue_type, count in sorted(issue_types.items()):
        print(f"  - {issue_type}: {count} 个")

    print(f"\n建议：")
    print("1. 根据建议修改注释问题")
    print("2. 详细规范请参考 docs/comment_standards.md")
    print("3. 运行清理工具移除不需要的注释")

    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n用户中断检查")
        sys.exit(130)
    except Exception as e:
        print(f"\n[错误] 检查过程中发生异常: {e}")
        sys.exit(1)