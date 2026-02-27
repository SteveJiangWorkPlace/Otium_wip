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
    """
    执行子进程命令并安全处理输出，特别处理Windows编码问题。

    Args:
        cmd (list): 命令参数列表，如['python', '-m', 'black', '.']
        description (str): 命令的人类可读描述，用于日志输出

    Returns:
        bool: 命令执行是否成功（返回码为0）

    Note:
        - 自动设置UTF-8环境变量解决Windows GBK编码问题
        - 安全处理Unicode字符，避免编码错误
        - 限制输出长度（500字符）避免日志过长
        - 提供详细的成功/失败信息
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
                        result.stdout[:500]
                        .encode("utf-8", errors="replace")
                        .decode("utf-8")
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
                    safe_stderr = result.stderr.encode(
                        "utf-8", errors="replace"
                    ).decode("utf-8")
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
    执行代码质量自动修复的完整流程。

    执行顺序:
        1. Black代码格式化
        2. isort导入排序
        3. Ruff自动修复代码问题
        4. Ruff代码格式化

    Returns:
        int: 退出码，0表示成功

    Note:
        - 所有命令输出UTF-8编码
        - 部分问题可能需要手动修复
        - 建议后续运行run_quality_checks.py检查剩余问题
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
