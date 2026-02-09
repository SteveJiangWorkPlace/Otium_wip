#!/usr/bin/env python3
"""
迁移回滚脚本

将数据从数据库导出到JSON格式，恢复原始文件。
用于紧急回滚到文件系统存储。
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
from models.database import get_session_local, User, UserUsage


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('rollback.log')
        ]
    )


def export_users_to_json(db_session) -> dict:
    """从数据库导出用户数据到JSON格式"""
    users = db_session.query(User).filter(User.is_admin == False).all()  # 排除管理员
    users_data = {}

    for user in users:
        users_data[user.username] = {
            "expiry_date": user.expiry_date.strftime("%Y-%m-%d"),
            "max_translations": user.max_translations,
            "password": "[HASHED]"  # 密码已哈希，无法恢复明文
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
            usage_data[user.username] = {
                "translations": usage.translations_count
            }

    logging.info(f"导出了 {len(usage_data)} 个用户的使用数据")
    return usage_data


def restore_original_files(users_data: dict, usage_data: dict) -> bool:
    """恢复原始文件"""
    try:
        # 恢复使用数据文件
        usage_file = settings.USAGE_DB_PATH
        with open(usage_file, 'w', encoding='utf-8') as f:
            json.dump(usage_data, f, ensure_ascii=False, indent=2)
        logging.info(f"恢复使用数据文件: {usage_file}")

        # 创建环境变量示例文件
        env_example = {
            "ALLOWED_USERS": json.dumps(users_data, ensure_ascii=False)
        }

        env_file = "restored_env_vars.txt"
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("# 恢复的环境变量值\n")
            f.write("# 复制以下内容到环境变量 ALLOWED_USERS\n\n")
            f.write(f"ALLOWED_USERS={json.dumps(users_data, ensure_ascii=False)}\n")

        logging.info(f"创建环境变量示例文件: {env_file}")

        return True

    except Exception as e:
        logging.error(f"恢复文件失败: {e}")
        return False


def main():
    """主回滚函数"""
    setup_logging()
    logging.info("=" * 60)
    logging.info("开始迁移回滚")
    logging.info("=" * 60)

    # 1. 检查迁移完成标记
    if not os.path.exists("migration_complete.txt"):
        logging.warning("未找到迁移完成标记，可能未进行迁移或标记已删除")
        response = input("是否继续回滚？(y/n): ")
        if response.lower() != 'y':
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
        backup_data = {
            "timestamp": timestamp,
            "users": users_data,
            "usage": usage_data
        }

        with open(db_backup_file, 'w', encoding='utf-8') as f:
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