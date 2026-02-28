#!/usr/bin/env python3
"""
测试文献调研提示词函数
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from prompts import (
    build_literature_research_prompt,
    build_literature_research_prompt_original,
    LITERATURE_RESEARCH_TEMPLATE_VERSION
)

def test_prompt_functions():
    """测试文献调研提示词函数"""
    print("=== 测试文献调研提示词函数 ===\n")

    # 测试数据
    test_prompt = "请调研人工智能在教育中的应用"

    print(f"测试输入: {test_prompt}")
    print(f"LITERATURE_RESEARCH_TEMPLATE_VERSION: {LITERATURE_RESEARCH_TEMPLATE_VERSION}")
    print("-" * 60)

    # 测试原始函数 - 普通模式
    print("1. 测试原始函数 (普通模式，不生成文献综述):")
    prompt1 = build_literature_research_prompt_original(
        prompt=test_prompt,
        generate_literature_review=False
    )
    print(f"   长度: {len(prompt1)} 字符")
    print(f"   前100字符: {prompt1[:100]}...")
    print()

    # 测试原始函数 - 文献综述模式
    print("2. 测试原始函数 (文献综述模式):")
    prompt2 = build_literature_research_prompt_original(
        prompt=test_prompt,
        generate_literature_review=True
    )
    print(f"   长度: {len(prompt2)} 字符")
    print(f"   前100字符: {prompt2[:100]}...")
    print()

    # 测试生产函数 - 普通模式
    print("3. 测试生产函数 (普通模式，不使用缓存):")
    prompt3 = build_literature_research_prompt(
        prompt=test_prompt,
        generate_literature_review=False,
        use_cache=False
    )
    print(f"   长度: {len(prompt3)} 字符")
    print(f"   前100字符: {prompt3[:100]}...")
    print()

    # 测试生产函数 - 文献综述模式
    print("4. 测试生产函数 (文献综述模式，不使用缓存):")
    prompt4 = build_literature_research_prompt(
        prompt=test_prompt,
        generate_literature_review=True,
        use_cache=False
    )
    print(f"   长度: {len(prompt4)} 字符")
    print(f"   前100字符: {prompt4[:100]}...")
    print()

    # 验证内容一致性
    print("5. 验证内容一致性:")

    # 原始函数普通模式 vs 生产函数普通模式
    if prompt1 == prompt3:
        print("   [成功] 原始函数普通模式与生产函数普通模式内容一致")
    else:
        print("   [失败] 原始函数普通模式与生产函数普通模式内容不一致")

    # 原始函数文献综述模式 vs 生产函数文献综述模式
    if prompt2 == prompt4:
        print("   [成功] 原始函数文献综述模式与生产函数文献综述模式内容一致")
    else:
        print("   [失败] 原始函数文献综述模式与生产函数文献综述模式内容不一致")

    # 检查是否包含用户输入
    print("\n6. 检查是否包含用户输入:")
    if test_prompt in prompt1:
        print(f"   [成功] 普通模式提示词包含用户输入")
    else:
        print(f"   [失败] 普通模式提示词不包含用户输入")

    if test_prompt in prompt2:
        print(f"   [成功] 文献综述模式提示词包含用户输入")
    else:
        print(f"   [失败] 文献综述模式提示词不包含用户输入")

    # 检查模式差异
    print("\n7. 检查模式差异:")
    if "首先撰写一段综合性的文献综述" in prompt2 and "首先撰写一段综合性的文献综述" not in prompt1:
        print("   [成功] 文献综述模式包含'首先撰写一段综合性的文献综述'，普通模式不包含")
    else:
        print("   [失败] 模式差异检查失败")

    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_prompt_functions()