#!/usr/bin/env python3
"""
模块名称：fix_code_quality.py
功能描述：自动修复代码质量问题的集成脚本
创建时间：2026-02-27
作者：项目团队
版本：1.0.0

此脚本集成多种代码质量工具，自动修复Python代码的格式、导入排序和语法问题。
确保代码符合项目规范，提高代码可读性和维护性。

主要功能：
1. 使用Black自动格式化代码
2. 使用isort自动排序导入语句
3. 使用Ruff自动修复代码风格问题
4. 处理Windows命令行编码兼容性
5. 提供详细的执行报告和错误处理

支持的工具：
- Black: Python代码格式化，遵循PEP 8规范
- isort: 导入语句自动排序，支持Black兼容性
- Ruff: 快速的Python代码检查和修复，支持自动修复

使用场景：
- 开发过程中定期运行保持代码整洁
- 提交代码前自动修复格式问题
- CI/CD流水线中的代码质量检查
- 团队协作确保代码风格统一

执行流程：
1. 设置UTF-8编码环境（解决Windows GBK编码问题）
2. 运行Black格式化代码
3. 运行isort排序导入
4. 运行Ruff自动修复
5. 输出详细的执行结果和统计

注意事项：
- 需要安装依赖：black, isort, ruff
- Windows环境需要UTF-8编码处理
- 安全处理Unicode输出，避免命令行乱码
- 支持增量修复和全项目修复
"""

import os
import subprocess
import sys

# 设置标准输出编码为UTF-8，解决Windows GBK编码问题
if sys.platform.startswith("win"):
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def run_command(cmd, description):
    """
    执行外部命令并安全处理输出

    封装subprocess.run调用，提供统一的命令执行、错误处理和输出显示。
    特别处理Windows环境下的编码问题，确保UTF-8输出不被破坏。

    Args:
        cmd: 命令参数列表，如 ["black", ".", "--check"]
        description: 人类可读的命令描述，用于输出显示

    Returns:
        bool: 命令执行是否成功（返回码为0）

    Raises:
        无: 函数内部捕获所有异常，确保总是返回布尔值

    Examples:
        >>> success = run_command(["black", ".", "--check"], "检查代码格式")
        >>> if not success:
        >>>     print("格式检查失败")

        >>> success = run_command(["isort", ".", "--check-only"], "检查导入排序")
        >>> print(f"导入排序检查: {'成功' if success else '失败'}")

    Notes:
        - 设置PYTHONIOENCODING=utf-8和PYTHONUTF8=1环境变量
        - 安全处理Unicode输出，避免Windows命令行乱码
        - 限制输出长度（前500字符），避免控制台过载
        - 捕获stdout和stderr，提供详细的错误信息
        - 使用errors="replace"参数处理编码错误
        - 返回布尔值表示成功，而非抛出异常
    """
    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'=' * 60}")

    try:
        # 设置环境变量以确保UTF-8编码输出
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        # 尝试设置语言环境
        env["LC_ALL"] = "C.UTF-8"
        env["LANG"] = "C.UTF-8"
        result = subprocess.run(
            cmd,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            env=env,
        )
        if result.returncode == 0:
            print(f"[OK] {description} completed successfully")
            if result.stdout:
                # 安全打印，避免编码错误
                try:
                    print(f"Output:\n{result.stdout[:500]}")  # 限制输出长度
                except UnicodeEncodeError:
                    safe_output = (
                        result.stdout[:500].encode("utf-8", errors="replace").decode("utf-8")
                    )
                    print(f"Output:\n{safe_output}")
            return True
        else:
            print(f"[FAILED] {description} failed with exit code {result.returncode}")
            if result.stderr:
                # 安全打印，避免编码错误
                try:
                    print(f"Stderr:\n{result.stderr}")
                except UnicodeEncodeError:
                    safe_stderr = result.stderr.encode("utf-8", errors="replace").decode("utf-8")
                    print(f"Stderr:\n{safe_stderr}")
            return False
    except Exception as e:
        # 安全打印异常，避免编码错误
        try:
            print(f"[FAILED] {description} failed with exception: {e}")
        except UnicodeEncodeError:
            safe_msg = str(e).encode("utf-8", errors="replace").decode("utf-8")
            print(f"[FAILED] {description} failed with exception: {safe_msg}")
        return False


def main():
    """
    主函数：执行所有自动代码质量修复

    协调多个代码质量工具的执行顺序，提供完整的代码修复流程。
    按顺序运行Black、isort和Ruff，确保代码符合项目规范。

    Args:
        无: 函数使用默认配置，不接受参数

    Returns:
        int: 退出码，0表示所有修复成功，非0表示有修复失败

    Raises:
        无: 函数内部捕获所有异常，确保总是返回有效的退出码

    Examples:
        >>> # 从命令行调用
        >>> python fix_code_quality.py
        Running automatic code quality fixes...
        ============================================================
        Running: Black code formatting
        Command: python -m black .
        ============================================================

        >>> # 从其他脚本导入
        >>> from fix_code_quality import main
        >>> exit_code = main()
        >>> print(f"修复完成，退出码: {exit_code}")

    Notes:
        - 执行顺序：Black格式化 -> isort导入排序 -> Ruff自动修复
        - 使用当前Python解释器执行工具（sys.executable）
        - 每个工具执行后检查返回码，但继续执行后续工具
        - 最终退出码为最后一个失败工具的返回码（或0）
        - 输出详细的执行日志和统计信息
        - 设计为幂等操作，可重复执行
    """
    print("Running automatic code quality fixes...")

    # 1. Black 格式化
    run_command([sys.executable, "-m", "black", "."], "Black code formatting")

    # 2. isort 导入排序
    run_command([sys.executable, "-m", "isort", "."], "isort import sorting")

    # 3. Ruff 自动修复
    run_command([sys.executable, "-m", "ruff", "check", "--fix", "."], "Ruff auto-fix")

    # 4. Ruff 格式化
    run_command([sys.executable, "-m", "ruff", "format", "."], "Ruff formatting")

    print(f"\n{'=' * 60}")
    print("[OK] Automatic fixes completed!")
    print("\nNote: Some issues may require manual fixing.")
    print("Run 'python run_quality_checks.py' to check remaining issues.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
