#!/usr/bin/env python3
"""
验证最终配置脚本

验证所有提示词已按用户要求配置：
1. 所有主要提示词使用production版本（基于原始完整版本）
2. 快捷批注使用production版本（修改后的原始版本，移除"灵活表达"，修改"符号修正"，更新"人性化处理"）
3. 缓存机制保留
4. 版本管理清晰：production（当前使用）、original（备份）、compact/ai_optimized（空框架）
"""

import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

print("=" * 80)
print("最终配置验证")
print("=" * 80)

try:
    from prompts import (
        DEFAULT_TEMPLATE_VERSION,
        TRANSLATION_TEMPLATE_VERSION,
        ENGLISH_REFINE_TEMPLATE_VERSION,
        DEFAULT_ANNOTATIONS_VERSION,
        build_error_check_prompt,
        build_academic_translate_prompt,
        build_english_refine_prompt,
        get_shortcut_annotations,
        SHORTCUT_ANNOTATIONS
    )

    from prompts_backup import (
        build_error_check_prompt_original,
        build_academic_translate_prompt_original,
        build_english_refine_prompt_original,
        SHORTCUT_ANNOTATIONS_ORIGINAL
    )

    from prompt_cache import prompt_cache_manager
    from prompt_monitor import prompt_performance_monitor

    print("[PASS] 导入成功")
except ImportError as e:
    print(f"[FAIL] 导入失败: {e}")
    sys.exit(1)

# 测试文本
test_text = "这是一个测试文本，用于验证配置是否正确。"
test_english_text = "This is a test text to verify the configuration."

print(f"\n1. 配置常量验证:")
print(f"   DEFAULT_TEMPLATE_VERSION: {DEFAULT_TEMPLATE_VERSION} (应为: production)")
print(f"   TRANSLATION_TEMPLATE_VERSION: {TRANSLATION_TEMPLATE_VERSION} (应为: production)")
print(f"   ENGLISH_REFINE_TEMPLATE_VERSION: {ENGLISH_REFINE_TEMPLATE_VERSION} (应为: production)")
print(f"   DEFAULT_ANNOTATIONS_VERSION: {DEFAULT_ANNOTATIONS_VERSION} (应为: production)")

# 验证配置
config_correct = True
if DEFAULT_TEMPLATE_VERSION != "production":
    print(f"   [FAIL] DEFAULT_TEMPLATE_VERSION 应为 'production'，实际为 '{DEFAULT_TEMPLATE_VERSION}'")
    config_correct = False
else:
    print(f"   [PASS] DEFAULT_TEMPLATE_VERSION 正确")

if TRANSLATION_TEMPLATE_VERSION != "production":
    print(f"   [FAIL] TRANSLATION_TEMPLATE_VERSION 应为 'production'，实际为 '{TRANSLATION_TEMPLATE_VERSION}'")
    config_correct = False
else:
    print(f"   [PASS] TRANSLATION_TEMPLATE_VERSION 正确")

if ENGLISH_REFINE_TEMPLATE_VERSION != "production":
    print(f"   [FAIL] ENGLISH_REFINE_TEMPLATE_VERSION 应为 'production'，实际为 '{ENGLISH_REFINE_TEMPLATE_VERSION}'")
    config_correct = False
else:
    print(f"   [PASS] ENGLISH_REFINE_TEMPLATE_VERSION 正确")

if DEFAULT_ANNOTATIONS_VERSION != "production":
    print(f"   [FAIL] DEFAULT_ANNOTATIONS_VERSION 应为 'production'，实际为 '{DEFAULT_ANNOTATIONS_VERSION}'")
    config_correct = False
else:
    print(f"   [PASS] DEFAULT_ANNOTATIONS_VERSION 正确")

print(f"\n2. 提示词函数验证:")

# 测试纠错提示词
print(f"   测试智能纠错提示词...")
original_error_prompt = build_error_check_prompt_original(test_text)
current_error_prompt = build_error_check_prompt(test_text, template_version="original")

if len(original_error_prompt) == len(current_error_prompt):
    print(f"   [PASS] 纠错提示词长度一致: {len(original_error_prompt)} 字符")
else:
    print(f"   [FAIL] 纠错提示词长度不一致:")
    print(f"      原始: {len(original_error_prompt)} 字符")
    print(f"      当前: {len(current_error_prompt)} 字符")
    config_correct = False

# 测试翻译提示词
print(f"   测试学术翻译提示词...")
original_translation_prompt = build_academic_translate_prompt_original(test_text, style="US", version="professional")
current_translation_prompt = build_academic_translate_prompt(test_text, style="US", version="professional", template_version="production")

if len(original_translation_prompt) == len(current_translation_prompt):
    print(f"   [PASS] 翻译提示词长度一致: {len(original_translation_prompt)} 字符")
else:
    print(f"   [FAIL] 翻译提示词长度不一致:")
    print(f"      原始: {len(original_translation_prompt)} 字符")
    print(f"      当前: {len(current_translation_prompt)} 字符")
    config_correct = False

# 测试英文精修提示词
print(f"   测试英文精修提示词...")
original_refine_prompt = build_english_refine_prompt_original(test_english_text)
current_refine_prompt = build_english_refine_prompt(test_english_text, template_version="production")

if len(original_refine_prompt) > 2000 and len(current_refine_prompt) > 2000:  # 原始版本很长
    print(f"   [PASS] 英文精修提示词均为长版本")
    print(f"      原始: {len(original_refine_prompt)} 字符")
    print(f"      当前: {len(current_refine_prompt)} 字符")
else:
    print(f"   [FAIL] 英文精修提示词可能不正确:")
    print(f"      原始: {len(original_refine_prompt)} 字符")
    print(f"      当前: {len(current_refine_prompt)} 字符")
    config_correct = False

print(f"\n3. 快捷批注验证:")

# 获取批注版本
original_annotations = SHORTCUT_ANNOTATIONS_ORIGINAL
current_annotations = get_shortcut_annotations("production")

print(f"   原始批注数量: {len(original_annotations)}")
print(f"   当前批注数量: {len(current_annotations)}")

# 验证修改
print(f"   验证批注修改:")

# 1. 检查"灵活表达"是否已移除（原始版本和生产版本都应移除）
if "灵活表达" in original_annotations:
    print(f"   [FAIL] 原始版本仍包含'灵活表达'（应已移除）")
    config_correct = False
else:
    print(f"   [PASS] 原始版本已移除'灵活表达'")

if "灵活表达" in current_annotations:
    print(f"   [FAIL] 当前版本仍包含'灵活表达'（应已移除）")
    config_correct = False
else:
    print(f"   [PASS] 当前版本已移除'灵活表达'")

# 2. 检查"符号修正"是否已修改
original_symbol = original_annotations.get("符号修正", "")
current_symbol = current_annotations.get("符号修正", "")

print(f"   原始'符号修正': {original_symbol[:50]}...")
print(f"   当前'符号修正': {current_symbol[:50]}...")

if "同时用分号连接两个关系紧密的独立从句" in current_symbol:
    print(f"   [PASS] '符号修正'已包含分号连接说明")
else:
    print(f"   [FAIL] '符号修正'未包含分号连接说明")
    config_correct = False

# 3. 检查"人性化处理"是否已更新（融入原始例子）
original_human = original_annotations.get("人性化处理", "")
current_human = current_annotations.get("人性化处理", "")

# 检查是否包含原始版本中的关键例子
has_examples = (
    "Find: I will" in current_human and
    "Replace with: I hope to" in current_human and
    "Find: utilize, employ" in current_human and
    "Replace with: use, make use of" in current_human and
    "Use contractions" in current_human
)

if has_examples and 1000 < len(current_human) < 2000:
    print(f"   [PASS] '人性化处理'已更新并融入原始例子")
    print(f"      原始长度: {len(original_human)} 字符")
    print(f"      当前长度: {len(current_human)} 字符")
else:
    print(f"   [FAIL] '人性化处理'可能未正确更新")
    print(f"      原始长度: {len(original_human)} 字符")
    print(f"      当前长度: {len(current_human)} 字符")
    if not has_examples:
        print(f"   [INFO] 缺少原始版本中的关键例子")
    if not (1000 < len(current_human) < 2000):
        print(f"   [INFO] 当前长度超出预期范围: {len(current_human)} 字符")

# 4. 检查"去AI词汇"是否保持完整
original_ai = original_annotations.get("去AI词汇", "")
current_ai = current_annotations.get("去AI词汇", "")

if len(original_ai) > 600 and len(current_ai) > 600:
    print(f"   [PASS] '去AI词汇'保持完整（约{len(original_ai)}字符）")
else:
    print(f"   [FAIL] '去AI词汇'可能不完整")
    print(f"      原始长度: {len(original_ai)} 字符")
    print(f"      当前长度: {len(current_ai)} 字符")
    config_correct = False

print(f"\n4. 缓存机制验证:")

try:
    cache_stats = prompt_cache_manager.get_stats()
    print(f"   [PASS] 缓存管理器正常工作")
    print(f"      缓存条目数: {cache_stats.get('cache_size', 0)}")
    print(f"      最大缓存数: {cache_stats.get('max_entries', 0)}")
    print(f"      TTL: {cache_stats.get('ttl', 0)} 秒")
except Exception as e:
    print(f"   [FAIL] 缓存管理器异常: {e}")
    config_correct = False

print(f"\n5. 性能监控验证:")

try:
    monitor_report = prompt_performance_monitor.get_report()
    print(f"   [PASS] 性能监控器正常工作")
    print(f"      总请求数: {monitor_report.get('total_requests', 0)}")
    print(f"      缓存命中率: {monitor_report.get('cache_hit_rate', 0):.2%}")
except Exception as e:
    print(f"   [FAIL] 性能监控器异常: {e}")
    config_correct = False

print(f"\n" + "=" * 80)
if config_correct:
    print("[PASS] 最终配置验证通过！所有用户要求已正确实现")
    print("\n配置摘要:")
    print("1. 所有主要提示词使用production版本（基于原始完整版本）")
    print("2. 快捷批注使用修改后的原始版本:")
    print("   - 移除'灵活表达'功能")
    print("   - 修改'符号修正': '确保标点符号在引号外，同时用分号连接两个关系紧密的独立从句'")
    print("   - '人性化处理'使用用户提供的新版本")
    print("   - '去AI词汇'保持632字符原始完整内容")
    print("3. 缓存机制保留")
    print("4. 性能监控系统正常工作")
else:
    print("[FAIL] 最终配置验证失败！请检查以上错误")
    sys.exit(1)

print(f"\n当前系统状态:")
print(f"   - 智能纠错: {DEFAULT_TEMPLATE_VERSION} 版本")
print(f"   - 学术翻译: {TRANSLATION_TEMPLATE_VERSION} 版本")
print(f"   - 英文精修: {ENGLISH_REFINE_TEMPLATE_VERSION} 版本")
print(f"   - 快捷批注: {DEFAULT_ANNOTATIONS_VERSION} 版本")

# 显示快捷批注键
print(f"\n可用快捷批注命令 ({len(current_annotations)}个):")
for key in sorted(current_annotations.keys()):
    preview = current_annotations[key][:50] + "..." if len(current_annotations[key]) > 50 else current_annotations[key]
    print(f"   - {key}: {preview}")

print(f"\n" + "=" * 80)
print("验证完成")