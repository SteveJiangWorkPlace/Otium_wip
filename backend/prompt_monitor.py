"""
提示词性能监控模块

用于监控提示词构建的性能指标，包括：
1. 构建时间
2. 缓存命中率
3. 提示词长度
4. 性能改进对比
"""

import time
from functools import wraps
from typing import Dict, Any, List, Callable
import statistics
from datetime import datetime


class PromptPerformanceMonitor:
    """提示词性能监控器"""

    # 类级别存储性能指标
    metrics: Dict[str, Any] = {
        "build_times": [],           # 构建时间列表（秒）
        "cache_hits": 0,             # 缓存命中次数
        "cache_misses": 0,           # 缓存未命中次数
        "prompt_lengths": [],        # 提示词长度列表
        "function_calls": {},        # 各函数调用统计
        "performance_history": []    # 性能历史记录
    }

    @classmethod
    def record_build_time(cls, func_name: str = None):
        """
        记录构建时间的装饰器

        Args:
            func_name: 可选，函数名称，用于更细粒度的监控
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()

                build_time = end_time - start_time
                cls.metrics["build_times"].append(build_time)
                cls.metrics["prompt_lengths"].append(len(result))

                # 记录函数调用统计
                if func_name:
                    if func_name not in cls.metrics["function_calls"]:
                        cls.metrics["function_calls"][func_name] = {
                            "count": 0,
                            "total_time": 0,
                            "avg_time": 0
                        }
                    func_stats = cls.metrics["function_calls"][func_name]
                    func_stats["count"] += 1
                    func_stats["total_time"] += build_time
                    func_stats["avg_time"] = func_stats["total_time"] / func_stats["count"]

                # 记录性能历史
                cls.metrics["performance_history"].append({
                    "timestamp": datetime.now().isoformat(),
                    "function": func_name or func.__name__,
                    "build_time_ms": build_time * 1000,
                    "prompt_length": len(result),
                    "cache_hit": kwargs.get("cache_hit", False) if "cache_hit" in kwargs else None
                })

                # 保持历史记录不超过1000条
                if len(cls.metrics["performance_history"]) > 1000:
                    cls.metrics["performance_history"] = cls.metrics["performance_history"][-1000:]

                return result
            return wrapper
        return decorator

    @classmethod
    def record_cache_hit(cls, hit: bool):
        """
        记录缓存命中

        Args:
            hit: True表示命中，False表示未命中
        """
        if hit:
            cls.metrics["cache_hits"] += 1
        else:
            cls.metrics["cache_misses"] += 1

    @classmethod
    def record_function_call(cls, func_name: str, build_time: float, prompt_length: int):
        """
        记录函数调用信息

        Args:
            func_name: 函数名称
            build_time: 构建时间（秒）
            prompt_length: 提示词长度
        """
        cls.metrics["build_times"].append(build_time)
        cls.metrics["prompt_lengths"].append(prompt_length)

        # 记录函数调用统计
        if func_name not in cls.metrics["function_calls"]:
            cls.metrics["function_calls"][func_name] = {
                "count": 0,
                "total_time": 0,
                "avg_time": 0,
                "total_length": 0,
                "avg_length": 0
            }

        func_stats = cls.metrics["function_calls"][func_name]
        func_stats["count"] += 1
        func_stats["total_time"] += build_time
        func_stats["total_length"] += prompt_length
        func_stats["avg_time"] = func_stats["total_time"] / func_stats["count"]
        func_stats["avg_length"] = func_stats["total_length"] / func_stats["count"]

    @classmethod
    def get_report(cls) -> Dict[str, Any]:
        """
        获取性能报告

        Returns:
            包含性能指标的字典
        """
        build_times = cls.metrics["build_times"]
        cache_hits = cls.metrics["cache_hits"]
        cache_misses = cls.metrics["cache_misses"]
        prompt_lengths = cls.metrics["prompt_lengths"]

        total_requests = cache_hits + cache_misses
        total_builds = len(build_times)

        # 计算缓存命中率
        hit_rate = cache_hits / total_requests if total_requests > 0 else 0

        # 计算构建时间统计
        if build_times:
            avg_build_time_ms = statistics.mean(build_times) * 1000
            min_build_time_ms = min(build_times) * 1000
            max_build_time_ms = max(build_times) * 1000
            p95_build_time_ms = statistics.quantiles(build_times, n=20)[18] * 1000 if len(build_times) >= 20 else None
        else:
            avg_build_time_ms = min_build_time_ms = max_build_time_ms = p95_build_time_ms = 0

        # 计算提示词长度统计
        if prompt_lengths:
            avg_prompt_length = statistics.mean(prompt_lengths)
            min_prompt_length = min(prompt_lengths)
            max_prompt_length = max(prompt_lengths)
            length_reduction_pct = 0  # 需要与基线对比
        else:
            avg_prompt_length = min_prompt_length = max_prompt_length = length_reduction_pct = 0

        # 函数调用统计
        function_stats = {}
        for func_name, stats in cls.metrics["function_calls"].items():
            function_stats[func_name] = {
                "call_count": stats["count"],
                "avg_build_time_ms": stats["avg_time"] * 1000,
                "avg_prompt_length": stats["avg_length"]
            }

        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_requests": total_requests,
                "total_builds": total_builds,
                "cache_hits": cache_hits,
                "cache_misses": cache_misses,
                "cache_hit_rate": f"{hit_rate:.2%}",
                "performance_improvement": "待计算（需要基线数据）"
            },
            "build_time_stats_ms": {
                "average": round(avg_build_time_ms, 2),
                "minimum": round(min_build_time_ms, 2),
                "maximum": round(max_build_time_ms, 2),
                "p95": round(p95_build_time_ms, 2) if p95_build_time_ms else None,
                "sample_count": total_builds
            },
            "prompt_length_stats": {
                "average": round(avg_prompt_length),
                "minimum": min_prompt_length,
                "maximum": max_prompt_length,
                "length_reduction_pct": f"{length_reduction_pct:.1%}",
                "sample_count": len(prompt_lengths)
            },
            "function_stats": function_stats,
            "monitoring_config": {
                "history_size": len(cls.metrics["performance_history"]),
                "max_history": 1000
            }
        }

    @classmethod
    def get_detailed_history(cls, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取详细的性能历史记录

        Args:
            limit: 返回的记录条数限制

        Returns:
            性能历史记录列表
        """
        return cls.metrics["performance_history"][-limit:]

    @classmethod
    def reset_metrics(cls):
        """重置所有性能指标"""
        cls.metrics = {
            "build_times": [],
            "cache_hits": 0,
            "cache_misses": 0,
            "prompt_lengths": [],
            "function_calls": {},
            "performance_history": []
        }

    @classmethod
    def set_baseline(cls, avg_build_time_ms: float, avg_prompt_length: int):
        """
        设置性能基线，用于计算改进百分比

        Args:
            avg_build_time_ms: 基线平均构建时间（毫秒）
            avg_prompt_length: 基线平均提示词长度
        """
        cls.metrics["baseline"] = {
            "avg_build_time_ms": avg_build_time_ms,
            "avg_prompt_length": avg_prompt_length,
            "set_at": datetime.now().isoformat()
        }

    @classmethod
    def calculate_improvement(cls) -> Dict[str, Any]:
        """
        计算性能改进百分比（与基线对比）

        Returns:
            包含改进百分比的计算结果
        """
        if "baseline" not in cls.metrics:
            return {"error": "未设置性能基线"}

        baseline = cls.metrics["baseline"]
        current_report = cls.get_report()

        # 当前平均构建时间
        current_avg_build_time_ms = current_report["build_time_stats_ms"]["average"]
        baseline_avg_build_time_ms = baseline["avg_build_time_ms"]

        # 当前平均提示词长度
        current_avg_length = current_report["prompt_length_stats"]["average"]
        baseline_avg_length = baseline["avg_prompt_length"]

        # 计算改进百分比
        build_time_improvement = 0
        if baseline_avg_build_time_ms > 0:
            build_time_improvement = ((baseline_avg_build_time_ms - current_avg_build_time_ms) /
                                      baseline_avg_build_time_ms) * 100

        length_reduction = 0
        if baseline_avg_length > 0:
            length_reduction = ((baseline_avg_length - current_avg_length) /
                                baseline_avg_length) * 100

        return {
            "build_time_improvement_pct": round(build_time_improvement, 1),
            "length_reduction_pct": round(length_reduction, 1),
            "baseline": {
                "avg_build_time_ms": baseline_avg_build_time_ms,
                "avg_prompt_length": baseline_avg_length,
                "set_at": baseline["set_at"]
            },
            "current": {
                "avg_build_time_ms": current_avg_build_time_ms,
                "avg_prompt_length": current_avg_length
            }
        }


# 全局监控器实例
prompt_performance_monitor = PromptPerformanceMonitor()