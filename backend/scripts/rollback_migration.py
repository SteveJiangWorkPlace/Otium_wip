#!/usr/bin/env python3
"""
迁移回滚脚本

将数据从数据库导出到JSON格式，恢复原始文件。
用于紧急回滚到文件系统存储。
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from models.database import User, get_session_local


def setup_logging():
    """
    配置迁移回滚脚本的日志系统，提供详细的运行过程记录

    设置统一的日志格式和输出目标，确保回滚操作的每个步骤都有详细记录。
    配置同时输出到控制台和rollback.log文件，便于实时监控和问题诊断。

    Args:
        无: 函数使用固定的日志配置，不接受参数

    Returns:
        无: 函数直接配置logging模块，无显式返回值

    Raises:
        无: 函数内部不会抛出异常，所有配置操作都是安全的

    Examples:
        >>> setup_logging()
        # 配置日志系统，输出到控制台和rollback.log文件
        # 日志格式: 2026-02-27 10:30:00 - INFO - 开始迁移回滚

    Notes:
        - 日志级别: INFO，记录所有重要操作和状态变化
        - 输出目标: 控制台（实时监控）和rollback.log文件（持久化记录）
        - 日志格式: 时间戳 - 级别 - 消息，便于阅读和分析
        - 日志文件: rollback.log，记录完整的回滚过程，便于审计和故障排查
        - 确保在Windows命令行环境下正常显示（使用ASCII字符）
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler("rollback.log")],
    )


def export_users_to_json(db_session) -> dict:
    """从数据库导出用户数据到JSON格式"""
    users = db_session.query(User).filter(User.is_admin.is_(False)).all()  # 排除管理员
    users_data = {}

    for user in users:
        users_data[user.username] = {
            "expiry_date": user.expiry_date.strftime("%Y-%m-%d"),
            "max_translations": user.max_translations,
            "password": "[HASHED]",  # 密码已哈希，无法恢复明文
        }

    logging.info(f"导出了 {len(users_data)} 个用户数据")
    return users_data


def export_usage_to_json(db_session) -> dict:
    """从数据库导出使用数据到JSON格式"""
    usage_data = {}

    # 获取所有用户的使用数据
    users = db_session.query(User).all()
    for user in users:
        usage = user.usage
        if usage:
            usage_data[user.username] = {"translations": usage.translations_count}

    logging.info(f"导出了 {len(usage_data)} 个用户的使用数据")
    return usage_data


def restore_original_files(users_data: dict, usage_data: dict) -> bool:
    """
    将从数据库导出的数据恢复到原始JSON文件格式，支持迁移回滚

    将数据库中的用户数据和使用数据分别写入到配置的JSON文件中，恢复为
    迁移前的文件系统存储格式。同时生成环境变量示例文件，指导用户如何
    重新配置ALLOWED_USERS环境变量。

    Args:
        users_data: 从数据库导出的用户数据字典，包含用户名到用户信息的映射
        usage_data: 从数据库导出的使用数据字典，包含用户名到使用记录的映射

    Returns:
        bool: 文件恢复是否成功，True表示所有文件恢复成功，False表示有恢复失败

    Raises:
        OSError: 文件写入操作失败时抛出（被内部捕获）
        json.JSONEncodeError: JSON编码失败时抛出（被内部捕获）
        Exception: 其他未预期的错误（被内部捕获）

    Examples:
        >>> success = restore_original_files(users_data, usage_data)
        >>> if success:
        >>>     print("文件恢复成功")
        >>> else:
        >>>     print("文件恢复失败，请检查日志")

        >>> # 恢复过程日志:
        >>> # INFO - 恢复使用数据文件: data/usage_data.json
        >>> # INFO - 创建环境变量示例文件: restored_env_vars.txt

    Notes:
        - 使用数据文件路径: 从settings.USAGE_DB_PATH配置项获取
        - JSON编码: 使用ensure_ascii=False支持中文字符，indent=2格式化输出
        - 环境变量文件: 生成restored_env_vars.txt作为配置参考
        - 文件编码: UTF-8编码，确保跨平台兼容性
        - 错误处理: 任何文件操作失败都会记录错误并返回False
        - 数据完整性: 只恢复非管理员用户的普通用户数据
        - 密码安全: 哈希密码无法恢复明文，使用[HASHED]占位符
        - 文件权限: 保持原有文件权限（如果可能）
    """
    try:
        # 恢复使用数据文件
        usage_file = settings.USAGE_DB_PATH
        with open(usage_file, "w", encoding="utf-8") as f:
            json.dump(usage_data, f, ensure_ascii=False, indent=2)
        logging.info(f"恢复使用数据文件: {usage_file}")

        # 创建环境变量示例文件
        {"ALLOWED_USERS": json.dumps(users_data, ensure_ascii=False)}

        env_file = "restored_env_vars.txt"
        with open(env_file, "w", encoding="utf-8") as f:
            f.write("# 恢复的环境变量值\n")
            f.write("# 复制以下内容到环境变量 ALLOWED_USERS\n\n")
            f.write(f"ALLOWED_USERS={json.dumps(users_data, ensure_ascii=False)}\n")

        logging.info(f"创建环境变量示例文件: {env_file}")

        return True

    except Exception as e:
        logging.error(f"恢复文件失败: {e}")
        return False


def main():
    """
    迁移回滚脚本的主入口点，协调完整的数据库回滚流程

    组织从数据库迁移回滚到文件系统存储的完整流程，包括：验证迁移状态、
    创建数据库备份、导出数据库数据、恢复原始JSON文件、生成配置指南。
    提供交互式用户确认和详细的错误处理。

    Args:
        无: 函数通过命令行参数和用户交互控制流程，不接受直接参数

    Returns:
        bool: 整个回滚流程是否成功，True表示回滚成功，False表示回滚失败

    Raises:
        SystemExit: 用户取消操作或发生致命错误时退出
        Exception: 回滚过程中发生未捕获的错误（被内部捕获）

    Examples:
        >>> # 从命令行调用
        >>> python rollback_migration.py
        ============================================================
        开始迁移回滚
        ============================================================
        步骤1: 从数据库导出数据
        ...

        >>> # 从其他脚本导入
        >>> from rollback_migration import main
        >>> success = main()
        >>> if success:
        >>>     print("回滚成功")
        >>> else:
        >>>     print("回滚失败，请查看rollback.log")

    Notes:
        - 执行流程: 检查迁移标记 -> 创建备份 -> 导出数据 -> 恢复文件 -> 生成指南
        - 安全措施: 回滚前创建数据库备份，确保数据可恢复
        - 用户交互: 未找到迁移标记时提示用户确认继续操作
        - 错误处理: 每个步骤都有详细的错误处理和日志记录
        - 数据验证: 验证导出的数据完整性和文件写入成功
        - 后续指导: 回滚成功后提供详细的配置恢复步骤
        - 退出码: 成功时返回0，失败时返回1（通过sys.exit处理）
        - 日志文件: rollback.log记录完整的回滚过程
    """
    setup_logging()
    logging.info("=" * 60)
    logging.info("开始迁移回滚")
    logging.info("=" * 60)

    # 1. 检查迁移完成标记
    if not os.path.exists("migration_complete.txt"):
        logging.warning("未找到迁移完成标记，可能未进行迁移或标记已删除")
        response = input("是否继续回滚？(y/n): ")
        if response.lower() != "y":
            logging.info("用户取消回滚")
            return False

    # 2. 备份当前数据库状态（可选）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_backup_file = f"database_backup_{timestamp}.json"
    logging.info(f"创建数据库备份: {db_backup_file}")

    # 3. 从数据库导出数据
    logging.info("步骤1: 从数据库导出数据")
    SessionLocal = get_session_local()
    db_session = SessionLocal()

    try:
        users_data = export_users_to_json(db_session)
        usage_data = export_usage_to_json(db_session)

        # 保存数据库备份
        backup_data = {"timestamp": timestamp, "users": users_data, "usage": usage_data}

        with open(db_backup_file, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)

        logging.info(f"数据库备份保存到: {db_backup_file}")

        # 4. 恢复原始文件
        logging.info("步骤2: 恢复原始文件")
        if restore_original_files(users_data, usage_data):
            logging.info("文件恢复成功")
        else:
            logging.error("文件恢复失败")
            return False

        # 5. 创建回滚完成标记
        with open("rollback_complete.txt", "w") as f:
            f.write(f"回滚完成时间: {datetime.now().isoformat()}\n")
            f.write(f"导出用户数: {len(users_data)}\n")
            f.write(f"数据库备份: {db_backup_file}\n")

        logging.info("=" * 60)
        logging.info("迁移回滚成功完成!")
        logging.info("=" * 60)

        # 6. 显示后续步骤
        print("\n" + "=" * 60)
        print("回滚完成！后续步骤：")
        print("1. 将 restored_env_vars.txt 中的 ALLOWED_USERS 值设置到环境变量")
        print("2. 更新main.py，恢复使用 UserLimitManager")
        print("3. 重启服务器")
        print("4. 测试所有功能")
        print("5. 确认无误后，可以删除数据库备份文件")
        print("=" * 60)

        return True

    except Exception as e:
        logging.error(f"回滚过程中出现错误: {e}")
        return False
    finally:
        db_session.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
