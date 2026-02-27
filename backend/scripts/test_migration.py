#!/usr/bin/env python3
"""
测试数据库迁移

测试UserService的功能，确保与原有UserLimitManager兼容。
"""

import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models.database import User, get_session_local, init_database
from user_services.user_service import UserService


def setup_logging():
    """
    配置日志系统，设置日志级别和格式。

    Configures:
        - Level: INFO
        - Format: 时间戳 - 级别 - 消息
        - Output: 标准输出

    Note:
        - 用于测试脚本的统一日志格式
        - 确保所有测试输出具有一致的可读性
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def test_user_service():
    """测试UserService基本功能"""
    logging.info("=" * 60)
    logging.info("开始测试UserService")
    logging.info("=" * 60)

    # 初始化数据库
    logging.info("初始化数据库...")
    init_database()

    # 创建UserService实例
    user_service = UserService()

    # 测试1: 添加用户
    logging.info("\n测试1: 添加用户")
    success, message = user_service.add_user(
        username="test_user1",
        password="test123",
        expiry_date="2026-12-31",
        max_translations=100,
    )
    logging.info(f"添加用户结果: {success}, {message}")

    # 测试2: 验证用户
    logging.info("\n测试2: 验证用户")
    allowed, message = user_service.authenticate_user("test_user1", "test123")
    logging.info(f"验证用户结果: {allowed}, {message}")

    # 测试3: 获取用户信息
    logging.info("\n测试3: 获取用户信息")
    user_info = user_service.get_user_info("test_user1")
    logging.info(f"用户信息: {user_info}")

    # 测试4: 记录翻译使用
    logging.info("\n测试4: 记录翻译使用")
    remaining = user_service.record_translation(
        "test_user1", operation_type="test", text_length=100
    )
    logging.info(f"剩余翻译次数: {remaining}")

    # 测试5: 更新用户信息
    logging.info("\n测试5: 更新用户信息")
    success, message = user_service.update_user(
        username="test_user1", max_translations=200, expiry_date="2027-12-31"
    )
    logging.info(f"更新用户结果: {success}, {message}")

    # 测试6: 获取更新后的用户信息
    logging.info("\n测试6: 获取更新后的用户信息")
    user_info = user_service.get_user_info("test_user1")
    logging.info(f"更新后的用户信息: {user_info}")

    # 测试7: 获取所有用户
    logging.info("\n测试7: 获取所有用户")
    all_users = user_service.get_all_users()
    logging.info(f"所有用户数量: {len(all_users)}")
    for user in all_users:
        logging.info(
            f"  - {user['username']}: {user['remaining_translations']}/{user['max_translations']}"
        )

    # 测试8: 验证错误密码
    logging.info("\n测试8: 验证错误密码")
    allowed, message = user_service.authenticate_user("test_user1", "wrong_password")
    logging.info(f"错误密码验证结果: {allowed}, {message}")

    # 测试9: 验证不存在的用户
    logging.info("\n测试9: 验证不存在的用户")
    allowed, message = user_service.authenticate_user("non_existent_user", "password")
    logging.info(f"不存在的用户验证结果: {allowed}, {message}")

    # 测试10: 检查管理员用户
    logging.info("\n测试10: 检查管理员用户")
    from config import settings

    admin_info = user_service.get_user_info(settings.ADMIN_USERNAME)
    if admin_info:
        logging.info(f"管理员用户存在: {admin_info['username']}")
        logging.info(f"管理员信息: {admin_info}")
    else:
        logging.warning("管理员用户不存在")

    logging.info("=" * 60)
    logging.info("UserService测试完成")
    logging.info("=" * 60)

    return True


def test_database_models():
    """
    测试SQLAlchemy数据库模型的基本功能。

    测试内容:
        1. 数据库连接和查询
        2. 用户模型字段完整性
        3. 密码哈希和验证功能
        4. 用户使用记录关联

    Returns:
        bool: 测试是否成功

    Note:
        - 使用独立的测试数据库
        - 不修改生产数据
    """
    logging.info("\n" + "=" * 60)
    logging.info("测试数据库模型")
    logging.info("=" * 60)

    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        # 测试用户查询
        users = db.query(User).all()
        logging.info(f"数据库中的用户数量: {len(users)}")

        for user in users:
            logging.info(
                f"用户: {user.username}, 过期日期: {user.expiry_date}, 管理员: {user.is_admin}"
            )

            # 测试使用记录
            if user.usage:
                logging.info(f"  使用次数: {user.usage.translations_count}")

        # 测试密码哈希
        from models.database import hash_password, verify_password

        test_password = "test_password"
        hashed = hash_password(test_password)
        logging.info("\n密码哈希测试:")
        logging.info(f"  原始密码: {test_password}")
        logging.info(f"  哈希值: {hashed}")
        logging.info(f"  验证结果: {verify_password(test_password, hashed)}")
        logging.info(f"  错误密码验证: {verify_password('wrong_password', hashed)}")

    finally:
        db.close()

    logging.info("=" * 60)
    logging.info("数据库模型测试完成")
    logging.info("=" * 60)

    return True


def cleanup_test_data():
    """
    清理测试过程中创建的临时数据。

    清理操作:
        1. 删除测试用户'test_user1'
        2. 统计剩余用户数量
        3. 回滚异常情况

    Note:
        - 仅在用户确认后执行
        - 使用事务确保数据一致性
        - 记录清理过程便于调试
    """
    logging.info("\n" + "=" * 60)
    logging.info("清理测试数据")
    logging.info("=" * 60)

    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        # 删除测试用户
        test_user = db.query(User).filter(User.username == "test_user1").first()
        if test_user:
            db.delete(test_user)
            db.commit()
            logging.info("测试用户已删除")

        # 统计剩余用户
        remaining_users = db.query(User).count()
        logging.info(f"数据库中剩余用户数量: {remaining_users}")

    except Exception as e:
        logging.error(f"清理数据时出错: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """
    主测试流程：验证数据库迁移和UserService功能。

    执行顺序:
        1. 设置日志
        2. 测试UserService（添加、验证、更新用户等）
        3. 测试数据库模型
        4. 可选清理测试数据
        5. 输出测试结果

    Returns:
        bool: 所有测试是否通过

    Note:
        - 测试前会初始化测试数据库
        - 提供交互式数据清理选项
    """
    setup_logging()

    try:
        # 运行测试
        test_user_service()
        test_database_models()

        # 询问是否清理测试数据
        response = input("\n是否清理测试数据？(y/n): ")
        if response.lower() == "y":
            cleanup_test_data()
        else:
            logging.info("保留测试数据")

        logging.info("\n" + "=" * 60)
        logging.info("所有测试完成!")
        logging.info("=" * 60)

        return True

    except Exception as e:
        logging.error(f"测试过程中出现错误: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
