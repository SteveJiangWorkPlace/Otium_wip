"""
数据库模型包

SQLAlchemy ORM模型定义，包含用户管理、使用统计和翻译记录等数据模型。
此包提供数据库操作的抽象层，支持SQLite和PostgreSQL数据库。

Modules:
    database: 数据库模型核心定义，包含User、UserUsage、TranslationRecord等模型类

Classes:
    User: 用户账户模型，包含认证信息和基本资料
    UserUsage: 用户使用统计模型，跟踪翻译和AI检测次数
    TranslationRecord: 翻译记录模型，详细记录用户操作历史
    Base: SQLAlchemy声明式基类，所有模型的共同基类

Functions:
    get_database_url: 获取数据库连接URL（支持多数据库类型）
    get_engine: 获取数据库引擎单例
    get_session_local: 创建数据库会话工厂
    init_database: 初始化数据库表结构
    ensure_admin_user_exists: 确保管理员用户存在
    hash_password: 密码哈希函数（SHA256）
    verify_password: 密码验证函数

Notes:
    - 使用SQLAlchemy ORM进行数据库操作
    - 支持关系型数据库（SQLite用于开发，PostgreSQL用于生产）
    - 所有模型继承自Base类，确保一致的元数据配置
    - 包含数据库迁移支持（通过Alembic）
"""
