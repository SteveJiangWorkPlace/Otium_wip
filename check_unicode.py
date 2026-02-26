#!/usr/bin/env python3
"""
检查项目中所有文件的Unicode字符
"""

import os
import re
import sys
from pathlib import Path

# Unicode字符范围
UNICODE_PATTERNS = [
    r"[\u2022-\u2027]",  # 项目符号等
    r"[\u2190-\u21ff]",  # 箭头
    r"[\u2600-\u26ff]",  # 杂项符号
    r"[\u2700-\u27bf]",  # 装饰符号
    r"[\u2713-\u2714]",  # 勾号
    r"[\u2717-\u2718]",  # 叉号
    r"[\u2757-\u2757]",  # 惊叹号
    r"[\u2794-\u2794]",  # 右箭头
    r"[\u27a1-\u27a1]",  # 右箭头
    r"[\u2934-\u2935]",  # 右箭头
    r"[\u2b05-\u2b07]",  # 箭头
    r"[\U0001f300-\U0001f5ff]",  # 符号和象形文字
    r"[\U0001f600-\U0001f64f]",  # 表情符号
    r"[\U0001f680-\U0001f6ff]",  # 交通和地图符号
    r"[\U0001f700-\U0001f77f]",  # 字母符号
    r"[\U0001f780-\U0001f7ff]",  # 几何图形扩展
    r"[\U0001f800-\U0001f8ff]",  # 补充箭头-C
    r"[\U0001f900-\U0001f9ff]",  # 补充符号和象形文字
    r"[\U0001fa00-\U0001fa6f]",  # 棋类符号
    r"[\U0001fa70-\U0001faff]",  # 符号和象形文字扩展-A
]

# 合并所有模式
combined_pattern = "|".join(UNICODE_PATTERNS)
unicode_regex = re.compile(combined_pattern)

# 要检查的文件扩展名
EXTENSIONS = {".md", ".txt", ".py", ".tsx", ".ts", ".js", ".jsx", ".css", ".json"}


def check_file(filepath):
    """检查单个文件的Unicode字符"""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        matches = list(unicode_regex.finditer(content))
        if matches:
            print(f"\n{filepath}: 找到 {len(matches)} 个Unicode字符")
            for match in matches[:5]:  # 只显示前5个
                start = max(0, match.start() - 20)
                end = min(len(content), match.end() + 20)
                context = content[start:end]
                print(f"  位置 {match.start()}: '{match.group()}'")
                print(f"  上下文: ...{context}...")
            if len(matches) > 5:
                print(f"  还有 {len(matches) - 5} 个未显示...")
            return len(matches)
        return 0
    except Exception as e:
        print(f"  错误读取文件 {filepath}: {e}")
        return 0


def main():
    project_root = Path(".")

    total_issues = 0
    files_with_issues = 0

    print("扫描项目中的Unicode字符...")

    # 排除的目录
    excluded_dirs = {
        ".git",
        "__pycache__",
        "node_modules",
        ".pytest_cache",
        "venv",
        ".venv",
    }

    for root, dirs, files in os.walk(project_root):
        # 排除目录
        dirs[:] = [d for d in dirs if d not in excluded_dirs]

        for file in files:
            filepath = Path(root) / file
            ext = filepath.suffix.lower()

            if ext in EXTENSIONS:
                issue_count = check_file(filepath)
                if issue_count > 0:
                    total_issues += issue_count
                    files_with_issues += 1

    print("\n扫描完成！")
    print(f"发现 {files_with_issues} 个文件包含Unicode字符")
    print(f"总共 {total_issues} 个Unicode字符")

    if total_issues > 0:
        print("\n建议：将这些Unicode字符替换为ASCII兼容的替代字符")
        return 1
    else:
        print("未发现Unicode字符问题")
        return 0


if __name__ == "__main__":
    sys.exit(main())
