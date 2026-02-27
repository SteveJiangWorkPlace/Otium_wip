"""
Alembic数据库迁移环境配置文件

此文件由Alembic迁移工具自动生成和维护，提供数据库迁移执行环境。
包含数据库连接配置、模型元数据引用和迁移执行逻辑。

主要功能：
1. 配置数据库连接（从config.get_database_url动态获取）
2. 设置SQLAlchemy模型元数据用于自动生成迁移
3. 提供迁移执行上下文和日志配置
4. 支持开发和生产环境的不同数据库配置

文件结构：
- 路径设置：添加项目根目录到Python路径
- 模型导入：导入Base模型和目标元数据
- 配置读取：从alembic.ini文件读取配置
- 引擎创建：根据配置创建数据库引擎
- 迁移执行：提供运行迁移的上下文

注意事项：
- 此文件由Alembic维护，手动修改需谨慎
- 数据库URL通过get_database_url()动态获取
- 目标元数据来自models.database.Base.metadata
- 支持SQLite（开发）和PostgreSQL（生产）
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# 添加项目根目录到Python路径，以便导入我们的模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入我们的数据库配置和模型
from models.database import Base, get_database_url  # noqa: E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # 使用动态数据库URL，而不是配置文件中的固定URL
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # 创建配置字典，设置动态数据库URL
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
