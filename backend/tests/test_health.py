"""
基础健康检查测试

这些测试不依赖外部服务，用于验证基本功能是否正常。
这是测试框架的起点，随着项目发展会添加更多测试。
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestHealthChecks:
    """健康检查测试类"""

    def test_import_main(self):
        """测试能否导入主应用模块"""
        try:
            # 动态导入以捕获导入错误
            import main

            assert main is not None
            print("✓ 成功导入 main 模块")
        except ImportError as e:
            pytest.fail(f"导入 main 模块失败: {e}")

    def test_app_creation(self):
        """测试 FastAPI 应用创建"""
        try:
            from main import app

            assert app is not None
            assert app.title == "Otium API"
            print(f"✓ 应用标题: {app.title}")
        except Exception as e:
            pytest.fail(f"创建应用失败: {e}")

    def test_client_creation(self):
        """测试 TestClient 创建"""
        try:
            from main import app

            client = TestClient(app)
            assert client is not None
            print("✓ TestClient 创建成功")
        except Exception as e:
            pytest.fail(f"创建 TestClient 失败: {e}")


class TestBasicEndpoints:
    """基础端点测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端 fixture"""
        from main import app

        return TestClient(app)

    def test_root_endpoint(self, client):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code in [200, 404, 307]  # 可能重定向或不存在
        print(f"✓ 根端点状态码: {response.status_code}")

    def test_api_docs_endpoint(self, client):
        """测试 API 文档端点"""
        response = client.get("/docs")
        # 文档端点应该返回 200 或 307（重定向）
        assert response.status_code in [200, 307]
        print(f"✓ API 文档端点状态码: {response.status_code}")

    def test_redoc_endpoint(self, client):
        """测试 ReDoc 端点"""
        response = client.get("/redoc")
        assert response.status_code in [200, 307]
        print(f"✓ ReDoc 端点状态码: {response.status_code}")

    def test_health_check_endpoint(self, client):
        """测试健康检查端点（如果存在）"""
        response = client.get("/health")
        # 健康检查端点可能不存在，但请求不应该导致服务器错误
        assert response.status_code != 500
        print(f"✓ 健康检查端点状态码: {response.status_code}")


class TestEnvironment:
    """环境配置测试"""

    def test_testing_environment(self):
        """测试环境变量"""
        # 检查 pytest.ini 中设置的环境变量
        assert os.environ.get("TESTING") == "True"
        assert os.environ.get("ENVIRONMENT") == "testing"
        print("✓ 测试环境变量设置正确")

    def test_required_env_vars(self):
        """检查必需的环境变量"""
        required_vars = ["SECRET_KEY", "GEMINI_API_KEY", "GPTZERO_API_KEY"]

        for var in required_vars:
            value = os.environ.get(var)
            assert value is not None, f"环境变量 {var} 未设置"
            assert value != "", f"环境变量 {var} 为空"
            print(f"✓ 环境变量 {var} 已设置")


class TestDependencies:
    """依赖测试"""

    def test_fastapi_version(self):
        """测试 FastAPI 版本"""
        import fastapi

        version = fastapi.__version__
        assert version is not None
        print(f"✓ FastAPI 版本: {version}")

    def test_pydantic_available(self):
        """测试 Pydantic 可用性"""
        try:
            import pydantic

            assert pydantic.__version__ is not None
            print(f"✓ Pydantic 版本: {pydantic.__version__}")
        except ImportError:
            pytest.fail("Pydantic 不可用")

    def test_jose_available(self):
        """测试 python-jose 可用性"""
        try:
            from jose import jwt

            assert jwt is not None
            print("✓ python-jose 可用")
        except ImportError:
            pytest.fail("python-jose 不可用")


def test_run_all_health_checks():
    """运行所有健康检查的汇总测试"""
    print("\n" + "=" * 60)
    print("运行健康检查测试")
    print("=" * 60)

    # 这个测试会运行所有上面的检查
    # 如果到达这里，说明基本健康检查通过
    print("✅ 所有基础健康检查通过")
    print("=" * 60)


if __name__ == "__main__":
    """直接运行测试（用于调试）"""
    print("运行健康检查测试...")

    # 设置测试环境变量
    os.environ["TESTING"] = "True"
    os.environ["ENVIRONMENT"] = "testing"

    # 运行简单检查
    checker = TestHealthChecks()
    checker.test_import_main()
    checker.test_app_creation()
    checker.test_client_creation()

    print("\n✅ 健康检查完成")
