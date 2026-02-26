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
    """设置测试环境"""
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
    """测试数据库URL"""
    db_path = project_root / "data" / "test_otium.db"
    return f"sqlite:///{db_path}"


@pytest.fixture(scope="session")
def engine(test_database_url):
    """创建测试数据库引擎"""
    engine = create_engine(test_database_url, connect_args={"check_same_thread": False})

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    yield engine

    # 清理：删除所有表
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(engine):
    """创建测试数据库会话"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # 创建新会话
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def override_get_db(db_session):
    """重写get_db依赖"""

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
    """创建测试客户端"""
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
    """模拟Gemini API"""
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
    """模拟GPTZero API"""
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
    """模拟requests库"""
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
    """模拟Manus API"""
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
    """测试用户数据"""
    return {
        "username": "testuser",
        "password": "TestPassword123!",
        "email": "test@example.com",
        "is_admin": False,
    }


@pytest.fixture
def test_admin_data():
    """测试管理员数据"""
    return {
        "username": "testadmin",
        "password": "AdminPassword123!",
        "email": "admin@example.com",
        "is_admin": True,
    }


@pytest.fixture
def test_text_data():
    """测试文本数据"""
    return {
        "chinese": "深度学习是机器学习的一个分支，它试图模仿人脑的工作方式。",
        "english": "Deep learning is a branch of machine learning that attempts to mimic the way the human brain works.",
    }


@pytest.fixture
def test_directives():
    """测试精修指令"""
    return ["请改进语法", "使表达更正式", "优化段落结构"]


# ==========================================
# 助手函数
# ==========================================


def create_test_user(db: Session, user_data: dict):
    """创建测试用户"""
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
    """获取认证头"""
    return {"Authorization": f"Bearer {token}"}
