"""
Otium 后端包

FastAPI后端应用程序包，包含API路由、业务逻辑、数据库模型和外部服务集成。
此包初始化文件确保正确的模块导入和包结构。

Modules:
    main: 主应用文件，定义API路由和FastAPI应用初始化
    config: 配置管理，环境变量处理和设置验证
    schemas: Pydantic数据模型，API请求/响应格式定义
    exceptions: 自定义异常处理和错误响应
    utils: 工具类（UserLimitManager、RateLimiter、TextValidator等）
    prompts: AI提示词构建系统（模板、缓存、监控）
    prompt_templates: 提示词模板系统（原始备份和优化版本）
    prompt_cache: 提示词缓存管理器（LRU策略、TTL）
    prompt_monitor: 提示词性能监控系统
    api_services: 外部API集成（Gemini AI、GPTZero）
    models: 数据库模型和ORM定义
    user_services: 用户认证、注册和管理服务

Notes:
    - 包结构遵循关注点分离原则，每个模块有单一职责
    - 所有模块通过此__init__.py文件进行组织和导入
    - 支持Python 3.9+，使用类型注解提高代码可读性
"""
