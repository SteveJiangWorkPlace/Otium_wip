"""
提示词缓存管理器

扩展现有的CacheManager，专门用于缓存提示词构建结果。
支持LRU淘汰策略、TTL和版本管理。
"""

import hashlib
import time
from typing import Any, TypedDict, cast

from utils import CacheManager


class _CacheStats(TypedDict):
    """缓存统计数据类型"""

    hits: int
    misses: int
    total_requests: int
    creation_times: dict[str, float]


class PromptCacheManager:
    """提示词缓存管理器，专门用于缓存提示词构建结果"""

    def __init__(self, ttl: int = 3600, max_entries: int = 1000):
        """
        初始化提示词缓存管理器

        Args:
            ttl: 缓存存活时间（秒），默认1小时
            max_entries: 最大缓存条目数，默认1000
        """
        # 使用现有的CacheManager作为底层实现
        self.cache_manager = CacheManager(ttl=ttl, max_entries=max_entries)
        self.ttl = ttl
        self.max_entries = max_entries
        self.access_times: dict[str, float] = {}  # 记录访问时间用于LRU
        self.cache_stats: _CacheStats = {
            "hits": 0,
            "misses": 0,
            "total_requests": 0,
            "creation_times": {},  # 记录创建时间
        }

    def get_prompt_key(
        self, text: str, style: str, version: str, template_version: str = "compact"
    ) -> str:
        """
        生成缓存键：文本前200字符的哈希+风格+版本+模板版本

        Args:
            text: 原始文本
            style: 风格（如"US"、"UK"）
            version: 版本（如"basic"、"professional"）
            template_version: 模板版本（"original"、"compact"、"ai_optimized"）

        Returns:
            缓存键字符串
        """
        # 截取文本前200字符作为哈希基础（避免过长文本）
        text_prefix = text[:200] if len(text) > 200 else text

        # 使用SHA256生成哈希
        text_hash = hashlib.sha256(text_prefix.encode()).hexdigest()[:12]

        # 构建缓存键
        return f"prompt_{text_hash}_{style}_{version}_{template_version}"

    def get(
        self, text: str, style: str, version: str, template_version: str = "compact"
    ) -> str | None:
        """
        获取缓存的提示词

        Args:
            text: 原始文本
            style: 风格
            version: 版本
            template_version: 模板版本

        Returns:
            缓存的提示词，如果未找到返回None
        """
        cache_key = self.get_prompt_key(text, style, version, template_version)

        # 更新统计
        self.cache_stats["total_requests"] += 1

        # 从底层缓存获取
        cached_value = self.cache_manager.get(cache_key)

        if cached_value is not None:
            # 缓存命中
            self.cache_stats["hits"] += 1
            self.access_times[cache_key] = time.time()
            return cast(str, cached_value)
        else:
            # 缓存未命中
            self.cache_stats["misses"] += 1
            return None

    def set(
        self,
        text: str,
        style: str,
        version: str,
        prompt: str,
        template_version: str = "compact",
    ):
        """
        缓存提示词

        Args:
            text: 原始文本
            style: 风格
            version: 版本
            prompt: 构建好的提示词
            template_version: 模板版本
        """
        cache_key = self.get_prompt_key(text, style, version, template_version)

        # 设置缓存
        self.cache_manager.set(cache_key, prompt)

        # 记录访问时间和创建时间
        current_time = time.time()
        self.access_times[cache_key] = current_time
        self.cache_stats["creation_times"][cache_key] = current_time

    def clear(self):
        """清空缓存"""
        self.cache_manager.clear()
        self.access_times.clear()
        self.cache_stats["creation_times"].clear()
        self.cache_stats["hits"] = 0
        self.cache_stats["misses"] = 0
        self.cache_stats["total_requests"] = 0

    def get_stats(self) -> dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            包含统计信息的字典
        """
        total_requests = self.cache_stats["total_requests"]
        hits = self.cache_stats["hits"]
        misses = self.cache_stats["misses"]

        hit_rate = hits / total_requests if total_requests > 0 else 0
        miss_rate = misses / total_requests if total_requests > 0 else 0

        return {
            "total_requests": total_requests,
            "hits": hits,
            "misses": misses,
            "hit_rate": f"{hit_rate:.2%}",
            "miss_rate": f"{miss_rate:.2%}",
            "cache_size": len(self.access_times),
            "max_entries": self.max_entries,
            "ttl_seconds": self.ttl,
        }

    def cleanup_old_entries(self):
        """清理过期和旧的缓存条目（LRU策略）"""
        current_time = time.time()

        # 清理过期的访问时间记录
        expired_keys = [
            key
            for key, access_time in self.access_times.items()
            if current_time - access_time > self.ttl
        ]

        for key in expired_keys:
            if key in self.access_times:
                del self.access_times[key]
            if key in self.cache_stats["creation_times"]:
                del self.cache_stats["creation_times"][key]

        # 如果缓存仍然超过最大限制，应用LRU
        if len(self.access_times) > self.max_entries:
            # 找到最久未访问的条目
            sorted_keys = sorted(self.access_times.items(), key=lambda x: x[1])
            keys_to_remove = [
                key for key, _ in sorted_keys[: len(self.access_times) - self.max_entries]
            ]

            for key in keys_to_remove:
                if key in self.access_times:
                    del self.access_times[key]
                if key in self.cache_stats["creation_times"]:
                    del self.cache_stats["creation_times"][key]


# 全局缓存管理器实例
prompt_cache_manager = PromptCacheManager()
