#!/usr/bin/env python3
"""
部署检查脚本
用于验证环境变量和配置是否正确
"""

import os
import sys
from pathlib import Path

import requests

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_backend_env():
    """检查后端环境变量"""
    print("=" * 60)
    print("检查后端环境变量")
    print("=" * 60)

    # 从 .env 文件读取（如果存在）
    env_file = project_root / "backend" / ".env"
    env_vars = {}

    if env_file.exists():
        print(f"读取环境变量文件: {env_file}")
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()

    # 必需的环境变量
    required_vars = {
        "DATABASE_TYPE": ["sqlite", "postgresql"],
        "ENVIRONMENT": ["development", "production"],
        "SECRET_KEY": None,  # 任何非空值
        "ADMIN_USERNAME": None,
        "ADMIN_PASSWORD": None,
    }

    # API 密钥（可选的，但建议设置）
    optional_vars = {
        "GEMINI_API_KEY": "Google Gemini API 密钥",
        "GPTZERO_API_KEY": "GPTZero API 密钥",
    }

    print("\n必需的环境变量:")
    for var, allowed_values in required_vars.items():
        value = env_vars.get(var, os.environ.get(var))
        if value:
            status = "[OK] 已设置"
            if allowed_values and value not in allowed_values:
                status = f"[WARNING]  已设置但值无效 (应为 {allowed_values})"
        else:
            status = "[ERROR] 未设置"

        masked_value = (
            value[:4] + "..." + value[-4:] if value and len(value) > 8 else value
        )
        print(f"  {var:30} {status:20} {masked_value or ''}")

    print("\n建议设置的 API 密钥:")
    for var, description in optional_vars.items():
        value = env_vars.get(var, os.environ.get(var))
        if value:
            status = "[OK] 已设置"
            masked_value = value[:4] + "..." + value[-4:] if len(value) > 8 else value
        else:
            status = "[WARNING]  未设置"
            masked_value = ""
            print(f"  {var:30} {status:20} {description}")

    return True


def check_frontend_env():
    """检查前端环境变量"""
    print("\n" + "=" * 60)
    print("检查前端环境变量")
    print("=" * 60)

    # 检查前端配置文件
    frontend_dir = project_root / "frontend"
    package_json = frontend_dir / "package.json"

    if package_json.exists():
        print(f"[OK] package.json 存在: {package_json}")
    else:
        print("[ERROR] package.json 不存在")
        return False

    # 检查环境变量
    print("\n前端需要的环境变量:")
    api_url = os.environ.get("REACT_APP_API_BASE_URL")
    if api_url:
        print(f"  REACT_APP_API_BASE_URL: [OK] 已设置 -> {api_url}")

        # 测试后端连接
        try:
            response = requests.get(f"{api_url}/api/health", timeout=5)
            if response.status_code == 200:
                print(f"  [OK] 后端连接正常: {response.json()}")
            else:
                print(f"  [WARNING]  后端连接异常: 状态码 {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  [ERROR] 后端连接失败: {e}")
    else:
        print("  REACT_APP_API_BASE_URL: [WARNING]  未设置")
        print("    本地开发默认: http://localhost:8000")
        print("    生产环境: https://your-backend.onrender.com")

    return True


def check_database_config():
    """检查数据库配置"""
    print("\n" + "=" * 60)
    print("检查数据库配置")
    print("=" * 60)

    db_type = os.environ.get("DATABASE_TYPE", "sqlite")
    print(f"数据库类型: {db_type}")

    if db_type == "sqlite":
        db_path = os.environ.get("DATABASE_PATH", "./data/otium.db")
        db_file = project_root / "backend" / db_path.replace("./", "")

        if db_file.exists():
            print(f"[OK] SQLite 数据库文件存在: {db_file}")
            size = db_file.stat().st_size
            print(f"  文件大小: {size:,} 字节 ({size / 1024:.1f} KB)")
        else:
            print(f"[WARNING]  SQLite 数据库文件不存在: {db_file}")
            print("  首次运行时会自动创建")

    elif db_type == "postgresql":
        db_url = os.environ.get("DATABASE_URL")
        if db_url:
            # 隐藏密码
            masked_url = db_url
            if "@" in db_url:
                parts = db_url.split("@")
                user_pass = parts[0]
                if ":" in user_pass:
                    user, _ = user_pass.split(":", 1)
                    masked_url = f"{user}:***@{parts[1]}"
            print(f"[OK] PostgreSQL 连接 URL: {masked_url}")
        else:
            print("[ERROR] DATABASE_URL 未设置")

    return True


def check_directory_structure():
    """检查目录结构"""
    print("\n" + "=" * 60)
    print("检查项目目录结构")
    print("=" * 60)

    required_dirs = [
        project_root / "backend",
        project_root / "frontend",
        project_root / "backend" / "data",
        project_root / "backend" / "logs",
    ]

    required_files = [
        project_root / "backend" / "requirements.txt",
        project_root / "backend" / "main.py",
        project_root / "backend" / "config.py",
        project_root / "frontend" / "package.json",
        project_root / "frontend" / "src" / "api" / "client.ts",
    ]

    print("必需目录:")
    for dir_path in required_dirs:
        if dir_path.exists():
            print(f"  [OK] {dir_path.relative_to(project_root)}")
        else:
            print(f"  [WARNING]  {dir_path.relative_to(project_root)} (不存在)")
            if "data" in str(dir_path) or "logs" in str(dir_path):
                print("    首次运行时会自动创建")

    print("\n必需文件:")
    for file_path in required_files:
        if file_path.exists():
            print(f"  [OK] {file_path.relative_to(project_root)}")
        else:
            print(f"  [ERROR] {file_path.relative_to(project_root)} (不存在)")

    return True


def generate_env_template():
    """生成环境变量模板"""
    print("\n" + "=" * 60)
    print("生成环境变量模板")
    print("=" * 60)

    template = """# ==================== 应用配置 ====================
ENVIRONMENT=development
DEBUG=True

# ==================== 服务器配置 ====================
HOST=0.0.0.0
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# ==================== JWT 认证配置 ====================
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ADMIN_TOKEN_EXPIRE_MINUTES=1440

# ==================== API 密钥配置 ====================
GEMINI_API_KEY=your_gemini_api_key_here
GPTZERO_API_KEY=your_gptzero_api_key_here

# ==================== 数据库配置 ====================
DATABASE_TYPE=sqlite
DATABASE_PATH=./data/otium.db
PASSWORD_HASH_ALGORITHM=sha256

# ==================== 管理员配置 ====================
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# ==================== 速率限制配置 ====================
RATE_LIMIT_PER_MINUTE=60
DAILY_TEXT_LIMIT=1000

# ==================== 日志配置 ====================
LOG_LEVEL=INFO
LOG_TO_CONSOLE=True

# ==================== 功能开关 ====================
ENABLE_AI_DETECTION=True
ENABLE_TEXT_REFINEMENT=True
ENABLE_TRANSLATION_DIRECTIVES=True
"""

    env_file = project_root / "backend" / ".env.example"
    if not env_file.exists():
        print(f"创建: {env_file}")
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(template)
        print("[OK] 环境变量模板已创建")
        print("请复制为 .env 并填写实际值:")
        print("  cd backend")
        print("  cp .env.example .env")
        print("  # 编辑 .env 文件")
    else:
        print(f"[OK] 环境变量模板已存在: {env_file}")

    return True


def main():
    """主函数"""
    print("Otium 部署配置检查工具")
    print("=" * 60)

    checks = [
        ("目录结构", check_directory_structure),
        ("后端环境变量", check_backend_env),
        ("前端环境变量", check_frontend_env),
        ("数据库配置", check_database_config),
        ("环境变量模板", generate_env_template),
    ]

    results = []
    for name, func in checks:
        try:
            print(f"\n执行检查: {name}")
            result = func()
            results.append((name, result))
        except Exception as e:
            print(f"检查失败: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("检查总结")
    print("=" * 60)

    for name, result in results:
        status = "[OK] 通过" if result else "[ERROR] 失败"
        print(f"{name:20} {status}")

    print("\n" + "=" * 60)
    print("下一步:")
    print("1. 确保所有必需的环境变量已设置")
    print("2. 运行后端测试: cd backend && python test_backend.py")
    print("3. 启动后端: cd backend && python main.py")
    print("4. 启动前端: cd frontend && npm start")
    print("5. 访问 http://localhost:3000")
    print("=" * 60)

    # 返回总体状态
    overall = all(result for _, result in results)
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
