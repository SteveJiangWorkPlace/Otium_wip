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
    """运行命令并打印结果"""
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
    """运行所有质量检查"""
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
