#!/usr/bin/env python3
"""
后台工作器服务

从数据库中获取待处理的后台任务并执行，支持长时间运行的任务如文献调研。
可以部署为独立的Render后台工作器服务或本地进程。

使用方法：
    python worker.py [--interval <秒>] [--max-tasks <数量>] [--once]

环境变量：
    ENABLE_BACKGROUND_WORKER: 必须设置为True以启用后台任务处理
    DATABASE_TYPE: 数据库类型（sqlite或postgresql）
    DATABASE_URL: PostgreSQL连接字符串（生产环境）
    MANUS_API_KEY: Manus API密钥（用于文献调研）
    GEMINI_API_KEY: Gemini API密钥（用于普通聊天）
    LOG_LEVEL: 日志级别（默认INFO）
"""

import argparse
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timedelta

# 添加项目路径到系统路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session

from config import settings
from models.database import get_session_local
from background_task_service import BackgroundTaskService

# 配置日志
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("worker")

# 全局标志，用于优雅关闭
_shutdown_requested = False


def signal_handler(signum, frame):
    """处理终止信号，实现优雅关闭"""
    global _shutdown_requested
    logger.info(f"收到信号 {signum}，正在优雅关闭...")
    _shutdown_requested = True


def setup_signal_handlers():
    """
    为后台工作进程设置Unix信号处理器，实现优雅关闭

    注册SIGINT（Ctrl+C）和SIGTERM（终止信号）的信号处理函数，确保工作进程
    在接收到终止信号时能够优雅地完成当前任务并清理资源，而不是立即终止。

    Args:
        无: 函数使用全局信号处理函数signal_handler，不接受参数

    Returns:
        无: 函数直接配置signal模块，无显式返回值

    Raises:
        无: 函数内部不会抛出异常，信号注册失败会被忽略

    Examples:
        >>> setup_signal_handlers()
        # 注册信号处理器后，工作进程会在收到Ctrl+C时调用signal_handler函数
        # 日志输出: "信号处理器已设置"

    Notes:
        - SIGINT信号通常由用户按Ctrl+C触发
        - SIGTERM信号通常由进程管理工具（如systemd）发送
        - 信号处理函数signal_handler设置全局标志_shutdown_requested为True
        - 工作进程主循环会定期检查_shutdown_requested标志，实现优雅关闭
        - 优雅关闭确保当前处理的任务不会被中断，数据不会丢失
    """
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    logger.debug("信号处理器已设置")


def process_pending_tasks(worker_id: int = 0, max_tasks: int = 10):
    """
    处理待处理的任务

    Args:
        worker_id: 工作器ID，用于日志标识
        max_tasks: 单次处理的最大任务数量
    """
    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        # 创建任务服务
        task_service = BackgroundTaskService(db)

        # 获取待处理任务
        pending_tasks = task_service.get_pending_tasks(limit=max_tasks)

        if not pending_tasks:
            logger.debug(f"工作器 {worker_id}: 没有待处理任务")
            return 0

        logger.info(f"工作器 {worker_id}: 找到 {len(pending_tasks)} 个待处理任务")

        processed_count = 0
        for task in pending_tasks:
            if _shutdown_requested:
                logger.info(f"工作器 {worker_id}: 收到关闭信号，停止处理新任务")
                break

            try:
                logger.info(f"工作器 {worker_id}: 开始处理任务 ID={task.id}, 类型={task.task_type}")

                # 处理任务
                result = task_service.process_task(task)

                logger.info(f"工作器 {worker_id}: 任务 ID={task.id} 处理完成，状态={task.status}")
                processed_count += 1

            except TimeoutError as e:
                logger.warning(f"工作器 {worker_id}: 任务 ID={task.id} 超时: {str(e)}")
                # 超时任务已经被标记为重试，继续处理下一个任务
            except Exception as e:
                error_msg = str(e)
                error_type = "unknown"

                # 简单的错误分类
                if any(keyword in error_msg.lower() for keyword in ["timeout", "connection", "network"]):
                    error_type = "network"
                elif any(keyword in error_msg.lower() for keyword in ["rate limit", "quota", "too many"]):
                    error_type = "rate_limit"
                elif any(keyword in error_msg.lower() for keyword in ["invalid", "unauthorized", "forbidden"]):
                    error_type = "auth"

                logger.error(
                    f"工作器 {worker_id}: 处理任务 ID={task.id} 失败 [type={error_type}]: {error_msg}",
                    exc_info=True
                )
                # 继续处理下一个任务

        db.commit()
        return processed_count

    except Exception as e:
        logger.error(f"工作器 {worker_id}: 处理任务时发生错误: {str(e)}", exc_info=True)
        db.rollback()
        return 0
    finally:
        db.close()


def cleanup_stuck_tasks(timeout_minutes: int = 30):
    """
    清理卡住的任务（处理中但超过超时时间的任务）

    Args:
        timeout_minutes: 超时时间（分钟），默认30分钟

    Returns:
        int: 清理的任务数量
    """
    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        task_service = BackgroundTaskService(db)
        cleaned_count = task_service.cleanup_stuck_tasks(timeout_minutes=timeout_minutes)

        if cleaned_count > 0:
            logger.warning(f"清理了 {cleaned_count} 个卡住的任务（超过{timeout_minutes}分钟）")

        db.commit()
        return cleaned_count
    except Exception as e:
        logger.error(f"清理卡住任务时发生错误: {str(e)}", exc_info=True)
        db.rollback()
        return 0
    finally:
        db.close()


def cleanup_old_tasks(days: int = 7):
    """
    清理数据库中超过指定天数的旧任务记录，维护数据库性能和存储空间

    定期清理已完成或失败的历史任务记录，防止数据库表无限增长。使用
    BackgroundTaskService的清理功能，基于任务完成时间筛选并删除旧记录。

    Args:
        days: 保留任务记录的天数阈值，默认7天。早于此天数的记录将被删除。

    Returns:
        int: 实际删除的任务记录数量，可用于监控清理效果

    Raises:
        Exception: 数据库操作失败时可能抛出，内部捕获并记录错误日志

    Examples:
        >>> deleted = cleanup_old_tasks(days=7)
        # 删除7天前的任务记录
        # 日志输出: "清理了 15 个 7 天前的旧任务记录"
        >>> print(f"删除了 {deleted} 条旧记录")

        >>> # 使用不同保留天数
        >>> cleanup_old_tasks(days=30)  # 保留30天记录

    Notes:
        - 清理操作通常由定时任务或维护脚本调用
        - 默认保留7天记录，平衡存储空间和调试需求
        - 只清理completed或failed状态的任务，pending和processing状态的任务保留
        - 使用数据库事务确保数据一致性
        - 错误时回滚事务并记录详细错误信息
        - 清理后释放数据库连接资源
    """
    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        task_service = BackgroundTaskService(db)
        deleted_count = task_service.cleanup_old_tasks(days=days)

        if deleted_count > 0:
            logger.info(f"清理了 {deleted_count} 个 {days} 天前的旧任务记录")

        db.commit()
        return deleted_count
    except Exception as e:
        logger.error(f"清理旧任务时发生错误: {str(e)}", exc_info=True)
        db.rollback()
        return 0
    finally:
        db.close()


def worker_loop(interval: int = 10, max_tasks: int = 5, worker_id: int = 0):
    """
    工作器主循环

    Args:
        interval: 轮询间隔（秒）
        max_tasks: 每次处理的最大任务数量
        worker_id: 工作器ID
    """
    logger.info(f"工作器 {worker_id} 启动，轮询间隔={interval}秒，最大任务数={max_tasks}")

    # 健康状态跟踪
    health_stats = {
        "start_time": datetime.now(),
        "total_cycles": 0,
        "total_tasks_processed": 0,
        "last_error_time": None,
        "consecutive_errors": 0,
    }

    last_cleanup = datetime.now()
    cleanup_interval = timedelta(hours=1)  # 每小时清理一次
    last_stuck_cleanup = datetime.now()
    stuck_cleanup_interval = timedelta(minutes=30)  # 每30分钟清理卡住任务

    while not _shutdown_requested:
        try:
            health_stats["total_cycles"] += 1

            # 处理待处理任务
            processed = process_pending_tasks(worker_id, max_tasks)
            health_stats["total_tasks_processed"] += processed

            # 重置连续错误计数
            health_stats["consecutive_errors"] = 0

            now = datetime.now()

            # 定期清理旧任务
            if now - last_cleanup > cleanup_interval:
                cleanup_old_tasks(days=7)
                last_cleanup = now

            # 定期清理卡住的任务
            if now - last_stuck_cleanup > stuck_cleanup_interval:
                cleanup_stuck_tasks(timeout_minutes=30)
                last_stuck_cleanup = now

            # 定期记录健康状态（每10个周期）
            if health_stats["total_cycles"] % 10 == 0:
                uptime = now - health_stats["start_time"]
                tasks_per_cycle = health_stats["total_tasks_processed"] / max(health_stats["total_cycles"], 1)
                logger.info(
                    f"工作器 {worker_id} 健康状态: "
                    f"运行时间={uptime.total_seconds():.0f}秒, "
                    f"总周期数={health_stats['total_cycles']}, "
                    f"处理任务数={health_stats['total_tasks_processed']}, "
                    f"平均每周期处理任务数={tasks_per_cycle:.2f}"
                )

            # 如果没有处理任何任务，休眠更长时间
            if processed == 0:
                logger.debug(f"工作器 {worker_id}: 没有任务需要处理，休眠 {interval} 秒")
                for _ in range(interval):
                    if _shutdown_requested:
                        break
                    time.sleep(1)
            else:
                # 处理了任务，短暂休眠后继续
                time.sleep(1)

        except Exception as e:
            error_time = datetime.now()
            health_stats["last_error_time"] = error_time
            health_stats["consecutive_errors"] += 1

            logger.error(f"工作器 {worker_id}: 主循环发生错误 [{health_stats['consecutive_errors']}]: {str(e)}", exc_info=True)

            # 如果连续错误过多，延长休眠时间
            sleep_time = interval
            if health_stats["consecutive_errors"] > 3:
                sleep_time = min(interval * health_stats["consecutive_errors"], 300)  # 最多5分钟
                logger.warning(f"工作器 {worker_id}: 连续错误过多，休眠 {sleep_time} 秒")

            time.sleep(sleep_time)

    logger.info(f"工作器 {worker_id} 已停止")


def main():
    """
    后台任务工作器的主入口点，提供命令行界面和运行模式控制

    解析命令行参数，配置工作器行为，支持多种运行模式：持续轮询模式、
    单次运行模式和清理模式。根据参数调用相应的处理函数，管理整个工作器
    的生命周期和优雅关闭。

    Args:
        无: 函数通过argparse解析命令行参数，不接受直接参数

    Returns:
        无: 函数执行工作流程，没有显式返回值

    Raises:
        SystemExit: 参数解析错误或环境配置不满足时退出
        Exception: 工作器运行过程中发生未捕获的错误时退出

    Examples:
        >>> # 持续运行模式（默认）
        >>> python worker.py
        # 后台工作器开始运行，每10秒检查一次新任务

        >>> # 单次运行模式
        >>> python worker.py --once
        # 只处理一次待处理任务，然后退出

        >>> # 清理模式
        >>> python worker.py --cleanup
        # 清理7天前的旧任务记录，然后退出

        >>> # 自定义参数
        >>> python worker.py --interval 30 --max-tasks 10 --worker-id 1
        # 每30秒检查一次，每次最多处理10个任务，工作器ID为1

    Notes:
        - 需要环境变量ENABLE_BACKGROUND_WORKER=True才能运行
        - 设置信号处理器支持Ctrl+C优雅关闭
        - 支持三种运行模式：持续轮询、单次执行、清理操作
        - 使用argparse提供用户友好的命令行界面
        - 错误处理包括键盘中断和未捕获异常
        - 日志记录详细的工作器状态和操作信息
    """
    parser = argparse.ArgumentParser(description="后台任务工作器")
    parser.add_argument("--interval", type=int, default=10, help="任务轮询间隔（秒），默认10秒")
    parser.add_argument("--max-tasks", type=int, default=5, help="每次处理的最大任务数，默认5")
    parser.add_argument("--worker-id", type=int, default=0, help="工作器ID，默认0")
    parser.add_argument("--once", action="store_true", help="只运行一次，不进入循环")
    parser.add_argument("--cleanup", action="store_true", help="只执行清理操作，然后退出")

    args = parser.parse_args()

    # 检查是否启用后台工作器
    if not settings.ENABLE_BACKGROUND_WORKER:
        logger.error("后台工作器未启用，请设置环境变量 ENABLE_BACKGROUND_WORKER=True")
        sys.exit(1)

    # 设置信号处理器
    setup_signal_handlers()

    if args.cleanup:
        logger.info("执行清理操作...")
        deleted = cleanup_old_tasks(days=7)
        logger.info(f"清理完成，删除了 {deleted} 条记录")
        return

    if args.once:
        logger.info("单次运行模式")
        processed = process_pending_tasks(args.worker_id, args.max_tasks)
        logger.info(f"单次运行完成，处理了 {processed} 个任务")
        return

    # 进入主循环
    try:
        worker_loop(
            interval=args.interval,
            max_tasks=args.max_tasks,
            worker_id=args.worker_id,
        )
    except KeyboardInterrupt:
        logger.info("用户中断")
    except Exception as e:
        logger.error(f"工作器发生未捕获的错误: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()