#!/usr/bin/env python3
"""
测试运行脚本

功能：
1. 运行后端测试
2. 生成测试报告
3. 检查测试覆盖率
4. 提供测试环境管理

使用方法：
python scripts/run_tests.py [选项]

示例：
python scripts/run_tests.py              # 运行所有测试
python scripts/run_tests.py --unit       # 只运行单元测试
python scripts/run_tests.py --coverage   # 运行测试并生成覆盖率报告
python scripts/run_tests.py --health     # 只运行健康检查
"""

import os
import sys
import subprocess
import argparse
import shutil
import datetime
from pathlib import Path
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestRunner:
    """测试运行器"""

    def __init__(self, backend_dir: str = "backend"):
        self.backend_dir = Path(backend_dir).resolve()
        self.project_root = self.backend_dir.parent
        self.test_results = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0
        }

    def check_prerequisites(self) -> bool:
        """检查前置条件"""
        logger.info("检查测试前置条件...")

        # 检查后端目录
        if not self.backend_dir.exists():
            logger.error(f"后端目录不存在: {self.backend_dir}")
            return False
        logger.info(f"✓ 后端目录: {self.backend_dir}")

        # 检查 requirements.txt
        requirements_file = self.backend_dir / "requirements.txt"
        if not requirements_file.exists():
            logger.error(f"requirements.txt 不存在: {requirements_file}")
            return False
        logger.info(f"✓ requirements.txt: {requirements_file}")

        # 检查测试目录
        test_dir = self.backend_dir / "tests"
        if not test_dir.exists():
            logger.warning(f"测试目录不存在: {test_dir}")
            logger.info("将创建测试目录...")
            test_dir.mkdir(exist_ok=True)
        logger.info(f"✓ 测试目录: {test_dir}")

        # 检查 pytest.ini
        pytest_ini = self.backend_dir / "pytest.ini"
        if not pytest_ini.exists():
            logger.warning(f"pytest.ini 不存在: {pytest_ini}")
            return False
        logger.info(f"✓ pytest.ini: {pytest_ini}")

        return True

    def setup_test_environment(self) -> bool:
        """设置测试环境"""
        logger.info("设置测试环境...")

        # 设置环境变量
        os.environ['TESTING'] = 'True'
        os.environ['ENVIRONMENT'] = 'testing'

        # 确保数据目录存在
        data_dir = self.backend_dir / "data"
        if not data_dir.exists():
            data_dir.mkdir(exist_ok=True)
            logger.info(f"创建数据目录: {data_dir}")

        # 确保日志目录存在
        log_dir = self.backend_dir / "logs"
        if not log_dir.exists():
            log_dir.mkdir(exist_ok=True)
            logger.info(f"创建日志目录: {log_dir}")

        # 检查测试数据库
        test_db = data_dir / "test.db"
        if test_db.exists():
            logger.info(f"清理测试数据库: {test_db}")
            try:
                test_db.unlink()
            except Exception as e:
                logger.warning(f"清理测试数据库失败: {e}")

        logger.info("✓ 测试环境设置完成")
        return True

    def run_pytest(self, args: list) -> bool:
        """运行 pytest"""
        logger.info("运行 pytest...")

        # 构建 pytest 命令
        cmd = [sys.executable, "-m", "pytest"]
        cmd.extend(args)

        logger.info(f"执行命令: {' '.join(cmd)}")

        try:
            # 运行测试
            result = subprocess.run(
                cmd,
                cwd=self.backend_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )

            # 输出结果
            if result.stdout:
                print("\n" + "="*60)
                print("测试输出")
                print("="*60)
                print(result.stdout)

            if result.stderr:
                print("\n" + "="*60)
                print("测试错误")
                print("="*60)
                print(result.stderr)

            # 解析结果
            return_code = result.returncode

            # 简单解析测试结果（简化版）
            if "passed" in result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if "passed" in line and "failed" in line:
                        # 解析类似 "3 passed, 1 failed in 0.12s" 的行
                        parts = line.split()
                        for part in parts:
                            if part.endswith('passed'):
                                self.test_results['passed'] = int(part[:-7])
                            elif part.endswith('failed'):
                                self.test_results['failed'] = int(part[:-6])
                            elif part.endswith('skipped'):
                                self.test_results['skipped'] = int(part[:-7])
                            elif part.endswith('errors'):
                                self.test_results['errors'] = int(part[:-6])

            if return_code == 0:
                logger.info("✓ 所有测试通过")
                return True
            else:
                logger.error(f"✗ 测试失败，返回码: {return_code}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("✗ 测试超时（5分钟）")
            return False
        except Exception as e:
            logger.error(f"✗ 运行测试时发生错误: {e}")
            return False

    def run_health_check(self) -> bool:
        """运行健康检查测试"""
        logger.info("运行健康检查测试...")

        # 运行特定的健康检查测试
        health_test = self.backend_dir / "tests" / "test_health.py"
        if not health_test.exists():
            logger.error(f"健康检查测试文件不存在: {health_test}")
            return False

        return self.run_pytest([str(health_test), "-v"])

    def run_unit_tests(self) -> bool:
        """运行单元测试"""
        logger.info("运行单元测试...")
        return self.run_pytest(["-m", "unit", "-v"])

    def run_all_tests(self) -> bool:
        """运行所有测试"""
        logger.info("运行所有测试...")
        return self.run_pytest(["-v"])

    def run_with_coverage(self) -> bool:
        """运行测试并生成覆盖率报告"""
        logger.info("运行测试覆盖率检查...")

        # 运行 pytest 并生成覆盖率报告
        args = [
            "--cov=.",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-report=xml",
            "--cov-fail-under=80",
            "-v"
        ]

        success = self.run_pytest(args)

        if success:
            coverage_dir = self.backend_dir / "htmlcov"
            if coverage_dir.exists():
                logger.info(f"✓ 覆盖率报告生成在: {coverage_dir}")
                index_file = coverage_dir / "index.html"
                if index_file.exists():
                    logger.info(f"打开报告: file://{index_file}")

        return success

    def generate_report(self) -> dict:
        """生成测试报告"""
        total = (self.test_results['passed'] + self.test_results['failed'] +
                 self.test_results['skipped'] + self.test_results['errors'])

        self.test_results['total'] = total

        report = {
            'summary': self.test_results.copy(),
            'success': self.test_results['failed'] == 0 and self.test_results['errors'] == 0,
            'coverage': None,  # 可以添加覆盖率数据
            'timestamp': datetime.now().isoformat()
        }

        return report

    def print_report(self, report: dict) -> None:
        """打印测试报告"""
        print("\n" + "="*60)
        print("测试运行报告")
        print("="*60)

        summary = report['summary']

        print(f"\n测试统计:")
        print(f"  总计: {summary['total']}")
        print(f"  通过: {summary['passed']}")
        print(f"  失败: {summary['failed']}")
        print(f"  跳过: {summary['skipped']}")
        print(f"  错误: {summary['errors']}")

        if summary['total'] > 0:
            pass_rate = (summary['passed'] / summary['total']) * 100
            print(f"  通过率: {pass_rate:.1f}%")

        print(f"\n结果: {'✅ 通过' if report['success'] else '❌ 失败'}")

        if not report['success']:
            print("\n建议:")
            if summary['failed'] > 0:
                print("  • 查看失败的测试详情")
                print("  • 运行单个失败测试进行调试")
            if summary['errors'] > 0:
                print("  • 检查测试环境设置")
                print("  • 验证依赖是否安装正确")

        print("="*60 + "\n")

    def cleanup(self) -> None:
        """清理测试环境"""
        logger.info("清理测试环境...")

        # 删除测试数据库
        test_db = self.backend_dir / "data" / "test.db"
        if test_db.exists():
            try:
                test_db.unlink()
                logger.info(f"删除测试数据库: {test_db}")
            except Exception as e:
                logger.warning(f"删除测试数据库失败: {e}")

        # 删除临时文件
        temp_files = [
            self.backend_dir / ".coverage",
            self.backend_dir / "coverage.xml"
        ]

        for temp_file in temp_files:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                    logger.info(f"删除临时文件: {temp_file}")
                except Exception as e:
                    logger.warning(f"删除临时文件失败: {e}")

        logger.info("✓ 清理完成")


def main():
    """命令行入口"""
    import datetime
    global datetime

    parser = argparse.ArgumentParser(
        description='测试运行脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s                     # 运行所有测试
  %(prog)s --health           # 只运行健康检查
  %(prog)s --unit             # 运行单元测试
  %(prog)s --coverage         # 运行测试并生成覆盖率报告
  %(prog)s --clean            # 清理后运行测试
  %(prog)s --verbose          # 详细输出
        """
    )

    parser.add_argument(
        '--health',
        action='store_true',
        help='只运行健康检查测试'
    )

    parser.add_argument(
        '--unit',
        action='store_true',
        help='运行单元测试'
    )

    parser.add_argument(
        '--coverage',
        action='store_true',
        help='运行测试并生成覆盖率报告'
    )

    parser.add_argument(
        '--clean',
        action='store_true',
        help='清理测试环境后运行'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='详细输出'
    )

    parser.add_argument(
        '--backend-dir',
        default='backend',
        help='后端目录路径（默认: backend）'
    )

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 创建测试运行器
    runner = TestRunner(backend_dir=args.backend_dir)

    # 检查前置条件
    if not runner.check_prerequisites():
        logger.error("前置条件检查失败")
        sys.exit(1)

    # 清理环境
    if args.clean:
        runner.cleanup()

    # 设置测试环境
    if not runner.setup_test_environment():
        logger.error("测试环境设置失败")
        sys.exit(1)

    # 运行测试
    success = False

    try:
        if args.health:
            success = runner.run_health_check()
        elif args.unit:
            success = runner.run_unit_tests()
        elif args.coverage:
            success = runner.run_with_coverage()
        else:
            success = runner.run_all_tests()

        # 生成报告
        report = runner.generate_report()
        runner.print_report(report)

        # 清理
        runner.cleanup()

        # 退出码
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.warning("\n测试被用户中断")
        runner.cleanup()
        sys.exit(130)
    except Exception as e:
        logger.error(f"测试运行器发生错误: {e}")
        runner.cleanup()
        sys.exit(1)


if __name__ == '__main__':
    main()