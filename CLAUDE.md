# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Otium 是一个全栈学术文本处理平台，专注于智能文本检查、AI检测、文本润色和翻译指令管理功能。平台采用前后端分离架构，支持多用户管理和实时处理。

## 开发工作流

### 环境设置

**后端环境：**
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Unix/macOS:
source venv/bin/activate
pip install -r requirements.txt
```

**前端环境：**
```bash
cd frontend
npm install
```

### 启动开发服务器

**后端（FastAPI）：**
```bash
cd backend
# 开发服务器（自动重载）
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 生产服务器（使用gunicorn）
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**前端（React）：**
```bash
cd frontend
# 开发服务器（热重载）
npm start

# 生产构建
npm run build
```

**端口占用处理：**
如果默认端口被占用，可以使用其他端口：
```bash
# 后端使用8001端口
uvicorn main:app --reload --host 0.0.0.0 --port 8001

# 前端使用3001端口（需要修改.env.local中的REACT_APP_API_BASE_URL）
PORT=3001 npm start
```

**生产构建：**
```bash
# 前端
cd frontend
npm run build

# 后端
cd backend
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 代码质量工具

项目配置了完整的代码质量工具链，确保代码风格一致和高质量。

**前端代码质量：**
- **ESLint**：代码检查，配置在 `.eslintrc.js`
- **Prettier**：代码格式化，配置在 `.prettierrc`
- **Husky**：Git钩子，配置在 `.husky/`
- **lint-staged**：提交前检查，配置在 `.lintstagedrc`

```bash
cd frontend
npm run lint          # 检查代码规范
npm run lint:fix      # 自动修复ESLint问题
npm run format:check  # 检查Prettier格式化
npm run format        # 自动格式化代码
```

**后端代码质量：**
- **Black**：代码格式化，配置在 `pyproject.toml`
- **isort**：导入排序，配置在 `pyproject.toml`
- **Flake8**：代码风格检查，配置在 `.flake8`
- **Ruff**：快速代码检查和格式化，配置在 `pyproject.toml`
- **Mypy**：类型检查，配置在 `pyproject.toml`
- **pre-commit**：预提交钩子，配置在 `.pre-commit-config.yaml`

```bash
cd backend
# 运行完整质量检查
python run_quality_checks.py

# 自动修复代码问题
python fix_code_quality.py

# 格式化代码
black .
isort .

# 安装pre-commit钩子
pip install pre-commit
pre-commit install
```

**Git钩子：** 提交时自动运行代码检查：
- **前端**：提交时自动运行lint-staged，检查并修复代码格式
- **后端**：可安装pre-commit钩子自动检查

### 测试

**后端测试：**
```bash
cd backend
pytest                          # 运行所有测试
pytest tests/test_health.py     # 运行单个测试文件
pytest -v                       # 详细输出
pytest --cov=. --cov-report=html  # 生成覆盖率报告

# 使用测试脚本
python ../scripts/run_tests.py              # 运行所有测试
python ../scripts/run_tests.py --unit       # 只运行单元测试
python ../scripts/run_tests.py --coverage   # 运行测试并生成覆盖率报告
python ../scripts/run_tests.py --health     # 只运行健康检查
```

**前端测试：**
```bash
cd frontend
npm test                       # 运行所有测试
npm test -- --testNamePattern="特定测试"  # 运行匹配的测试
```

**重要：** 每次新增功能后必须检查并补充相应的单元测试。测试脚本应避免使用Unicode字符（如✓✗⚠），使用ASCII兼容标记如`[成功]`、`[失败]`、`[警告]`，确保在Windows命令行（GBK编码）下正常运行。

### 数据库迁移

项目使用 SQLite（开发）和 PostgreSQL（生产）支持：
```bash
cd backend
# 初始化数据库
python -c "from models.database import init_database; init_database()"

# 确保管理员用户存在
python -c "from models.database import ensure_admin_user_exists; ensure_admin_user_exists()"

# Alembic 迁移（当配置时）
alembic upgrade head      # 应用所有迁移
alembic revision --autogenerate -m "描述"  # 创建新迁移
```

## 架构概览

### 技术栈

**前端：**
- **React 18** + **TypeScript** - 用户界面框架
- **Zustand** - 状态管理（每个功能模块有独立的store）
- **Axios** - HTTP客户端（封装在 `frontend/src/api/client.ts`）
- **Ant Design** - UI组件库
- **模块化CSS** - 样式系统

**后端：**
- **FastAPI** - Python Web框架
- **Pydantic** - 数据验证和序列化
- **SQLAlchemy** - ORM数据库访问
- **JWT认证** - 用户身份验证和授权
- **模块化架构** - 11个专注模块（config, schemas, exceptions, utils, prompts等）

**外部服务：**
- **Gemini AI** - Google的AI模型服务
- **GPTZero** - AI文本检测服务

### 项目结构

```
Otium/
├── backend/                 # FastAPI后端
│   ├── main.py             # 主应用文件（API路由定义）
│   ├── config.py           # 配置管理
│   ├── schemas.py          # Pydantic数据模型
│   ├── exceptions.py       # 自定义异常处理
│   ├── utils.py            # 工具类（UserLimitManager, RateLimiter等）
│   ├── prompts.py          # AI提示词构建（已优化，集成模板、缓存、监控）
│   ├── prompt_templates.py # 提示词模板系统（包含原始备份）
│   ├── prompt_cache.py     # 提示词缓存管理器
│   ├── prompt_monitor.py   # 性能监控系统
│   ├── prompts_backup.py   # 原始提示词完整备份（安全回滚）
│   ├── api_services.py     # 外部API集成（Gemini, GPTZero）
│   ├── models/             # 数据库模型
│   └── scripts/            # 工具脚本
├── frontend/               # React前端
│   ├── src/
│   │   ├── api/            # API客户端（基于Axios的封装）
│   │   ├── components/     # React组件
│   │   ├── pages/          # 页面组件
│   │   ├── store/          # Zustand状态管理
│   │   └── types/          # TypeScript类型定义
│   ├── package.json
│   └── 其他配置
├── docs/                   # 项目文档
├── scripts/                # 工具脚本
└── data/                   # 数据存储目录
```

### 状态管理系统

前端使用模块化Zustand stores：
- `useAuthStore.ts` - 认证状态
- `useGlobalProgressStore.ts` - 全局进度状态（管理跨页面任务进度）
- `useCorrectionStore.ts` - 纠错状态
- `useTranslationStore.ts` - 翻译状态
- `useModificationStore.ts` - 文本修改状态
- `useDetectionStore.ts` - AI检测状态
- `useAIChatStore.ts` - AI聊天状态

**全局进度系统：** 所有长时间运行的任务通过全局进度条显示状态，位于每个功能页面的workspaceContainer顶部。

### API通信模式

**传统REST API：** 用于用户认证、文本检查、AI检测等同步操作
**流式SSE API：** 用于翻译和文本修改，支持逐句显示结果

**认证：** JWT令牌通过Authorization头传递
**错误处理：** 统一错误响应格式，前端自动处理令牌刷新

### AI集成模式
- **Gemini API调用**：使用gemini-2.5-flash作为主要模型，gemini-2.5-pro作为后备
- **提示词缓存**：基于文本哈希的LRU缓存，最大1000条目，TTL 1小时
- **流式处理**：支持实时响应和进度更新
- **文本验证**：AI处理前进行文本验证和清理
- **API密钥灵活性**：支持环境变量或请求头传递API密钥

### 错误处理系统
- **集中式错误处理**：通过`@api_error_handler`装饰器统一处理异常
- **结构化错误响应**：包含错误代码、消息和详细信息的标准化响应
- **优雅降级**：外部服务不可用时提供替代方案
- **日志记录**：适当级别的全面日志记录

### 数据流

1. 用户在前端页面输入文本并选择选项
2. 前端调用对应API（传统或流式）
3. 后端验证请求、检查用户限制、构建提示词（可能使用缓存）
4. 调用外部AI服务（Gemini/GPTZero）
5. 处理结果并返回给前端
6. 前端更新状态并显示结果，全局进度条显示任务状态

## 关键配置

### 环境变量

**后端（`backend/.env`）：**
- `GEMINI_API_KEY` - Google Gemini API密钥
- `GPTZERO_API_KEY` - GPTZero API密钥
- `SECRET_KEY` / `JWT_SECRET_KEY` - JWT签名密钥
- `DATABASE_TYPE` - "sqlite" 或 "postgresql"
- `DATABASE_URL` - PostgreSQL连接字符串（生产环境）
- `ADMIN_USERNAME` / `ADMIN_PASSWORD` - 管理员凭证
- `RESEND_API_KEY` - 邮件服务API密钥
- `CORS_ORIGINS` - 允许的跨域来源（逗号分隔）

**前端（`frontend/.env.local`）：**
- `REACT_APP_API_BASE_URL` - API基础URL（默认：http://localhost:8000）

### 用户管理

- 默认管理员：`admin` / `admin123`
- 用户限制通过 `UserLimitManager` 管理每日API调用次数
- 邮箱验证注册流程

## 提示词性能优化系统（最终配置）

### 系统概述

提示词性能优化系统通过模板化、缓存和监控解决Gemini API处理提示词"阅读有点慢"的问题。

**核心配置：**
1. **所有主要提示词使用生产版本**：基于原始完整版本，确保翻译质量和语义完整性
2. **快捷批注使用修改后的原始版本**：进行用户指定的修改
3. **保留缓存机制和性能监控**：提升系统性能，提供可观测性
4. **保留多版本模板架构**：压缩版本已注释掉，便于未来优化

### 监控和调试

```bash
# 查看性能指标
curl http://localhost:8000/api/debug/prompt-metrics

# 清空缓存
curl -X POST http://localhost:8000/api/debug/prompt-cache/clear

# 验证配置
cd backend
python verify_final_config.py

# 运行系统测试
python final_system_test.py
```

## 开发说明

### Windows命令行编码注意事项
- **Windows命令行默认使用GBK编码**（代码页936），在编写Python脚本时应避免使用Unicode字符（如✓✗⚠）
- **建议使用ASCII兼容标记**：使用`[成功]`、`[失败]`、`[警告]`代替特殊符号
- **PowerShell UTF-8编码**：为避免乱码，PowerShell启动时设置：`$OutputEncoding = [System.Text.Encoding]::UTF8`
- **测试脚本兼容性**：所有测试脚本应确保在Windows命令行下正常运行

### 前端组件设计

- UI组件位于 `frontend/src/components/ui/`
- 遵循组合模式，提供一致的API
- Button组件：loading状态只禁用按钮，不显示加载动画
- 全局进度条组件：`GlobalProgressBar` 显示在所有功能页面相同位置

### 后端模块化设计

后端采用11个专注模块的模块化设计：
- **配置管理** (`config.py`)：集中管理环境变量和设置，支持开发/生产环境检测
- **数据验证** (`schemas.py`)：Pydantic模型定义API请求/响应格式，确保类型安全
- **异常处理** (`exceptions.py`)：统一错误处理和HTTP异常，提供结构化错误响应
- **工具类** (`utils.py`)：UserLimitManager（用户限制管理）、RateLimiter（速率限制）、TextValidator（文本验证）等
- **提示词系统** (`prompts.py`)：AI提示词构建（已优化，集成模板、缓存、监控）
- **提示词模板** (`prompt_templates.py`)：提示词模板系统（包含原始备份和修改版本）
- **提示词缓存** (`prompt_cache.py`)：基于文本哈希的LRU缓存管理器，提升性能
- **性能监控** (`prompt_monitor.py`)：性能监控系统，跟踪构建时间、缓存命中率
- **原始备份** (`prompts_backup.py`)：原始提示词完整备份，支持安全回滚
- **API服务** (`api_services.py`)：外部API集成（Gemini AI和GPTZero）
- **主应用** (`main.py`)：API路由定义和FastAPI应用初始化

### 最近UI修改（2026-02-18更新）

1. **取消所有"执行中，请稍后"提示**：
   - 移除了所有页面的loadingMessage组件
   - 改为使用全局进度条显示任务状态

2. **按钮加载状态修改**：
   - Button组件的loading属性不再显示加载动画
   - 只应用disabled状态，保持按钮形状大小和位置不变

3. **侧边栏优化**：
   - 移除侧边栏API密钥输入功能，后续通过环境变量配置
   - 登出图标替换为自定义logout.svg，使用fill="#000000"确保主题黑色填充
   - 登出图标放大至20px，按钮尺寸增至32px
   - 登出按钮对齐至侧边栏右侧（justify-content: flex-end）
   - 按钮背景与侧边栏底色一致（var(--color-gray-50)）
   - 侧边栏宽度从224px扩大至280px
   - 菜单项整体下移，通过增加.nav的padding-top至var(--spacing-12)实现与右侧工作区标题对齐

4. **工作区用户信息图标**：
   - 在工作区右上角（gemini图标上方，与全局状态栏高度齐平）添加圆形用户信息图标
   - 图标填充色为var(--color-gray-900)（主题黑色/深灰色），字体为白色
   - 图标内容为当前用户名的前两个字母大写
   - 点击图标显示弹出框，包含用户名、角色、今日翻译次数和AI检测次数
   - 在所有功能页面添加顶部状态栏区域（.topBarContainer），包含GlobalProgressBar和用户信息图标

5. **已修改的页面**：
   - TextCorrection.tsx
   - TextTranslation.tsx
   - AIDetectionPage.tsx
   - TextModification.tsx

### 页面结构

所有功能页面遵循相同布局：
1. AppLayout提供侧边栏导航
2. 页面容器包含workspaceContainer和可选的AIChatPanel
3. workspaceContainer顶部显示GlobalProgressBar
4. 主要内容区域（输入、选项、结果显示）

## 故障排查

### 常见问题

1. **端口占用**：修改启动脚本中的端口号（如 --port 8001）
2. **API密钥缺失**：确保 `.env` 文件正确配置
3. **CORS错误**：检查后端 `CORS_ORIGINS` 配置是否包含前端地址
4. **模块导入错误**：确保Python虚拟环境已激活

### 调试建议

- 后端API文档：http://localhost:8000/docs
- 前端React开发者工具
- 浏览器网络面板查看API请求

## 文档引用

**重要文档**：
- **CLAUDE.md**（本文档）- 开发指南和架构概述
- **backend/CLAUDE.md** - 后端特定开发指南（包含更详细的后端配置）
- **docs/faq.md** - 常见问题解答
- **docs/deployment.md** - 部署文档
- **docs/email_service_setup.md** - 邮件服务设置指南

**文档更新要求**：
- 每次优化后需同步更新相关文档
- 确保文档保持最新状态

## 扩展开发

### 添加新功能页面

1. 在 `frontend/src/pages/` 创建新页面组件
2. 在 `frontend/src/store/` 创建对应的状态管理
3. 在 `frontend/src/types/` 添加类型定义
4. 在 `backend/main.py` 添加API端点
5. 在 `backend/schemas.py` 添加Pydantic模型
6. 在侧边栏添加导航链接

### 添加新的AI服务

1. 在 `backend/api_services.py` 添加服务类
2. 在 `backend/prompts.py` 添加提示词模板
3. 在 `backend/main.py` 添加API端点
4. 在前端API客户端添加对应方法

### 修改UI组件

- UI组件位于 `frontend/src/components/ui/`
- 修改后需测试所有使用该组件的页面
- 保持API向后兼容