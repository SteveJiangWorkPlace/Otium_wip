#!/usr/bin/env python3
"""
备份工具 - 安全文件编辑工具

遵循备份策略：
1. 首次修改文件时，在同目录下创建`.backup`文件
2. 后续修改时，如果`.backup`文件已存在，则不再创建
3. 备份文件命名：`原文件名.backup`
4. 备份位置：与原始文件同目录
5. 备份内容：文件的完整原始内容
"""

import argparse
import os
import shutil
import sys
from pathlib import Path


def safe_edit_file(file_path, new_content, verbose=True):
    """
    安全编辑文件，遵循备份策略

    Args:
        file_path: 要编辑的文件路径
        new_content: 新的文件内容
        verbose: 是否输出详细信息

    Returns:
        bool: 是否成功
    """
    file_path = Path(file_path)
    backup_path = file_path.with_suffix(file_path.suffix + ".backup")

    # 检查文件是否存在
    if not file_path.exists():
        if verbose:
            print(f"错误：文件不存在 - {file_path}")
        return False

    # 如果是首次修改，创建备份
    if not backup_path.exists():
        try:
            # 读取原始内容
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # 创建备份
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)

            if verbose:
                print(f"创建备份: {backup_path}")

        except Exception as e:
            if verbose:
                print(f"创建备份失败: {e}")
            return False

    # 进行实际修改
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        if verbose:
            print(f"文件已更新: {file_path}")
        return True

    except Exception as e:
        if verbose:
            print(f"文件更新失败: {e}")

        # 尝试从备份恢复
        if backup_path.exists():
            try:
                with open(backup_path, 'r', encoding='utf-8') as f:
                    backup_content = f.read()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(backup_content)
                if verbose:
                    print(f"已从备份恢复: {backup_path}")
            except Exception as restore_error:
                if verbose:
                    print(f"恢复备份失败: {restore_error}")

        return False

def restore_from_backup(file_path, verbose=True):
    """
    从备份恢复文件

    Args:
        file_path: 要恢复的文件路径
        verbose: 是否输出详细信息

    Returns:
        bool: 是否成功
    """
    file_path = Path(file_path)
    backup_path = file_path.with_suffix(file_path.suffix + ".backup")

    if not backup_path.exists():
        if verbose:
            print(f"错误：备份文件不存在 - {backup_path}")
        return False

    try:
        # 读取备份内容
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_content = f.read()

        # 恢复到原文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(backup_content)

        if verbose:
            print(f"已从备份恢复: {file_path}")
        return True

    except Exception as e:
        if verbose:
            print(f"恢复失败: {e}")
        return False

def check_backup(file_path, verbose=True):
    """
    检查文件是否有备份

    Args:
        file_path: 文件路径
        verbose: 是否输出详细信息

    Returns:
        bool: 是否有备份
    """
    file_path = Path(file_path)
    backup_path = file_path.with_suffix(file_path.suffix + ".backup")

    exists = backup_path.exists()
    if verbose:
        if exists:
            print(f"备份存在: {backup_path}")
            try:
                backup_size = backup_path.stat().st_size
                print(f"备份大小: {backup_size} 字节")
            except:
                pass
        else:
            print(f"备份不存在: {backup_path}")

    return exists

def list_backups(directory=".", verbose=True):
    """
    列出目录中的所有备份文件

    Args:
        directory: 目录路径
        verbose: 是否输出详细信息

    Returns:
        list: 备份文件路径列表
    """
    directory = Path(directory)
    backup_files = []

    for file_path in directory.rglob("*.backup"):
        original_file = file_path.with_suffix("")
        backup_files.append({
            "backup": str(file_path),
            "original": str(original_file),
            "exists": original_file.exists()
        })

    if verbose:
        if backup_files:
            print(f"找到 {len(backup_files)} 个备份文件:")
            for i, backup in enumerate(backup_files, 1):
                status = "[成功]" if backup["exists"] else "[失败]"
                print(f"{i}. {backup['backup']} -> {backup['original']} {status}")
        else:
            print("未找到备份文件")

    return backup_files

def main():
    """命令行主函数"""
    parser = argparse.ArgumentParser(
        description="安全文件编辑工具 - 遵循备份策略",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s edit backend/main.py "新内容"
  %(prog)s restore backend/main.py
  %(prog)s check backend/main.py
  %(prog)s list

备份策略:
  1. 首次修改文件时，在同目录下创建`.backup`文件
  2. 后续修改时，如果`.backup`文件已存在，则不再创建
  3. 备份文件命名：`原文件名.backup`
  4. 备份位置：与原始文件同目录
  5. 备份内容：文件的完整原始内容
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="命令")

    # edit 命令
    edit_parser = subparsers.add_parser("edit", help="安全编辑文件")
    edit_parser.add_argument("file", help="要编辑的文件路径")
    edit_parser.add_argument("content", help="新的文件内容（使用@从文件读取）")
    edit_parser.add_argument("--quiet", action="store_true", help="安静模式，不输出详细信息")

    # restore 命令
    restore_parser = subparsers.add_parser("restore", help="从备份恢复文件")
    restore_parser.add_argument("file", help="要恢复的文件路径")
    restore_parser.add_argument("--quiet", action="store_true", help="安静模式，不输出详细信息")

    # check 命令
    check_parser = subparsers.add_parser("check", help="检查文件是否有备份")
    check_parser.add_argument("file", help="要检查的文件路径")
    check_parser.add_argument("--quiet", action="store_true", help="安静模式，不输出详细信息")

    # list 命令
    list_parser = subparsers.add_parser("list", help="列出所有备份文件")
    list_parser.add_argument("directory", nargs="?", default=".", help="目录路径（默认当前目录）")
    list_parser.add_argument("--quiet", action="store_true", help="安静模式，不输出详细信息")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    verbose = not args.quiet

    if args.command == "edit":
        # 处理内容参数
        content = args.content
        if content.startswith("@"):
            # 从文件读取内容
            content_file = Path(content[1:])
            if not content_file.exists():
                print(f"错误：内容文件不存在 - {content_file}")
                return 1
            try:
                with open(content_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                print(f"读取内容文件失败: {e}")
                return 1

        success = safe_edit_file(args.file, content, verbose)
        return 0 if success else 1

    elif args.command == "restore":
        success = restore_from_backup(args.file, verbose)
        return 0 if success else 1

    elif args.command == "check":
        exists = check_backup(args.file, verbose)
        return 0 if exists else 1

    elif args.command == "list":
        list_backups(args.directory, verbose)
        return 0

    return 0

if __name__ == "__main__":
    sys.exit(main())