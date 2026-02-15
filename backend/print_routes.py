#!/usr/bin/env python3
"""
打印FastAPI应用的所有路由
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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