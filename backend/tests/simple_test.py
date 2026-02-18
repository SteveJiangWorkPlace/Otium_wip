#!/usr/bin/env python3
"""
简单测试脚本 - 验证提示词优化功能
"""

import os
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入优化版本
from prompts import (
    build_academic_translate_prompt,
    build_error_check_prompt,
    clear_prompt_cache,
    get_cache_stats,
    get_prompt_stats,
    get_shortcut_annotations,
)

# 导入原始版本
from prompts_backup import (
    SHORTCUT_ANNOTATIONS_ORIGINAL,
    build_academic_translate_prompt_original,
    build_error_check_prompt_original,
)


def test_basic_functionality():
    """测试基本功能"""
    print("测试提示词优化系统基本功能")
    print("=" * 60)

    test_text = "这是一个测试文本，用于验证提示词优化系统的功能。"

    # 1. 测试纠错提示词
    print("\n1. 测试纠错提示词:")

    # 原始版本
    original_prompt = build_error_check_prompt_original(test_text)
    print(f"   原始版本长度: {len(original_prompt)} 字符")

    # 优化版本 (compact)
    compact_prompt = build_error_check_prompt(test_text, template_version="compact")
    print(f"   Compact版本长度: {len(compact_prompt)} 字符")
    print(
        f"   长度减少: {((len(original_prompt) - len(compact_prompt)) / len(original_prompt) * 100):.1f}%"
    )

    # 优化版本 (ai_optimized)
    ai_prompt = build_error_check_prompt(test_text, template_version="ai_optimized")
    print(f"   AI优化版本长度: {len(ai_prompt)} 字符")
    print(
        f"   长度减少: {((len(original_prompt) - len(ai_prompt)) / len(original_prompt) * 100):.1f}%"
    )

    # 2. 测试翻译提示词和缓存
    print("\n2. 测试翻译提示词和缓存:")

    # 清除缓存
    clear_prompt_cache()

    # 原始版本
    original_trans_prompt = build_academic_translate_prompt_original(test_text)
    print(f"   原始版本长度: {len(original_trans_prompt)} 字符")

    # 优化版本 - 第一次（构建并缓存）
    start_time = time.time()
    opt_prompt_1 = build_academic_translate_prompt(test_text, use_cache=True)
    time_1 = time.time() - start_time
    print(f"   优化版本第一次构建时间: {time_1 * 1000:.2f}ms")
    print(f"   优化版本长度: {len(opt_prompt_1)} 字符")
    print(
        f"   长度减少: {((len(original_trans_prompt) - len(opt_prompt_1)) / len(original_trans_prompt) * 100):.1f}%"
    )

    # 优化版本 - 第二次（从缓存读取）
    start_time = time.time()
    build_academic_translate_prompt(test_text, use_cache=True)
    time_2 = time.time() - start_time
    print(f"   优化版本第二次构建时间: {time_2 * 1000:.2f}ms")
    print(
        f"   缓存加速: {((time_1 - time_2) / time_1 * 100):.1f}%"
        if time_1 > 0
        else "   缓存加速: N/A"
    )

    # 3. 测试快捷批注
    print("\n3. 测试快捷批注:")

    original_ann = SHORTCUT_ANNOTATIONS_ORIGINAL
    compact_ann = get_shortcut_annotations("compact")
    ai_ann = get_shortcut_annotations("ai_optimized")

    print(f"   原始批注数量: {len(original_ann)}")
    print(f"   Compact批注数量: {len(compact_ann)}")
    print(f"   AI优化批注数量: {len(ai_ann)}")

    # 检查关键批注
    key = "去AI词汇"
    if key in original_ann:
        orig_len = len(original_ann[key])
        comp_len = len(compact_ann.get(key, ""))
        ai_len = len(ai_ann.get(key, ""))

        print(f"\n   批注 '{key}' 长度对比:")
        print(f"     原始: {orig_len} 字符")
        print(
            f"     Compact: {comp_len} 字符 (减少 {((orig_len - comp_len) / orig_len * 100):.1f}%)"
            if comp_len > 0
            else "     Compact: N/A"
        )
        print(
            f"     AI优化: {ai_len} 字符 (减少 {((orig_len - ai_len) / orig_len * 100):.1f}%)"
            if ai_len > 0
            else "     AI优化: N/A"
        )

    # 4. 测试性能监控
    print("\n4. 测试性能监控:")

    stats = get_prompt_stats()
    cache_stats = get_cache_stats()

    print("   性能统计:")
    print(f"     总请求数: {stats.get('summary', {}).get('total_requests', 0)}")
    print(f"     缓存命中率: {stats.get('summary', {}).get('cache_hit_rate', '0%')}")

    print("   缓存统计:")
    print(f"     缓存大小: {cache_stats.get('cache_size', 0)}/{cache_stats.get('max_entries', 0)}")
    print(f"     命中率: {cache_stats.get('hit_rate', '0%')}")

    # 5. 测试不同模板版本
    print("\n5. 测试不同模板版本:")

    for version in ["original", "compact", "ai_optimized"]:
        prompt = build_academic_translate_prompt(
            test_text, style="US", version="professional", template_version=version, use_cache=False
        )
        print(f"   {version:12s}: {len(prompt):5d} 字符")

    print("\n" + "=" * 60)
    print("测试完成!")

    # 总结
    print("\n优化效果总结:")
    print(
        f"1. 纠错提示词长度减少: {((len(original_prompt) - len(ai_prompt)) / len(original_prompt) * 100):.1f}%"
    )
    print(
        f"2. 翻译提示词长度减少: {((len(original_trans_prompt) - len(opt_prompt_1)) / len(original_trans_prompt) * 100):.1f}%"
    )
    print(
        f"3. 缓存命中后构建时间减少: {((time_1 - time_2) / time_1 * 100):.1f}%"
        if time_1 > 0
        else "3. 缓存命中后构建时间减少: N/A"
    )

    return True


if __name__ == "__main__":
    try:
        success = test_basic_functionality()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
