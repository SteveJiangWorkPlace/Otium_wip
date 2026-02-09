"""
数据库模型模块

定义SQLAlchemy ORM模型和数据库连接工具。
支持SQLite（开发）和PostgreSQL（生产）。
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func

from config import settings

# SQLAlchemy基类
Base = declarative_base()

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
                echo=settings.DEBUG  # 调试模式下显示SQL语句
            )
        else:
            # PostgreSQL配置
            _engine = create_engine(
                database_url,
                pool_size=5,  # 连接池大小
                max_overflow=10,  # 最大溢出连接数
                pool_pre_ping=True,  # 连接前检查
                echo=settings.DEBUG  # 调试模式下显示SQL语句
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
    password_hash = Column(String(255), nullable=False)  # SHA256哈希
    expiry_date = Column(Date, nullable=False)
    max_translations = Column(Integer, default=1000)
    daily_translation_limit = Column(Integer, default=10)  # 每日翻译限制
    daily_ai_detection_limit = Column(Integer, default=10)  # 每日AI检测限制
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    usage = relationship("UserUsage", back_populates="user", uselist=False, cascade="all, delete-orphan")
    translation_records = relationship("TranslationRecord", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（兼容现有API）"""
        return {
            "username": self.username,
            "expiry_date": self.expiry_date.strftime("%Y-%m-%d") if self.expiry_date else None,
            "max_translations": self.max_translations,
            "daily_translation_limit": self.daily_translation_limit,
            "daily_ai_detection_limit": self.daily_ai_detection_limit,
            "is_admin": self.is_admin,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class UserUsage(Base):
    """用户使用统计表"""
    __tablename__ = "user_usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    translations_count = Column(Integer, default=0)
    last_translation_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="usage")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（兼容现有API）"""
        return {
            "translations": self.translations_count,
            "last_translation_at": self.last_translation_at.isoformat() if self.last_translation_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class TranslationRecord(Base):
    """翻译记录表（详细记录，用于扩展）"""
    __tablename__ = "translation_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    operation_type = Column(String(50), nullable=False)  # error_check, translate_us, translate_uk, refine, detect_ai, chat
    text_length = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())
    record_metadata = Column(Text, nullable=True)  # JSON字符串

    # 关系
    user = relationship("User", back_populates="translation_records")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "operation_type": self.operation_type,
            "text_length": self.text_length,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.record_metadata
        }


# ==========================================
# 数据库工具函数
# ==========================================

def hash_password(password: str) -> str:
    """使用SHA256哈希密码"""
    import hashlib
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    return hash_password(password) == password_hash


def create_admin_user(db: Session) -> User:
    """创建或更新管理员用户"""
    from config import settings

    admin_user = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()

    if admin_user:
        # 更新现有管理员用户
        admin_user.password_hash = hash_password(settings.ADMIN_PASSWORD)
        admin_user.expiry_date = datetime.strptime("2099-12-31", "%Y-%m-%d").date()
        admin_user.max_translations = 99999
        admin_user.daily_translation_limit = 999
        admin_user.daily_ai_detection_limit = 999
        admin_user.is_admin = True
        admin_user.is_active = True
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
            is_active=True
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