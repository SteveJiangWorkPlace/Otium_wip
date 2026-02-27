#!/usr/bin/env python3
"""注释清理工具

清理不需要的注释和被注释掉的代码，
根据注释规范化标准进行清理。
"""

import os
import re
import sys
import shutil
from pathlib import Path
from typing import List, Tuple, Optional

# 设置标准输出编码为UTF-8，解决Windows GBK编码问题
if sys.platform.startswith("win"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


class CommentCleaner:
    """注释清理器基类"""

    def __init__(self, filepath: str, backup: bool = True):
        self.filepath = filepath
        self.backup = backup
        self.content = ""
        self.lines = []
        self.changes = []
        self.stats = {
            'removed_commented_code': 0,
            'removed_redundant_comments': 0,
            'updated_todo_markers': 0,
            'added_file_headers': 0,
            'total_lines_removed': 0
        }

    def load_file(self):
        """加载文件内容"""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.content = f.read()
                self.lines = self.content.split('\n')
        except UnicodeDecodeError:
            with open(self.filepath, 'r', encoding='gbk', errors='replace') as f:
                self.content = f.read()
                self.lines = self.content.split('\n')

    def save_file(self):
        """保存文件"""
        if self.backup:
            self.create_backup()

        new_content = '\n'.join(self.lines)
        with open(self.filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

    def create_backup(self):
        """创建备份文件"""
        backup_path = f"{self.filepath}.backup"
        if os.path.exists(backup_path):
            # 如果备份已存在，创建带时间戳的备份
            import time
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.filepath}.backup_{timestamp}"

        shutil.copy2(self.filepath, backup_path)
        self.changes.append(f"创建备份: {backup_path}")

    def clean(self) -> Tuple[bool, dict]:
        """执行清理，返回是否有修改和统计信息"""
        raise NotImplementedError

    def log_change(self, line_num: int, action: str, description: str):
        """记录修改"""
        self.changes.append(f"行 {line_num}: {action} - {description}")

    def print_changes(self):
        """打印修改记录"""
        if not self.changes:
            print(f"[信息] {self.filepath}: 没有进行修改")
            return

        print(f"\n{'=' * 80}")
        print(f"文件: {self.filepath}")
        print(f"进行了 {len(self.changes)} 处修改")
        print(f"{'=' * 80}")

        for change in self.changes:
            print(f"  {change}")

        print(f"\n统计:")
        for key, value in self.stats.items():
            if value > 0:
                print(f"  - {key}: {value}")


class PythonCommentCleaner(CommentCleaner):
    """Python注释清理器"""

    def clean(self) -> Tuple[bool, dict]:
        """清理Python文件的注释"""
        self.load_file()

        original_line_count = len(self.lines)

        # 清理被注释掉的代码
        self.remove_commented_code()

        # 清理冗余注释
        self.remove_redundant_comments()

        # 更新TODO/FIXME标记格式
        self.update_todo_markers()

        # 添加文件头（如果需要）
        self.add_file_header()

        # 更新统计信息
        self.stats['total_lines_removed'] = original_line_count - len(self.lines)

        # 检查是否有修改
        has_changes = len(self.changes) > 0

        if has_changes:
            self.save_file()

        return has_changes, self.stats

    def remove_commented_code(self):
        """移除被注释掉的代码"""
        i = 0
        while i < len(self.lines):
            line = self.lines[i]
            stripped = line.strip()

            # 跳过空行
            if not stripped:
                i += 1
                continue

            # 检查被注释掉的代码行
            if stripped.startswith('#') and len(stripped) > 1:
                code_part = stripped[1:].strip()

                # 判断是否看起来像代码
                code_indicators = [
                    # 赋值操作
                    (' = ', '赋值语句'),
                    (' == ', '相等比较'),
                    (' != ', '不等比较'),
                    (' += ', '加等赋值'),
                    (' -= ', '减等赋值'),
                    (' *= ', '乘等赋值'),
                    (' /= ', '除等赋值'),
                    # 控制结构
                    (' if ', '条件语句'),
                    (' for ', '循环语句'),
                    (' while ', '循环语句'),
                    (' def ', '函数定义'),
                    (' class ', '类定义'),
                    (' import ', '导入语句'),
                    (' from ', '导入语句'),
                    # 关键字
                    (' return ', '返回语句'),
                    (' yield ', '生成器'),
                    (' pass', '空语句'),
                    (' break', '跳出循环'),
                    (' continue', '继续循环'),
                    (' raise ', '抛出异常'),
                    (' try:', '异常处理'),
                    (' except ', '异常处理'),
                    (' finally:', '异常处理'),
                    # 常见模式
                    ('print(', '打印语句'),
                    ('logging.', '日志语句'),
                    ('import ', '导入语句'),
                    ('# import ', '被注释的导入'),
                    ('# from ', '被注释的导入'),
                ]

                is_code = False
                reason = ""

                for indicator, desc in code_indicators:
                    if indicator in code_part:
                        is_code = True
                        reason = desc
                        break

                # 检查括号模式
                if not is_code:
                    bracket_pairs = [
                        ('(', ')'),
                        ('[', ']'),
                        ('{', '}')
                    ]
                    for open_bracket, close_bracket in bracket_pairs:
                        if open_bracket in code_part and close_bracket in code_part:
                            is_code = True
                            reason = f"包含{open_bracket}{close_bracket}括号"
                            break

                if is_code:
                    # 特殊处理：保留有参考价值的调试注释
                    keep_comment = False
                    keep_reasons = [
                        'DEBUG:', '示例:', '示例代码:', '参考:', '注意:',
                        '重要:', '警告:', 'TODO:', 'FIXME:', 'XXX:', 'HACK:', 'BUG:'
                    ]

                    for keep_reason in keep_reasons:
                        if keep_reason in line:
                            keep_comment = True
                            break

                    if not keep_comment:
                        self.log_change(
                            line_num=i + 1,
                            action="移除",
                            description=f"被注释掉的代码 ({reason})"
                        )
                        del self.lines[i]
                        self.stats['removed_commented_code'] += 1
                        continue  # 不增加i，因为删除了当前行

            i += 1

    def remove_redundant_comments(self):
        """移除冗余注释"""
        simple_comment_patterns = [
            # 过于简单的注释
            (r'^#\s*(设置|获取|定义|初始化|开始|结束|循环|条件|判断|返回|调用|创建|删除|更新|添加|移除|计算|处理)[：:].*$',
             '过于简单的注释'),
            # 重复代码行为的注释
            (r'^#\s*(设置变量|获取值|定义函数|调用函数|返回结果|创建对象|删除对象)[：:].*$',
             '描述明显行为的注释'),
            # 空注释
            (r'^#\s*$', '空注释'),
            # 只有标点的注释
            (r'^#\s*[。，；！？、]*\s*$', '无意义注释'),
        ]

        i = 0
        while i < len(self.lines):
            line = self.lines[i]

            if line.strip().startswith('#'):
                for pattern, description in simple_comment_patterns:
                    if re.match(pattern, line.strip()):
                        # 检查是否是重要注释的一部分
                        important_keywords = ['注意', '警告', '重要', 'TODO', 'FIXME', 'XXX', 'HACK', 'BUG']
                        if not any(keyword in line for keyword in important_keywords):
                            self.log_change(
                                line_num=i + 1,
                                action="移除",
                                description=description
                            )
                            del self.lines[i]
                            self.stats['removed_redundant_comments'] += 1
                            break  # 跳出内层循环
                else:
                    i += 1
            else:
                i += 1

    def update_todo_markers(self):
        """更新TODO/FIXME标记格式"""
        todo_patterns = [
            (r'^#\s*TODO\s*[：:]\s*(.*)$', 'TODO'),
            (r'^#\s*FIXME\s*[：:]\s*(.*)$', 'FIXME'),
            (r'^#\s*XXX\s*[：:]\s*(.*)$', 'XXX'),
            (r'^#\s*HACK\s*[：:]\s*(.*)$', 'HACK'),
            (r'^#\s*BUG\s*[：:]\s*(.*)$', 'BUG'),
        ]

        for i, line in enumerate(self.lines):
            original_line = line
            updated_line = line

            for pattern, marker in todo_patterns:
                match = re.match(pattern, line.strip())
                if match:
                    description = match.group(1).strip()

                    # 检查是否已经有作者和日期
                    if not re.search(r'\[.*?\]\s*\[.*?\]', line):
                        # 添加默认作者和日期
                        import datetime
                        today = datetime.datetime.now().strftime("%Y-%m-%d")
                        new_comment = f"# {marker}: [维护团队] [{today}] {description}"

                        updated_line = line.replace(line.strip(), new_comment)

                        if updated_line != original_line:
                            self.log_change(
                                line_num=i + 1,
                                action="更新",
                                description=f"标准化{marker}标记格式"
                            )
                            self.lines[i] = updated_line
                            self.stats['updated_todo_markers'] += 1

    def add_file_header(self):
        """添加文件头（如果缺少）"""
        # 跳过空行
        first_content_line = 0
        while first_content_line < len(self.lines) and not self.lines[first_content_line].strip():
            first_content_line += 1

        if first_content_line >= len(self.lines):
            return

        first_line = self.lines[first_content_line].strip()

        # 检查是否已经有文件头docstring
        has_header = first_line.startswith('"""') or first_line.startswith("'''")

        if not has_header:
            # 获取文件名和相对路径
            filename = os.path.basename(self.filepath)
            rel_path = os.path.relpath(self.filepath, os.path.dirname(os.path.dirname(self.filepath)))

            import datetime
            today = datetime.datetime.now().strftime("%Y-%m-%d")

            header = f'''"""
文件名称：{filename}
功能描述：{self.get_module_description()}
创建时间：{today}
作者：项目团队
版本：1.0.0
"""'''

            # 插入文件头
            self.lines.insert(first_content_line, header)
            self.log_change(
                line_num=first_content_line + 1,
                action="添加",
                description="文件头docstring"
            )
            self.stats['added_file_headers'] += 1

    def get_module_description(self) -> str:
        """根据文件名推测模块描述"""
        filename = os.path.basename(self.filepath)

        descriptions = {
            'main.py': 'FastAPI主应用文件，包含所有API路由定义',
            'config.py': '配置管理模块，处理环境变量和设置',
            'api_services.py': 'AI服务集成模块，处理Gemini和GPTZero API调用',
            'prompts.py': '提示词系统模块，管理AI提示词模板和缓存',
            'schemas.py': '数据模型模块，定义Pydantic请求/响应模型',
            'utils.py': '工具函数模块，提供通用工具和辅助函数',
            'database.py': '数据库模型模块，定义SQLAlchemy ORM模型',
            '__init__.py': '包初始化文件',
        }

        return descriptions.get(filename, 'Python模块')


class TypeScriptCommentCleaner(CommentCleaner):
    """TypeScript注释清理器"""

    def clean(self) -> Tuple[bool, dict]:
        """清理TypeScript文件的注释"""
        self.load_file()

        original_line_count = len(self.lines)

        # 清理被注释掉的代码
        self.remove_commented_code()

        # 清理冗余注释
        self.remove_redundant_comments()

        # 更新TODO/FIXME标记格式
        self.update_todo_markers()

        # 添加文件头（如果需要）
        self.add_file_header()

        # 更新统计信息
        self.stats['total_lines_removed'] = original_line_count - len(self.lines)

        # 检查是否有修改
        has_changes = len(self.changes) > 0

        if has_changes:
            self.save_file()

        return has_changes, self.stats

    def remove_commented_code(self):
        """移除被注释掉的代码"""
        in_block_comment = False
        i = 0

        while i < len(self.lines):
            line = self.lines[i]
            stripped = line.strip()

            # 处理块注释开始
            if '/*' in line and '*/' not in line:
                in_block_comment = True
                i += 1
                continue

            # 处理块注释结束
            if '*/' in line and in_block_comment:
                in_block_comment = False
                i += 1
                continue

            # 跳过块注释内的行
            if in_block_comment:
                i += 1
                continue

            # 检查被注释掉的单行代码
            if stripped.startswith('//') and len(stripped) > 2:
                code_part = stripped[2:].strip()

                # 判断是否看起来像代码
                code_indicators = [
                    # 赋值和操作
                    (' = ', '赋值语句'),
                    (' == ', '相等比较'),
                    (' != ', '不等比较'),
                    (' += ', '加等赋值'),
                    (' -= ', '减等赋值'),
                    (' *= ', '乘等赋值'),
                    (' /= ', '除等赋值'),
                    # 声明
                    ('const ', '常量声明'),
                    ('let ', '变量声明'),
                    ('var ', '变量声明'),
                    ('function ', '函数声明'),
                    ('class ', '类声明'),
                    ('interface ', '接口声明'),
                    ('type ', '类型声明'),
                    ('export ', '导出语句'),
                    ('import ', '导入语句'),
                    # 控制结构
                    ('if ', '条件语句'),
                    ('for ', '循环语句'),
                    ('while ', '循环语句'),
                    ('switch ', '选择语句'),
                    ('return ', '返回语句'),
                    ('break', '跳出循环'),
                    ('continue', '继续循环'),
                    ('throw ', '抛出异常'),
                    ('try ', '异常处理'),
                    ('catch ', '异常处理'),
                    ('finally ', '异常处理'),
                    # 常见模式
                    ('console.', '控制台输出'),
                    ('React.', 'React相关'),
                    ('useState', 'React Hook'),
                    ('useEffect', 'React Hook'),
                    ('axios.', 'HTTP客户端'),
                ]

                is_code = False
                reason = ""

                for indicator, desc in code_indicators:
                    if indicator in code_part:
                        is_code = True
                        reason = desc
                        break

                # 检查括号和箭头函数
                if not is_code:
                    if '=>' in code_part:
                        is_code = True
                        reason = "箭头函数"
                    elif '(' in code_part and ')' in code_part:
                        is_code = True
                        reason = "函数调用"

                if is_code:
                    # 特殊处理：保留有参考价值的注释
                    keep_comment = False
                    keep_reasons = [
                        'DEBUG:', '示例:', '示例代码:', '参考:', '注意:',
                        '重要:', '警告:', 'TODO:', 'FIXME:', 'XXX:', 'HACK:', 'BUG:'
                    ]

                    for keep_reason in keep_reasons:
                        if keep_reason in line:
                            keep_comment = True
                            break

                    if not keep_comment:
                        self.log_change(
                            line_num=i + 1,
                            action="移除",
                            description=f"被注释掉的代码 ({reason})"
                        )
                        del self.lines[i]
                        self.stats['removed_commented_code'] += 1
                        continue  # 不增加i，因为删除了当前行

            i += 1

    def remove_redundant_comments(self):
        """移除冗余注释"""
        simple_comment_patterns = [
            # 过于简单的注释
            (r'^//\s*(设置|获取|定义|初始化|开始|结束|循环|条件|判断|返回|调用|创建|删除|更新|添加|移除|计算|处理)[：:].*$',
             '过于简单的注释'),
            # 重复代码行为的注释
            (r'^//\s*(设置变量|获取值|定义函数|调用函数|返回结果|创建对象|删除对象)[：:].*$',
             '描述明显行为的注释'),
            # 空注释
            (r'^//\s*$', '空注释'),
            # 只有标点的注释
            (r'^//\s*[。，；！？、]*\s*$', '无意义注释'),
        ]

        i = 0
        while i < len(self.lines):
            line = self.lines[i]

            if line.strip().startswith('//'):
                for pattern, description in simple_comment_patterns:
                    if re.match(pattern, line.strip()):
                        # 检查是否是重要注释的一部分
                        important_keywords = ['注意', '警告', '重要', 'TODO', 'FIXME', 'XXX', 'HACK', 'BUG']
                        if not any(keyword in line for keyword in important_keywords):
                            self.log_change(
                                line_num=i + 1,
                                action="移除",
                                description=description
                            )
                            del self.lines[i]
                            self.stats['removed_redundant_comments'] += 1
                            break  # 跳出内层循环
                else:
                    i += 1
            else:
                i += 1

    def update_todo_markers(self):
        """更新TODO/FIXME标记格式"""
        todo_patterns = [
            (r'^//\s*TODO\s*[：:]\s*(.*)$', 'TODO'),
            (r'^//\s*FIXME\s*[：:]\s*(.*)$', 'FIXME'),
            (r'^//\s*XXX\s*[：:]\s*(.*)$', 'XXX'),
            (r'^//\s*HACK\s*[：:]\s*(.*)$', 'HACK'),
            (r'^//\s*BUG\s*[：:]\s*(.*)$', 'BUG'),
        ]

        for i, line in enumerate(self.lines):
            original_line = line
            updated_line = line

            for pattern, marker in todo_patterns:
                match = re.match(pattern, line.strip())
                if match:
                    description = match.group(1).strip()

                    # 检查是否已经有作者和日期
                    if not re.search(r'\[.*?\]\s*\[.*?\]', line):
                        # 添加默认作者和日期
                        import datetime
                        today = datetime.datetime.now().strftime("%Y-%m-%d")
                        new_comment = f"// {marker}: [维护团队] [{today}] {description}"

                        updated_line = line.replace(line.strip(), new_comment)

                        if updated_line != original_line:
                            self.log_change(
                                line_num=i + 1,
                                action="更新",
                                description=f"标准化{marker}标记格式"
                            )
                            self.lines[i] = updated_line
                            self.stats['updated_todo_markers'] += 1

    def add_file_header(self):
        """添加文件头（如果缺少）"""
        # 跳过空行
        first_content_line = 0
        while first_content_line < len(self.lines) and not self.lines[first_content_line].strip():
            first_content_line += 1

        if first_content_line >= len(self.lines):
            return

        first_line = self.lines[first_content_line].strip()

        # 检查是否已经有JSDoc文件头
        has_header = first_line.startswith('/**')

        if not has_header:
            # 获取文件名和相对路径
            filename = os.path.basename(self.filepath)
            rel_path = os.path.relpath(self.filepath, os.path.dirname(os.path.dirname(self.filepath)))

            import datetime
            today = datetime.datetime.now().strftime("%Y-%m-%d")

            header = f'''/**
 * 文件名称：{filename}
 * 功能描述：{self.get_module_description()}
 * 创建时间：{today}
 * 作者：项目团队
 * 版本：1.0.0
 */'''

            # 插入文件头
            self.lines.insert(first_content_line, header)
            self.log_change(
                line_num=first_content_line + 1,
                action="添加",
                description="JSDoc文件头注释"
            )
            self.stats['added_file_headers'] += 1

    def get_module_description(self) -> str:
        """根据文件名推测模块描述"""
        filename = os.path.basename(self.filepath)

        descriptions = {
            'App.tsx': 'React主应用组件，包含路由和全局布局',
            'client.ts': 'API客户端模块，处理HTTP请求和响应拦截',
            'index.tsx': 'React应用入口文件',
            'index.ts': 'TypeScript模块入口文件',
            '__tests__': '测试文件目录',
        }

        # 根据文件扩展名判断
        if filename.endswith('.tsx'):
            base_name = filename[:-4]
            return f'React组件：{base_name}'
        elif filename.endswith('.ts'):
            base_name = filename[:-3]
            return f'TypeScript模块：{base_name}'
        else:
            return 'TypeScript/JavaScript模块'


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
    print("注释清理工具")
    print("清理不需要的注释和被注释掉的代码")
    print("=" * 80)

    # 确定项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 查找源代码文件
    print("\n搜索源代码文件...")
    python_files, typescript_files = find_source_files(project_root)

    print(f"找到 {len(python_files)} 个Python文件")
    print(f"找到 {len(typescript_files)} 个TypeScript文件")

    # 询问用户要清理哪些文件
    print("\n选择清理范围：")
    print("1. 清理所有文件")
    print("2. 只清理Python文件")
    print("3. 只清理TypeScript文件")
    print("4. 清理指定文件")

    choice = input("请选择 (1-4): ").strip()

    files_to_clean = []
    if choice == '1':
        files_to_clean = python_files + typescript_files
        print(f"将清理所有 {len(files_to_clean)} 个文件")
    elif choice == '2':
        files_to_clean = python_files
        print(f"将清理 {len(files_to_clean)} 个Python文件")
    elif choice == '3':
        files_to_clean = typescript_files
        print(f"将清理 {len(files_to_clean)} 个TypeScript文件")
    elif choice == '4':
        # 让用户输入文件路径
        file_path = input("请输入文件路径（相对或绝对路径）: ").strip()
        if not os.path.isabs(file_path):
            file_path = os.path.join(project_root, file_path)

        if os.path.exists(file_path):
            files_to_clean = [file_path]
            print(f"将清理文件: {file_path}")
        else:
            print(f"[错误] 文件不存在: {file_path}")
            return 1
    else:
        print("[错误] 无效的选择")
        return 1

    # 确认清理
    if not files_to_clean:
        print("[信息] 没有文件需要清理")
        return 0

    print(f"\n即将清理 {len(files_to_clean)} 个文件")
    confirm = input("是否继续？(y/N): ").strip().lower()

    if confirm not in ['y', 'yes']:
        print("取消清理操作")
        return 0

    # 执行清理
    total_stats = {
        'removed_commented_code': 0,
        'removed_redundant_comments': 0,
        'updated_todo_markers': 0,
        'added_file_headers': 0,
        'total_lines_removed': 0,
        'files_modified': 0
    }

    print(f"\n{'=' * 80}")
    print("开始清理...")

    for i, filepath in enumerate(files_to_clean, 1):
        print(f"\n[{i}/{len(files_to_clean)}] 清理: {os.path.relpath(filepath, project_root)}")

        # 根据文件类型选择清理器
        if filepath.endswith('.py'):
            cleaner = PythonCommentCleaner(filepath, backup=(i == 1))
        else:
            cleaner = TypeScriptCommentCleaner(filepath, backup=(i == 1))

        try:
            has_changes, stats = cleaner.clean()

            if has_changes:
                cleaner.print_changes()
                total_stats['files_modified'] += 1

                # 累加统计信息
                for key in stats:
                    if key in total_stats:
                        total_stats[key] += stats[key]
            else:
                print(f"[信息] 没有进行修改")

        except Exception as e:
            print(f"[错误] 清理文件时发生错误: {e}")

    # 总结报告
    print(f"\n{'=' * 80}")
    print("清理完成！")
    print(f"{'=' * 80}")

    if total_stats['files_modified'] == 0:
        print("[信息] 没有文件被修改")
        return 0

    print(f"清理统计:")
    for key, value in total_stats.items():
        if value > 0:
            display_name = {
                'removed_commented_code': '移除被注释代码',
                'removed_redundant_comments': '移除冗余注释',
                'updated_todo_markers': '更新TODO标记',
                'added_file_headers': '添加文件头',
                'total_lines_removed': '总删除行数',
                'files_modified': '修改文件数'
            }.get(key, key)
            print(f"  - {display_name}: {value}")

    print(f"\n建议：")
    print("1. 运行测试验证功能正常")
    print("2. 使用 git diff 检查修改内容")
    print("3. 如有需要，可以从备份文件恢复（.backup文件）")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n用户中断清理")
        sys.exit(130)
    except Exception as e:
        print(f"\n[错误] 清理过程中发生异常: {e}")
        sys.exit(1)