#!/usr/bin/env python3
"""
数据库迁移脚本

将现有数据从环境变量和JSON文件迁移到数据库。
包括：
1. 从环境变量ALLOWED_USERS迁移用户数据
2. 从usage_data.json迁移使用数据
3. 将明文密码转换为SHA256哈希
4. 创建原始文件备份
"""

import os
import sys
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from models.database import init_database, get_session_local, User, UserUsage, hash_password
from user_services.user_service import UserService


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('migration.log')
        ]
    )


def backup_file(file_path: str) -> str:
    """备份文件"""
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


def load_allowed_users_from_env() -> dict:
    """从环境变量加载用户数据"""
    try:
        users_env = os.environ.get("ALLOWED_USERS", "{}")
        users_data = json.loads(users_env)
        logging.info(f"从环境变量加载了 {len(users_data)} 个用户")
        return users_data
    except Exception as e:
        logging.error(f"加载环境变量用户数据失败: {e}")
        return {}


def load_usage_data_from_json() -> dict:
    """从JSON文件加载使用数据"""
    usage_file = settings.USAGE_DB_PATH
    if not os.path.exists(usage_file):
        logging.warning(f"使用数据文件不存在: {usage_file}")
        return {}

    try:
        with open(usage_file, 'r', encoding='utf-8') as f:
            usage_data = json.load(f)
        logging.info(f"从JSON文件加载了 {len(usage_data)} 个用户的使用数据")
        return usage_data
    except Exception as e:
        logging.error(f"加载使用数据失败: {e}")
        return {}


def migrate_users(db_session, users_data: dict, usage_data: dict):
    """迁移用户数据到数据库"""
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
                is_active=True
            )
            db_session.add(user)
            db_session.flush()  # 获取用户ID

            # 创建使用记录
            user_usage = usage_data.get(username, {})
            translations_count = user_usage.get("translations", 0)

            usage = UserUsage(
                user_id=user.id,
                translations_count=translations_count
            )
            db_session.add(usage)

            migrated_count += 1
            logging.info(f"迁移用户: {username}, 过期日期: {expiry_date}, 最大翻译: {max_translations}, 已使用: {translations_count}")

        except Exception as e:
            error_count += 1
            logging.error(f"迁移用户失败: {username}, 错误: {e}")
            db_session.rollback()

    db_session.commit()
    return migrated_count, skipped_count, error_count


def verify_migration(db_session, users_data: dict, usage_data: dict) -> bool:
    """验证迁移结果"""
    logging.info("开始验证迁移结果...")

    # 验证用户数量
    db_users_count = db_session.query(User).count()
    original_users_count = len(users_data)

    # 管理员用户会自动添加，所以数据库用户数可能比原始多1
    expected_min = original_users_count
    expected_max = original_users_count + 1  # 加上管理员

    if not (expected_min <= db_users_count <= expected_max):
        logging.error(f"用户数量验证失败: 数据库有 {db_users_count} 个用户，原始有 {original_users_count} 个用户")
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
            logging.warning(f"用户 {username} 过期日期不匹配: 原始={original_expiry}, 数据库={db_expiry}")

        # 验证使用数据
        usage = user.usage
        original_usage = usage_data.get(username, {}).get("translations", 0)
        db_usage = usage.translations_count if usage else 0

        if original_usage != db_usage:
            logging.warning(f"用户 {username} 使用次数不匹配: 原始={original_usage}, 数据库={db_usage}")

    logging.info("迁移验证完成")
    return True


def main():
    """主迁移函数"""
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
        migrated_count, skipped_count, error_count = migrate_users(db_session, users_data, usage_data)
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