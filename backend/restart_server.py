#!/usr/bin/env python3
"""
重启后端服务器，确保运行最新代码
"""

import logging
import os
import subprocess
import sys
import time

import psutil

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def kill_port_8000():
    """终止所有占用端口8000的进程"""
    logger.info("终止端口8000的所有进程...")
    killed = False

    try:
        # 使用psutil查找并终止进程
        for proc in psutil.process_iter(["pid", "name", "connections"]):
            try:
                # 检查进程是否监听端口8000
                for conn in proc.connections(kind="inet"):
                    if conn.status == psutil.CONN_LISTEN and conn.laddr.port == 8000:
                        logger.info(f"找到进程 PID={proc.pid}, 名称={proc.name()} 监听端口8000")
                        proc.terminate()
                        try:
                            proc.wait(timeout=5)
                            logger.info(f"已终止进程 PID={proc.pid}")
                        except psutil.TimeoutExpired:
                            proc.kill()
                            logger.info(f"强制杀死进程 PID={proc.pid}")
                        killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        if not killed:
            logger.info("未找到监听端口8000的进程")
        else:
            logger.info("端口8000进程清理完成")

    except ImportError:
        logger.warning("psutil未安装，使用简单方法终止进程")
        # 使用taskkill命令
        os.system("taskkill //F //IM python.exe //T 2>nul")
        os.system("taskkill //F //IM uvicorn.exe //T 2>nul")


def start_server():
    """在虚拟环境中启动服务器"""
    logger.info("在虚拟环境中启动服务器...")

    # 检查虚拟环境
    venv_python = "venv/Scripts/python.exe"
    if not os.path.exists(venv_python):
        logger.error(f"虚拟环境不存在: {venv_python}")
        return None

    # 构建命令
    cmd = [
        venv_python,
        "-m",
        "uvicorn",
        "main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload",
    ]

    logger.info(f"执行命令: {' '.join(cmd)}")

    # 启动进程
    try:
        # 使用subprocess.Popen在后台启动
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            universal_newlines=True,
        )

        logger.info(f"服务器进程已启动，PID: {process.pid}")

        # 等待服务器启动
        logger.info("等待服务器启动...")
        time.sleep(5)

        # 检查服务器是否在运行
        try:
            import requests

            response = requests.get("http://localhost:8000/api/health", timeout=5)
            if response.status_code == 200:
                logger.info("[成功] 服务器启动成功")
                return process
            else:
                logger.error(f"服务器健康检查失败: {response.status_code}")
                process.terminate()
                return None
        except Exception as e:
            logger.error(f"服务器启动检查失败: {e}")
            # 读取进程输出以获取更多信息
            try:
                output, _ = process.communicate(timeout=2)
                logger.info(f"进程输出: {output[:500]}")
            except Exception:
                pass
            process.terminate()
            return None

    except Exception as e:
        logger.error(f"启动服务器失败: {e}")
        return None


def main():
    logger.info("=== 重启后端服务器 ===")

    # 终止现有进程
    kill_port_8000()
    time.sleep(2)

    # 启动新服务器
    server_process = start_server()

    if server_process:
        logger.info("[成功] 服务器重启成功")
        logger.info(f"进程PID: {server_process.pid}")

        # 保持脚本运行，以便进程继续
        try:
            # 读取并输出进程日志
            logger.info("服务器输出日志:")
            for line in iter(server_process.stdout.readline, ""):
                if line:
                    print(f"[Server] {line.rstrip()}")
        except KeyboardInterrupt:
            logger.info("接收到中断信号，终止服务器...")
            server_process.terminate()
        except Exception as e:
            logger.error(f"读取服务器输出时出错: {e}")

        server_process.wait()
        logger.info("服务器已停止")
    else:
        logger.error("[失败] 服务器启动失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
