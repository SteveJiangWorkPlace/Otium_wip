#!/usr/bin/env python3
"""
打印FastAPI应用的所有路由
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
