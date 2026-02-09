"""
工具模块

包含各种工具类和辅助函数：
- UserLimitManager: 用户限制管理
- RateLimiter: 速率限制器
- TextValidator: 文本验证器
- CacheManager: 缓存管理
- 辅助函数：安全哈希生成、批注处理等
"""

import json
import os
import time
import threading
import logging
import hashlib
import uuid
from datetime import datetime
from collections import deque
from typing import Dict, List, Any, Optional, Tuple

from config import settings, is_expired


# ==========================================
# 用户限制管理
# ==========================================

class UserLimitManager:
    """管理用户使用限制，包括时间和使用次数

    注意：此类已弃用，请使用 services.user_service.UserService 替代。
    新版本使用数据库存储用户数据，支持密码哈希和更好的数据持久化。
    """

    def __init__(self):
        logging.warning("UserLimitManager 已弃用，请使用 services.user_service.UserService 替代")

        # 修复文件存储路径问题
        self.usage_db_path = os.environ.get("USAGE_DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "usage_data.json"))
        self.allowed_users = {}
        self.load_allowed_users()
        # 线程锁，防止同一进程内的并发访问
        self._lock = threading.RLock()
        logging.info(f"用户数据存储路径: {self.usage_db_path}")

    def load_allowed_users(self):
        """从环境变量或配置文件加载允许的用户"""
        try:
            # 尝试从环境变量 ALLOWED_USERS 获取用户配置
            # 如果环境变量不存在，则使用空的 JSON 对象 "{}" 作为默认值
            users_env = os.environ.get("ALLOWED_USERS", "{}")

            # 将 JSON 字符串解析为 Python 字典
            users_data = json.loads(users_env)

            # 遍历所有用户数据
            for username, data in users_data.items():
                # 获取用户过期日期，如果不存在则默认为 2099-12-31
                expiry_date = data.get("expiry_date", "2099-12-31")

                # 验证日期格式是否正确
                try:
                    datetime.strptime(expiry_date, '%Y-%m-%d')
                except ValueError:
                    # 如果日期格式不正确，记录警告并使用默认值
                    logging.warning(f"用户 {username} 的过期日期格式不正确: {expiry_date}，设置为默认值")
                    expiry_date = "2099-12-31"

                # 将用户信息添加到 allowed_users 字典中
                self.allowed_users[username] = {
                    "expiry_date": expiry_date,
                    "max_translations": data.get("max_translations", 1000),  # 默认翻译次数限制为 1000
                    "password": data.get("password", "")  # 默认密码为空字符串
                }
        except Exception as e:
            # 如果解析过程中出现任何错误，记录警告并使用默认配置
            logging.warning(f"无法加载用户配置，使用默认配置: {e}")
            self.allowed_users = {
                "test": {
                    "expiry_date": "2099-12-31",
                    "max_translations": 10,
                    "password": "test123"
                },
                "test_user": {
                    "expiry_date": "2026-12-31",
                    "max_translations": 1000,
                    "password": "test123"
                }
            }

        # 自动添加管理员用户（使用环境变量或默认值）
        admin_username = os.environ.get("ADMIN_USERNAME", "admin")
        admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")

        # 确保管理员用户总是存在
        if admin_username not in self.allowed_users:
            self.allowed_users[admin_username] = {
                "expiry_date": "2099-12-31",
                "max_translations": 99999,  # 管理员有非常大的翻译次数限制
                "password": admin_password
            }
            logging.info(f"自动添加管理员用户: {admin_username}")
        else:
            # 如果已存在，确保密码和配置正确
            self.allowed_users[admin_username]["password"] = admin_password
            self.allowed_users[admin_username]["expiry_date"] = "2099-12-31"
            self.allowed_users[admin_username]["max_translations"] = 99999
            logging.info(f"更新管理员用户配置: {admin_username}")

    def load_usage_data(self):
        """加载使用数据"""
        try:
            if os.path.exists(self.usage_db_path):
                logging.info(f"从文件加载使用数据: {self.usage_db_path}")
                with open(self.usage_db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logging.info(f"成功加载 {len(data)} 个用户的使用数据")
                    return data
            else:
                logging.info(f"使用数据文件不存在: {self.usage_db_path}，返回空数据")
                return {}
        except Exception as e:
            logging.error(f"加载使用数据失败: {str(e)}", exc_info=True)
            return {}

    def save_usage_data(self, data):
        """保存使用数据（兼容旧版本，新代码请使用_atomic_save_usage_data）"""
        try:
            # 确保目录存在
            dir_path = os.path.dirname(self.usage_db_path)
            if dir_path:  # 如果目录路径不为空
                os.makedirs(dir_path, exist_ok=True)
                logging.info(f"确保目录存在: {dir_path}")

            logging.info(f"正在保存使用数据到: {self.usage_db_path}")
            with open(self.usage_db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logging.info(f"使用数据保存成功，包含 {len(data)} 个用户的使用记录")
            return True
        except Exception as e:
            logging.error(f"保存使用数据失败: {str(e)}", exc_info=True)
            return False

    def _atomic_save_usage_data(self, data):
        """原子性保存使用数据，使用文件锁防止多进程并发"""
        lock_file = self.usage_db_path + ".lock"
        temp_file = self.usage_db_path + ".tmp"
        max_retries = 3
        retry_delay = 0.1  # 秒

        for attempt in range(max_retries):
            try:
                # 尝试创建锁文件（独占创建）
                lock_fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                # 成功获取锁
                try:
                    # 确保目录存在
                    dir_path = os.path.dirname(self.usage_db_path)
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)

                    # 写入临时文件
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

                    # 原子性重命名（POSIX和Windows都保证原子性）
                    os.replace(temp_file, self.usage_db_path)

                    logging.info(f"原子保存成功，包含 {len(data)} 个用户的使用记录")
                    return
                finally:
                    # 释放锁：关闭文件描述符并删除锁文件
                    os.close(lock_fd)
                    try:
                        os.unlink(lock_file)
                    except:
                        pass

            except (OSError, IOError) as e:
                # 锁文件已存在，表示其他进程正在操作
                if attempt < max_retries - 1:
                    logging.debug(f"等待文件锁，重试 {attempt + 1}/{max_retries}")
                    time.sleep(retry_delay)
                else:
                    logging.warning(f"无法获取文件锁，使用线程锁保护的单进程保存")
                    # 降级方案：使用线程锁保护的标准保存
                    with self._lock:
                        self.save_usage_data(data)
                    return
            except Exception as e:
                logging.error(f"原子保存失败: {str(e)}", exc_info=True)
                raise RuntimeError(f"原子保存失败: {str(e)}")

    def is_user_allowed(self, username, password=None):
        """检查用户是否被允许使用"""
        # 检查是否是管理员（完全跳过所有限制）
        admin_username = os.environ.get("ADMIN_USERNAME", "admin")
        if username == admin_username:
            logging.info(f"管理员用户 {username} 跳过所有限制检查")
            return True, "管理员验证通过"

        logging.info(f"=== 登录验证开始 ===")
        logging.info(f"用户名: {username}")
        logging.info(f"输入密码: {'*****' if password else 'None'}")
        logging.info(f"所有用户: {list(self.allowed_users.keys())}")

        if username not in self.allowed_users:
            logging.error(f"用户不存在: {username}")
            return False, "用户不存在"

        user_data = self.allowed_users[username]
        logging.info(f"用户数据: {user_data}")

        if password is not None and user_data.get("password", "") != password:
            logging.error(f"密码不匹配！输入: '{password}', 存储: '{user_data.get('password', '')}'")
            return False, "密码错误"

        logging.info(f"密码验证通过！")

        # 检查账户有效期
        expiry_date_str = user_data.get('expiry_date', '2099-12-31')
        logging.info(f"检查账户有效期: {expiry_date_str}")

        if is_expired(expiry_date_str):
            logging.error(f"账户已过期: {expiry_date_str}")
            return False, f"账户已于 {expiry_date_str} 过期"

        logging.info("账户有效期检查通过")

        usage_data = self.load_usage_data()
        user_usage = usage_data.get(username, {"translations": 0})
        used_translations = user_usage["translations"]
        max_translations = user_data["max_translations"]
        logging.info(f"用户使用量检查: 已使用 {used_translations}/{max_translations} 次翻译")
        if used_translations >= max_translations:
            return False, f"已达到最大翻译次数限制 ({max_translations})"

        return True, "验证通过"

    def record_translation(self, username):
        """记录一次翻译使用，使用线程锁确保原子性"""
        # 添加类型检查和转换
        if hasattr(username, 'username'):
            username = username.username
        elif not isinstance(username, (str, int)):
            username = str(username)

        # 检查用户是否存在
        if username not in self.allowed_users:
            logging.error(f"用户 {username} 不在允许的用户列表中，无法记录翻译使用")
            raise ValueError(f"用户 {username} 不存在")

        # 使用可重入锁确保原子操作
        with self._lock:
            usage_data = self.load_usage_data()
            previous_count = usage_data.get(username, {"translations": 0})["translations"]

            if username not in usage_data:
                usage_data[username] = {"translations": 0}

            usage_data[username]["translations"] += 1
            new_count = usage_data[username]["translations"]

            logging.info(f"记录翻译使用: 用户 {username}, 之前次数: {previous_count}, 现在次数: {new_count}")

            # 保存使用数据，失败时抛出异常
            try:
                self._atomic_save_usage_data(usage_data)
                logging.info(f"翻译使用记录保存成功: 用户 {username}, 总使用次数: {new_count}")
            except Exception as e:
                logging.error(f"保存翻译使用记录失败，数据可能丢失！用户: {username}, 次数: {new_count}, 错误: {str(e)}")
                raise RuntimeError(f"无法保存翻译使用记录: {str(e)}")

            max_translations = self.allowed_users[username]["max_translations"]
            remaining = max_translations - new_count
            logging.info(f"用户 {username} 剩余翻译次数: {remaining}/{max_translations}")

            return remaining

    def get_user_info(self, username):
        """获取用户信息"""
        # 添加类型检查和转换
        if hasattr(username, 'username'):
            username = username.username
        elif not isinstance(username, (str, int)):
            username = str(username)

        if username not in self.allowed_users:
            return None

        user_data = self.allowed_users[username]
        usage_data = self.load_usage_data()
        user_usage = usage_data.get(username, {"translations": 0})
        used_translations = user_usage["translations"]
        max_translations = user_data["max_translations"]
        remaining = max_translations - used_translations

        logging.info(f"获取用户信息: {username}, 已使用 {used_translations}/{max_translations} 次翻译, 剩余 {remaining} 次")

        return {
            "username": username,
            "expiry_date": user_data["expiry_date"],
            "max_translations": max_translations,
            "used_translations": used_translations,
            "remaining_translations": remaining
        }

    def update_user(self, username: str, expiry_date: str = None, max_translations: int = None, password: str = None):
        """更新用户信息"""
        if username not in self.allowed_users:
            return False, "用户不存在"

        if expiry_date:
            self.allowed_users[username]["expiry_date"] = expiry_date
        if max_translations is not None:
            self.allowed_users[username]["max_translations"] = max_translations
        if password:
            self.allowed_users[username]["password"] = password

        # 这里应该持久化到文件或数据库
        # 简化起见，仅在内存中更新
        return True, "更新成功"

    def add_user(self, username: str, password: str, expiry_date: str, max_translations: int):
        """添加新用户"""
        if username in self.allowed_users:
            return False, "用户已存在"

        self.allowed_users[username] = {
            "expiry_date": expiry_date,
            "max_translations": max_translations,
            "password": password
        }

        return True, "添加成功"

    def get_all_users(self):
        """获取所有用户信息"""
        users = []
        usage_data = self.load_usage_data()

        for username in self.allowed_users:
            user_info = self.get_user_info(username)
            if user_info:
                users.append(user_info)

        return users


# ==========================================
# 速率限制器（按用户）
# ==========================================

class RateLimiter:
    """速率限制器 - 按用户控制API调用频率"""

    def __init__(self, max_calls=5, time_window=60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = {}  # {user_id: deque()}

    def is_allowed(self, user_id):
        """检查是否允许调用"""
        # 添加类型检查和转换
        if hasattr(user_id, 'username'):
            user_id = user_id.username
        elif not isinstance(user_id, (str, int)):
            user_id = str(user_id)

        current_time = time.time()

        if user_id not in self.calls:
            self.calls[user_id] = deque()

        user_calls = self.calls[user_id]

        # 清理过期记录
        while user_calls and user_calls[0] < current_time - self.time_window:
            user_calls.popleft()

        if len(user_calls) < self.max_calls:
            user_calls.append(current_time)
            return True, None

        next_available = user_calls[0] + self.time_window
        wait_time = int(max(0, next_available - current_time))
        return False, wait_time

    def reset(self, user_id: str):
        """重置指定用户的限制器"""
        # 添加类型检查和转换
        if hasattr(user_id, 'username'):
            user_id = user_id.username
        elif not isinstance(user_id, (str, int)):
            user_id = str(user_id)

        if user_id in self.calls:
            self.calls[user_id].clear()


# ==========================================
# 文本验证器
# ==========================================

class TextValidator:
    """文本验证器"""

    GEMINI_MAX_CHARS = 30000
    GPTZERO_MAX_CHARS = 25000
    UI_MAX_CHARS = 1000
    GEMINI_MIN_CHARS = 1
    GPTZERO_MIN_CHARS = 250

    @staticmethod
    def _validate_base(text, min_chars, max_chars, api_name):
        if not text or len(text.strip()) == 0:
            return False, "文本不能为空"

        text_length = len(text)

        if text_length < min_chars:
            return False, f"文本过短，{api_name} 要求至少 {min_chars} 字符，当前 {text_length} 字符"

        if text_length > max_chars:
            return False, f"文本过长，{api_name} 限制为 {max_chars} 字符，当前 {text_length} 字符"

        return True, "验证通过"

    @staticmethod
    def validate_for_gemini(text):
        return TextValidator._validate_base(
            text,
            TextValidator.GEMINI_MIN_CHARS,
            TextValidator.GEMINI_MAX_CHARS,
            "Gemini API"
        )

    @staticmethod
    def validate_for_gptzero(text):
        return TextValidator._validate_base(
            text,
            TextValidator.GPTZERO_MIN_CHARS,
            TextValidator.GPTZERO_MAX_CHARS,
            "GPTZero API"
        )


# ==========================================
# 缓存管理（模拟Streamlit缓存）
# ==========================================

class CacheManager:
    """简单的内存缓存管理器"""

    def __init__(self, ttl=3600, max_entries=100):
        self.cache = {}
        self.ttl = ttl
        self.max_entries = max_entries

    def get(self, key):
        """获取缓存"""
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                return entry["value"]
            else:
                del self.cache[key]
        return None

    def set(self, key, value):
        """设置缓存"""
        # 如果缓存满了，删除最旧的条目
        if len(self.cache) >= self.max_entries:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]

        self.cache[key] = {
            "value": value,
            "timestamp": time.time()
        }

    def clear(self):
        """清空缓存"""
        self.cache.clear()


# ==========================================
# 辅助函数
# ==========================================

def generate_safe_hash(text: str, length: int = 12) -> str:
    """生成安全的文本哈希值"""
    try:
        # 使用SHA256生成哈希
        hash_obj = hashlib.sha256(text.encode('utf-8'))
        # 返回指定长度的十六进制字符串（前length个字符）
        return hash_obj.hexdigest()[:length]
    except Exception as e:
        logging.error(f"生成哈希失败: {e}")
        # 回退方案：使用UUID
        return str(uuid.uuid4())[:length]


def contains_annotation(text: str) -> bool:
    """检测文本是否包含批注标记"""
    if not text:
        return False

    # 检查是否有[[...]]格式的批注
    import re
    pattern = r'\[\[([^\]]+)\]\]'
    return bool(re.search(pattern, text))


def extract_annotations(text: str) -> Tuple[str, List[str]]:
    """从文本中提取批注标记"""
    if not text:
        return text, []

    import re
    pattern = r'\[\[([^\]]+)\]\]'

    # 查找所有批注
    annotations = re.findall(pattern, text)

    # 移除批注标记，只保留纯文本
    clean_text = re.sub(pattern, '', text)

    # 清理多余的空白
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    return clean_text, annotations


# ==========================================
# 全局实例（将在main.py中初始化）
# ==========================================

# 注意：全局实例在main.py中创建，这里只导出类定义