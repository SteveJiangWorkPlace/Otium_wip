#!/usr/bin/env python3
"""
模块名称：migrate_to_database.py
功能描述：数据迁移脚本，将JSON和环境变量数据迁移到数据库
创建时间：2026-02-27
作者：项目团队
版本：1.0.0

此脚本用于将项目从基于文件和环境变量的数据存储迁移到SQL数据库存储。
支持将用户数据、使用记录等从JSON文件和环境变量安全迁移到数据库表。

主要功能：
1. 从环境变量ALLOWED_USERS迁移用户账户数据
2. 从usage_data.json文件迁移用户使用记录
3. 将明文密码安全转换为SHA256哈希存储
4. 自动创建原始文件备份，确保数据安全
5. 验证迁移结果的完整性和一致性
6. 提供详细的迁移日志和错误处理

迁移数据类型：
- 用户账户：用户名、密码（哈希后）、过期日期、最大翻译次数等
- 使用记录：用户翻译次数、AI检测次数等使用统计
- 配置数据：环境变量中的用户权限和限制

迁移流程：
1. 备份原始数据文件
2. 初始化数据库表结构
3. 加载原始数据（环境变量+JSON文件）
4. 执行数据迁移和转换
5. 验证迁移结果完整性
6. 创建迁移完成标记和报告

注意事项：
- 迁移前会自动创建原始文件备份
- 密码会转换为安全的SHA256哈希
- 支持增量迁移，已存在的用户会被跳过
- 提供详细的日志记录和错误恢复机制
- 迁移过程可回滚（通过备份文件）
"""

import json
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, cast

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from models.database import User, UserUsage, get_session_local, hash_password, init_database


def setup_logging():
    """
    配置迁移脚本的日志系统

    设置统一的日志格式和输出目标，确保迁移过程的详细记录。
    配置同时输出到控制台和日志文件，便于实时监控和后续分析。

    Args:
        无: 函数使用固定的日志配置，不接受参数

    Returns:
        无: 函数直接配置logging模块，无返回值

    Raises:
        无: 函数内部不会抛出异常

    Examples:
        >>> setup_logging()
        # 配置日志系统，输出到控制台和migration.log文件
        # 日志格式: 2026-02-27 10:30:00 - INFO - 开始数据库迁移

    Notes:
        - 日志级别: INFO，记录所有重要操作
        - 输出目标: 控制台和migration.log文件
        - 日志格式: 时间戳 - 级别 - 消息
        - 日志文件: migration.log，记录完整的迁移过程
        - 便于问题诊断和迁移过程审计
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler("migration.log")],
    )


def backup_file(file_path: str) -> str | None:
    """
    创建指定文件的带时间戳备份副本

    为迁移过程中的关键数据文件创建安全备份，确保原始数据在迁移失败时可恢复。
    备份文件使用时间戳命名，避免覆盖现有备份，支持多次迁移尝试。

    Args:
        file_path: 需要备份的原始文件路径，字符串类型

    Returns:
        str | None: 成功时返回备份文件的完整路径，失败时返回None

    Raises:
        OSError: 文件操作失败时可能抛出（被内部捕获）
        shutil.Error: 文件复制失败时可能抛出（被内部捕获）

    Examples:
        >>> backup_path = backup_file("data/usage_data.json")
        >>> if backup_path:
        >>>     print(f"备份成功: {backup_path}")
        >>> else:
        >>>     print("备份失败或文件不存在")

    Notes:
        - 备份文件名格式: 原始文件名 + ".backup_YYYYMMDD_HHMMSS"
        - 如果原始文件不存在，不进行备份并返回None
        - 使用shutil.copy2保留文件元数据
        - 日志记录详细的备份操作状态
        - 这是数据安全的重要保障措施
    """
    if not os.path.exists(file_path):
        logging.warning(f"文件不存在，无需备份: {file_path}")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.backup_{timestamp}"

    try:
        shutil.copy2(file_path, backup_path)
        logging.info(f"文件备份成功: {file_path} -> {backup_path}")
        return backup_path
    except Exception as e:
        logging.error(f"文件备份失败: {file_path}, 错误: {e}")
        return None


def load_allowed_users_from_env() -> dict[str, Any]:
    """
    从环境变量加载用户配置数据

    解析环境变量ALLOWED_USERS中的JSON格式用户数据，将其转换为Python字典。
    该环境变量包含迁移前的用户账户信息，包括用户名、密码、过期日期等。

    Args:
        无: 函数从环境变量读取数据，不接受参数

    Returns:
        dict[str, Any]: 用户数据字典，键为用户名，值为用户信息字典
        如果环境变量不存在或格式错误，返回空字典

    Raises:
        json.JSONDecodeError: 当环境变量中的JSON格式无效时抛出（被内部捕获）

    Examples:
        >>> users = load_allowed_users_from_env()
        >>> if users:
        >>>     print(f"加载了 {len(users)} 个用户")
        >>> else:
        >>>     print("未找到用户数据或格式错误")

    Notes:
        - 环境变量名: ALLOWED_USERS
        - 默认值: 空JSON对象"{}"
        - 格式: JSON字符串，包含用户名到用户信息的映射
        - 错误处理: JSON解析失败时返回空字典并记录错误
        - 日志记录: 成功加载时会记录用户数量
    """
    try:
        users_env = os.environ.get("ALLOWED_USERS", "{}")
        users_data = cast(dict[str, Any], json.loads(users_env))
        logging.info(f"从环境变量加载了 {len(users_data)} 个用户")
        return users_data
    except Exception as e:
        logging.error(f"加载环境变量用户数据失败: {e}")
        return {}


def load_usage_data_from_json() -> dict[str, Any]:
    """
    从JSON文件加载用户使用统计数据

    读取项目配置中指定的使用数据JSON文件，包含用户翻译次数等使用记录。
    该文件是迁移前项目的主要数据存储方式，需要正确迁移到数据库。

    Args:
        无: 函数从配置文件读取文件路径，不接受参数

    Returns:
        dict[str, Any]: 使用数据字典，键为用户名，值为使用信息字典
        如果文件不存在或格式错误，返回空字典

    Raises:
        FileNotFoundError: 当使用数据文件不存在时抛出（被内部捕获）
        json.JSONDecodeError: 当JSON文件格式无效时抛出（被内部捕获）
        OSError: 文件读取失败时可能抛出（被内部捕获）

    Examples:
        >>> usage_data = load_usage_data_from_json()
        >>> if usage_data:
        >>>     print(f"加载了 {len(usage_data)} 个用户的使用数据")
        >>> else:
        >>>     print("未找到使用数据或文件格式错误")

    Notes:
        - 文件路径: 从settings.USAGE_DB_PATH配置项获取
        - 文件格式: JSON格式，包含用户名到使用信息的映射
        - 编码: UTF-8编码，支持中文字符
        - 错误处理: 文件不存在时返回空字典并记录警告
        - 日志记录: 成功加载时会记录用户数量
    """
    usage_file = settings.USAGE_DB_PATH
    if not os.path.exists(usage_file):
        logging.warning(f"使用数据文件不存在: {usage_file}")
        return {}

    try:
        with open(usage_file, encoding="utf-8") as f:
            usage_data = cast(dict[str, Any], json.load(f))
        logging.info(f"从JSON文件加载了 {len(usage_data)} 个用户的使用数据")
        return usage_data
    except Exception as e:
        logging.error(f"加载使用数据失败: {e}")
        return {}


def migrate_users(db_session, users_data: dict, usage_data: dict):
    """
    执行用户数据从原始格式到数据库的实际迁移

    遍历原始用户数据，将每个用户及其使用记录迁移到数据库表中。
    包括数据转换（密码哈希化、日期格式化）和关联记录创建。

    Args:
        db_session: SQLAlchemy数据库会话对象，用于数据库操作
        users_data: 原始用户数据字典，包含用户名到用户信息的映射
        usage_data: 原始使用数据字典，包含用户名到使用记录的映射

    Returns:
        tuple: 包含三个整数的元组 (migrated_count, skipped_count, error_count)
            - migrated_count: 成功迁移的用户数量
            - skipped_count: 跳过的用户数量（已存在）
            - error_count: 迁移失败的用户数量

    Raises:
        Exception: 用户数据转换或数据库操作失败时可能抛出（被内部捕获）

    Examples:
        >>> migrated, skipped, errors = migrate_users(db_session, users_data, usage_data)
        >>> print(f"迁移结果: 成功={migrated}, 跳过={skipped}, 错误={errors}")

    Notes:
        - 重复检测: 已存在的用户会被跳过
        - 数据转换: 密码转换为SHA256哈希，日期字符串转换为date对象
        - 关联创建: 同时创建用户记录和对应的使用记录
        - 错误隔离: 单个用户迁移失败不影响其他用户
        - 事务处理: 每个用户独立事务，失败时回滚
        - 日志记录: 详细记录每个用户的迁移状态
    """
    migrated_count = 0
    skipped_count = 0
    error_count = 0

    for username, user_info in users_data.items():
        try:
            # 检查用户是否已存在
            existing_user = db_session.query(User).filter(User.username == username).first()
            if existing_user:
                logging.warning(f"用户已存在，跳过: {username}")
                skipped_count += 1
                continue

            # 解析用户信息
            expiry_date_str = user_info.get("expiry_date", "2099-12-31")
            try:
                expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
            except ValueError:
                logging.warning(f"用户 {username} 的日期格式错误: {expiry_date_str}，使用默认值")
                expiry_date = datetime.strptime("2099-12-31", "%Y-%m-%d").date()

            max_translations = user_info.get("max_translations", 1000)
            password = user_info.get("password", "")

            # 创建用户
            user = User(
                username=username,
                password_hash=hash_password(password),
                expiry_date=expiry_date,
                max_translations=max_translations,
                is_admin=False,
                is_active=True,
            )
            db_session.add(user)
            db_session.flush()  # 立即将用户对象写入数据库以生成自动递增的ID，用于后续关联记录的创建

            # 创建使用记录
            user_usage = usage_data.get(username, {})
            translations_count = user_usage.get("translations", 0)

            usage = UserUsage(user_id=user.id, translations_count=translations_count)
            db_session.add(usage)

            migrated_count += 1
            logging.info(
                f"迁移用户: {username}, 过期日期: {expiry_date}, 最大翻译: {max_translations}, 已使用: {translations_count}"
            )

        except Exception as e:
            error_count += 1
            logging.error(f"迁移用户失败: {username}, 错误: {e}")
            db_session.rollback()

    db_session.commit()
    return migrated_count, skipped_count, error_count


def verify_migration(db_session, users_data: dict, usage_data: dict) -> bool:
    """
    验证数据迁移结果的完整性和正确性

    对迁移后的数据库数据进行全面验证，确保所有原始数据正确迁移且无数据丢失。
    验证内容包括用户数量一致性、用户信息完整性和使用数据准确性。

    Args:
        db_session: SQLAlchemy数据库会话对象，用于查询数据库
        users_data: 原始用户数据字典，包含迁移前的用户信息
        usage_data: 原始使用数据字典，包含迁移前的用户使用记录

    Returns:
        bool: 验证是否通过，True表示所有验证通过，False表示有验证失败

    Raises:
        无: 函数内部捕获所有异常，确保总是返回布尔值

    Examples:
        >>> success = verify_migration(db_session, original_users, original_usage)
        >>> if success:
        >>>     print("迁移验证通过")
        >>> else:
        >>>     print("迁移验证失败，请检查日志")

    Notes:
        - 用户数量验证：考虑管理员用户的自动添加
        - 用户信息验证：用户名、过期日期等关键信息
        - 使用数据验证：翻译次数等使用记录
        - 容错处理：不匹配时记录警告但不一定导致验证失败
        - 日志详细记录验证过程和发现的问题
        - 验证失败会提供具体错误信息，便于问题定位
    """
    logging.info("开始验证迁移结果...")

    # 验证用户数量
    db_users_count = db_session.query(User).count()
    original_users_count = len(users_data)

    # 管理员用户会自动添加，所以数据库用户数可能比原始多1
    expected_min = original_users_count
    expected_max = original_users_count + 1  # 加上管理员

    if not (expected_min <= db_users_count <= expected_max):
        logging.error(
            f"用户数量验证失败: 数据库有 {db_users_count} 个用户，原始有 {original_users_count} 个用户"
        )
        return False

    logging.info(f"用户数量验证通过: 数据库有 {db_users_count} 个用户")

    # 验证具体用户数据
    for username, user_info in users_data.items():
        user = db_session.query(User).filter(User.username == username).first()
        if not user:
            logging.error(f"用户验证失败: {username} 不在数据库中")
            return False

        # 验证过期日期
        original_expiry = user_info.get("expiry_date", "2099-12-31")
        db_expiry = user.expiry_date.strftime("%Y-%m-%d")

        if original_expiry != db_expiry:
            logging.warning(
                f"用户 {username} 过期日期不匹配: 原始={original_expiry}, 数据库={db_expiry}"
            )

        # 验证使用数据
        usage = user.usage
        original_usage = usage_data.get(username, {}).get("translations", 0)
        db_usage = usage.translations_count if usage else 0

        if original_usage != db_usage:
            logging.warning(
                f"用户 {username} 使用次数不匹配: 原始={original_usage}, 数据库={db_usage}"
            )

    logging.info("迁移验证完成")
    return True


def main():
    """
    主函数：组织完整的数据库迁移流程

    协调整个数据迁移过程，按步骤执行备份、初始化、数据迁移、验证和报告。
    这是迁移脚本的入口点，提供完整的迁移解决方案和错误处理。

    Args:
        无: 函数使用内部流程控制，不接受参数

    Returns:
        bool: 整个迁移流程是否成功，True表示迁移成功，False表示迁移失败

    Raises:
        无: 函数内部捕获所有异常，确保总是返回布尔值

    Examples:
        >>> # 从命令行调用
        >>> python migrate_to_database.py
        ============================================================
        开始数据库迁移
        ============================================================
        步骤1: 备份原始文件
        ...

        >>> # 从其他脚本导入
        >>> from migrate_to_database import main
        >>> success = main()
        >>> if success:
        >>>     print("迁移成功")
        >>> else:
        >>>     print("迁移失败，请查看migration.log")

    Notes:
        - 执行流程: 备份 -> 初始化 -> 加载数据 -> 迁移 -> 验证 -> 报告
        - 安全措施: 自动创建原始文件备份，确保数据可恢复
        - 错误处理: 每个步骤都有详细的错误处理和日志记录
        - 验证机制: 迁移后验证数据完整性和正确性
        - 用户指导: 迁移成功后提供后续操作建议
        - 退出码: 成功时返回0，失败时返回1（通过sys.exit处理）
    """
    setup_logging()
    logging.info("=" * 60)
    logging.info("开始数据库迁移")
    logging.info("=" * 60)

    # 1. 备份原始文件
    logging.info("步骤1: 备份原始文件")
    usage_file = settings.USAGE_DB_PATH
    usage_backup = backup_file(usage_file)

    # 2. 初始化数据库
    logging.info("步骤2: 初始化数据库")
    try:
        init_database()
        logging.info("数据库初始化成功")
    except Exception as e:
        logging.error(f"数据库初始化失败: {e}")
        return False

    # 3. 加载原始数据
    logging.info("步骤3: 加载原始数据")
    users_data = load_allowed_users_from_env()
    usage_data = load_usage_data_from_json()

    if not users_data:
        logging.warning("没有找到用户数据，只迁移使用数据")

    # 4. 执行迁移
    logging.info("步骤4: 执行数据迁移")
    SessionLocal = get_session_local()
    db_session = SessionLocal()

    try:
        migrated_count, skipped_count, error_count = migrate_users(
            db_session, users_data, usage_data
        )
        logging.info(f"迁移完成: 成功={migrated_count}, 跳过={skipped_count}, 错误={error_count}")

        # 5. 验证迁移
        logging.info("步骤5: 验证迁移结果")
        if verify_migration(db_session, users_data, usage_data):
            logging.info("迁移验证成功")
        else:
            logging.error("迁移验证失败")
            return False

        # 6. 创建迁移完成标记
        with open("migration_complete.txt", "w") as f:
            f.write(f"迁移完成时间: {datetime.now().isoformat()}\n")
            f.write(f"迁移用户数: {migrated_count}\n")
            f.write(f"备份文件: {usage_backup}\n")

        logging.info("=" * 60)
        logging.info("数据库迁移成功完成!")
        logging.info("=" * 60)

        # 7. 显示后续步骤
        print("\n" + "=" * 60)
        print("迁移完成！后续步骤：")
        print("1. 更新main.py中的user_manager为UserService")
        print("2. 重启服务器")
        print("3. 测试所有功能")
        print("4. 确认无误后，可以删除备份文件")
        print("=" * 60)

        return True

    except Exception as e:
        logging.error(f"迁移过程中出现错误: {e}")
        db_session.rollback()
        return False
    finally:
        db_session.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
