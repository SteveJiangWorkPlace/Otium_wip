#!/usr/bin/env python3
"""
模块名称：install_dependencies.py
功能描述：数据库迁移依赖安装和管理工具
创建时间：2026-02-27
作者：项目团队
版本：1.0.0

此脚本用于安装和管理数据库迁移所需的Python依赖包，确保项目数据库迁移功能
能够正常运行。脚本支持安装核心数据库迁移库，并提供安装验证功能。

主要功能：
1. 安装SQLAlchemy、psycopg2-binary、Alembic等数据库迁移依赖包
2. 验证依赖包是否正确安装并可导入
3. 提供详细的安装过程反馈和错误处理
4. 支持开发和生产环境依赖管理

支持安装的依赖：
- SQLAlchemy>=2.0.0：Python SQL工具包和ORM框架
- psycopg2-binary>=2.9.0：PostgreSQL数据库适配器（二进制分发版）
- Alembic>=1.13.0：数据库迁移工具，集成SQLAlchemy

使用场景：
- 首次部署项目时的数据库迁移依赖安装
- 开发环境依赖更新和验证
- 生产环境部署前的依赖检查
- 持续集成流程中的依赖验证

注意事项：
- 需要Python包管理工具pip可用
- 依赖安装过程需要网络连接
- 安装失败时提供清晰的错误信息和手动安装指令
- 重复执行是安全的，已安装的包不会被重复安装
"""

import subprocess
import sys


def install_dependencies():
    """
    安装数据库迁移所需的核心依赖包

    按顺序安装SQLAlchemy、psycopg2-binary和Alembic等数据库迁移必需的Python包。
    使用系统的Python解释器和pip包管理器执行安装，提供详细的安装进度反馈。

    Args:
        无: 函数使用预定义的依赖包列表，不接受参数

    Returns:
        bool: 安装是否全部成功，True表示所有依赖安装成功，False表示有安装失败

    Raises:
        subprocess.CalledProcessError: 当pip安装命令执行失败时抛出（被内部捕获）

    Examples:
        >>> success = install_dependencies()
        安装数据库迁移依赖...
        安装 sqlalchemy>=2.0.0...
          sqlalchemy>=2.0.0 安装成功
        安装 psycopg2-binary>=2.9.0...
          psycopg2-binary>=2.9.0 安装成功
        安装 alembic>=1.13.0...
          alembic>=1.13.0 安装成功

        所有依赖安装完成!
        >>> print(f"安装结果: {success}")
        安装结果: True

    Notes:
        - 使用pip包管理器进行安装，确保网络连接正常
        - 安装顺序：SQLAlchemy -> psycopg2-binary -> Alembic
        - 每个依赖安装失败都会立即停止并返回False
        - 已安装的包不会被重复安装，但会尝试升级到指定版本
        - 使用[成功]、[失败]等ASCII标记，确保Windows命令行兼容性
    """
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
    """
    验证已安装的数据库迁移依赖包

    检查SQLAlchemy、psycopg2和Alembic等核心包是否已正确安装并可导入。
    通过尝试导入每个模块来验证安装状态，提供详细的验证结果反馈。

    Args:
        无: 函数使用预定义的模块名称列表，不接受参数

    Returns:
        bool: 验证是否全部通过，True表示所有依赖可正确导入，False表示有导入失败

    Raises:
        ImportError: 当模块导入失败时抛出（被内部捕获）

    Examples:
        >>> all_ok = check_installation()
        检查安装...
          [成功] sqlalchemy 已安装
          [成功] psycopg2 已安装
          [成功] alembic 已安装
        >>> print(f"验证结果: {all_ok}")
        验证结果: True

    Notes:
        - 仅检查模块是否可以导入，不验证版本号是否匹配
        - 使用Python的__import__内置函数进行导入测试
        - 结果使用[成功]、[失败]等ASCII标记，确保Windows命令行兼容性
        - 验证失败会打印详细错误信息，方便问题诊断
        - 此函数通常与install_dependencies()配合使用，确保安装成功
    """
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
    """
    主函数：协调完整的数据库迁移依赖安装流程

    组织数据库迁移依赖的安装和验证流程，提供完整的工具使用体验。
    按顺序执行依赖安装、安装验证，并提供详细的状态反馈和使用指导。

    Args:
        无: 函数使用内部流程控制，不接受参数

    Returns:
        bool: 整个安装流程是否成功，True表示安装和验证均成功，False表示有步骤失败

    Raises:
        无: 函数内部捕获所有异常，确保总是返回布尔值

    Examples:
        >>> # 从命令行调用
        >>> python install_dependencies.py
        ============================================================
        数据库迁移依赖安装工具
        ============================================================
        安装数据库迁移依赖...
        安装 sqlalchemy>=2.0.0...
          sqlalchemy>=2.0.0 安装成功
        ...

        >>> # 从其他脚本导入
        >>> from install_dependencies import main
        >>> success = main()
        >>> if success:
        >>>     print("安装成功，可以继续执行迁移脚本")
        >>> else:
        >>>     print("安装失败，请检查错误信息")

    Notes:
        - 执行流程：依赖安装 -> 安装验证 -> 结果反馈 -> 使用指导
        - 成功标准：所有依赖安装成功且验证通过
        - 失败处理：提供清晰的手动安装指令和问题诊断信息
        - 使用指导：安装成功后提示下一步操作（运行迁移脚本）
        - 退出码：成功时返回0，失败时返回1（通过sys.exit处理）
        - 使用[成功]、[失败]等ASCII标记，确保Windows命令行兼容性
    """
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
