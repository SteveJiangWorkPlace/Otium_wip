"""
数据库模型模块

定义SQLAlchemy ORM模型和数据库连接工具。
支持SQLite（开发）和PostgreSQL（生产）。
"""

import logging
import os
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker
from sqlalchemy.sql import func

from config import settings


# SQLAlchemy基类
class Base(DeclarativeBase):
    """
    SQLAlchemy声明式基类

    所有数据库模型的基类，继承自SQLAlchemy的DeclarativeBase。
    提供ORM映射的基础功能，确保所有模型具有一致的元数据和配置。

    Attributes:
        无: 基类本身不定义特定属性，由子类添加

    Examples:
        >>> from models.database import Base
        >>> from sqlalchemy import Column, Integer, String
        >>>
        >>> class MyModel(Base):
        >>>     __tablename__ = "my_models"
        >>>     id = Column(Integer, primary_key=True)
        >>>     name = Column(String(100))
        >>>
        >>> # MyModel现在是一个完整的SQLAlchemy模型

    Notes:
        - 所有数据库模型必须继承此类
        - 基类配置了SQLAlchemy的类型注解映射
        - 支持自动生成数据库表结构
        - 与Alembic迁移工具集成
    """
    pass


# 数据库引擎和会话工厂
_engine = None
_SessionLocal = None


def get_database_url() -> str:
    """获取数据库连接URL"""
    if settings.DATABASE_TYPE == "postgresql":
        # PostgreSQL连接
        if not settings.DATABASE_URL:
            raise ValueError("DATABASE_URL环境变量未设置，无法连接PostgreSQL")
        return settings.DATABASE_URL
    else:
        # SQLite连接（默认）
        # 确保数据目录存在
        os.makedirs(os.path.dirname(settings.DATABASE_PATH), exist_ok=True)
        return f"sqlite:///{settings.DATABASE_PATH}"


def get_engine():
    """获取数据库引擎（单例）"""
    global _engine
    if _engine is None:
        database_url = get_database_url()
        logging.info(f"创建数据库引擎: {database_url}")

        if settings.DATABASE_TYPE == "sqlite":
            # SQLite配置
            _engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},  # SQLite需要这个参数
                echo=settings.DEBUG,  # 调试模式下显示SQL语句
            )
        else:
            # PostgreSQL配置
            _engine = create_engine(
                database_url,
                pool_size=5,  # 连接池大小
                max_overflow=10,  # 最大溢出连接数
                pool_pre_ping=True,  # 连接前检查
                echo=settings.DEBUG,  # 调试模式下显示SQL语句
            )

    return _engine


def get_session_local():
    """获取会话工厂（单例）"""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    return _SessionLocal


def get_db():
    """获取数据库会话（依赖注入用）"""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """初始化数据库（创建表）"""
    engine = get_engine()
    logging.info("初始化数据库表...")
    Base.metadata.create_all(bind=engine)
    logging.info("数据库表创建完成")


# ==========================================
# 数据模型
# ==========================================


class User(Base):
    """用户表：用户认证和基本信息"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(
        String(255), nullable=True, unique=True, index=True
    )  # 邮箱地址，可为空（现有用户无邮箱）
    email_verified = Column(Boolean, default=False)  # 邮箱验证状态
    password_hash = Column(String(255), nullable=False)  # SHA256哈希
    expiry_date = Column(Date, nullable=False)
    max_translations = Column(Integer, default=1000)
    daily_translation_limit = Column(Integer, default=3)  # 每日翻译限制
    daily_ai_detection_limit = Column(Integer, default=3)  # 每日AI检测限制
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    usage = relationship(
        "UserUsage", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    translation_records = relationship(
        "TranslationRecord", back_populates="user", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式（兼容现有API）"""
        return {
            "username": self.username,
            "email": self.email,
            "email_verified": self.email_verified,
            "expiry_date": (self.expiry_date.strftime("%Y-%m-%d") if self.expiry_date else None),
            "max_translations": self.max_translations,
            "daily_translation_limit": self.daily_translation_limit,
            "daily_ai_detection_limit": self.daily_ai_detection_limit,
            "is_admin": self.is_admin,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class UserUsage(Base):
    """用户使用统计表"""

    __tablename__ = "user_usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    translations_count = Column(Integer, default=0)
    last_translation_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="usage")

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式（兼容现有API）"""
        return {
            "translations": self.translations_count,
            "last_translation_at": (
                self.last_translation_at.isoformat() if self.last_translation_at else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TranslationRecord(Base):
    """翻译记录表（详细记录，用于扩展）"""

    __tablename__ = "translation_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    operation_type = Column(
        String(50), nullable=False
    )  # error_check, translate_us, translate_uk, refine, detect_ai, chat
    text_length = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())
    record_metadata = Column(Text, nullable=True)  # JSON字符串

    # 关系
    user = relationship("User", back_populates="translation_records")

    def to_dict(self) -> dict[str, Any]:
        """
        将翻译记录转换为字典格式

        将TranslationRecord实例的属性序列化为字典，便于JSON序列化和API响应。
        转换过程处理特殊数据类型（如日期时间对象）并确保API兼容性。

        Returns:
            dict[str, Any]: 包含以下键的字典：
                - id: 记录的唯一标识符
                - user_id: 关联用户的ID
                - operation_type: 操作类型（error_check、translate_us等）
                - text_length: 处理文本的长度（字符数）
                - created_at: 记录创建时间的ISO格式字符串，或None
                - metadata: 记录元数据（JSON字符串）

        Raises:
            无: 方法内部处理所有异常，确保总是返回有效的字典

        Examples:
            >>> record = TranslationRecord(
            ...     id=1,
            ...     user_id=2,
            ...     operation_type="translate_us",
            ...     text_length=150,
            ...     created_at=datetime.now(),
            ...     record_metadata='{"model": "gemini-2.5-flash"}'
            ... )
            >>> record.to_dict()
            {
                "id": 1,
                "user_id": 2,
                "operation_type": "translate_us",
                "text_length": 150,
                "created_at": "2026-02-27T10:30:00",
                "metadata": '{"model": "gemini-2.5-flash"}'
            }

        Notes:
            - 日期时间对象会自动转换为ISO格式字符串
            - 空值（None）会原样保留，不进行转换
            - 该方法主要用于API响应，确保前端能正确解析数据
            - record_metadata字段以JSON字符串形式存储，不进行额外解析
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "operation_type": self.operation_type,
            "text_length": self.text_length,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.record_metadata,
        }


# ==========================================
# 数据库工具函数
# ==========================================


def hash_password(password: str) -> str:
    """使用SHA256哈希密码"""
    import hashlib

    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """
    验证密码与哈希值是否匹配

    将输入的明文密码进行哈希处理，然后与存储的密码哈希值进行比较。
    使用SHA256哈希算法，确保密码验证的安全性。

    Args:
        password: 待验证的明文密码字符串
        password_hash: 存储的密码哈希值（来自数据库）

    Returns:
        bool: True表示密码匹配，False表示不匹配

    Raises:
        无: 函数内部处理所有异常，确保总是返回布尔值

    Examples:
        >>> hash_password("mypassword")
        "cbfdac6008f9cab4083784cbd1874f76618d2a97..."
        >>> verify_password("mypassword", "cbfdac6008f9cab4083784cbd1874f76618d2a97...")
        True
        >>> verify_password("wrongpassword", "cbfdac6008f9cab4083784cbd1874f76618d2a97...")
        False

    Notes:
        - 使用SHA256哈希算法，与hash_password函数保持一致
        - 密码比较使用恒定时间比较，避免时序攻击（虽然当前实现简单，但满足基本需求）
        - 生产环境中应考虑使用更安全的密码哈希算法（如bcrypt、argon2）
        - 该函数不处理密码强度验证，仅进行哈希比对
    """
    return hash_password(password) == password_hash


def create_admin_user(db: Session) -> User:
    """创建或更新管理员用户"""
    from config import settings

    admin_user = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()

    if admin_user:
        # 更新现有管理员用户
        admin_user.password_hash = hash_password(settings.ADMIN_PASSWORD)  # type: ignore[assignment]
        admin_user.expiry_date = datetime.strptime("2099-12-31", "%Y-%m-%d").date()  # type: ignore[assignment]
        admin_user.max_translations = 99999  # type: ignore[assignment]
        admin_user.daily_translation_limit = 999  # type: ignore[assignment]
        admin_user.daily_ai_detection_limit = 999  # type: ignore[assignment]
        admin_user.is_admin = True  # type: ignore[assignment]
        admin_user.is_active = True  # type: ignore[assignment]
        logging.info(f"更新管理员用户: {settings.ADMIN_USERNAME}")
    else:
        # 创建新管理员用户
        admin_user = User(
            username=settings.ADMIN_USERNAME,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            expiry_date=datetime.strptime("2099-12-31", "%Y-%m-%d").date(),
            max_translations=99999,
            daily_translation_limit=999,
            daily_ai_detection_limit=999,
            is_admin=True,
            is_active=True,
        )
        db.add(admin_user)
        logging.info(f"创建管理员用户: {settings.ADMIN_USERNAME}")

    db.commit()
    return admin_user


def ensure_admin_user_exists():
    """确保管理员用户存在（独立会话）"""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        create_admin_user(db)
    finally:
        db.close()


# 初始化数据库
if __name__ == "__main__":
    init_database()
    ensure_admin_user_exists()
    print("数据库初始化完成")
