#!/usr/bin/env python3
"""
提示词优化测试脚本

用于测试优化后的提示词构建系统的性能和功能。
"""

import os
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from prompts import (
    build_academic_translate_prompt,
    build_error_check_prompt,
    clear_prompt_cache,
    get_cache_stats,
    get_prompt_stats,
    get_shortcut_annotations,
    test_prompt_build_performance,
)
from prompts_backup import (
    SHORTCUT_ANNOTATIONS_ORIGINAL,
    build_academic_translate_prompt_original,
    build_error_check_prompt_original,
)


def test_error_check_prompt():
    """测试纠错提示词构建"""
    print("\n" + "=" * 60)
    print("测试纠错提示词构建")
    print("=" * 60)

    test_text = "这是一个测试文本，包含一些错别字和重复字字。"

    # 测试原始版本
    start_time = time.time()
    original_prompt = build_error_check_prompt_original(test_text)
    original_time = time.time() - start_time
    original_length = len(original_prompt)

    print("原始版本:")
    print(f"  构建时间: {original_time * 1000:.2f}ms")
    print(f"  提示词长度: {original_length} 字符")
    print(f"  内容预览: {original_prompt[:100]}...")

    # 测试优化版本（compact）
    start_time = time.time()
    compact_prompt = build_error_check_prompt(test_text, template_version="compact")
    compact_time = time.time() - start_time
    compact_length = len(compact_prompt)

    print("\n优化版本 (compact):")
    print(f"  构建时间: {compact_time * 1000:.2f}ms")
    print(f"  提示词长度: {compact_length} 字符")
    print(f"  长度减少: {(original_length - compact_length) / original_length * 100:.1f}%")
    if original_time > 0:
        print(f"  构建时间减少: {(original_time - compact_time) / original_time * 100:.1f}%")
    else:
        print("  构建时间减少: N/A (原始构建时间过短)")
    print(f"  内容预览: {compact_prompt[:100]}...")

    # 测试优化版本（ai_optimized）
    start_time = time.time()
    ai_prompt = build_error_check_prompt(test_text, template_version="ai_optimized")
    ai_time = time.time() - start_time
    ai_length = len(ai_prompt)

    print("\n优化版本 (ai_optimized):")
    print(f"  构建时间: {ai_time * 1000:.2f}ms")
    print(f"  提示词长度: {ai_length} 字符")
    print(f"  长度减少: {(original_length - ai_length) / original_length * 100:.1f}%")
    if original_time > 0:
        print(f"  构建时间减少: {(original_time - ai_time) / original_time * 100:.1f}%")
    else:
        print("  构建时间减少: N/A (原始构建时间过短)")
    print(f"  内容预览: {ai_prompt[:100]}...")


def test_translation_prompt():
    """测试翻译提示词构建和缓存"""
    print("\n" + "=" * 60)
    print("测试翻译提示词构建和缓存")
    print("=" * 60)

    test_text = "人工智能是当今最重要的技术之一，它正在改变我们的生活和工作方式。"

    # 清除缓存
    clear_prompt_cache()

    # 测试原始版本
    start_time = time.time()
    original_prompt = build_academic_translate_prompt_original(test_text)
    original_time = time.time() - start_time
    original_length = len(original_prompt)

    print("原始版本 (无缓存):")
    print(f"  构建时间: {original_time * 1000:.2f}ms")
    print(f"  提示词长度: {original_length} 字符")

    # 测试优化版本 - 第一次（无缓存）
    start_time = time.time()
    optimized_prompt_1 = build_academic_translate_prompt(test_text, use_cache=True)
    optimized_time_1 = time.time() - start_time
    optimized_length_1 = len(optimized_prompt_1)

    print("\n优化版本 - 第一次调用 (无缓存):")
    print(f"  构建时间: {optimized_time_1 * 1000:.2f}ms")
    print(f"  提示词长度: {optimized_length_1} 字符")
    print(f"  长度减少: {(original_length - optimized_length_1) / original_length * 100:.1f}%")
    if original_time > 0:
        print(f"  构建时间减少: {(original_time - optimized_time_1) / original_time * 100:.1f}%")
    else:
        print("  构建时间减少: N/A (原始构建时间过短)")

    # 测试优化版本 - 第二次（有缓存）
    start_time = time.time()
    optimized_prompt_2 = build_academic_translate_prompt(test_text, use_cache=True)
    optimized_time_2 = time.time() - start_time
    len(optimized_prompt_2)

    print("\n优化版本 - 第二次调用 (有缓存):")
    print(f"  构建时间: {optimized_time_2 * 1000:.2f}ms")
    if optimized_time_1 > 0:
        print(
            f"  缓存命中时间减少: {(optimized_time_1 - optimized_time_2) / optimized_time_1 * 100:.1f}%"
        )
    else:
        print("  缓存命中时间减少: N/A (第一次构建时间过短)")

    # 测试不同模板版本
    print("\n不同模板版本对比:")
    for version in ["original", "compact", "ai_optimized"]:
        start_time = time.time()
        prompt = build_academic_translate_prompt(
            test_text, style="US", version="professional", template_version=version, use_cache=False
        )
        build_time = time.time() - start_time
        print(f"  {version:12s}: {build_time * 1000:6.2f}ms, {len(prompt):5d} 字符")


def test_shortcut_annotations():
    """测试快捷批注优化"""
    print("\n" + "=" * 60)
    print("测试快捷批注优化")
    print("=" * 60)

    original = SHORTCUT_ANNOTATIONS_ORIGINAL
    compact = get_shortcut_annotations("compact")
    ai_optimized = get_shortcut_annotations("ai_optimized")

    print(f"原始版本批注数量: {len(original)}")
    print(f"Compact版本批注数量: {len(compact)}")
    print(f"AI优化版本批注数量: {len(ai_optimized)}")

    # 对比几个关键批注的长度
    test_keys = ["去AI词汇", "人性化处理", "句式修正"]
    for key in test_keys:
        if key in original:
            original_len = len(original[key])
            compact_len = len(compact.get(key, ""))
            ai_len = len(ai_optimized.get(key, ""))

            print(f"\n批注 '{key}':")
            print(f"  原始版本: {original_len:5d} 字符")
            if compact_len > 0:
                print(
                    f"  Compact版本: {compact_len:5d} 字符 (减少 {(original_len - compact_len) / original_len * 100:.1f}%)"
                )
            if ai_len > 0:
                print(
                    f"  AI优化版本: {ai_len:5d} 字符 (减少 {(original_len - ai_len) / original_len * 100:.1f}%)"
                )


def test_performance_monitor():
    """测试性能监控"""
    print("\n" + "=" * 60)
    print("测试性能监控")
    print("=" * 60)

    # 生成一些测试调用
    test_text = "测试性能监控系统的功能。"

    for i in range(5):
        build_error_check_prompt(f"{test_text} {i}")
        build_academic_translate_prompt(f"{test_text} {i}", use_cache=True)

    # 获取统计信息
    stats = get_prompt_stats()
    cache_stats = get_cache_stats()

    print("性能统计:")
    print(f"  总请求数: {stats.get('summary', {}).get('total_requests', 0)}")
    print(f"  缓存命中率: {stats.get('summary', {}).get('cache_hit_rate', '0%')}")
    print(f"  平均构建时间: {stats.get('build_time_stats_ms', {}).get('average', 0):.2f}ms")

    print("\n缓存统计:")
    print(f"  总请求数: {cache_stats.get('total_requests', 0)}")
    print(f"  命中率: {cache_stats.get('hit_rate', '0%')}")
    print(f"  缓存大小: {cache_stats.get('cache_size', 0)}/{cache_stats.get('max_entries', 0)}")


def run_comprehensive_test():
    """运行全面测试"""
    print("提示词优化系统测试")
    print("=" * 60)
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        test_error_check_prompt()
        test_translation_prompt()
        test_shortcut_annotations()
        test_performance_monitor()

        # 运行内置性能测试
        print("\n" + "=" * 60)
        print("运行内置性能测试")
        print("=" * 60)
        perf_results = test_prompt_build_performance()

        print(f"纠错提示词构建时间: {perf_results['error_check']['time_ms']}ms")
        print(f"翻译提示词构建时间 (无缓存): {perf_results['translation_no_cache']['time_ms']}ms")
        print(f"翻译提示词构建时间 (有缓存): {perf_results['translation_with_cache']['time_ms']}ms")
        print(f"缓存命中率: {perf_results['cache_stats']['hit_rate']}")

        print("\n" + "=" * 60)
        print("测试完成!")
        print(f"结束时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
