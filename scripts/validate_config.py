#!/usr/bin/env python3
"""
环境变量配置验证脚本

功能：
1. 检查必要的环境变量是否设置
2. 验证环境变量格式
3. 提供配置建议
4. 生成配置报告

使用方法：
python scripts/validate_config.py
或
cd backend && python ../scripts/validate_config.py
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConfigValidator:
    """环境变量配置验证器"""

    # 必需的环境变量（根据 .env.example）
    REQUIRED_VARS = [
        'SECRET_KEY',
        'GEMINI_API_KEY',
        'GPTZERO_API_KEY'
    ]

    # 推荐设置的环境变量
    RECOMMENDED_VARS = [
        'ENVIRONMENT',
        'DEBUG',
        'CORS_ORIGINS',
        'ALGORITHM',
        'ACCESS_TOKEN_EXPIRE_MINUTES'
    ]

    # 环境变量验证规则
    VALIDATION_RULES = {
        'SECRET_KEY': {
            'min_length': 32,
            'description': 'JWT密钥，建议使用openssl rand -hex 32生成'
        },
        'GEMINI_API_KEY': {
            'min_length': 10,
            'description': 'Gemini API密钥'
        },
        'GPTZERO_API_KEY': {
            'min_length': 10,
            'description': 'GPTZero API密钥'
        },
        'ENVIRONMENT': {
            'allowed_values': ['development', 'production', 'testing'],
            'default': 'development'
        },
        'DEBUG': {
            'allowed_values': ['True', 'False', 'true', 'false', '1', '0'],
            'default': 'True'
        },
        'ACCESS_TOKEN_EXPIRE_MINUTES': {
            'type': int,
            'min_value': 5,
            'max_value': 1440,
            'default': 30
        },
        'ADMIN_TOKEN_EXPIRE_MINUTES': {
            'type': int,
            'min_value': 60,
            'max_value': 10080,
            'default': 1440
        },
        'CORS_ORIGINS': {
            'description': 'CORS允许的来源，用逗号分隔'
        }
    }

    def __init__(self, env_file: Optional[str] = None):
        """
        初始化验证器

        Args:
            env_file: .env文件路径，如果为None则从环境变量读取
        """
        self.env_file = env_file
        self.results = {
            'required': {'passed': [], 'failed': [], 'warnings': []},
            'recommended': {'missing': [], 'present': []},
            'validation': {'passed': [], 'failed': []}
        }

    def load_env_file(self) -> bool:
        """从.env文件加载环境变量"""
        if not self.env_file:
            return True

        env_path = Path(self.env_file)
        if not env_path.exists():
            logger.warning(f".env文件不存在: {env_path}")
            return False

        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # 跳过空行和注释
                    if not line or line.startswith('#'):
                        continue

                    # 解析键值对
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()

                        # 移除值的引号
                        if (value.startswith('"') and value.endswith('"')) or \
                           (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]

                        # 设置环境变量（如果尚未设置）
                        if key and value and key not in os.environ:
                            os.environ[key] = value
                            logger.debug(f"从文件加载: {key}=***")

            logger.info(f"从文件加载了环境变量: {env_path}")
            return True

        except Exception as e:
            logger.error(f"加载.env文件失败: {e}")
            return False

    def check_required_vars(self) -> None:
        """检查必需的环境变量"""
        logger.info("检查必需的环境变量...")

        for var in self.REQUIRED_VARS:
            value = os.environ.get(var)

            if value and value.strip() and not value.startswith('your-'):
                self.results['required']['passed'].append(var)
                logger.info(f"  ✓ {var}: 已设置")
            else:
                self.results['required']['failed'].append(var)
                logger.error(f"  ✗ {var}: 未设置或为默认值")

                # 特殊警告
                if value and value.startswith('your-'):
                    self.results['required']['warnings'].append(
                        f"{var} 使用默认值，请在生产环境中修改"
                    )

    def check_recommended_vars(self) -> None:
        """检查推荐的环境变量"""
        logger.info("检查推荐的环境变量...")

        for var in self.RECOMMENDED_VARS:
            value = os.environ.get(var)

            if value is not None:
                self.results['recommended']['present'].append(var)
                logger.info(f"  ✓ {var}: 已设置")
            else:
                self.results['recommended']['missing'].append(var)
                logger.warning(f"  ! {var}: 未设置（使用默认值）")

    def validate_var_format(self, var: str, value: str) -> Tuple[bool, str]:
        """验证单个环境变量的格式"""
        rules = self.VALIDATION_RULES.get(var)
        if not rules:
            return True, "无验证规则"

        # 检查允许的值
        if 'allowed_values' in rules:
            if value not in rules['allowed_values']:
                allowed = ', '.join(rules['allowed_values'])
                return False, f"值 '{value}' 不在允许范围内: [{allowed}]"

        # 检查最小长度
        if 'min_length' in rules:
            if len(value) < rules['min_length']:
                return False, f"长度不足 {rules['min_length']} 字符"

        # 检查整数范围
        if 'type' in rules and rules['type'] == int:
            try:
                int_value = int(value)
                if 'min_value' in rules and int_value < rules['min_value']:
                    return False, f"值 {int_value} 小于最小值 {rules['min_value']}"
                if 'max_value' in rules and int_value > rules['max_value']:
                    return False, f"值 {int_value} 大于最大值 {rules['max_value']}"
            except ValueError:
                return False, f"值 '{value}' 不是有效的整数"

        return True, "格式正确"

    def validate_vars(self) -> None:
        """验证环境变量格式"""
        logger.info("验证环境变量格式...")

        for var in self.VALIDATION_RULES.keys():
            value = os.environ.get(var)

            if value is None:
                # 如果没有设置，跳过验证（使用默认值）
                continue

            is_valid, message = self.validate_var_format(var, value)

            if is_valid:
                self.results['validation']['passed'].append(f"{var}: {message}")
                logger.info(f"  ✓ {var}: {message}")
            else:
                self.results['validation']['failed'].append(f"{var}: {message}")
                logger.error(f"  ✗ {var}: {message}")

    def check_render_specific(self) -> None:
        """检查Render特定配置"""
        logger.info("检查Render部署配置...")

        is_render = os.environ.get('RENDER') == 'true'

        if is_render:
            logger.info("  ✓ 运行在Render平台上")

            # 检查生产环境配置
            if os.environ.get('ENVIRONMENT') != 'production':
                logger.warning("  ! ENVIRONMENT 应设置为 'production'")

            if os.environ.get('DEBUG', '').lower() in ['true', '1']:
                logger.warning("  ! DEBUG 应设置为 False 在生产环境")

            # 检查端口配置
            port = os.environ.get('PORT')
            if port:
                logger.info(f"  ✓ PORT: {port}")
            else:
                logger.warning("  ! PORT 未设置（Render应自动设置）")
        else:
            logger.info("  ✓ 运行在本地环境")

    def generate_report(self) -> Dict:
        """生成验证报告"""
        total_required = len(self.REQUIRED_VARS)
        passed_required = len(self.results['required']['passed'])

        total_recommended = len(self.RECOMMENDED_VARS)
        present_recommended = len(self.results['recommended']['present'])

        total_validation = len(self.VALIDATION_RULES)
        passed_validation = len(self.results['validation']['passed'])

        report = {
            'summary': {
                'required_passed': passed_required,
                'required_total': total_required,
                'required_percentage': (passed_required / total_required * 100) if total_required > 0 else 0,
                'recommended_present': present_recommended,
                'recommended_total': total_recommended,
                'recommended_percentage': (present_recommended / total_recommended * 100) if total_recommended > 0 else 0,
                'validation_passed': passed_validation,
                'validation_total': total_validation,
                'validation_percentage': (passed_validation / total_validation * 100) if total_validation > 0 else 0
            },
            'details': self.results,
            'recommendations': []
        }

        # 生成建议
        if passed_required < total_required:
            report['recommendations'].append(
                f"请设置缺失的必需环境变量: {', '.join(self.results['required']['failed'])}"
            )

        if self.results['required']['warnings']:
            report['recommendations'].extend(self.results['required']['warnings'])

        if len(self.results['recommended']['missing']) > 0:
            report['recommendations'].append(
                f"建议设置推荐环境变量: {', '.join(self.results['recommended']['missing'])}"
            )

        if len(self.results['validation']['failed']) > 0:
            report['recommendations'].append(
                f"请修正格式错误的环境变量: {', '.join([f.split(':')[0] for f in self.results['validation']['failed']])}"
            )

        return report

    def print_report(self, report: Dict) -> None:
        """打印验证报告"""
        print("\n" + "="*60)
        print("环境变量配置验证报告")
        print("="*60)

        summary = report['summary']

        # 必需变量
        print(f"\n必需环境变量: {summary['required_passed']}/{summary['required_total']} "
              f"({summary['required_percentage']:.1f}%)")

        if self.results['required']['failed']:
            print("  缺失:")
            for var in self.results['required']['failed']:
                print(f"    - {var}")

        # 推荐变量
        print(f"\n推荐环境变量: {summary['recommended_present']}/{summary['recommended_total']} "
              f"({summary['recommended_percentage']:.1f}%)")

        if self.results['recommended']['missing']:
            print("  缺失:")
            for var in self.results['recommended']['missing']:
                print(f"    - {var}")

        # 格式验证
        print(f"\n格式验证: {summary['validation_passed']}/{summary['validation_total']} "
              f"({summary['validation_percentage']:.1f}%)")

        if self.results['validation']['failed']:
            print("  错误:")
            for error in self.results['validation']['failed']:
                print(f"    - {error}")

        # 建议
        if report['recommendations']:
            print("\n建议:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"  {i}. {rec}")

        # 总体评估
        print("\n" + "-"*60)
        if summary['required_percentage'] < 100:
            print("❌ 配置不完整：必需环境变量缺失")
            print("   应用可能无法正常运行")
        elif summary['required_percentage'] == 100 and summary['recommended_percentage'] < 50:
            print("⚠️  配置基本完整，但建议完善推荐设置")
            print("   应用可以运行，但可能缺少某些功能")
        else:
            print("✅ 配置良好")
            print("   应用可以正常运行")

        print("="*60 + "\n")

    def run(self) -> bool:
        """运行完整验证流程"""
        logger.info("开始环境变量配置验证...")

        # 加载.env文件
        if self.env_file:
            self.load_env_file()

        # 执行检查
        self.check_required_vars()
        self.check_recommended_vars()
        self.validate_vars()
        self.check_render_specific()

        # 生成报告
        report = self.generate_report()
        self.print_report(report)

        # 返回是否通过（必需变量全部设置）
        return report['summary']['required_percentage'] == 100


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description='环境变量配置验证脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s                     # 验证当前环境变量
  %(prog)s --env .env          # 从.env文件加载并验证
  %(prog)s --env backend/.env  # 指定文件路径
  %(prog)s --quiet             # 安静模式，只输出结果
        """
    )

    parser.add_argument(
        '--env',
        help='.env文件路径（默认从环境变量读取）',
        default=None
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='安静模式，减少输出'
    )

    args = parser.parse_args()

    # 设置日志级别
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    # 运行验证
    validator = ConfigValidator(env_file=args.env)
    success = validator.run()

    # 返回退出码
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()