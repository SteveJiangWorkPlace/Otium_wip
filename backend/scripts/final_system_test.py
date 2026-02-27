#!/usr/bin/env python3
"""
模块名称：final_system_test.py
功能描述：最终系统配置验证测试脚本
创建时间：2026-02-27
作者：项目团队
版本：1.0.0

此脚本执行最终系统配置验证，确保提示词系统按照最新要求正确配置。
验证生产环境配置的正确性和完整性，包括提示词版本、缓存机制和性能监控。

测试目标：
1. 验证所有主要提示词使用生产版本（基于原始完整版本）
2. 验证快捷批注使用修改后的生产版本
3. 验证缓存机制正常工作
4. 验证性能监控系统正常运行
5. 验证API服务集成正确

具体验证点：
- 移除"灵活表达"指令（快捷批注）
- 修改"符号修正"指令（快捷批注）
- 更新"人性化处理"指令（快捷批注）
- 保留所有原始函数和缓存逻辑
- 确保监控指标可访问

测试方法：
1. 导入所有关键模块和函数
2. 检查版本常量和配置
3. 执行示例提示词构建
4. 验证缓存命中率
5. 检查监控数据可用性

输出结果：
- 详细测试步骤和结果
- 配置验证状态
- 错误信息和修复建议
- 最终测试结论

使用场景：
- 部署前的最终验证
- 配置变更后的回归测试
- 系统维护后的功能验证
- 开发环境配置检查

注意事项：
- 需要后端依赖模块可导入
- 不执行实际API调用，仅验证配置
- 使用测试文本避免外部依赖
- 输出详细的验证报告
"""

import sys
from pathlib import Path

# 添加当前目录和父目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))  # backend目录
sys.path.insert(0, str(current_dir))  # scripts目录

print("=" * 80)
print("最终系统测试")
print("=" * 80)

# 测试文本
test_text = "这是一个测试文本，用于验证系统是否正确配置。"
test_english_text = "This is a test text to verify the system configuration."

try:
    from prompts import (
        DEFAULT_ANNOTATIONS_VERSION,
        DEFAULT_TEMPLATE_VERSION,
        ENGLISH_REFINE_TEMPLATE_VERSION,
        SHORTCUT_ANNOTATIONS_ORIGINAL,
        TRANSLATION_TEMPLATE_VERSION,
        build_academic_translate_prompt,
        build_academic_translate_prompt_original,
        build_english_refine_prompt,
        build_english_refine_prompt_original,
        build_error_check_prompt,
        build_error_check_prompt_original,
        get_cache_stats,
        get_prompt_stats,
        get_shortcut_annotations,
    )

    print("[PASS] 模块导入成功")
except ImportError as e:
    print(f"[FAIL] 模块导入失败: {e}")
    sys.exit(1)

# 测试1：配置常量验证
print("\n1. 配置常量验证:")
print(f"   智能纠错模板版本: {DEFAULT_TEMPLATE_VERSION}")
print(f"   学术翻译模板版本: {TRANSLATION_TEMPLATE_VERSION}")
print(f"   英文精修模板版本: {ENGLISH_REFINE_TEMPLATE_VERSION}")
print(f"   快捷批注默认版本: {DEFAULT_ANNOTATIONS_VERSION}")

config_correct = True
if DEFAULT_TEMPLATE_VERSION != "production":
    print(
        f"   [FAIL] DEFAULT_TEMPLATE_VERSION 应为 'production'，实际为 '{DEFAULT_TEMPLATE_VERSION}'"
    )
    config_correct = False
else:
    print("   [PASS] 智能纠错使用生产版本")

if TRANSLATION_TEMPLATE_VERSION != "production":
    print(
        f"   [FAIL] TRANSLATION_TEMPLATE_VERSION 应为 'production'，实际为 '{TRANSLATION_TEMPLATE_VERSION}'"
    )
    config_correct = False
else:
    print("   [PASS] 学术翻译使用生产版本")

if ENGLISH_REFINE_TEMPLATE_VERSION != "production":
    print(
        f"   [FAIL] ENGLISH_REFINE_TEMPLATE_VERSION 应为 'production'，实际为 '{ENGLISH_REFINE_TEMPLATE_VERSION}'"
    )
    config_correct = False
else:
    print("   [PASS] 英文精修使用生产版本")

if DEFAULT_ANNOTATIONS_VERSION != "production":
    print(
        f"   [FAIL] DEFAULT_ANNOTATIONS_VERSION 应为 'production'，实际为 '{DEFAULT_ANNOTATIONS_VERSION}'"
    )
    config_correct = False
else:
    print("   [PASS] 快捷批注使用生产版本（修改后的原始版本）")

# 测试2：主要提示词函数验证
print("\n2. 主要提示词函数验证:")
print("   测试智能纠错提示词...")
original_error = build_error_check_prompt_original(test_text)
current_error = build_error_check_prompt(test_text, template_version="production")

if len(original_error) == len(current_error):
    print(f"   [PASS] 智能纠错提示词长度一致: {len(original_error)} 字符")
else:
    print("   [FAIL] 智能纠错提示词长度不一致")
    print(f"      原始: {len(original_error)} 字符")
    print(f"      当前: {len(current_error)} 字符")
    config_correct = False

print("   测试学术翻译提示词...")
original_translation = build_academic_translate_prompt_original(
    test_text, style="US", version="professional"
)
current_translation = build_academic_translate_prompt(
    test_text, style="US", version="professional", template_version="production"
)

if len(original_translation) == len(current_translation):
    print(f"   [PASS] 学术翻译提示词长度一致: {len(original_translation)} 字符")
else:
    print("   [FAIL] 学术翻译提示词长度不一致")
    print(f"      原始: {len(original_translation)} 字符")
    print(f"      当前: {len(current_translation)} 字符")
    config_correct = False

print("   测试英文精修提示词...")
original_refine = build_english_refine_prompt_original(
    text_with_instructions=test_english_text, hidden_instructions="", annotations=None
)
current_refine = build_english_refine_prompt(
    text_with_instructions=test_english_text,
    hidden_instructions="",
    annotations=None,
    template_version="production",
)

if len(original_refine) == len(current_refine):
    print(f"   [PASS] 英文精修提示词长度一致: {len(original_refine)} 字符")
else:
    print("   [FAIL] 英文精修提示词长度不一致")
    print(f"      原始: {len(original_refine)} 字符")
    print(f"      当前: {len(current_refine)} 字符")
    config_correct = False

# 测试3：快捷批注验证
print("\n3. 快捷批注验证:")
original_annotations = SHORTCUT_ANNOTATIONS_ORIGINAL
current_annotations = get_shortcut_annotations("production")

print(f"   原始批注数量: {len(original_annotations)}")
print(f"   当前批注数量: {len(current_annotations)}")

# 验证"灵活表达"已移除
if "灵活表达" in original_annotations:
    print("   [INFO] 原始版本包含'灵活表达'，检查是否已移除")
    if "灵活表达" in current_annotations:
        print("   [FAIL] 当前版本仍包含'灵活表达'（应已移除）")
        config_correct = False
    else:
        print("   [PASS] 当前版本已移除'灵活表达'")
else:
    print("   [INFO] 原始版本不包含'灵活表达'（已满足移除要求）")
    if "灵活表达" in current_annotations:
        print("   [FAIL] 当前版本不应添加'灵活表达'")
        config_correct = False
    else:
        print("   [PASS] 当前版本无'灵活表达'（符合要求）")

# 验证"符号修正"已修改
original_symbol = original_annotations.get("符号修正", "")
current_symbol = current_annotations.get("符号修正", "")

print(f"   原始'符号修正'长度: {len(original_symbol)} 字符")
print(f"   当前'符号修正'长度: {len(current_symbol)} 字符")

if "分号连接两个关系紧密的独立从句" in current_symbol:
    print("   [PASS] '符号修正'已包含分号连接说明")
else:
    print("   [FAIL] '符号修正'未包含分号连接说明")
    config_correct = False

# 验证"人性化处理"已更新
original_human = original_annotations.get("人性化处理", "")
current_human = current_annotations.get("人性化处理", "")

print(f"   原始'人性化处理'长度: {len(original_human)} 字符")
print(f"   当前'人性化处理'长度: {len(current_human)} 字符")

if "Revise the text to sound more like a thoughtful but less confident human" in current_human:
    print("   [PASS] '人性化处理'已更新为用户提供的新版本")
else:
    print("   [FAIL] '人性化处理'未正确更新")
    config_correct = False

# 验证"去AI词汇"保持完整
original_ai = original_annotations.get("去AI词汇", "")
current_ai = current_annotations.get("去AI词汇", "")

print(f"   原始'去AI词汇'长度: {len(original_ai)} 字符")
print(f"   当前'去AI词汇'长度: {len(current_ai)} 字符")

if len(original_ai) > 600 and len(current_ai) > 600:
    print(f"   [PASS] '去AI词汇'保持完整（约{len(original_ai)}字符）")
else:
    print("   [FAIL] '去AI词汇'可能不完整")
    print(f"      原始长度: {len(original_ai)} 字符")
    print(f"      当前长度: {len(current_ai)} 字符")
    config_correct = False

# 测试4：缓存和性能监控验证
print("\n4. 缓存和性能监控验证:")

try:
    cache_stats = get_cache_stats()
    print("   [PASS] 缓存系统正常工作")
    print(f"      缓存条目数: {cache_stats.get('cache_size', 0)}")
    print(f"      最大缓存数: {cache_stats.get('max_entries', 0)}")
    print(f"      TTL: {cache_stats.get('ttl', 0)} 秒")
except Exception as e:
    print(f"   [FAIL] 缓存系统异常: {e}")
    config_correct = False

try:
    performance_stats = get_prompt_stats()
    print("   [PASS] 性能监控系统正常工作")
    print(f"      总请求数: {performance_stats.get('total_requests', 0)}")
    print(f"      缓存命中率: {performance_stats.get('cache_hit_rate', 0):.2%}")
    print(f"      平均构建时间: {performance_stats.get('avg_build_time_ms', 0):.2f} ms")
except Exception as e:
    print(f"   [FAIL] 性能监控系统异常: {e}")
    config_correct = False

print("\n" + "=" * 80)
if config_correct:
    print("[SUCCESS] 最终系统测试通过！所有用户要求已正确实现")
    print("\n系统配置摘要:")
    print("1. [PASS] 所有主要提示词使用生产版本")
    print("2. [PASS] 快捷批注使用生产版本（修改后的原始版本）:")
    print("   - 移除'灵活表达'功能 [PASS]")
    print(
        "   - 修改'符号修正': '确保标点符号在引号外，同时用分号连接两个关系紧密的独立从句' [PASS]"
    )
    print("   - '人性化处理'使用用户提供的新版本 [PASS]")
    print("   - '去AI词汇'保持原始完整内容 [PASS]")
    print("3. [PASS] 缓存机制保留")
    print("4. [PASS] 性能监控系统正常工作")

    print("\n当前系统状态:")
    print(f"   智能纠错: {DEFAULT_TEMPLATE_VERSION} 版本")
    print(f"   学术翻译: {TRANSLATION_TEMPLATE_VERSION} 版本")
    print(f"   英文精修: {ENGLISH_REFINE_TEMPLATE_VERSION} 版本")
    print(f"   快捷批注: {DEFAULT_ANNOTATIONS_VERSION} 版本")

    print(f"\n可用快捷批注命令 ({len(current_annotations)}个):")
    for key in sorted(current_annotations.keys()):
        preview = (
            current_annotations[key][:80] + "..."
            if len(current_annotations[key]) > 80
            else current_annotations[key]
        )
        print(f"   - {key}: {preview}")

    print("\n系统性能指标:")
    print(f"   缓存命中率: {performance_stats.get('cache_hit_rate', 0):.2%}")
    print(f"   平均构建时间: {performance_stats.get('avg_build_time_ms', 0):.2f} ms")
    print(f"   总请求数: {performance_stats.get('total_requests', 0)}")

else:
    print("[FAILURE] 最终系统测试失败！请检查以上错误")
    sys.exit(1)

print("\n" + "=" * 80)
print("测试完成")
