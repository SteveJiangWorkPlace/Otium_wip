#!/usr/bin/env python3
"""
模块名称：init_db.py
功能描述：数据库初始化和管理员用户创建脚本
创建时间：2026-02-27
作者：项目团队
版本：1.0.0

此脚本用于初始化项目数据库，创建必要的表和确保管理员用户存在。
适用于开发环境部署和生产环境数据库初始化。

主要功能：
1. 初始化数据库表结构（通过SQLAlchemy模型）
2. 创建或更新管理员用户账户
3. 处理初始化过程中的异常和错误
4. 提供详细的执行状态反馈

使用场景：
- 首次部署项目时的数据库初始化
- 开发环境重置数据库
- 测试环境数据准备
- 自动化部署流程中的数据库准备

执行步骤：
1. 导入数据库模块（models.database）
2. 调用init_database()创建表结构
3. 调用ensure_admin_user_exists()创建管理员
4. 输出成功/失败状态

注意事项：
- 依赖models.database模块的正确配置
- 需要正确的数据库连接设置（环境变量）
- 管理员凭证从环境变量读取（ADMIN_USERNAME/ADMIN_PASSWORD）
- 重复执行是安全的（幂等操作）
"""

import os
import sys

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # 导入数据库模块
    from models.database import ensure_admin_user_exists, init_database

    print("正在初始化数据库...")
    init_database()
    print("数据库表创建完成")

    print("确保管理员用户存在...")
    ensure_admin_user_exists()
    print("管理员用户已创建/更新")

    print("数据库初始化成功完成")
except Exception as e:
    print(f"数据库初始化失败: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
