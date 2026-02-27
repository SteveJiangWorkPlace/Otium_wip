"""
测试包

后端应用程序的单元测试和集成测试。
包含API端点、业务逻辑、工具类和数据库操作的测试用例。

Test Modules:
    test_health: 健康检查端点测试
    test_auth: 用户认证和授权测试
    test_api: 主要API功能测试（文本处理、翻译、AI检测等）
    test_utils: 工具类和辅助函数测试
    test_schemas: Pydantic数据模型验证测试

Test Categories:
    - 单元测试：测试独立函数和类的功能
    - 集成测试：测试模块间交互和API端点
    - 功能测试：测试完整的业务流程
    - 性能测试：测试系统性能和响应时间

Testing Tools:
    - pytest: 主要的测试框架
    - pytest-cov: 代码覆盖率分析
    - pytest-asyncio: 异步测试支持
    - unittest.mock: 模拟外部依赖

Notes:
    - 所有测试文件以test_前缀命名
    - 使用pytest fixtures进行测试数据准备
    - 测试数据库使用内存SQLite，避免影响生产数据
    - 测试覆盖率目标：>80%
    - 测试标记：@pytest.mark.unit, @pytest.mark.integration, @pytest.mark.slow
"""
