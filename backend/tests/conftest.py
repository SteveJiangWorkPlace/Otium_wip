"""
pytest配置文件

定义测试夹具、配置测试环境、设置测试数据库等。
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from main import app  # noqa: E402
from models.database import Base, get_db  # noqa: E402

# ==========================================
# 测试配置
# ==========================================


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    设置测试环境变量，确保测试隔离。

    Sets:
        - ENVIRONMENT: "testing"
        - DATABASE_PATH: 指向测试数据库路径

    Yields:
        None: 仅在测试前后修改环境变量

    Scope:
        session: 整个测试会话期间生效

    Note:
        - 测试完成后恢复原始环境变量
        - 确保数据目录存在
    """
    # 修改配置为测试环境
    original_env = os.environ.get("ENVIRONMENT", "")
    os.environ["ENVIRONMENT"] = "testing"

    # 设置测试数据库路径
    os.environ["DATABASE_PATH"] = str(project_root / "data" / "test_otium.db")

    # 确保数据目录存在
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)

    yield

    # 恢复原始环境
    if original_env:
        os.environ["ENVIRONMENT"] = original_env
    else:
        os.environ.pop("ENVIRONMENT", None)


# ==========================================
# 数据库测试夹具
# ==========================================


@pytest.fixture(scope="session")
def test_database_url():
    """
    提供测试数据库的SQLite连接URL。

    Returns:
        str: SQLite数据库URL格式：sqlite:///{path_to_test_db}

    Scope:
        session: 整个测试会话期间不变
    """
    db_path = project_root / "data" / "test_otium.db"
    return f"sqlite:///{db_path}"


@pytest.fixture(scope="session")
def engine(test_database_url):
    """
    创建SQLAlchemy引擎并初始化测试数据库表。

    Args:
        test_database_url: 来自test_database_url fixture的数据库URL

    Yields:
        sqlalchemy.engine.Engine: 配置好的数据库引擎

    Scope:
        session: 在整个测试会话中重用

    Note:
        - 在yield前创建所有表
        - 在yield后删除所有表，确保测试隔离
    """
    engine = create_engine(test_database_url, connect_args={"check_same_thread": False})

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    yield engine

    # 清理：删除所有表
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(engine):
    """
    为每个测试函数提供独立的数据库会话。

    Args:
        engine: 来自engine fixture的数据库引擎

    Yields:
        sqlalchemy.orm.Session: 配置好的数据库会话

    Scope:
        function: 每个测试函数获得新会话

    Note:
        - 测试完成后自动关闭会话
        - 支持事务回滚
    """
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # 创建新会话
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def override_get_db(db_session):
    """
    重写FastAPI的get_db依赖，使用测试数据库会话。

    Args:
        db_session: 来自db_session fixture的数据库会话

    Returns:
        function: 可调用函数，用于FastAPI依赖注入

    Scope:
        function: 每个测试函数使用独立的依赖

    Note:
        - 替换主应用的数据库连接为测试数据库
        - 测试后自动清理依赖重写
    """

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    return _override_get_db


# ==========================================
# FastAPI应用测试夹具
# ==========================================


@pytest.fixture(scope="function")
def test_client(override_get_db):
    """
    创建FastAPI测试客户端，用于API端点测试。

    Args:
        override_get_db: 来自override_get_db fixture的数据库依赖

    Yields:
        fastapi.testclient.TestClient: 配置好的测试客户端

    Scope:
        function: 每个测试函数获得独立的客户端

    Note:
        - 自动设置测试数据库依赖
        - 测试后清理依赖重写，避免影响其他测试
    """
    # 重写get_db依赖
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    # 清理重写
    app.dependency_overrides.clear()


# ==========================================
# 模拟外部API的夹具
# ==========================================


@pytest.fixture(scope="function")
def mock_gemini_api():
    """
    模拟Google Gemini AI API，用于测试AI功能。

    Yields:
        unittest.mock.MagicMock: 模拟的GenerativeModel实例

    Scope:
        function: 每个测试函数使用独立的模拟

    Note:
        - 配置返回预定义的测试响应
        - 避免实际调用外部API
        - 确保测试的可靠性和速度
    """
    with patch("api_services.google.generativeai.GenerativeModel") as mock_model:
        mock_instance = MagicMock()
        mock_model.return_value = mock_instance

        # 配置模拟响应
        mock_response = MagicMock()
        mock_response.text = "这是一个模拟的Gemini API响应。"
        mock_instance.generate_content.return_value = mock_response

        yield mock_instance


@pytest.fixture(scope="function")
def mock_gptzero_api():
    """
    模拟GPTZero AI检测API，用于测试AI文本检测功能。

    Yields:
        unittest.mock.MagicMock: 模拟的requests.post函数

    Scope:
        function: 每个测试函数使用独立的模拟

    Note:
        - 返回预定义的检测结果（likely_human）
        - 模拟HTTP 200响应状态
        - 避免实际调用外部API
    """
    with patch("api_services.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "documents": [
                {
                    "average_generated_prob": 0.15,
                    "completely_generated_prob": 0.05,
                    "overall_burstiness": 0.25,
                    "paragraphs": [],
                    "sentences": [],
                    "summary": "likely_human",
                    "word_count": 100,
                }
            ]
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        yield mock_post


@pytest.fixture(scope="function")
def mock_requests():
    """
    模拟requests库，用于测试HTTP请求功能。

    Yields:
        unittest.mock.MagicMock: 模拟的requests模块

    Scope:
        function: 每个测试函数使用独立的模拟

    Note:
        - 模拟get()和post()方法，返回HTTP 200响应
        - 配置空JSON响应作为默认值
        - 避免实际网络请求
    """
    with patch("api_services.requests") as mock_requests:
        # 配置默认响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_requests.get.return_value = mock_response
        mock_requests.post.return_value = mock_response

        yield mock_requests


@pytest.fixture(scope="function")
def mock_manus_api():
    """
    模拟Manus AI API，用于测试异步AI任务功能。

    Yields:
        unittest.mock.MagicMock: 模拟的requests.post函数

    Scope:
        function: 每个测试函数使用独立的模拟

    Note:
        - 返回测试任务ID和processing状态
        - 模拟HTTP 200响应状态
        - 避免实际调用外部API
    """
    with patch("api_services.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "task_id": "test_task_123",
            "status": "processing",
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        yield mock_post


# ==========================================
# 测试数据和助手函数
# ==========================================


@pytest.fixture
def test_user_data():
    """
    提供测试普通用户数据。

    Returns:
        dict: 包含普通用户信息的字典，包括用户名、密码、邮箱、角色等

    Note:
        - 密码符合安全要求（包含大小写字母、数字、符号）
        - 邮箱使用示例域名
        - is_admin设置为False
    """
    return {
        "username": "testuser",
        "password": "TestPassword123!",
        "email": "test@example.com",
        "is_admin": False,
    }


@pytest.fixture
def test_admin_data():
    """
    提供测试管理员用户数据。

    Returns:
        dict: 包含管理员用户信息的字典，包括用户名、密码、邮箱、角色等

    Note:
        - 密码符合安全要求（包含大小写字母、数字、符号）
        - 邮箱使用示例域名
        - is_admin设置为True
    """
    return {
        "username": "testadmin",
        "password": "AdminPassword123!",
        "email": "admin@example.com",
        "is_admin": True,
    }


@pytest.fixture
def test_text_data():
    """
    提供中英文测试文本数据。

    Returns:
        dict: 包含中英文文本对的字典，用于翻译和文本处理测试

    Note:
        - 中文文本：关于深度学习的学术描述
        - 英文文本：对应的英文翻译
        - 可用于测试翻译、纠错、AI检测等功能
    """
    return {
        "chinese": "深度学习是机器学习的一个分支，它试图模仿人脑的工作方式。",
        "english": "Deep learning is a branch of machine learning that attempts to mimic the way the human brain works.",
    }


@pytest.fixture
def test_directives():
    """
    提供文本精修指令列表，用于测试文本优化功能。

    Returns:
        list[str]: 包含文本精修指令的列表

    Note:
        - 指令包括语法改进、表达正式化、结构优化等
        - 用于测试文本精修和指令跟随功能
    """
    return ["请改进语法", "使表达更正式", "优化段落结构"]


# ==========================================
# 助手函数
# ==========================================


def create_test_user(db: Session, user_data: dict):
    """
    在测试数据库中创建用户记录。

    Args:
        db (sqlalchemy.orm.Session): 数据库会话
        user_data (dict): 用户数据字典，包含用户名、密码、邮箱等信息

    Returns:
        models.database.User: 创建的User对象

    Note:
        - 自动对密码进行哈希处理
        - 设置默认的最大翻译次数（100）和过期日期（2099-12-31）
        - 提交更改到数据库并刷新对象
    """
    from models.database import User
    from user_services.user_service import hash_password

    user = User(
        username=user_data["username"],
        password_hash=hash_password(user_data["password"]),
        email=user_data.get("email", f"{user_data['username']}@example.com"),
        is_admin=user_data.get("is_admin", False),
        max_translations=100,
        used_translations=0,
        expiry_date="2099-12-31",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_auth_headers(token: str):
    """
    根据JWT令牌生成HTTP认证头部。

    Args:
        token (str): JWT认证令牌

    Returns:
        dict: 包含Authorization头的字典，格式为{"Authorization": "Bearer {token}"}

    Note:
        - 用于测试需要认证的API端点
        - 符合标准的Bearer令牌格式
    """
    return {"Authorization": f"Bearer {token}"}
