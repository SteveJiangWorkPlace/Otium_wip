"""
用户服务模块

替代原有的UserLimitManager，使用数据库存储用户数据。
保持相同的API接口，实现向后兼容。
"""

import os
import json
import logging
import threading
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func

from config import settings, is_expired
from models.database import (
    get_db, User, UserUsage, TranslationRecord,
    hash_password, verify_password, create_admin_user
)


class UserService:
    """用户服务类 - 使用数据库存储用户数据"""

    DAILY_LIMIT = 3  # 每个用户每天的翻译使用次数限制

    def __init__(self):
        """初始化用户服务"""
        self._lock = threading.RLock()  # 线程锁，防止并发访问
        self._ensure_admin_user()
        logging.info("UserService初始化完成，使用数据库存储")
        logging.info(f"每日翻译限制: {settings.DAILY_TRANSLATION_LIMIT} 次")
        logging.info(f"每日AI检测限制: {settings.DAILY_AI_DETECTION_LIMIT} 次")

    def _ensure_admin_user(self):
        """确保管理员用户存在"""
        from models.database import ensure_admin_user_exists
        ensure_admin_user_exists()

    def _get_db_session(self) -> Session:
        """获取数据库会话（独立会话）"""
        from models.database import get_session_local
        SessionLocal = get_session_local()
        return SessionLocal()

    def authenticate_user(self, username: str, password: Optional[str] = None) -> Tuple[bool, str]:
        """验证用户（对应原is_user_allowed方法）"""
        logging.info(f"=== 登录验证开始 ===")
        logging.info(f"用户名: {username}")
        logging.info(f"输入密码: {'*****' if password else 'None'}")

        db = self._get_db_session()
        try:
            user = db.query(User).filter(User.username == username).first()

            if not user:
                logging.error(f"用户不存在: {username}")
                return False, "用户不存在"

            if not user.is_active:
                logging.error(f"用户已被禁用: {username}")
                return False, "用户已被禁用"

            logging.info(f"用户数据: {user.to_dict()}")

            if password is not None:
                if not verify_password(password, user.password_hash):
                    logging.error(f"密码不匹配！")
                    return False, "密码错误"

            logging.info(f"密码验证通过！")

            # 检查账户有效性（仅检查是否被禁用）
            if not user.is_active:
                logging.error(f"用户已被禁用: {username}")
                return False, "用户已被禁用"

            logging.info("用户验证通过")

            return True, "验证通过"

        finally:
            db.close()

    def record_usage(self, username: str, operation_type: str = "translation", text_length: Optional[int] = None, metadata: Optional[Dict] = None) -> int:
        """记录一次使用（翻译、AI检测等）"""
        # 添加类型检查和转换
        if hasattr(username, 'username'):
            username = username.username
        elif not isinstance(username, (str, int)):
            username = str(username)

        # 使用线程锁确保原子操作
        with self._lock:
            db = self._get_db_session()
            try:
                user = db.query(User).filter(User.username == username).first()

                if not user:
                    logging.error(f"用户 {username} 不存在，无法记录翻译使用")
                    raise ValueError(f"用户 {username} 不存在")

                # 检查每日限制
                today = datetime.utcnow().date()

                # 根据操作类型确定每日限制（使用用户特定的限制值）
                if operation_type in ["translate_us", "translate_uk"]:
                    daily_limit = user.daily_translation_limit
                    limit_type = "翻译"
                elif operation_type == "ai_detection":
                    daily_limit = user.daily_ai_detection_limit
                    limit_type = "AI检测"
                else:
                    daily_limit = 10  # 默认限制
                    limit_type = "操作"

                # 查询今日该操作类型的记录数
                daily_count = db.query(TranslationRecord).filter(
                    TranslationRecord.user_id == user.id,
                    func.date(TranslationRecord.created_at) == today,
                    TranslationRecord.operation_type == operation_type
                ).count()

                if daily_count >= daily_limit:
                    logging.warning(f"用户 {username} 今日{limit_type}次数已达上限 ({daily_limit} 次)")
                    raise ValueError(f"今日{limit_type}次数已达上限 ({daily_limit} 次)，请明天再试")

                # 获取或创建使用记录
                usage = user.usage
                if not usage:
                    usage = UserUsage(user_id=user.id, translations_count=0)
                    db.add(usage)

                previous_count = usage.translations_count or 0
                usage.translations_count = (usage.translations_count or 0) + 1
                usage.last_translation_at = datetime.now()

                # 创建详细记录
                if metadata:
                    metadata_json = json.dumps(metadata)
                else:
                    metadata_json = None

                record = TranslationRecord(
                    user_id=user.id,
                    operation_type=operation_type,
                    text_length=text_length,
                    record_metadata=metadata_json
                )
                db.add(record)

                db.commit()

                new_count = usage.translations_count
                logging.info(f"记录使用({operation_type}): 用户 {username}, 之前总次数: {previous_count}, 现在总次数: {new_count}")
                logging.info(f"使用记录保存成功: 用户 {username}, 总使用次数: {new_count}")

                # 不再计算和返回剩余次数，现在只使用每日限制
                # 返回0表示成功，前端不需要处理剩余次数
                return 0

            except Exception as e:
                db.rollback()
                logging.error(f"保存使用记录失败，数据可能丢失！用户: {username}, 操作类型: {operation_type}, 错误: {str(e)}")
                raise RuntimeError(f"无法保存使用记录: {str(e)}")
            finally:
                db.close()

    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        # 添加类型检查和转换
        if hasattr(username, 'username'):
            username = username.username
        elif not isinstance(username, (str, int)):
            username = str(username)

        db = self._get_db_session()
        try:
            user = db.query(User).filter(User.username == username).first()

            if not user:
                return None

            # 不再需要总使用次数统计，只保留每日限制

            # 获取今日使用统计
            today = datetime.utcnow().date()
            daily_translation_used = db.query(TranslationRecord).filter(
                TranslationRecord.user_id == user.id,
                func.date(TranslationRecord.created_at) == today,
                TranslationRecord.operation_type.in_(["translate_us", "translate_uk"])
            ).count()

            daily_ai_detection_used = db.query(TranslationRecord).filter(
                TranslationRecord.user_id == user.id,
                func.date(TranslationRecord.created_at) == today,
                TranslationRecord.operation_type == "ai_detection"
            ).count()

            logging.info(f"获取用户信息: {username}")
            logging.info(f"今日使用: 翻译 {daily_translation_used}/{user.daily_translation_limit} 次, AI检测 {daily_ai_detection_used}/{user.daily_ai_detection_limit} 次")

            return {
                "username": username,
                "daily_translation_limit": user.daily_translation_limit,
                "daily_ai_detection_limit": user.daily_ai_detection_limit,
                "daily_translation_used": daily_translation_used,
                "daily_ai_detection_used": daily_ai_detection_used,
                "is_admin": user.is_admin,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            }

        finally:
            db.close()

    def update_user(self, username: str, password: Optional[str] = None, daily_translation_limit: Optional[int] = None, daily_ai_detection_limit: Optional[int] = None) -> Tuple[bool, str]:
        """更新用户信息（密码和每日限制）"""
        db = self._get_db_session()
        try:
            user = db.query(User).filter(User.username == username).first()

            if not user:
                return False, "用户不存在"

            if password:
                user.password_hash = hash_password(password)

            if daily_translation_limit is not None:
                user.daily_translation_limit = daily_translation_limit

            if daily_ai_detection_limit is not None:
                user.daily_ai_detection_limit = daily_ai_detection_limit

            db.commit()
            return True, ""

        except Exception as e:
            db.rollback()
            logging.error(f"更新用户密码失败: {str(e)}")
            return False, f"更新失败: {str(e)}"
        finally:
            db.close()

    def add_user(self, username: str, password: str, daily_translation_limit: int = 10, daily_ai_detection_limit: int = 10) -> Tuple[bool, str]:
        """添加新用户"""
        db = self._get_db_session()
        try:
            # 检查用户是否已存在
            existing_user = db.query(User).filter(User.username == username).first()
            if existing_user:
                return False, "用户已存在"

            # 设置默认值：过期时间设为2099-12-31，最大翻译次数设为0（不再使用）
            expiry_date_obj = date(2099, 12, 31)

            # 创建新用户
            new_user = User(
                username=username,
                password_hash=hash_password(password),
                expiry_date=expiry_date_obj,
                max_translations=0,  # 不再使用总次数限制
                daily_translation_limit=daily_translation_limit,
                daily_ai_detection_limit=daily_ai_detection_limit,
                is_admin=False,
                is_active=True
            )
            db.add(new_user)
            db.flush()  # 获取用户ID

            # 创建使用记录
            usage = UserUsage(user_id=new_user.id)
            db.add(usage)

            db.commit()
            return True, ""

        except Exception as e:
            db.rollback()
            logging.error(f"添加用户失败: {str(e)}")
            return False, f"添加失败: {str(e)}"
        finally:
            db.close()

    def get_all_users(self) -> List[Dict[str, Any]]:
        """获取所有用户信息"""
        db = self._get_db_session()
        try:
            users = db.query(User).order_by(User.created_at.desc()).all()
            result = []

            for user in users:
                user_info = self.get_user_info(user.username)
                if user_info:
                    result.append(user_info)

            return result

        finally:
            db.close()

    def get_user_usage_stats(self, username: str) -> Optional[Dict[str, Any]]:
        """获取用户使用统计（扩展功能）"""
        db = self._get_db_session()
        try:
            user = db.query(User).filter(User.username == username).first()

            if not user:
                return None

            usage = user.usage
            if not usage:
                return {
                    "translations_count": 0,
                    "last_translation_at": None,
                    "translation_records": []
                }

            # 获取最近的翻译记录
            records = db.query(TranslationRecord).filter(
                TranslationRecord.user_id == user.id
            ).order_by(TranslationRecord.created_at.desc()).limit(10).all()

            return {
                "translations_count": usage.translations_count,
                "last_translation_at": usage.last_translation_at.isoformat() if usage.last_translation_at else None,
                "translation_records": [record.to_dict() for record in records]
            }

        finally:
            db.close()

    def reset_user_usage(self, username: str) -> Tuple[bool, str]:
        """重置用户使用次数（管理员功能）"""
        db = self._get_db_session()
        try:
            user = db.query(User).filter(User.username == username).first()

            if not user:
                return False, "用户不存在"

            usage = user.usage
            if usage:
                usage.translations_count = 0
                usage.last_translation_at = None
                db.commit()
                return True, "使用次数已重置"
            else:
                return False, "用户使用记录不存在"

        except Exception as e:
            db.rollback()
            logging.error(f"重置用户使用次数失败: {str(e)}")
            return False, f"重置失败: {str(e)}"
        finally:
            db.close()

    def deactivate_user(self, username: str) -> Tuple[bool, str]:
        """禁用用户"""
        db = self._get_db_session()
        try:
            user = db.query(User).filter(User.username == username).first()

            if not user:
                return False, "用户不存在"

            if user.is_admin:
                return False, "不能禁用管理员用户"

            user.is_active = False
            db.commit()
            return True, "用户已禁用"

        except Exception as e:
            db.rollback()
            logging.error(f"禁用用户失败: {str(e)}")
            return False, f"禁用失败: {str(e)}"
        finally:
            db.close()

    def activate_user(self, username: str) -> Tuple[bool, str]:
        """启用用户"""
        db = self._get_db_session()
        try:
            user = db.query(User).filter(User.username == username).first()

            if not user:
                return False, "用户不存在"

            user.is_active = True
            db.commit()
            return True, "用户已启用"

        except Exception as e:
            db.rollback()
            logging.error(f"启用用户失败: {str(e)}")
            return False, f"启用失败: {str(e)}"
        finally:
            db.close()


# 向后兼容的别名
# 注意：为了保持完全兼容，我们提供is_user_allowed方法
UserService.is_user_allowed = UserService.authenticate_user