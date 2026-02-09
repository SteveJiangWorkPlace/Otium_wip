"""
服务模块包

包含各种业务逻辑服务：
- user_service: 用户管理服务（数据库版本）
"""

from .user_service import UserService

__all__ = ["UserService"]