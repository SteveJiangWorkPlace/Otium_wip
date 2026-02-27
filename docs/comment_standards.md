# 项目注释规范化标准

## 概述

本文档定义了Otium项目的注释规范，旨在提高代码可读性、一致性和可维护性。规范基于项目当前现状，针对中文开发团队优化。

## 核心原则

1. **只修改注释，不修改代码逻辑**：所有注释规范化工作不得改变代码执行逻辑
2. **渐进式修改**：逐个文件进行，确保可回滚
3. **验证优先**：每次修改后运行测试验证功能
4. **规范统一**：建立并遵循一致的注释标准

## Python注释规范

### 1. 文件头注释

每个Python文件应在开头添加模块文档字符串（docstring）：

```python
"""
模块名称：main.py
功能描述：FastAPI主应用文件，包含所有API路由定义
创建时间：2026-02-27
作者：项目团队
版本：1.0.0
"""
```

**要求**：
- 使用三引号docstring格式
- 包含模块名称、功能描述、创建时间、作者、版本
- 对于工具脚本，可添加使用说明

### 2. 函数/方法文档字符串

所有公开函数、方法必须有完整的docstring：

```python
def function_name(param1: type, param2: type) -> return_type:
    """函数功能描述

    Args:
        param1: 参数1描述
        param2: 参数2描述

    Returns:
        返回值描述

    Raises:
        ExceptionType: 异常情况描述

    Examples:
        >>> function_name(value1, value2)
        expected_result

    Notes:
        额外说明或注意事项
    """
```

**要求**：
- 私有方法（以`_`开头）可简化描述
- 包含参数、返回值、异常说明
- 复杂函数应包含示例
- 使用中文描述

### 3. 类文档字符串

所有类必须有类级别docstring：

```python
class ClassName:
    """类功能描述

    类的详细说明，包括：
    - 主要功能
    - 设计考虑
    - 使用示例
    """

    def __init__(self, param: type):
        """初始化实例

        Args:
            param: 参数描述
        """
```

### 4. 行内注释

```python
# 注释内容，解释代码意图或注意事项
variable = value  # 简短说明，与代码同行时使用
```

**规则**：
- 使用中文注释
- 解释"为什么"而不是"做什么"
- 避免显而易见的注释（如`# 设置变量`）
- 复杂逻辑需要详细注释
- 注释在代码行上方，简短说明可在同行

### 5. 区块分隔注释

```python
# ==================== 用户认证API ====================
# 或者更简洁的格式
# --- 用户认证API ---
```

**规则**：
- 用于分隔功能模块
- 保持一致性，整个文件使用相同格式
- 建议使用`# ====================`格式

### 6. TODO/FIXME标记

```python
# TODO: [作者] [YYYY-MM-DD] 需要实现的功能描述
# FIXME: [作者] [YYYY-MM-DD] 需要修复的问题描述
# XXX: [作者] [YYYY-MM-DD] 需要注意的代码
# HACK: [作者] [YYYY-MM-DD] 临时解决方案说明
# BUG: [作者] [YYYY-MM-DD] 已知bug描述
```

**规则**：
- 必须包含作者和日期
- 描述要具体可操作
- 定期清理已解决的标记

### 7. 调试代码处理

**应移除**：
- 长期不用的调试代码
- 已废弃的临时解决方案
- 无关的导入语句

**可保留**：
- 有参考价值的调试示例
- 重要的历史记录
- 使用日志级别控制而非注释掉

## TypeScript/React注释规范

### 1. 文件头注释

```typescript
/**
 * 文件名称：App.tsx
 * 功能描述：React主应用组件，包含路由和全局布局
 * 创建时间：2026-02-27
 * 作者：项目团队
 * 版本：1.0.0
 */
```

### 2. React组件注释

```typescript
/**
 * 组件名称：TextCorrection
 * 功能描述：文本纠错页面组件，提供文本输入、纠错选项和结果显示
 *
 * @param {Object} props - 组件属性
 * @param {string} props.initialText - 初始文本内容
 * @param {boolean} props.autoFocus - 是否自动聚焦输入框
 * @returns {JSX.Element} 渲染的组件
 *
 * @example
 * <TextCorrection initialText="示例文本" autoFocus={true} />
 */
const TextCorrection: React.FC<TextCorrectionProps> = ({ initialText, autoFocus }) => {
```

### 3. 函数/方法注释

```typescript
/**
 * 函数功能描述
 *
 * @param {string} param1 - 参数1描述
 * @param {number} param2 - 参数2描述，默认值说明
 * @returns {ReturnType} 返回值描述
 * @throws {ErrorType} 异常情况描述
 */
function functionName(param1: string, param2: number = 0): ReturnType {
```

### 4. 接口/类型注释

```typescript
/**
 * 用户认证信息接口
 */
interface AuthInfo {
  /** 用户ID */
  userId: string;
  /** 用户名 */
  username: string;
  /** 用户角色：user或admin */
  role: 'user' | 'admin';
  /** JWT令牌 */
  token: string;
}
```

### 5. 行内注释

```typescript
// 注释内容，解释代码意图或注意事项
const variable = value; // 简短说明，与代码同行时使用
```

### 6. 区块分隔注释

```typescript
// ==================== 用户认证逻辑 ====================
// 或者更简洁的格式
// --- 用户认证逻辑 ---
```

### 7. TODO/FIXME标记

```typescript
// TODO: [作者] [YYYY-MM-DD] 需要实现的功能描述
// FIXME: [作者] [YYYY-MM-DD] 需要修复的问题描述
// XXX: [作者] [YYYY-MM-DD] 需要注意的代码
```

## 清理标准

### 需要移除的注释

1. **被注释掉的代码**：
   - 长期不用的调试代码
   - 废弃功能代码
   - 无关的导入语句

2. **冗余注释**：
   - 描述明显代码行为的注释
   - 重复的注释内容
   - 过于简单的注释（如`// 设置变量`）

3. **过时注释**：
   - 与当前代码逻辑不符的注释
   - 引用已删除功能的注释
   - 过时的配置说明

### 需要保留的注释

1. **业务逻辑解释**：
   - 复杂算法说明
   - 业务规则解释
   - 特殊处理逻辑

2. **设计决策**：
   - 架构选择原因
   - 技术选型考虑
   - 性能优化策略

3. **外部依赖说明**：
   - 第三方API的特殊处理
   - 外部服务的限制
   - 集成注意事项

4. **安全警告**：
   - 安全相关的注意事项
   - 权限检查说明
   - 敏感数据处理

5. **性能优化**：
   - 性能关键代码的解释
   - 缓存策略说明
   - 优化技巧

## 实施指南

### 修改顺序

1. **Python后端**：
   ```
   1. main.py (核心应用文件)
   2. api_services.py (AI服务集成)
   3. config.py (配置管理)
   4. prompts.py (提示词系统)
   5. models/ (数据库模型)
   6. utils.py (工具类)
   7. 其他Python文件
   ```

2. **TypeScript前端**：
   ```
   1. client.ts (API客户端)
   2. App.tsx (主应用组件)
   3. pages/ (页面组件)
   4. store/ (状态管理)
   5. components/ui/ (UI组件)
   6. utils/ (工具函数)
   7. 其他TypeScript文件
   ```

### 验证方法

1. **代码逻辑验证**：
   ```bash
   git diff --word-diff  # 检查只修改了注释
   ```

2. **功能测试**：
   ```bash
   # 后端测试
   cd backend && pytest

   # 前端测试
   cd frontend && npm test
   ```

3. **注释质量检查**：
   - 检查公开函数是否有docstring/JSDoc
   - 检查类是否有类级别注释
   - 检查复杂逻辑是否有行内注释
   - 检查TODO/FIXME标记格式

### 自动化工具建议

1. **Python检查工具**：
   ```bash
   # 使用pydocstyle检查docstring规范
   pydocstyle .

   # 使用flake8检查注释相关规则
   flake8 --select=D,E,W
   ```

2. **TypeScript检查工具**：
   ```bash
   # ESLint JSDoc规则
   npm run lint
   ```

## 示例

### Python完整示例

```python
"""
模块名称：user_service.py
功能描述：用户认证和管理服务
创建时间：2026-02-27
作者：项目团队
版本：1.0.0
"""

import hashlib
from datetime import datetime, timedelta
from typing import Optional

# ==================== 用户认证服务 ====================

class UserService:
    """用户认证和管理服务类

    处理用户注册、登录、验证等操作，使用JWT进行身份验证。
    """

    def __init__(self, db_session):
        """初始化用户服务

        Args:
            db_session: 数据库会话对象
        """
        self.db_session = db_session

    def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """验证用户身份

        Args:
            username: 用户名
            password: 密码（明文）

        Returns:
            dict: 包含用户信息和令牌的字典，验证失败返回None

        Raises:
            ValueError: 当用户名或密码为空时抛出

        Examples:
            >>> service = UserService(session)
            >>> result = service.authenticate_user("admin", "password")
            >>> result["username"]
            'admin'
        """
        # TODO: [张三] [2026-02-27] 添加密码强度检查

        if not username or not password:
            raise ValueError("用户名和密码不能为空")

        # 查询用户信息
        user = self._find_user_by_username(username)

        if not user:
            # 记录认证失败日志
            logging.warning(f"用户认证失败: 用户名 {username} 不存在")
            return None

        # 验证密码（实际使用哈希比较）
        if not self._verify_password(password, user.password_hash):
            return None

        # FIXME: [李四] [2026-02-26] JWT令牌过期时间应配置化
        token_expires = datetime.utcnow() + timedelta(hours=24)

        return {
            "username": user.username,
            "role": user.role,
            "token": self._generate_jwt_token(user.id, token_expires)
        }
```

### TypeScript完整示例

```typescript
/**
 * 文件名称：authApi.ts
 * 功能描述：用户认证API客户端
 * 创建时间：2026-02-27
 * 作者：项目团队
 * 版本：1.0.0
 */

import axios from 'axios';
import { AuthResponse, LoginRequest, RegisterRequest } from '../types/auth';

// ==================== 认证API配置 ====================

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

/**
 * 用户登录函数
 *
 * @param {LoginRequest} credentials - 登录凭据
 * @returns {Promise<AuthResponse>} 认证响应
 * @throws {Error} 网络错误或认证失败
 *
 * @example
 * const result = await login({ username: 'admin', password: 'password' });
 * console.log(result.token); // JWT令牌
 */
export async function login(credentials: LoginRequest): Promise<AuthResponse> {
  // XXX: [王五] [2026-02-26] 需要考虑处理网络超时

  try {
    const response = await axios.post<AuthResponse>(
      `${API_BASE_URL}/api/login`,
      credentials
    );

    // 保存令牌到localStorage
    if (response.data.token) {
      localStorage.setItem('auth_token', response.data.token);
      localStorage.setItem('user_info', JSON.stringify(response.data));
    }

    return response.data;
  } catch (error) {
    // TODO: [赵六] [2026-02-27] 改进错误处理，提供更友好的错误消息

    if (axios.isAxiosError(error)) {
      throw new Error(`登录失败: ${error.response?.data?.detail || error.message}`);
    }

    throw error;
  }
}

/**
 * 用户注册信息接口
 */
interface UserRegistration {
  /** 用户名，3-20个字符 */
  username: string;
  /** 邮箱地址，用于验证 */
  email: string;
  /** 密码，至少8个字符 */
  password: string;
  /** 确认密码，必须与password一致 */
  confirmPassword: string;
}
```

## 维护与更新

1. **定期检查**：每季度检查一次注释规范执行情况
2. **代码审查**：在代码审查中检查注释质量
3. **团队培训**：新成员入职时培训注释规范
4. **规范更新**：根据团队反馈和技术发展更新规范

## 参考资料

1. [Google Python风格指南](https://google.github.io/styleguide/pyguide.html)
2. [PEP 257 - Docstring约定](https://www.python.org/dev/peps/pep-0257/)
3. [TypeScript JSDoc参考](https://www.typescriptlang.org/docs/handbook/jsdoc-supported-types.html)
4. [React文档最佳实践](https://reactjs.org/docs/jsx-in-depth.html)

---
*最后更新：2026-02-27*