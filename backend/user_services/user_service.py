"""
用户服务模块

替代原有的UserLimitManager，使用数据库存储用户数据。
保持相同的API接口，实现向后兼容。
"""

import json
import logging
import threading
from datetime import date, datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from config import settings
from models.database import TranslationRecord, User, UserUsage, hash_password, verify_password


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
        return SessionLocal()  # type: ignore[no-any-return]

    def authenticate_user(self, username: str, password: str | None = None) -> tuple[bool, str]:
        """验证用户（对应原is_user_allowed方法）"""
        logging.info("=== 登录验证开始 ===")
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
                if not verify_password(password, user.password_hash):  # type: ignore[arg-type]
                    logging.error("密码不匹配！")
                    return False, "密码错误"

            logging.info("密码验证通过！")

            # 检查账户有效性（仅检查是否被禁用）
            if not user.is_active:
                logging.error(f"用户已被禁用: {username}")
                return False, "用户已被禁用"

            logging.info("用户验证通过")

            return True, "验证通过"

        finally:
            db.close()

    def record_usage(
        self,
        username: str,
        operation_type: str = "translation",
        text_length: int | None = None,
        metadata: dict | None = None,
    ) -> int:
        """记录一次使用（翻译、AI检测等）"""
        # 添加类型检查和转换
        if hasattr(username, "username"):
            username = username.username
        elif not isinstance(username, str | int):
            username = str(username)  # type: ignore[unreachable]

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
                daily_limit: int
                if operation_type in ["translate_us", "translate_uk"]:
                    daily_limit = user.daily_translation_limit  # type: ignore[assignment]
                    limit_type = "翻译"
                elif operation_type == "ai_detection":
                    daily_limit = user.daily_ai_detection_limit  # type: ignore[assignment]
                    limit_type = "AI检测"
                else:
                    daily_limit = 10  # 默认限制
                    limit_type = "操作"

                # 查询今日该操作类型的记录数
                daily_count = (
                    db.query(TranslationRecord)
                    .filter(
                        TranslationRecord.user_id == user.id,
                        func.date(TranslationRecord.created_at) == today,
                        TranslationRecord.operation_type == operation_type,
                    )
                    .count()
                )

                if daily_count >= daily_limit:
                    logging.warning(
                        f"用户 {username} 今日{limit_type}次数已达上限 ({daily_limit} 次)"
                    )
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
                    record_metadata=metadata_json,
                )
                db.add(record)

                db.commit()

                new_count = usage.translations_count
                logging.info(
                    f"记录使用({operation_type}): 用户 {username}, 之前总次数: {previous_count}, 现在总次数: {new_count}"
                )
                logging.info(f"使用记录保存成功: 用户 {username}, 总使用次数: {new_count}")

                # 不再计算和返回剩余次数，现在只使用每日限制
                # 返回0表示成功，前端不需要处理剩余次数
                return 0

            except Exception as e:
                db.rollback()
                logging.error(
                    f"保存使用记录失败，数据可能丢失！用户: {username}, 操作类型: {operation_type}, 错误: {str(e)}"
                )
                raise RuntimeError(f"无法保存使用记录: {str(e)}") from e
            finally:
                db.close()

    def get_user_info(self, username: str) -> dict[str, Any] | None:
        """
        获取指定用户的详细信息

        根据用户名查询用户完整信息，包括基本信息、今日使用统计和账户状态。
        如果用户不存在，返回None。

        Args:
            username: 要查询的用户名（字符串）

        Returns:
            dict[str, Any] | None: 用户信息字典，包含以下字段：
                - id: 用户ID
                - username: 用户名
                - email: 邮箱地址
                - is_admin: 是否为管理员
                - is_active: 账户是否激活
                - expiry_date: 账户过期日期
                - daily_translation_limit: 每日翻译限制
                - daily_ai_detection_limit: 每日AI检测限制
                - daily_translation_used: 今日已使用翻译次数
                - daily_ai_detection_used: 今日已使用AI检测次数
                - created_at: 创建时间
                如果用户不存在，返回None

        Raises:
            无: 函数内部处理所有异常，确保总是返回有效结果

        Examples:
            >>> service = UserService()
            >>> info = service.get_user_info("test_user")
            >>> print(info["username"])
            "test_user"

        Notes:
            - 用户名支持多种类型输入（字符串、整数、用户对象）
            - 自动进行类型转换，确保查询正确性
            - 只返回今日使用统计，历史统计不再包含
            - 数据库连接在函数内部管理，调用者无需担心资源泄漏
        """
        # 添加类型检查和转换
        if hasattr(username, "username"):
            username = username.username
        elif not isinstance(username, str | int):
            username = str(username)  # type: ignore[unreachable]

        db = self._get_db_session()
        try:
            user = db.query(User).filter(User.username == username).first()

            if not user:
                return None

            # 不再需要总使用次数统计，只保留每日限制

            # 获取今日使用统计
            today = datetime.utcnow().date()
            daily_translation_used = (
                db.query(TranslationRecord)
                .filter(
                    TranslationRecord.user_id == user.id,
                    func.date(TranslationRecord.created_at) == today,
                    TranslationRecord.operation_type.in_(["translate_us", "translate_uk"]),
                )
                .count()
            )

            daily_ai_detection_used = (
                db.query(TranslationRecord)
                .filter(
                    TranslationRecord.user_id == user.id,
                    func.date(TranslationRecord.created_at) == today,
                    TranslationRecord.operation_type == "ai_detection",
                )
                .count()
            )

            logging.info(f"获取用户信息: {username}")
            logging.info(
                f"今日使用: 翻译 {daily_translation_used}/{user.daily_translation_limit} 次, AI检测 {daily_ai_detection_used}/{user.daily_ai_detection_limit} 次"
            )

            return {
                "username": username,
                "daily_translation_limit": user.daily_translation_limit,
                "daily_ai_detection_limit": user.daily_ai_detection_limit,
                "daily_translation_used": daily_translation_used,
                "daily_ai_detection_used": daily_ai_detection_used,
                "is_admin": user.is_admin,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            }

        finally:
            db.close()

    def update_user(
        self,
        username: str,
        password: str | None = None,
        daily_translation_limit: int | None = None,
        daily_ai_detection_limit: int | None = None,
    ) -> tuple[bool, str]:
        """更新用户信息（密码和每日限制）"""
        db = self._get_db_session()
        try:
            user = db.query(User).filter(User.username == username).first()

            if not user:
                return False, "用户不存在"

            if password:
                user.password_hash = hash_password(password)  # type: ignore[assignment]

            if daily_translation_limit is not None:
                user.daily_translation_limit = daily_translation_limit  # type: ignore[assignment]

            if daily_ai_detection_limit is not None:
                user.daily_ai_detection_limit = daily_ai_detection_limit  # type: ignore[assignment]

            db.commit()
            return True, ""

        except Exception as e:
            db.rollback()
            logging.error(f"更新用户密码失败: {str(e)}")
            return False, f"更新失败: {str(e)}"
        finally:
            db.close()

    def add_user(
        self,
        username: str,
        password: str,
        daily_translation_limit: int = 10,
        daily_ai_detection_limit: int = 10,
    ) -> tuple[bool, str]:
        """
        添加新用户到系统

        创建新的用户账户，设置密码哈希、每日使用限制和账户基本信息。
        自动创建关联的用户使用记录表，确保账户完整初始化。

        Args:
            username: 新用户的用户名，必须唯一
            password: 用户的明文密码，函数内部会进行哈希处理
            daily_translation_limit: 每日翻译次数限制，默认10次
            daily_ai_detection_limit: 每日AI检测次数限制，默认10次

        Returns:
            tuple[bool, str]: 操作结果元组，包含：
                - 布尔值：操作是否成功
                - 字符串：成功时为空字符串，失败时为错误消息

        Raises:
            无: 函数内部捕获所有异常并转换为错误消息返回

        Examples:
            >>> service = UserService()
            >>> success, message = service.add_user("newuser", "password123")
            >>> print(f"成功: {success}, 消息: {message}")
            成功: True, 消息: ""

            >>> success, message = service.add_user("existing_user", "password")
            >>> print(f"成功: {success}, 消息: {message}")
            成功: False, 消息: "用户已存在"

        Notes:
            - 用户密码使用SHA256哈希算法存储，不保存明文
            - 默认设置账户过期时间为2099-12-31（长期有效）
            - 不再使用总翻译次数限制（max_translations设为0）
            - 自动创建UserUsage记录表，用于跟踪每日使用统计
            - 用户默认为非管理员、已激活状态
            - 用户名重复时会返回"用户已存在"错误
        """
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
                is_active=True,
            )
            db.add(new_user)
            db.flush()  # 立即将用户数据写入数据库以生成ID，用于后续关联记录创建

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

    def get_all_users(self) -> list[dict[str, Any]]:
        """
        获取系统中所有用户的完整信息列表

        查询数据库中的所有用户记录，按创建时间倒序排列，返回每个用户的详细信息。
        每个用户信息通过get_user_info方法获取，确保数据格式一致。

        Args:
            无: 此方法不接受参数

        Returns:
            list[dict[str, Any]]: 用户信息字典列表，每个字典包含以下字段：
                - id: 用户ID
                - username: 用户名
                - email: 邮箱地址
                - is_admin: 是否为管理员
                - is_active: 账户是否激活
                - expiry_date: 账户过期日期
                - daily_translation_limit: 每日翻译限制
                - daily_ai_detection_limit: 每日AI检测限制
                - daily_translation_used: 今日已使用翻译次数
                - daily_ai_detection_used: 今日已使用AI检测次数
                - created_at: 创建时间
                如果系统中没有用户，返回空列表

        Raises:
            无: 函数内部处理所有异常，确保总是返回有效结果

        Examples:
            >>> service = UserService()
            >>> all_users = service.get_all_users()
            >>> print(f"总用户数: {len(all_users)}")
            总用户数: 5

            >>> for user in all_users[:2]:
            >>>     print(user["username"])
            "user1"
            "user2"

        Notes:
            - 返回列表按用户创建时间倒序排列（最近创建的在前）
            - 每个用户信息通过get_user_info方法获取，确保数据一致性
            - 空数据库时返回空列表，而非None
            - 数据库连接在函数内部管理，调用者无需担心资源泄漏
            - 主要用于管理员界面显示所有用户信息
        """
        db = self._get_db_session()
        try:
            users = db.query(User).order_by(User.created_at.desc()).all()
            result = []

            for user in users:
                user_info = self.get_user_info(user.username)  # type: ignore[arg-type]
                if user_info:
                    result.append(user_info)

            return result

        finally:
            db.close()

    def get_user_usage_stats(self, username: str) -> dict[str, Any] | None:
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
                    "translation_records": [],
                }

            # 获取最近的翻译记录
            records = (
                db.query(TranslationRecord)
                .filter(TranslationRecord.user_id == user.id)
                .order_by(TranslationRecord.created_at.desc())
                .limit(10)
                .all()
            )

            return {
                "translations_count": usage.translations_count,
                "last_translation_at": (
                    usage.last_translation_at.isoformat() if usage.last_translation_at else None
                ),
                "translation_records": [record.to_dict() for record in records],
            }

        finally:
            db.close()

    def reset_user_usage(self, username: str) -> tuple[bool, str]:
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

    def deactivate_user(self, username: str) -> tuple[bool, str]:
        """
        禁用指定用户的账户

        将用户的is_active字段设为False，使其无法登录和使用系统功能。
        管理员账户无法被禁用，确保系统管理功能始终可用。

        Args:
            username: 要禁用的用户名

        Returns:
            tuple[bool, str]: 操作结果元组，包含：
                - 布尔值：操作是否成功
                - 字符串：成功时返回"用户已禁用"，失败时返回错误消息

        Raises:
            无: 函数内部捕获所有异常并转换为错误消息返回

        Examples:
            >>> service = UserService()
            >>> success, message = service.deactivate_user("inactive_user")
            >>> print(f"成功: {success}, 消息: {message}")
            成功: True, 消息: "用户已禁用"

            >>> success, message = service.deactivate_user("admin")
            >>> print(f"成功: {success}, 消息: {message}")
            成功: False, 消息: "不能禁用管理员账户"

        Notes:
            - 管理员账户（is_admin=True）不能被禁用，保护系统管理功能
            - 已禁用的用户再次禁用会返回成功（幂等操作）
            - 禁用用户后，其账户将无法登录和使用任何API功能
            - 可以通过activate_user方法重新激活账户
            - 主要用于处理违规账户或临时停用
        """
        db = self._get_db_session()
        try:
            user = db.query(User).filter(User.username == username).first()

            if not user:
                return False, "用户不存在"

            if user.is_admin:
                return False, "不能禁用管理员用户"

            user.is_active = False  # type: ignore[assignment]
            db.commit()
            return True, "用户已禁用"

        except Exception as e:
            db.rollback()
            logging.error(f"禁用用户失败: {str(e)}")
            return False, f"禁用失败: {str(e)}"
        finally:
            db.close()

    def activate_user(self, username: str) -> tuple[bool, str]:
        """
        启用指定用户的账户

        将用户的is_active字段设为True，恢复其登录和使用系统功能的权限。
        可以重新激活之前被禁用的用户账户。

        Args:
            username: 要启用的用户名

        Returns:
            tuple[bool, str]: 操作结果元组，包含：
                - 布尔值：操作是否成功
                - 字符串：成功时返回"用户已启用"，失败时返回错误消息

        Raises:
            无: 函数内部捕获所有异常并转换为错误消息返回

        Examples:
            >>> service = UserService()
            >>> success, message = service.activate_user("reactivated_user")
            >>> print(f"成功: {success}, 消息: {message}")
            成功: True, 消息: "用户已启用"

            >>> success, message = service.activate_user("nonexistent_user")
            >>> print(f"成功: {success}, 消息: {message}")
            成功: False, 消息: "用户不存在"

        Notes:
            - 只能启用已存在的用户账户
            - 已启用的用户再次启用会返回成功（幂等操作）
            - 启用用户后，其账户将恢复正常的登录和API使用权限
            - 通常与deactivate_user配合使用，用于账户状态管理
            - 主要用于恢复被临时禁用的账户
        """
        db = self._get_db_session()
        try:
            user = db.query(User).filter(User.username == username).first()

            if not user:
                return False, "用户不存在"

            user.is_active = True  # type: ignore[assignment]
            db.commit()
            return True, "用户已启用"

        except Exception as e:
            db.rollback()
            logging.error(f"启用用户失败: {str(e)}")
            return False, f"启用失败: {str(e)}"
        finally:
            db.close()

    def register_user(
        self, username: str, email: str, password: str, email_verified: bool = False
    ) -> tuple[bool, str]:
        """注册新用户

        Args:
            username: 用户名
            email: 邮箱地址
            password: 密码
            email_verified: 邮箱是否已验证（默认False）

        Returns:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        db = self._get_db_session()
        try:
            # 验证用户名长度和格式
            if len(username) < 3:
                return False, "用户名至少需要3个字符"
            if len(username) > 50:
                return False, "用户名不能超过50个字符"

            # 验证密码长度
            if len(password) < 6:
                return False, "密码至少需要6个字符"

            # 验证邮箱格式（简单验证）
            if "@" not in email or "." not in email:
                return False, "邮箱格式不正确"

            # 检查用户名是否已存在
            existing_user = db.query(User).filter(User.username == username).first()
            if existing_user:
                return False, "用户名已被使用"

            # 检查邮箱是否已存在（如果有邮箱验证要求）
            if email:
                existing_email = db.query(User).filter(User.email == email).first()
                if existing_email:
                    return False, "邮箱已被注册"

            # 设置默认值：过期时间设为2099-12-31
            expiry_date_obj = date(2099, 12, 31)

            # 创建新用户
            new_user = User(
                username=username,
                email=email,
                email_verified=email_verified,
                password_hash=hash_password(password),
                expiry_date=expiry_date_obj,
                max_translations=0,  # 不再使用总次数限制
                daily_translation_limit=settings.DAILY_TRANSLATION_LIMIT,  # 使用默认配置
                daily_ai_detection_limit=settings.DAILY_AI_DETECTION_LIMIT,  # 使用默认配置
                is_admin=False,
                is_active=True,
            )
            db.add(new_user)
            db.flush()  # 立即将用户数据写入数据库以生成ID，用于后续关联记录创建

            # 创建使用记录
            usage = UserUsage(user_id=new_user.id)
            db.add(usage)

            db.commit()
            logging.info(f"用户注册成功: {username} ({email})")
            return True, "注册成功"

        except Exception as e:
            db.rollback()
            logging.error(f"注册用户失败: {str(e)}")
            return False, f"注册失败: {str(e)}"
        finally:
            db.close()

    def update_user_email(
        self, username: str, email: str, email_verified: bool = False
    ) -> tuple[bool, str]:
        """更新用户邮箱

        Args:
            username: 用户名
            email: 新邮箱地址
            email_verified: 邮箱是否已验证

        Returns:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        db = self._get_db_session()
        try:
            user = db.query(User).filter(User.username == username).first()

            if not user:
                return False, "用户不存在"

            # 验证邮箱格式
            if "@" not in email or "." not in email:
                return False, "邮箱格式不正确"

            # 检查邮箱是否已被其他用户使用
            existing_email = (
                db.query(User).filter(User.email == email, User.username != username).first()
            )
            if existing_email:
                return False, "邮箱已被其他用户使用"

            user.email = email  # type: ignore[assignment]
            user.email_verified = email_verified  # type: ignore[assignment]
            db.commit()

            logging.info(f"用户邮箱更新成功: {username} -> {email}")
            return True, "邮箱更新成功"

        except Exception as e:
            db.rollback()
            logging.error(f"更新用户邮箱失败: {str(e)}")
            return False, f"更新失败: {str(e)}"
        finally:
            db.close()

    def verify_user_email(self, username: str) -> tuple[bool, str]:
        """验证用户邮箱（标记为已验证）

        Args:
            username: 用户名

        Returns:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        db = self._get_db_session()
        try:
            user = db.query(User).filter(User.username == username).first()

            if not user:
                return False, "用户不存在"

            if not user.email:
                return False, "用户没有设置邮箱"

            user.email_verified = True  # type: ignore[assignment]
            db.commit()

            logging.info(f"用户邮箱验证成功: {username}")
            return True, "邮箱验证成功"

        except Exception as e:
            db.rollback()
            logging.error(f"验证用户邮箱失败: {str(e)}")
            return False, f"验证失败: {str(e)}"
        finally:
            db.close()

    def request_password_reset(self, email: str) -> tuple[bool, str, str | None]:
        """请求密码重置（验证邮箱存在性）

        Args:
            email: 邮箱地址

        Returns:
            Tuple[bool, str, Optional[str]]: (是否成功, 错误信息, 用户名或None)
        """
        db = self._get_db_session()
        try:
            # 查找邮箱对应的用户
            user = db.query(User).filter(User.email == email).first()

            if not user:
                return False, "该邮箱未注册", None

            if not user.is_active:
                return False, "用户已被禁用", None

            logging.info(f"密码重置请求: {email} -> {user.username}")
            return True, "重置请求已接受", user.username  # type: ignore[return-value]

        except Exception as e:
            logging.error(f"处理密码重置请求失败: {str(e)}")
            return False, f"处理失败: {str(e)}", None
        finally:
            db.close()

    def reset_password(self, username: str, new_password: str) -> tuple[bool, str]:
        """重置用户密码

        Args:
            username: 用户名
            new_password: 新密码

        Returns:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        # 验证密码长度
        if len(new_password) < 6:
            return False, "密码至少需要6个字符"

        db = self._get_db_session()
        try:
            user = db.query(User).filter(User.username == username).first()

            if not user:
                return False, "用户不存在"

            if not user.is_active:
                return False, "用户已被禁用"

            # 更新密码
            user.password_hash = hash_password(new_password)  # type: ignore[assignment]
            db.commit()

            logging.info(f"密码重置成功: {username}")
            return True, "密码重置成功"

        except Exception as e:
            db.rollback()
            logging.error(f"重置密码失败: {str(e)}")
            return False, f"重置失败: {str(e)}"
        finally:
            db.close()

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """通过邮箱获取用户信息

        Args:
            email: 邮箱地址

        Returns:
            Optional[Dict[str, Any]]: 用户信息或None
        """
        db = self._get_db_session()
        try:
            user = db.query(User).filter(User.email == email).first()

            if not user:
                return None

            return {
                "username": user.username,
                "email": user.email,
                "email_verified": user.email_verified,
                "is_admin": user.is_admin,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }

        finally:
            db.close()

    def check_username_available(self, username: str) -> tuple[bool, str]:
        """检查用户名是否可用

        Args:
            username: 用户名

        Returns:
            Tuple[bool, str]: (是否可用, 错误信息)
        """
        # 验证用户名长度和格式
        if len(username) < 3:
            return False, "用户名至少需要3个字符"
        if len(username) > 50:
            return False, "用户名不能超过50个字符"

        # 检查是否包含非法字符（仅允许字母、数字、下划线、连字符）
        import re

        if not re.match(r"^[a-zA-Z0-9_-]+$", username):
            return False, "用户名只能包含字母、数字、下划线和连字符"

        db = self._get_db_session()
        try:
            existing_user = db.query(User).filter(User.username == username).first()
            if existing_user:
                return False, "用户名已被使用"

            return True, "用户名可用"

        finally:
            db.close()

    def check_email_available(self, email: str) -> tuple[bool, str]:
        """检查邮箱是否可用

        Args:
            email: 邮箱地址

        Returns:
            Tuple[bool, str]: (是否可用, 错误信息)
        """
        # 验证邮箱格式
        if "@" not in email or "." not in email:
            return False, "邮箱格式不正确"

        db = self._get_db_session()
        try:
            existing_email = db.query(User).filter(User.email == email).first()
            if existing_email:
                return False, "邮箱已被注册"

            return True, "邮箱可用"

        finally:
            db.close()


# 向后兼容的别名
# 注意：为了保持完全兼容，我们提供is_user_allowed方法
UserService.is_user_allowed = UserService.authenticate_user  # type: ignore[attr-defined]
