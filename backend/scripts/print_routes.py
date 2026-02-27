#!/usr/bin/env python3
"""
模块名称：print_routes.py
功能描述：FastAPI应用路由打印工具
创建时间：2026-02-27
作者：项目团队
版本：1.0.0

此脚本用于打印FastAPI应用中定义的所有API路由信息，包括HTTP方法和路径。
便于开发者查看和理解应用的路由结构，支持主路由和子路由（APIRouter）的显示。

主要功能：
1. 导入FastAPI应用并解析路由信息
2. 显示每个路由的HTTP方法和路径
3. 支持嵌套路由（APIRouter）的递归显示
4. 提供路由统计信息（总路由数）
5. 输出格式化的路由列表，便于阅读和分析

输出格式：
- 每行显示一个路由：HTTP方法（左对齐，宽度20字符）和路径
- 路由按HTTP方法排序显示
- 子路由缩进显示（当使用APIRouter时）
- 统计信息：总路由数

使用场景：
- 开发过程中快速查看API路由结构
- 调试路由配置问题
- 文档生成和API清单创建
- 部署前验证路由完整性

执行流程：
1. 添加项目路径到Python导入路径
2. 导入FastAPI应用实例（从main.py）
3. 遍历所有路由对象
4. 提取HTTP方法和路径信息
5. 格式化并打印路由信息
6. 显示统计信息

注意事项：
- 需要确保后端服务可导入（依赖main.py）
- 脚本应运行在项目根目录或backend目录
- 仅显示已注册的路由，不显示中间件等其他组件
- 路径可能包含路径参数（如/user/{id}）
"""

import os
import sys

# 添加backend目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)  # backend目录
project_root = os.path.dirname(backend_dir)  # 项目根目录

# 添加backend和project_root到Python路径
sys.path.insert(0, backend_dir)
sys.path.insert(0, project_root)

from main import app

print("=== FastAPI应用路由 ===")
for route in app.routes:
    if hasattr(route, "methods"):
        methods = ", ".join(sorted(route.methods))
        path = getattr(route, "path", "N/A")
        print(f"{methods:20} {path}")
    elif hasattr(route, "routes"):  # 子路由，如APIRouter
        for subroute in route.routes:
            if hasattr(subroute, "methods"):
                methods = ", ".join(sorted(subroute.methods))
                path = getattr(subroute, "path", "N/A")
                print(f"{methods:20} {path}")

print(f"\n总计: {len(app.routes)} 个路由")
print("===================")
