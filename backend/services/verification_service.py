"""
验证服务模块

处理验证码的生成、存储和验证，支持多种用途：
- 邮箱验证码 (purpose: "verify")
- 重置密码令牌 (purpose: "reset")
- 邮箱验证状态令牌 (purpose: "verified")
"""

import logging
import random
import string
from typing import cast

from config import settings
from utils import CacheManager

logger = logging.getLogger(__name__)


class VerificationService:
    """验证服务类"""

    def __init__(self):
        """初始化验证服务"""
        # 验证码缓存：10分钟TTL，最多1000条
        self.verification_cache = CacheManager(ttl=settings.VERIFICATION_CODE_TTL, max_entries=1000)

        # 重置令牌缓存：24小时TTL，最多1000条
        self.reset_token_cache = CacheManager(ttl=settings.RESET_TOKEN_TTL, max_entries=1000)

        # 已验证令牌缓存：30分钟TTL，最多1000条（用于注册流程中的邮箱验证状态）
        self.verified_cache = CacheManager(ttl=1800, max_entries=1000)  # 30分钟

        logger.info("验证服务初始化完成")

    def generate_code(self, length: int = 6) -> str:
        """生成数字验证码

        Args:
            length: 验证码长度，默认6位

        Returns:
            str: 数字验证码
        """
        return "".join(random.choices(string.digits, k=length))

    def generate_alphanumeric_code(self, length: int = 8) -> str:
        """生成字母数字验证码（用于令牌）

        Args:
            length: 验证码长度，默认8位

        Returns:
            str: 字母数字验证码
        """
        chars = string.ascii_letters + string.digits
        return "".join(random.choices(chars, k=length))

    def store_verification_code(self, email: str, code: str) -> None:
        """存储验证码到缓存

        Args:
            email: 邮箱地址
            code: 验证码
        """
        key = f"verify:{email}"
        self.verification_cache.set(key, code)
        logger.debug(f"存储验证码: {email} -> {code}")

    def verify_code(self, email: str, code: str) -> tuple[bool, str]:
        """验证验证码

        Args:
            email: 邮箱地址
            code: 用户输入的验证码

        Returns:
            Tuple[bool, str]: (是否验证成功, 错误信息)
        """
        key = f"verify:{email}"
        stored_code = self.verification_cache.get(key)

        if not stored_code:
            return False, "验证码已过期或不存在，请重新发送"

        if stored_code != code:
            return False, "验证码错误，请重新输入"

        # 验证成功后删除验证码，防止重复使用
        self.verification_cache.cache.pop(key, None)
        logger.debug(f"验证码验证成功: {email}")
        return True, "验证成功"

    def store_reset_token(self, email: str, token: str) -> None:
        """存储重置令牌到缓存

        Args:
            email: 邮箱地址
            token: 重置令牌
        """
        key = f"reset:{token}"
        self.reset_token_cache.set(key, email)
        logger.debug(f"存储重置令牌: {email} -> {token}")

    def verify_reset_token(self, token: str) -> tuple[bool, str | None]:
        """验证重置令牌

        Args:
            token: 重置令牌

        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 邮箱地址或None)
        """
        key = f"reset:{token}"
        email = self.reset_token_cache.get(key)

        if not email:
            return False, None

        logger.debug(f"重置令牌验证成功: {token} -> {email}")
        return True, email

    def consume_reset_token(self, token: str) -> str | None:
        """使用并删除重置令牌（一次性使用）

        Args:
            token: 重置令牌

        Returns:
            Optional[str]: 邮箱地址或None（如果令牌无效）
        """
        key = f"reset:{token}"
        email = self.reset_token_cache.get(key)

        if email:
            # 删除令牌，防止重复使用
            self.reset_token_cache.cache.pop(key, None)
            logger.debug(f"使用重置令牌: {token} -> {email}")
            # 类型断言：email不为None
            assert email is not None
            return cast(str, email)

        return None

    def store_verified_token(self, email: str, token: str) -> None:
        """存储已验证令牌（用于注册流程）

        Args:
            email: 已验证的邮箱
            token: 令牌
        """
        key = f"verified:{token}"
        self.verified_cache.set(key, email)
        logger.debug(f"存储已验证令牌: {email} -> {token}")

    def verify_verified_token(self, token: str) -> tuple[bool, str | None]:
        """验证已验证令牌

        Args:
            token: 已验证令牌

        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 邮箱地址或None)
        """
        key = f"verified:{token}"
        email: str | None = self.verified_cache.get(key)

        if not email:
            return False, None

        logger.debug(f"已验证令牌验证成功: {token} -> {email}")
        return True, email

    def consume_verified_token(self, token: str) -> str | None:
        """使用并删除已验证令牌（一次性使用）

        Args:
            token: 已验证令牌

        Returns:
            Optional[str]: 邮箱地址或None（如果令牌无效）
        """
        key = f"verified:{token}"
        email: str | None = self.verified_cache.get(key)

        if email:
            # 删除令牌，防止重复使用
            self.verified_cache.cache.pop(key, None)
            logger.debug(f"使用已验证令牌: {token} -> {email}")
            # 类型断言：email不为None
            assert email is not None
            return email

        return None

    def get_verification_attempts(self, email: str) -> int:
        """获取验证尝试次数（简单实现）

        在实际生产环境中，可能需要更复杂的速率限制逻辑。

        Args:
            email: 邮箱地址

        Returns:
            int: 尝试次数
        """
        # 这里可以扩展为更复杂的速率限制逻辑
        # 目前返回0表示无限制
        return 0

    def increment_verification_attempts(self, email: str) -> None:
        """增加验证尝试次数

        Args:
            email: 邮箱地址
        """
        # 这里可以扩展为更复杂的速率限制逻辑
        pass

    def clear_verification_attempts(self, email: str) -> None:
        """清除验证尝试次数

        Args:
            email: 邮箱地址
        """
        # 这里可以扩展为更复杂的速率限制逻辑
        pass

    def is_rate_limited(self, email: str, purpose: str = "verify") -> bool:
        """检查是否达到速率限制

        Args:
            email: 邮箱地址
            purpose: 用途类型 ("verify", "reset")

        Returns:
            bool: 是否被限制
        """
        # 简单的速率限制：同一邮箱10分钟内最多发送3次
        if purpose == "verify":
            # 这里可以扩展为更复杂的速率限制逻辑
            # 目前返回False表示无限制
            return False
        return False


# 全局验证服务实例
verification_service = VerificationService()
