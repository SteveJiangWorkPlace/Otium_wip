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
        """加载文件内容"""
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
        """添加问题记录"""
        self.issues.append({
            'file': self.filepath,
            'line': line_num,
            'type': issue_type,
            'description': description,
            'suggestion': suggestion
        })

    def print_issues(self):
        """打印检查结果"""
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
        """检查文件头docstring"""
        # 跳过空行
        line_num = 0
        while line_num < len(self.lines) and not self.lines[line_num].strip():
            line_num += 1

        if line_num >= len(self.lines):
            return

        first_line = self.lines[line_num].strip()

        # 检查是否有文件头docstring
        if not (first_line.startswith('"""') or first_line.startswith("'''")):
            self.add_issue(
                line_num=1,
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
        """检查被注释掉的代码"""
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
        """检查行内注释质量"""
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
        """检查文件头注释"""
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
        """检查被注释掉的代码"""
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
        """检查行内注释质量"""
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
    """主函数"""
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