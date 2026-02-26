#!/usr/bin/env python3
"""
打印FastAPI应用的所有路由
"""

import sys
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))
# 同时添加项目根目录以确保其他导入正常工作
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.main import app

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
