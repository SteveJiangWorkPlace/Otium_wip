#!/usr/bin/env python3
"""
安装数据库迁移所需的依赖
"""

import subprocess
import sys


def install_dependencies():
    """安装依赖"""
    dependencies = ["sqlalchemy>=2.0.0", "psycopg2-binary>=2.9.0", "alembic>=1.13.0"]

    print("安装数据库迁移依赖...")

    for dep in dependencies:
        print(f"安装 {dep}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"  {dep} 安装成功")
        except subprocess.CalledProcessError as e:
            print(f"  {dep} 安装失败: {e}")
            return False

    print("\n所有依赖安装完成!")
    return True


def check_installation():
    """检查安装"""
    print("\n检查安装...")

    modules = ["sqlalchemy", "psycopg2", "alembic"]
    all_ok = True

    for module in modules:
        try:
            __import__(module)
            print(f"  [成功] {module} 已安装")
        except ImportError:
            print(f"  [失败] {module} 未安装")
            all_ok = False

    return all_ok


def main():
    """主函数"""
    print("=" * 60)
    print("数据库迁移依赖安装工具")
    print("=" * 60)

    # 安装依赖
    if not install_dependencies():
        print("\n依赖安装失败，请手动安装:")
        print("pip install sqlalchemy psycopg2-binary alembic")
        return False

    # 检查安装
    if not check_installation():
        print("\n部分依赖未正确安装，请检查")
        return False

    print("\n" + "=" * 60)
    print("依赖安装完成!")
    print("现在可以运行迁移脚本:")
    print("python scripts/migrate_to_database.py")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
