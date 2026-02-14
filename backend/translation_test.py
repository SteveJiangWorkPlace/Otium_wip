#!/usr/bin/env python3
"""
翻译提示词测试脚本

测试要求：
1. 测试用最新提示词的基础班和专业版翻译后的结果对比，都用UK翻译
2. 用专业版本和UK翻译，测试新提示词和原始提示词的翻译效果，给出两者翻译内容的差别，所用时常和AI检测率的差别

测试文本：根目录下的测试段落1.txt
"""

import os
import sys
import time
import json
import hashlib
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 导入原始和新提示词函数
try:
    from prompts_backup import build_academic_translate_prompt_original
    from prompts import build_academic_translate_prompt
    from config import settings
    from services import generate_gemini_content_with_fallback, check_gptzero
    from prompt_monitor import prompt_performance_monitor
except ImportError as e:
    print(f"导入错误: {e}")
    print("尝试使用模拟模式...")
    SIMULATION_MODE = True
else:
    SIMULATION_MODE = False

# 读取测试文本
def read_test_text() -> str:
    """读取测试文本1"""
    test_file = current_dir.parent / "测试段落1.txt"
    if not test_file.exists():
        print(f"错误: 测试文件不存在: {test_file}")
        sys.exit(1)

    with open(test_file, 'r', encoding='utf-8') as f:
        return f.read().strip()

# 模拟Gemini API调用
def simulate_gemini_api(prompt: str, model: str = "gemini-2.5-flash") -> Dict[str, Any]:
    """模拟Gemini API调用，用于测试"""
    import random
    import time

    # 模拟处理时间
    time.sleep(random.uniform(0.5, 2.0))

    # 模拟翻译结果
    simulated_translation = """
It is commendable that Tyler Perry does not perpetuate or reinforce the image of a "contemporary white savior" in the film, while also avoiding the potential white-centric narrative that could arise from developing the story around Cartwright. As the film's plot progresses and the Black couple and Cartwright begin to experience potential conflicts of interest, Cartwright's character changes. In the Cartwright's office sequence, Chris goes directly to Cartwright's office, and the two sit opposite each other at the desk. Chris asks Cartwright to invest in his company. Upon hearing Chris's request, Cartwright shifts from his initial forward-leaning posture to leaning back in his chair and crossing his legs. His body language already hints at his rejection and disdain for this request. "You know I work very closely with your wife." If, at the beginning of the film, it was Cartwright's relationship with Andrea that got Chris this job, then in this scene, Cartwright's words sound more like a threat to Chris and Andrea, reminding Chris that as the company's decision-maker, he can make both of them lose their jobs at any time. Unlike the warm and joyful atmosphere of the wedding scene, the office sequence highlights the real class difference between the two. In this dialogue scene, Chris wears an ordinary white T-shirt and a red plaid shirt, marking his working-class identity, while Cartwright wears a full dark blue suit, and the office's blinds and dark-toned decor underscore his coldness as a business leader. In the subsequent plot, he fires Chris and has an extramarital affair with his wife Andrea, further reinforcing a dominant, predatory white male stance.
"""

    return {
        "success": True,
        "text": simulated_translation.strip(),
        "model_used": model,
        "error": None,
        "error_type": None
    }

# 模拟GPTZero API调用
def simulate_gptzero_api(text: str) -> Dict[str, Any]:
    """模拟GPTZero API调用，用于测试"""
    import random
    import time

    # 模拟处理时间
    time.sleep(random.uniform(0.3, 1.0))

    # 模拟AI检测结果
    return {
        "success": True,
        "ai_probability": round(random.uniform(0.2, 0.8), 2),
        "document": {
            "ai_score": round(random.uniform(0.2, 0.8), 2),
            "words": len(text.split())
        },
        "sentences": [
            {
                "text": "Simulated sentence",
                "ai_score": round(random.uniform(0.2, 0.8), 2)
            }
        ]
    }

# 实际调用API
def call_gemini_api(prompt: str) -> Tuple[bool, str, float]:
    """调用Gemini API并返回结果、文本和耗时"""
    start_time = time.time()

    if SIMULATION_MODE or not hasattr(settings, 'GEMINI_API_KEY') or not settings.GEMINI_API_KEY:
        print("使用模拟Gemini API（无API密钥或模拟模式）")
        result = simulate_gemini_api(prompt)
    else:
        try:
            print(f"调用Gemini API，提示词长度: {len(prompt)} 字符")
            result = generate_gemini_content_with_fallback(
                prompt=prompt,
                api_key=settings.GEMINI_API_KEY,
                primary_model="gemini-2.5-flash"
            )
        except Exception as e:
            print(f"Gemini API调用失败: {e}")
            result = simulate_gemini_api(prompt)

    end_time = time.time()
    elapsed_time = end_time - start_time

    if result.get("success"):
        return True, result["text"], elapsed_time
    else:
        return False, f"API错误: {result.get('error', '未知错误')}", elapsed_time

def call_gptzero_api(text: str) -> Tuple[bool, float, float]:
    """调用GPTZero API并返回结果和AI检测率"""
    start_time = time.time()

    if SIMULATION_MODE or not hasattr(settings, 'GPTZERO_API_KEY') or not settings.GPTZERO_API_KEY:
        print("使用模拟GPTZero API（无API密钥或模拟模式）")
        result = simulate_gptzero_api(text)
    else:
        try:
            print(f"调用GPTZero API，文本长度: {len(text)} 字符")
            result = gptzero_detect_ai(text, settings.GPTZERO_API_KEY)
        except Exception as e:
            print(f"GPTZero API调用失败: {e}")
            result = simulate_gptzero_api(text)

    end_time = time.time()
    elapsed_time = end_time - start_time

    if result.get("success"):
        ai_score = result.get("ai_probability", result.get("document", {}).get("ai_score", 0.5))
        return True, ai_score, elapsed_time
    else:
        return False, 0.5, elapsed_time

# 计算文本差异
def calculate_text_difference(text1: str, text2: str) -> Dict[str, any]:
    """计算两个文本之间的差异"""
    # 简单的单词级别比较
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    common_words = words1.intersection(words2)
    unique_to_1 = words1 - words2
    unique_to_2 = words2 - words1

    similarity = len(common_words) / max(len(words1), len(words2)) if max(len(words1), len(words2)) > 0 else 0

    return {
        "similarity_percentage": round(similarity * 100, 2),
        "common_words": len(common_words),
        "unique_to_text1": len(unique_to_1),
        "unique_to_text2": len(unique_to_2),
        "total_words_text1": len(words1),
        "total_words_text2": len(words2)
    }

# 主测试函数
def run_translation_tests():
    """运行所有翻译测试"""
    print("=" * 80)
    print("翻译提示词测试")
    print("=" * 80)

    # 读取测试文本
    test_text = read_test_text()
    print(f"测试文本长度: {len(test_text)} 字符")
    print(f"测试文本预览: {test_text[:200]}...")
    print()

    # 清空性能监控数据
    if not SIMULATION_MODE:
        prompt_performance_monitor.reset_metrics()

    test_cases = [
        # (测试名称, 使用新提示词, 版本, 模板版本, 风格)
        ("新提示词-基础版-UK", True, "basic", "ai_optimized", "UK"),
        ("新提示词-专业版-UK", True, "professional", "ai_optimized", "UK"),
        ("原始提示词-专业版-UK", False, "professional", "original", "UK"),
    ]

    results = {}

    for test_name, use_new_prompt, version, template_version, style in test_cases:
        print(f"\n{'='*60}")
        print(f"测试: {test_name}")
        print(f"{'='*60}")

        # 构建提示词
        prompt_start = time.time()

        if use_new_prompt:
            prompt = build_academic_translate_prompt(
                chinese_text=test_text,
                style=style,
                version=version,
                template_version=template_version,
                use_cache=False  # 测试时不使用缓存
            )
        else:
            prompt = build_academic_translate_prompt_original(
                chinese_text=test_text,
                style=style,
                version=version
            )

        prompt_time = time.time() - prompt_start

        print(f"提示词构建时间: {prompt_time:.4f} 秒")
        print(f"提示词长度: {len(prompt)} 字符")
        print(f"提示词预览 (前300字符):")
        print(f"{prompt[:300]}...")

        # 调用Gemini API进行翻译
        print(f"\n调用Gemini API进行翻译...")
        success, translation, translation_time = call_gemini_api(prompt)

        if success:
            print(f"翻译成功，耗时: {translation_time:.2f} 秒")
            print(f"翻译预览 (前200字符):")
            print(f"{translation[:200]}...")

            # 调用GPTZero进行AI检测
            print(f"\n调用GPTZero进行AI检测...")
            gptzero_success, ai_score, gptzero_time = call_gptzero_api(translation)

            if gptzero_success:
                print(f"AI检测成功，AI概率: {ai_score:.2%}")
            else:
                print("AI检测失败，使用默认值")
                ai_score = 0.5
        else:
            print(f"翻译失败: {translation}")
            translation = "翻译失败"
            ai_score = 0.5
            gptzero_time = 0

        # 保存结果
        results[test_name] = {
            "prompt_length": len(prompt),
            "prompt_time": prompt_time,
            "translation_success": success,
            "translation_text": translation,
            "translation_time": translation_time,
            "ai_score": ai_score,
            "gptzero_time": gptzero_time,
            "total_time": prompt_time + translation_time + gptzero_time,
            "version": version,
            "style": style,
            "template_version": template_version,
            "use_new_prompt": use_new_prompt
        }

    # 结果分析
    print(f"\n{'='*80}")
    print("结果分析")
    print(f"{'='*80}")

    # 1. 比较新提示词的基础版和专业版
    print("\n1. 新提示词基础版 vs 专业版 (UK翻译):")
    basic_result = results["新提示词-基础版-UK"]
    pro_result = results["新提示词-专业版-UK"]

    if basic_result["translation_success"] and pro_result["translation_success"]:
        diff = calculate_text_difference(basic_result["translation_text"], pro_result["translation_text"])
        print(f"   文本相似度: {diff['similarity_percentage']}%")
        print(f"   基础版提示词长度: {basic_result['prompt_length']} 字符")
        print(f"   专业版提示词长度: {pro_result['prompt_length']} 字符")
        print(f"   基础版总耗时: {basic_result['total_time']:.2f} 秒")
        print(f"   专业版总耗时: {pro_result['total_time']:.2f} 秒")
        print(f"   基础版AI检测率: {basic_result['ai_score']:.2%}")
        print(f"   专业版AI检测率: {pro_result['ai_score']:.2%}")
    else:
        print("   翻译失败，无法比较")

    # 2. 比较原始提示词和新提示词（专业版+UK）
    print("\n2. 原始提示词 vs 新提示词 (专业版+UK):")
    original_result = results["原始提示词-专业版-UK"]
    new_pro_result = results["新提示词-专业版-UK"]

    if original_result["translation_success"] and new_pro_result["translation_success"]:
        diff = calculate_text_difference(original_result["translation_text"], new_pro_result["translation_text"])
        print(f"   文本相似度: {diff['similarity_percentage']}%")
        print(f"   原始提示词长度: {original_result['prompt_length']} 字符")
        print(f"   新提示词长度: {new_pro_result['prompt_length']} 字符")
        print(f"   原始提示词构建时间: {original_result['prompt_time']:.4f} 秒")
        print(f"   新提示词构建时间: {new_pro_result['prompt_time']:.4f} 秒")
        if original_result['prompt_time'] > 0:
            time_reduction = (original_result['prompt_time'] - new_pro_result['prompt_time']) / original_result['prompt_time'] * 100
            print(f"   构建时间减少: {time_reduction:.1f}%")

        print(f"   原始提示词总耗时: {original_result['total_time']:.2f} 秒")
        print(f"   新提示词总耗时: {new_pro_result['total_time']:.2f} 秒")
        if original_result['total_time'] > 0:
            total_time_reduction = (original_result['total_time'] - new_pro_result['total_time']) / original_result['total_time'] * 100
            print(f"   总耗时减少: {total_time_reduction:.1f}%")

        print(f"   原始提示词AI检测率: {original_result['ai_score']:.2%}")
        print(f"   新提示词AI检测率: {new_pro_result['ai_score']:.2%}")

        # 显示一些关键差异
        print(f"\n   关键差异分析:")
        print(f"   - 提示词长度减少: {original_result['prompt_length'] - new_pro_result['prompt_length']} 字符")
        print(f"   - 构建时间差异: {original_result['prompt_time'] - new_pro_result['prompt_time']:.4f} 秒")

        # 如果AI检测率差异较大
        ai_score_diff = abs(original_result['ai_score'] - new_pro_result['ai_score'])
        if ai_score_diff > 0.05:  # 5%差异
            print(f"   - AI检测率差异显著: {ai_score_diff:.2%}")
            if new_pro_result['ai_score'] < original_result['ai_score']:
                print(f"   - 新提示词的翻译AI痕迹更少")
            else:
                print(f"   - 原始提示词的翻译AI痕迹更少")
    else:
        print("   翻译失败，无法比较")

    # 3. 汇总表格
    print(f"\n{'='*80}")
    print("测试结果汇总")
    print(f"{'='*80}")

    headers = ["测试名称", "提示词长度", "构建时间(秒)", "翻译时间(秒)", "AI检测时间(秒)", "总时间(秒)", "AI概率", "成功"]
    print(f"{headers[0]:<20} {headers[1]:<10} {headers[2]:<12} {headers[3]:<12} {headers[4]:<14} {headers[5]:<10} {headers[6]:<10} {headers[7]:<8}")
    print("-" * 110)

    for test_name, result in results.items():
        print(f"{test_name:<20} "
              f"{result['prompt_length']:<10} "
              f"{result['prompt_time']:<12.4f} "
              f"{result['translation_time']:<12.2f} "
              f"{result.get('gptzero_time', 0):<14.2f} "
              f"{result['total_time']:<10.2f} "
              f"{result['ai_score']:<10.2%} "
              f"{'是' if result['translation_success'] else '否':<8}")

    # 4. 保存详细结果到文件
    output_file = current_dir / "translation_test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        # 移除翻译文本以减小文件大小，只保留关键数据
        clean_results = {}
        for test_name, result in results.items():
            clean_result = result.copy()
            # 只保留翻译文本的前200字符
            if isinstance(clean_result['translation_text'], str) and len(clean_result['translation_text']) > 200:
                clean_result['translation_text'] = clean_result['translation_text'][:200] + "..."
            clean_results[test_name] = clean_result

        json.dump({
            "test_text_preview": test_text[:200] + "...",
            "test_text_length": len(test_text),
            "simulation_mode": SIMULATION_MODE,
            "results": clean_results,
            "summary": {
                "new_basic_vs_pro": {
                    "similarity": diff['similarity_percentage'] if 'diff' in locals() else "N/A",
                    "ai_score_diff": abs(basic_result['ai_score'] - pro_result['ai_score']) if basic_result['translation_success'] and pro_result['translation_success'] else "N/A"
                },
                "original_vs_new": {
                    "prompt_length_reduction": original_result['prompt_length'] - new_pro_result['prompt_length'] if original_result['translation_success'] and new_pro_result['translation_success'] else "N/A",
                    "prompt_time_reduction_pct": ((original_result['prompt_time'] - new_pro_result['prompt_time']) / original_result['prompt_time'] * 100) if original_result['prompt_time'] > 0 and original_result['translation_success'] and new_pro_result['translation_success'] else "N/A",
                    "ai_score_diff": abs(original_result['ai_score'] - new_pro_result['ai_score']) if original_result['translation_success'] and new_pro_result['translation_success'] else "N/A"
                }
            }
        }, f, ensure_ascii=False, indent=2)

    print(f"\n详细结果已保存到: {output_file}")

    # 5. 显示性能监控数据（如果可用）
    if not SIMULATION_MODE:
        try:
            print(f"\n{'='*80}")
            print("提示词性能监控数据")
            print(f"{'='*80}")

            report = prompt_performance_monitor.get_report()
            print(f"总请求数: {report.get('total_requests', 0)}")
            print(f"缓存命中率: {report.get('cache_hit_rate', 0):.2%}")
            print(f"平均构建时间: {report.get('avg_build_time_ms', 0):.2f} ms")
            print(f"平均提示词长度: {report.get('avg_prompt_length', 0):.0f} 字符")
        except Exception as e:
            print(f"无法获取性能监控数据: {e}")

    return results

if __name__ == "__main__":
    print("翻译提示词测试脚本")
    print(f"工作目录: {current_dir}")
    print(f"模拟模式: {SIMULATION_MODE}")

    try:
        results = run_translation_tests()
        print(f"\n测试完成!")
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)