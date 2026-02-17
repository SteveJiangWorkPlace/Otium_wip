#!/usr/bin/env python3
"""自动修复代码质量问题的脚本"""

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
            cmd, capture_output=True, encoding="utf-8", errors="replace", check=False, env=env
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
    """运行所有自动修复"""
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
