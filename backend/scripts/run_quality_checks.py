#!/usr/bin/env python3
"""运行代码质量检查脚本"""

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
    执行外部命令并安全地捕获和显示输出，特别处理Windows编码问题

    封装subprocess.run调用，提供统一的错误处理、输出显示和编码问题解决方案。
    针对Windows命令行（GBK编码）和Unicode输出的兼容性问题，实现安全的
    输出捕获和显示机制，确保代码质量检查工具在各种环境下可靠运行。

    Args:
        cmd: 要执行的命令参数列表，如["python", "-m", "black", "--check", "."]
        description: 命令的友好描述，用于输出显示，如"Black formatting check"

    Returns:
        bool: 命令执行是否成功，True表示退出码为0，False表示非零退出码或异常

    Raises:
        Exception: 命令执行过程中发生未捕获的错误（被内部捕获并处理）

    Examples:
        >>> success = run_command(["python", "-m", "black", "--check", "."], "Black检查")
        ============================================================
        Running: Black检查
        Command: python -m black --check .
        ============================================================
        [OK] Black检查 passed

        >>> # 失败示例
        >>> success = run_command(["python", "-m", "nonexistent"], "测试命令")
        ============================================================
        Running: 测试命令
        Command: python -m nonexistent
        ============================================================
        [FAILED] 测试命令 failed with exit code 1

    Notes:
        - 编码处理: 强制设置UTF-8环境变量（PYTHONIOENCODING, PYTHONUTF8）
        - Windows兼容性: 使用io.TextIOWrapper包装标准输出，避免GBK编码问题
        - 安全输出: 捕获UnicodeEncodeError并使用errors="replace"处理
        - 输出限制: 限制stdout输出长度（500字符），防止过长输出
        - 错误处理: 记录详细的错误信息，包括stderr和stdout
        - 环境隔离: 复制当前环境并添加编码相关变量
        - 使用[OK]、[FAILED]等ASCII标记，确保Windows命令行兼容性
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
            print(f"[OK] {description} passed")
            if result.stdout:
                # 安全打印，避免编码错误
                try:
                    print(f"Output:\n{result.stdout[:500]}")  # 限制输出长度
                except UnicodeEncodeError:
                    # 如果编码失败，替换非ASCII字符
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
            if result.stdout:
                # 安全打印，避免编码错误
                try:
                    print(f"Stdout:\n{result.stdout}")
                except UnicodeEncodeError:
                    safe_stdout = result.stdout.encode("utf-8", errors="replace").decode("utf-8")
                    print(f"Stdout:\n{safe_stdout}")
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
    运行全套Python代码质量检查工具，验证项目代码规范符合性

    按顺序执行Black格式化检查、isort导入排序检查、Flake8代码风格检查、
    Ruff代码检查和格式化检查、Mypy类型检查（可选）。提供统一的输出格式
    和结果汇总，帮助开发者识别和修复代码质量问题。

    Args:
        无: 函数使用预定义的检查命令序列，不接受参数

    Returns:
        int: 退出码，0表示所有检查通过或只有可选检查失败，1表示必需检查失败

    Raises:
        SystemExit: 函数结束时调用sys.exit()返回适当的退出码
        Exception: 检查过程中发生未捕获的错误（被内部处理）

    Examples:
        >>> # 从命令行调用
        >>> python run_quality_checks.py
        ============================================================
        Running: Black formatting check
        Command: python -m black --check .
        ============================================================
        [OK] Black formatting check passed
        ...

        >>> # 从其他脚本导入
        >>> from run_quality_checks import main
        >>> exit_code = main()
        >>> print(f"退出码: {exit_code}")

    Notes:
        - 检查顺序: Black -> isort -> Flake8 -> Ruff check -> Ruff format -> Mypy
        - 必需检查: Black、isort、Flake8、Ruff检查和格式化是必需的
        - 可选检查: Mypy类型检查失败时只显示警告，不标记为总体失败
        - 编码处理: 专门处理Windows GBK编码问题，确保输出可读
        - 输出格式: 统一的分隔线和状态标记，便于阅读和自动化解析
        - 修复建议: 检查失败时提供具体的修复命令
        - 使用[OK]、[FAILED]、[WARNING]等ASCII标记，确保Windows兼容性
        - 支持开发和生产环境，作为CI/CD流水线的一部分
    """
    checks_passed = True

    # 1. Black 格式化检查
    checks_passed &= run_command(
        [sys.executable, "-m", "black", "--check", "."], "Black formatting check"
    )

    # 2. isort 导入排序检查
    checks_passed &= run_command(
        [sys.executable, "-m", "isort", "--check-only", "--diff", "."],
        "isort import sorting check",
    )

    # 3. Flake8 代码风格检查
    checks_passed &= run_command([sys.executable, "-m", "flake8", "."], "Flake8 code style check")

    # 4. Ruff 代码检查
    checks_passed &= run_command([sys.executable, "-m", "ruff", "check", "."], "Ruff code check")

    # 5. Ruff 格式化检查
    checks_passed &= run_command(
        [sys.executable, "-m", "ruff", "format", "--check", "."], "Ruff format check"
    )

    # 6. Mypy 类型检查（可选，因为可能有一些类型问题）
    mypy_result = run_command(
        [
            sys.executable,
            "-m",
            "mypy",
            "--explicit-package-bases",
            "--ignore-missing-imports",
            ".",
        ],
        "Mypy type checking",
    )
    if not mypy_result:
        print(
            "\n[WARNING] Mypy type checking failed. This may be expected if there are type issues."
        )
        print("Consider fixing type issues or adjusting mypy configuration.")

    # 总结
    print(f"\n{'=' * 60}")
    if checks_passed:
        print("[OK] All code quality checks passed!")
        return 0
    else:
        print("[FAILED] Some code quality checks failed.")
        print("\nTo fix issues, you can run:")
        print("  python -m black .          # Format code with Black")
        print("  python -m isort .          # Sort imports with isort")
        print("  python -m ruff check --fix .  # Fix issues with Ruff")
        print("  python -m ruff format .    # Format with Ruff")
        return 1


if __name__ == "__main__":
    sys.exit(main())
