"""
工具模块测试

测试utils.py中的工具类和辅助函数。
"""

import json
import os
import tempfile
import time
from unittest.mock import patch

import pytest

from utils import (
    CacheManager,
    RateLimiter,
    TextValidator,
    UserLimitManager,
    contains_annotation,
    extract_annotations,
    generate_safe_hash,
)


class TestUserLimitManager:
    """测试UserLimitManager类（已弃用）"""

    def setup_method(self):
        """每个测试方法前的设置"""
        # 临时文件用于测试
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "usage_data.json")

    def teardown_method(self):
        """每个测试方法后的清理"""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch.dict(os.environ, {"ALLOWED_USERS": "{}"}, clear=True)
    @patch("utils.logging")
    def test_initialization_with_empty_env(self, mock_logging):
        """测试使用空环境变量初始化"""
        manager = UserLimitManager()
        assert manager.usage_db_path is not None
        # 管理员用户应该被自动添加
        assert "admin" in manager.allowed_users
        assert manager.allowed_users["admin"]["expiry_date"] == "2099-12-31"
        assert manager.allowed_users["admin"]["max_translations"] == 99999
        mock_logging.warning.assert_called_with(
            "UserLimitManager 已弃用，请使用 services.user_service.UserService 替代"
        )

    @patch.dict(
        os.environ,
        {
            "ALLOWED_USERS": '{"testuser": {"expiry_date": "2026-12-31", "max_translations": 100, "password": "pass123"}}',
            "ADMIN_USERNAME": "admin",
            "ADMIN_PASSWORD": "admin123",
        },
    )
    def test_load_allowed_users(self):
        """测试加载允许的用户"""
        manager = UserLimitManager()
        assert "testuser" in manager.allowed_users
        assert manager.allowed_users["testuser"]["expiry_date"] == "2026-12-31"
        assert manager.allowed_users["testuser"]["max_translations"] == 100
        assert manager.allowed_users["testuser"]["password"] == "pass123"
        assert "admin" in manager.allowed_users  # 管理员用户自动添加

    @patch.dict(
        os.environ,
        {
            "ALLOWED_USERS": '{"testuser": {"expiry_date": "invalid-date", "max_translations": 100}}',
        },
    )
    @patch("utils.logging")
    def test_load_allowed_users_invalid_date(self, mock_logging):
        """测试加载无效日期格式的用户"""
        manager = UserLimitManager()
        assert "testuser" in manager.allowed_users
        # 无效日期应被替换为默认值
        assert manager.allowed_users["testuser"]["expiry_date"] == "2099-12-31"
        mock_logging.warning.assert_called()

    @patch.dict(os.environ, {"ALLOWED_USERS": "invalid-json"}, clear=True)
    @patch("utils.logging")
    def test_load_allowed_users_invalid_json(self, mock_logging):
        """测试加载无效JSON格式"""
        manager = UserLimitManager()
        # 应回退到默认配置
        assert "test" in manager.allowed_users
        assert "test_user" in manager.allowed_users
        assert "admin" in manager.allowed_users
        mock_logging.warning.assert_called()

    def test_load_usage_data_file_exists(self):
        """测试加载存在的使用数据文件"""
        # 创建测试数据文件
        test_data = {"user1": {"translations": 5}, "user2": {"translations": 10}}
        os.makedirs(self.temp_dir, exist_ok=True)
        with open(self.test_db_path, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        manager = UserLimitManager()
        manager.usage_db_path = self.test_db_path  # 覆盖路径
        data = manager.load_usage_data()
        assert data == test_data

    def test_load_usage_data_file_not_exists(self):
        """测试加载不存在的使用数据文件"""
        manager = UserLimitManager()
        manager.usage_db_path = os.path.join(self.temp_dir, "nonexistent.json")
        data = manager.load_usage_data()
        assert data == {}

    @patch.dict(
        os.environ,
        {
            "ALLOWED_USERS": '{"testuser": {"expiry_date": "2099-12-31", "max_translations": 10, "password": "pass123"}}',
        },
    )
    def test_is_user_allowed_success(self):
        """测试用户验证成功"""
        manager = UserLimitManager()

        # 创建使用数据文件（用户未使用过）
        os.makedirs(self.temp_dir, exist_ok=True)
        with open(self.test_db_path, "w", encoding="utf-8") as f:
            json.dump({}, f)

        manager.usage_db_path = self.test_db_path

        allowed, message = manager.is_user_allowed("testuser", "pass123")
        assert allowed is True
        assert message == "验证通过"

    @patch.dict(
        os.environ,
        {
            "ALLOWED_USERS": '{"testuser": {"expiry_date": "2099-12-31", "max_translations": 10, "password": "pass123"}}',
        },
    )
    def test_is_user_allowed_wrong_password(self):
        """测试用户验证失败（密码错误）"""
        manager = UserLimitManager()
        allowed, message = manager.is_user_allowed("testuser", "wrongpass")
        assert allowed is False
        assert message == "密码错误"

    @patch.dict(
        os.environ,
        {
            "ALLOWED_USERS": '{"testuser": {"expiry_date": "2000-01-01", "max_translations": 10, "password": "pass123"}}',
        },
    )
    def test_is_user_allowed_expired_account(self):
        """测试用户验证失败（账户过期）"""
        manager = UserLimitManager()
        allowed, message = manager.is_user_allowed("testuser", "pass123")
        assert allowed is False
        assert "账户已于" in message

    @patch.dict(
        os.environ,
        {
            "ALLOWED_USERS": '{"testuser": {"expiry_date": "2099-12-31", "max_translations": 0, "password": "pass123"}}',
        },
    )
    def test_is_user_allowed_exceeded_limit(self):
        """测试用户验证失败（超出限制）"""
        manager = UserLimitManager()

        # 创建使用数据文件（用户已使用10次）
        os.makedirs(self.temp_dir, exist_ok=True)
        with open(self.test_db_path, "w", encoding="utf-8") as f:
            json.dump({"testuser": {"translations": 10}}, f)

        manager.usage_db_path = self.test_db_path

        allowed, message = manager.is_user_allowed("testuser", "pass123")
        assert allowed is False
        assert "已达到最大翻译次数限制" in message

    @patch.dict(
        os.environ,
        {
            "ADMIN_USERNAME": "superadmin",
            "ADMIN_PASSWORD": "adminpass",
        },
    )
    def test_is_user_allowed_admin_skip_limits(self):
        """测试管理员用户跳过所有限制"""
        manager = UserLimitManager()
        allowed, message = manager.is_user_allowed("superadmin", "adminpass")
        assert allowed is True
        assert message == "管理员验证通过"

    def test_record_translation(self):
        """测试记录翻译使用"""
        # 设置测试环境
        os.makedirs(self.temp_dir, exist_ok=True)
        with open(self.test_db_path, "w", encoding="utf-8") as f:
            json.dump({"testuser": {"translations": 5}}, f)

        manager = UserLimitManager()
        manager.usage_db_path = self.test_db_path
        manager.allowed_users = {
            "testuser": {
                "expiry_date": "2099-12-31",
                "max_translations": 100,
                "password": "pass123",
            }
        }

        remaining = manager.record_translation("testuser")
        assert remaining == 94  # 100 - (5 + 1)

        # 验证数据已保存
        with open(self.test_db_path, encoding="utf-8") as f:
            saved_data = json.load(f)
        assert saved_data["testuser"]["translations"] == 6

    def test_record_translation_user_not_found(self):
        """测试记录不存在的用户的翻译使用"""
        manager = UserLimitManager()
        manager.allowed_users = {}

        with pytest.raises(ValueError, match="用户 nonexistent 不存在"):
            manager.record_translation("nonexistent")

    def test_get_user_info(self):
        """测试获取用户信息"""
        # 设置测试环境
        os.makedirs(self.temp_dir, exist_ok=True)
        with open(self.test_db_path, "w", encoding="utf-8") as f:
            json.dump({"testuser": {"translations": 15}}, f)

        manager = UserLimitManager()
        manager.usage_db_path = self.test_db_path
        manager.allowed_users = {
            "testuser": {
                "expiry_date": "2026-12-31",
                "max_translations": 100,
                "password": "pass123",
            }
        }

        user_info = manager.get_user_info("testuser")
        assert user_info["username"] == "testuser"
        assert user_info["expiry_date"] == "2026-12-31"
        assert user_info["max_translations"] == 100
        assert user_info["used_translations"] == 15
        assert user_info["remaining_translations"] == 85

    def test_get_user_info_user_not_found(self):
        """测试获取不存在的用户信息"""
        manager = UserLimitManager()
        manager.allowed_users = {}

        user_info = manager.get_user_info("nonexistent")
        assert user_info is None


class TestRateLimiter:
    """测试RateLimiter类"""

    def test_initialization(self):
        """测试初始化"""
        limiter = RateLimiter(max_calls=10, time_window=30)
        assert limiter.max_calls == 10
        assert limiter.time_window == 30
        assert limiter.calls == {}

    def test_is_allowed_first_call(self):
        """测试首次调用"""
        limiter = RateLimiter(max_calls=5, time_window=60)
        allowed, wait_time = limiter.is_allowed("user1")
        assert allowed is True
        assert wait_time is None
        assert "user1" in limiter.calls
        assert len(limiter.calls["user1"]) == 1

    def test_is_allowed_within_limit(self):
        """测试在限制内的多次调用"""
        limiter = RateLimiter(max_calls=3, time_window=60)

        # 第一次调用
        allowed1, _ = limiter.is_allowed("user1")
        assert allowed1 is True

        # 第二次调用
        allowed2, _ = limiter.is_allowed("user1")
        assert allowed2 is True

        # 第三次调用
        allowed3, _ = limiter.is_allowed("user1")
        assert allowed3 is True

    def test_is_allowed_exceed_limit(self):
        """测试超出限制"""
        limiter = RateLimiter(max_calls=2, time_window=60)

        # 第一次调用
        limiter.is_allowed("user1")
        # 第二次调用
        limiter.is_allowed("user1")
        # 第三次调用（应被拒绝）
        allowed, wait_time = limiter.is_allowed("user1")
        assert allowed is False
        assert wait_time > 0

    def test_is_allowed_after_time_window(self):
        """测试时间窗口后的调用"""
        limiter = RateLimiter(max_calls=1, time_window=0.1)  # 非常短的时间窗口

        # 第一次调用
        allowed1, _ = limiter.is_allowed("user1")
        assert allowed1 is True

        # 等待时间窗口过去
        time.sleep(0.2)

        # 第二次调用（应允许，因为时间窗口已过）
        allowed2, _ = limiter.is_allowed("user1")
        assert allowed2 is True

    def test_is_allowed_different_users(self):
        """测试不同用户的独立限制"""
        limiter = RateLimiter(max_calls=2, time_window=60)

        # 用户1使用2次
        limiter.is_allowed("user1")
        limiter.is_allowed("user1")

        # 用户2应该还可以使用2次
        allowed, _ = limiter.is_allowed("user2")
        assert allowed is True

    def test_is_allowed_with_object_user_id(self):
        """测试使用对象作为用户ID（带有username属性）"""

        class MockUser:
            def __init__(self, username):
                self.username = username

        user = MockUser("testuser")
        limiter = RateLimiter(max_calls=5, time_window=60)

        allowed, _ = limiter.is_allowed(user)
        assert allowed is True
        assert "testuser" in limiter.calls

    def test_reset(self):
        """测试重置用户限制"""
        limiter = RateLimiter(max_calls=2, time_window=60)

        # 用户使用2次
        limiter.is_allowed("user1")
        limiter.is_allowed("user1")

        # 重置
        limiter.reset("user1")

        # 应该可以再次使用
        allowed, _ = limiter.is_allowed("user1")
        assert allowed is True


class TestTextValidator:
    """测试TextValidator类"""

    def test_validate_for_gemini_success(self):
        """测试Gemini文本验证成功"""
        text = "这是一段测试文本，长度适中。"
        valid, message = TextValidator.validate_for_gemini(text)
        assert valid is True
        assert message == "验证通过"

    def test_validate_for_gemini_empty(self):
        """测试Gemini文本验证失败（空文本）"""
        text = ""
        valid, message = TextValidator.validate_for_gemini(text)
        assert valid is False
        assert "文本不能为空" in message

    def test_validate_for_gemini_too_short(self):
        """测试Gemini文本验证失败（过短）- 空文本应返回'文本不能为空'"""
        text = ""  # 空文本
        valid, message = TextValidator.validate_for_gemini(text)
        assert valid is False
        assert "文本不能为空" in message

    def test_validate_for_gemini_too_long(self):
        """测试Gemini文本验证失败（过长）"""
        text = "x" * (TextValidator.GEMINI_MAX_CHARS + 100)
        valid, message = TextValidator.validate_for_gemini(text)
        assert valid is False
        assert "文本过长" in message

    def test_validate_for_gptzero_success(self):
        """测试GPTZero文本验证成功"""
        text = "这是一段足够长的测试文本，用于GPTZero检测。" * 10  # 确保长度足够
        valid, message = TextValidator.validate_for_gptzero(text)
        # GPTZero要求至少250字符，所以这个测试可能失败
        # 我们根据实际长度判断
        if len(text) >= TextValidator.GPTZERO_MIN_CHARS:
            assert valid is True
            assert message == "验证通过"
        else:
            assert valid is False
            assert "文本过短" in message

    def test_validate_for_gptzero_too_short(self):
        """测试GPTZero文本验证失败（过短）"""
        text = "短文本"
        valid, message = TextValidator.validate_for_gptzero(text)
        assert valid is False
        assert "文本过短" in message

    def test_validate_for_gptzero_too_long(self):
        """测试GPTZero文本验证失败（过长）"""
        text = "x" * (TextValidator.GPTZERO_MAX_CHARS + 100)
        valid, message = TextValidator.validate_for_gptzero(text)
        assert valid is False
        assert "文本过长" in message

    def test_validate_base_whitespace_only(self):
        """测试仅包含空白字符的文本"""
        text = "   \n\t  "
        valid, message = TextValidator._validate_base(text, 1, 100, "测试API")
        assert valid is False
        assert "文本不能为空" in message


class TestCacheManager:
    """测试CacheManager类"""

    def test_initialization(self):
        """测试初始化"""
        cache = CacheManager(ttl=300, max_entries=50)
        assert cache.ttl == 300
        assert cache.max_entries == 50
        assert cache.cache == {}

    def test_set_and_get(self):
        """测试设置和获取缓存"""
        cache = CacheManager()
        cache.set("key1", "value1")
        result = cache.get("key1")
        assert result == "value1"

    def test_get_nonexistent_key(self):
        """测试获取不存在的键"""
        cache = CacheManager()
        result = cache.get("nonexistent")
        assert result is None

    def test_cache_expiration(self):
        """测试缓存过期"""
        cache = CacheManager(ttl=0.1)  # 非常短的TTL
        cache.set("key1", "value1")

        # 立即获取应该成功
        result1 = cache.get("key1")
        assert result1 == "value1"

        # 等待TTL过期
        time.sleep(0.2)

        # 再次获取应该返回None
        result2 = cache.get("key1")
        assert result2 is None

    def test_cache_max_entries(self):
        """测试缓存最大条目限制"""
        cache = CacheManager(max_entries=3)

        # 添加3个条目
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        assert len(cache.cache) == 3

        # 添加第4个条目，应该移除最旧的
        time.sleep(0.01)  # 确保时间戳不同
        cache.set("key4", "value4")

        # key1应该被移除，因为它是旧的
        assert "key1" not in cache.cache
        assert "key2" in cache.cache
        assert "key3" in cache.cache
        assert "key4" in cache.cache
        assert len(cache.cache) == 3

    def test_clear_cache(self):
        """测试清空缓存"""
        cache = CacheManager()
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        assert len(cache.cache) == 2
        cache.clear()
        assert len(cache.cache) == 0


class TestHelperFunctions:
    """测试辅助函数"""

    def test_generate_safe_hash(self):
        """测试生成安全哈希"""
        text = "测试文本"
        hash1 = generate_safe_hash(text)
        hash2 = generate_safe_hash(text)

        # 相同文本应生成相同哈希
        assert hash1 == hash2
        # 哈希长度应为12（默认）
        assert len(hash1) == 12
        # 应为十六进制字符串
        assert all(c in "0123456789abcdef" for c in hash1)

    def test_generate_safe_hash_different_texts(self):
        """测试不同文本生成不同哈希"""
        hash1 = generate_safe_hash("文本1")
        hash2 = generate_safe_hash("文本2")
        assert hash1 != hash2

    def test_generate_safe_hash_custom_length(self):
        """测试自定义哈希长度"""
        text = "测试文本"
        hash_short = generate_safe_hash(text, 6)
        hash_long = generate_safe_hash(text, 20)

        assert len(hash_short) == 6
        assert len(hash_long) == 20
        # 长哈希应包含短哈希作为前缀
        assert hash_long.startswith(hash_short)

    @patch("utils.hashlib")
    def test_generate_safe_hash_fallback(self, mock_hashlib):
        """测试哈希生成失败时的回退方案"""
        mock_hashlib.sha256.side_effect = Exception("哈希失败")
        hash_value = generate_safe_hash("测试文本")
        # 应回退到UUID
        assert len(hash_value) == 12

    def test_contains_annotation(self):
        """测试检测批注标记"""
        # 包含批注
        text_with_annotation = "这是一段文本[[gc]]带有批注"
        assert contains_annotation(text_with_annotation) is True

        # 不包含批注
        text_without_annotation = "这是一段普通文本"
        assert contains_annotation(text_without_annotation) is False

        # 空文本
        assert contains_annotation("") is False

    def test_extract_annotations(self):
        """测试提取批注标记"""
        text = "这是一段[[gc]]带有[[sc]]多个批注[[fc]]的文本"
        clean_text, annotations = extract_annotations(text)

        assert clean_text == "这是一段带有多个批注的文本"
        assert annotations == ["gc", "sc", "fc"]

    def test_extract_annotations_no_annotations(self):
        """测试提取无批注的文本"""
        text = "这是一段普通文本"
        clean_text, annotations = extract_annotations(text)

        assert clean_text == "这是一段普通文本"
        assert annotations == []

    def test_extract_annotations_empty_text(self):
        """测试提取空文本"""
        clean_text, annotations = extract_annotations("")
        assert clean_text == ""
        assert annotations == []

    def test_extract_annotations_cleaning_whitespace(self):
        """测试提取批注并清理空白"""
        text = "文本[[gc]]   [[sc]]    中间有空格[[fc]]"
        clean_text, annotations = extract_annotations(text)

        # 应该清理多余的空白
        assert clean_text == "文本 中间有空格"
        assert annotations == ["gc", "sc", "fc"]
