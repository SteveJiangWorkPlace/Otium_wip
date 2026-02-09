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

from config import settings, is_expired
from models.database import (
    get_db, User, UserUsage, TranslationRecord,
    hash_password, verify_password, create_admin_user
)


class UserService:
    """用户服务类 - 使用数据库存储用户数据"""

    def __init__(self):
        """初始化用户服务"""
        self._lock = threading.RLock()  # 线程锁，防止并发访问
        self._ensure_admin_user()
        logging.info("UserService初始化完成，使用数据库存储")

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

            # 检查账户有效期
            expiry_date = user.expiry_date
            logging.info(f"检查账户有效期: {expiry_date}")

            if is_expired(expiry_date.strftime("%Y-%m-%d")):
                logging.error(f"账户已过期: {expiry_date}")
                return False, f"账户已于 {expiry_date} 过期"

            logging.info("账户有效期检查通过")

            # 检查使用次数
            usage = user.usage
            if not usage:
                # 创建使用记录
                usage = UserUsage(user_id=user.id)
                db.add(usage)
                db.commit()

            used_translations = usage.translations_count
            max_translations = user.max_translations
            logging.info(f"用户使用量检查: 已使用 {used_translations}/{max_translations} 次翻译")

            # 管理员用户跳过使用次数限制
            if not user.is_admin and used_translations >= max_translations:
                return False, f"已达到最大翻译次数限制 ({max_translations})"

            return True, "验证通过"

        finally:
            db.close()

    def record_translation(self, username: str, operation_type: str = "translation", text_length: Optional[int] = None, metadata: Optional[Dict] = None) -> int:
        """记录一次翻译使用"""
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

                # 获取或创建使用记录
                usage = user.usage
                if not usage:
                    usage = UserUsage(user_id=user.id)
                    db.add(usage)

                previous_count = usage.translations_count
                usage.translations_count += 1
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
                logging.info(f"记录翻译使用: 用户 {username}, 之前次数: {previous_count}, 现在次数: {new_count}")
                logging.info(f"翻译使用记录保存成功: 用户 {username}, 总使用次数: {new_count}")

                max_translations = user.max_translations
                remaining = max_translations - new_count
                logging.info(f"用户 {username} 剩余翻译次数: {remaining}/{max_translations}")

                return remaining

            except Exception as e:
                db.rollback()
                logging.error(f"保存翻译使用记录失败，数据可能丢失！用户: {username}, 错误: {str(e)}")
                raise RuntimeError(f"无法保存翻译使用记录: {str(e)}")
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

            usage = user.usage
            if not usage:
                used_translations = 0
            else:
                used_translations = usage.translations_count

            max_translations = user.max_translations
            remaining = max_translations - used_translations

            logging.info(f"获取用户信息: {username}, 已使用 {used_translations}/{max_translations} 次翻译, 剩余 {remaining} 次")

            return {
                "username": username,
                "expiry_date": user.expiry_date.strftime("%Y-%m-%d"),
                "max_translations": max_translations,
                "used_translations": used_translations,
                "remaining_translations": remaining,
                "is_admin": user.is_admin,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            }

        finally:
            db.close()

    def update_user(self, username: str, expiry_date: Optional[str] = None, max_translations: Optional[int] = None, password: Optional[str] = None) -> Tuple[bool, str]:
        """更新用户信息"""
        db = self._get_db_session()
        try:
            user = db.query(User).filter(User.username == username).first()

            if not user:
                return False, "用户不存在"

            if expiry_date:
                try:
                    user.expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d").date()
                except ValueError:
                    return False, "日期格式错误，请使用YYYY-MM-DD格式"

            if max_translations is not None:
                user.max_translations = max_translations

            if password:
                user.password_hash = hash_password(password)

            db.commit()
            return True, "更新成功"

        except Exception as e:
            db.rollback()
            logging.error(f"更新用户失败: {str(e)}")
            return False, f"更新失败: {str(e)}"
        finally:
            db.close()

    def add_user(self, username: str, password: str, expiry_date: str, max_translations: int) -> Tuple[bool, str]:
        """添加新用户"""
        db = self._get_db_session()
        try:
            # 检查用户是否已存在
            existing_user = db.query(User).filter(User.username == username).first()
            if existing_user:
                return False, "用户已存在"

            # 验证日期格式
            try:
                expiry_date_obj = datetime.strptime(expiry_date, "%Y-%m-%d").date()
            except ValueError:
                return False, "日期格式错误，请使用YYYY-MM-DD格式"

            # 创建新用户
            new_user = User(
                username=username,
                password_hash=hash_password(password),
                expiry_date=expiry_date_obj,
                max_translations=max_translations,
                is_admin=False,
                is_active=True
            )
            db.add(new_user)
            db.flush()  # 获取用户ID

            # 创建使用记录
            usage = UserUsage(user_id=new_user.id)
            db.add(usage)

            db.commit()
            return True, "添加成功"

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