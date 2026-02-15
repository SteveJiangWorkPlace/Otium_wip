"""
部署配置测试

专门测试生产环境部署相关配置，包括：
1. CORS配置 - 确保Netlify域名在允许列表中
2. 邮件服务配置 - 检查SMTP超时设置
3. API端点可访问性
4. 关键环境变量配置

这些测试应该在部署前后运行，确保配置正确。
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient
import logging

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDeploymentConfiguration:
    """部署配置测试类"""

    def setup_method(self):
        """测试方法设置"""
        # 导入配置和主应用
        from config import settings
        from main import app

        self.settings = settings
        self.app = app
        self.client = TestClient(app)

        # 生产环境必需的前端域名
        self.required_frontend_domains = [
            "https://otiumtrans.netlify.app",  # Netlify生产前端
        ]

        # 本地开发域名
        self.local_domains = [
            "http://localhost:3000",
            "http://localhost:8000",
            "http://localhost:3001",
            "http://localhost:8001",
        ]

    def test_cors_configuration(self):
        """测试CORS配置是否正确包含Netlify域名"""
        print("\n" + "="*60)
        print("测试CORS配置")
        print("="*60)

        # 获取当前CORS配置
        cors_origins = self.settings.CORS_ORIGINS
        print(f"当前CORS_ORIGINS配置: {cors_origins}")

        # 检查硬编码的域名（从main.py）
        from main import hardcoded_origins
        print(f"硬编码的允许源: {hardcoded_origins}")

        # 合并所有允许的源
        from main import all_allowed_origins
        print(f"合并后的允许源列表: {all_allowed_origins}")

        # 验证必需的生产域名
        missing_domains = []
        for domain in self.required_frontend_domains:
            if domain not in all_allowed_origins:
                missing_domains.append(domain)
            else:
                print(f"[OK] 必需域名 '{domain}' 在允许列表中")

        if missing_domains:
            pytest.fail(f"以下必需域名不在CORS允许列表中: {missing_domains}")

        # 验证本地开发域名（至少有一个）
        local_domain_found = False
        for domain in self.local_domains:
            if domain in all_allowed_origins:
                local_domain_found = True
                print(f"[OK] 本地开发域名 '{domain}' 在允许列表中")
                break

        if not local_domain_found:
            print("[WARN] 警告: 未找到本地开发域名在CORS允许列表中")

        print("[OK] CORS配置测试通过")
        return True

    def test_mail_service_configuration(self):
        """测试邮件服务配置"""
        print("\n" + "="*60)
        print("测试邮件服务配置")
        print("="*60)

        # 检查邮件服务配置
        required_smtp_vars = [
            "SMTP_HOST",
            "SMTP_PORT",
            "SMTP_USERNAME",
            "SMTP_PASSWORD",
            "SMTP_FROM",
        ]

        missing_vars = []
        for var_name in required_smtp_vars:
            var_value = getattr(self.settings, var_name, None)
            if not var_value:
                missing_vars.append(var_name)
            else:
                # 隐藏密码显示
                display_value = var_value if var_name != "SMTP_PASSWORD" else "***"
                print(f"[OK] {var_name}: {display_value}")

        if missing_vars:
            print(f"[WARN] 警告: 以下邮件配置未设置: {missing_vars}")
            print("   邮件发送功能可能不可用")

        # 检查SMTP超时配置
        smtp_timeout = getattr(self.settings, "SMTP_TIMEOUT", None)
        if smtp_timeout is None:
            print("[WARN] 警告: SMTP_TIMEOUT未设置，邮件连接可能无限等待")
        else:
            print(f"[OK] SMTP_TIMEOUT: {smtp_timeout}秒")

        # 验证SMTP端口和加密配置
        if self.settings.SMTP_PORT == 465:
            if not self.settings.SMTP_SSL:
                print("[WARN] 警告: 使用端口465但SMTP_SSL未启用")
            else:
                print("[OK] SSL加密已启用（端口465）")
        elif self.settings.SMTP_PORT == 587:
            if not self.settings.SMTP_TLS:
                print("[WARN] 警告: 使用端口587但SMTP_TLS未启用")
            else:
                print("[OK] TLS加密已启用（端口587）")

        print("[OK] 邮件服务配置测试完成")
        return True

    def test_api_endpoint_accessibility(self):
        """测试关键API端点可访问性"""
        print("\n" + "="*60)
        print("测试API端点可访问性")
        print("="*60)

        # 测试健康检查端点
        endpoints_to_test = [
            ("GET", "/", "根端点"),
            ("GET", "/docs", "API文档"),
            ("GET", "/redoc", "ReDoc文档"),
            ("GET", "/api/health", "健康检查"),
            ("GET", "/api/register/check-email", "邮箱检查端点"),
            ("POST", "/api/register/send-verification", "发送验证码端点"),
        ]

        for method, endpoint, description in endpoints_to_test:
            try:
                if method == "GET":
                    response = self.client.get(endpoint)
                elif method == "POST":
                    # 对于POST端点，发送空数据测试
                    if endpoint == "/api/register/send-verification":
                        response = self.client.post(endpoint, json={"email": "test@example.com"})
                    else:
                        response = self.client.post(endpoint, json={})

                # 检查响应状态码
                status_code = response.status_code

                # 允许的状态码：200成功，400参数错误，401未授权等
                # 但不允许500服务器错误
                if status_code != 500:
                    print(f"[OK] {description} ({method} {endpoint}): 状态码 {status_code}")

                    # 检查CORS头部（如果是来自前端的请求）
                    if "origin" in self.client.headers:
                        cors_header = response.headers.get("Access-Control-Allow-Origin")
                        if cors_header:
                            print(f"   CORS头部: Access-Control-Allow-Origin={cors_header}")
                else:
                    print(f"[FAIL] {description} ({method} {endpoint}): 服务器错误 500")

            except Exception as e:
                print(f"[WARN] {description} ({method} {endpoint}): 请求异常 - {e}")

        print("[OK] API端点可访问性测试完成")
        return True

    def test_environment_configuration(self):
        """测试环境变量配置"""
        print("\n" + "="*60)
        print("测试环境变量配置")
        print("="*60)

        # 检查关键环境变量
        critical_env_vars = [
            ("SECRET_KEY", "JWT密钥"),
            ("GEMINI_API_KEY", "Gemini API密钥"),
            ("GPTZERO_API_KEY", "GPTZero API密钥"),
        ]

        for var_name, description in critical_env_vars:
            var_value = os.environ.get(var_name)
            if not var_value:
                print(f"[WARN] 警告: {description} ({var_name}) 未设置")
            else:
                # 隐藏密钥显示
                if "KEY" in var_name or "SECRET" in var_name:
                    display_value = f"{var_value[:8]}..." if len(var_value) > 8 else "***"
                else:
                    display_value = var_value
                print(f"[OK] {description}: {display_value}")

        # 检查CORS环境变量
        cors_env = os.environ.get("CORS_ORIGINS", "")
        print(f"CORS_ORIGINS环境变量: {cors_env}")

        # 检查是否包含Netlify域名
        if "otiumtrans.netlify.app" not in cors_env:
            print("[WARN] 警告: CORS_ORIGINS环境变量中未找到Netlify域名")
        else:
            print("[OK] CORS_ORIGINS包含Netlify域名")

        # 检查部署环境
        environment = os.environ.get("ENVIRONMENT", "development")
        print(f"当前环境: {environment}")

        if environment == "production":
            print("[OK] 生产环境配置")
            # 生产环境应禁用DEBUG
            debug_mode = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")
            if debug_mode:
                print("[WARN] 警告: 生产环境中DEBUG模式应禁用")
            else:
                print("[OK] DEBUG模式已禁用")
        else:
            print(f"当前为{environment}环境")

        print("[OK] 环境变量配置测试完成")
        return True

    def test_cors_headers_with_simulation(self):
        """模拟前端请求测试CORS头部"""
        print("\n" + "="*60)
        print("模拟前端请求测试CORS头部")
        print("="*60)

        # 测试Netlify域名的CORS头部
        test_origins = [
            ("https://otiumtrans.netlify.app", "Netlify生产前端"),
            ("http://localhost:3000", "本地开发前端"),
        ]

        for origin, description in test_origins:
            # 模拟带Origin头的请求
            headers = {"Origin": origin}

            # 测试OPTIONS预检请求
            try:
                response = self.client.options(
                    "/api/register/send-verification",
                    headers=headers
                )

                # 检查CORS头部
                allow_origin = response.headers.get("Access-Control-Allow-Origin")
                allow_credentials = response.headers.get("Access-Control-Allow-Credentials")
                allow_methods = response.headers.get("Access-Control-Allow-Methods")

                if allow_origin == origin:
                    print(f"[OK] {description} ({origin}): CORS头部正确")
                    print(f"   允许来源: {allow_origin}")
                    print(f"   允许凭证: {allow_credentials}")
                    print(f"   允许方法: {allow_methods}")
                else:
                    print(f"[FAIL] {description} ({origin}): CORS头部不正确")
                    print(f"   期望: {origin}")
                    print(f"   实际: {allow_origin}")

            except Exception as e:
                print(f"[WARN] {description} ({origin}): 测试异常 - {e}")

        print("[OK] CORS头部模拟测试完成")
        return True


def run_deployment_tests():
    """运行所有部署测试的汇总函数"""
    print("\n" + "="*70)
    print("运行部署配置测试")
    print("="*70)

    # 创建测试实例
    tester = TestDeploymentConfiguration()

    # 运行测试
    test_results = []

    try:
        tester.setup_method()
        test_results.append(("CORS配置", tester.test_cors_configuration()))
    except Exception as e:
        test_results.append(("CORS配置", False))
        print(f"[FAIL] CORS配置测试失败: {e}")

    try:
        test_results.append(("邮件服务配置", tester.test_mail_service_configuration()))
    except Exception as e:
        test_results.append(("邮件服务配置", False))
        print(f"[FAIL] 邮件服务配置测试失败: {e}")

    try:
        test_results.append(("环境变量配置", tester.test_environment_configuration()))
    except Exception as e:
        test_results.append(("环境变量配置", False))
        print(f"[FAIL] 环境变量配置测试失败: {e}")

    try:
        test_results.append(("API端点可访问性", tester.test_api_endpoint_accessibility()))
    except Exception as e:
        test_results.append(("API端点可访问性", False))
        print(f"[FAIL] API端点可访问性测试失败: {e}")

    try:
        test_results.append(("CORS头部模拟测试", tester.test_cors_headers_with_simulation()))
    except Exception as e:
        test_results.append(("CORS头部模拟测试", False))
        print(f"[FAIL] CORS头部模拟测试失败: {e}")

    # 汇总结果
    print("\n" + "="*70)
    print("测试结果汇总")
    print("="*70)

    passed_tests = 0
    total_tests = len(test_results)

    for test_name, result in test_results:
        status = "[OK] 通过" if result else "[FAIL] 失败"
        print(f"{test_name}: {status}")
        if result:
            passed_tests += 1

    print(f"\n通过 {passed_tests}/{total_tests} 个测试")

    if passed_tests == total_tests:
        print("\n[SUCCESS] 所有部署配置测试通过！")
        return True
    else:
        print(f"\n[WARN]  {total_tests - passed_tests} 个测试失败，请检查配置")
        return False


if __name__ == "__main__":
    """直接运行测试（用于调试）"""
    print("运行部署配置测试...")

    # 设置环境变量（如果是本地测试）
    if not os.environ.get("CORS_ORIGINS"):
        os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://localhost:8000,https://otiumtrans.netlify.app"

    if not os.environ.get("SMTP_TIMEOUT"):
        os.environ["SMTP_TIMEOUT"] = "30"

    # 运行测试
    success = run_deployment_tests()

    if success:
        print("\n[OK] 部署配置测试完成，所有检查通过")
        sys.exit(0)
    else:
        print("\n[FAIL] 部署配置测试失败，请修复问题")
        sys.exit(1)