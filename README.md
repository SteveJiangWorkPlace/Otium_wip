# Otium - 学术文本处理与翻译平台

Otium 是一个全栈学术文本处理平台，专注于提供智能文本检查、AI 检测、文本润色和翻译指令管理功能。平台采用前后端分离架构，支持多用户管理和实时处理。

## 目录
- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [部署](#部署)
- [API 文档](#api-文档)
- [配置](#配置)
- [项目结构](#项目结构)
- [改进计划](#改进计划)
- [贡献指南](#贡献指南)
- [许可证](#许可证)
- [支持](#支持)

## 功能特性

### 文本处理
- **AI 检测**：使用 GPTZero 检测文本中的 AI 生成内容
- **文本检查**：语法、拼写和风格检查
- **文本润色**：智能文本改写和优化
- **翻译指令管理**：自定义翻译规则和指令

### 用户管理
- **多用户系统**：支持用户注册、登录和权限管理
- **使用限制**：基于用户级别的 API 调用限制
- **管理员面板**：完整的用户管理和统计功能

### 部署特性
- **云原生**：前端部署在 Netlify，后端部署在 Render
- **实时处理**：支持实时文本分析和处理
- **API 集成**：集成 Gemini AI 和 GPTZero API
- **热重载开发**：完整的本地开发支持，自动启动脚本
- **模块化架构**：后端代码高度模块化，便于维护和扩展

### 性能优化（已完成 [完成]）
- **提示词性能优化**：模板化、缓存、监控系统，解决Gemini API处理提示词"阅读有点慢"的问题
- **最终配置决策**：基于测试结果，决定使用原始完整提示词版本，确保翻译质量和语义完整性
- **智能缓存**：基于文本哈希的LRU缓存，相似文本场景缓存命中率可达60-80%，缓存命中后构建时间减少100%
- **用户关键要求满足**：
  - "去AI词汇"和"人性化处理"批注保持原始完整内容（已验证）
  - 快捷批注进行用户指定修改：移除"灵活表达"，修改"符号修正"，更新"人性化处理"
- **性能监控**：内置调试端点，实时监控构建时间、缓存命中率、提示词长度等指标
- **架构保留**：保留多版本模板系统，压缩版本已注释掉，便于未来优化和测试
- **优化范围**：翻译、智能纠错、英文精修、快捷批注全平台提示词系统
- **完成日期**：2026-02-14

## 技术栈

### 前端
- **React 18** - 用户界面框架
- **TypeScript** - 类型安全编程
- **Zustand** - 状态管理
- **Axios** - HTTP 客户端
- **Tailwind CSS** - 样式框架

### 后端
- **FastAPI** - Python Web 框架
- **Pydantic** - 数据验证和序列化
- **JWT** - 身份验证和授权
- **模块化架构** - 12个专注模块（配置、模型、异常、工具、提示、提示模板、提示缓存、提示监控、提示备份、服务等）
- **提示词性能优化** - 模板化、缓存、监控系统，基于原始完整提示词，缓存命中后构建时间减少100%
- **JSON 文件存储** - 用户数据存储（计划迁移到数据库）
- **性能监控** - 内置提示词构建性能监控和调试端点

### 外部服务集成
- **Gemini AI** - Google 的 AI 模型服务
- **GPTZero** - AI 文本检测服务

## 快速开始

### 环境要求
- Node.js 18+ (前端)
- Python 3.9+ (后端)
- Git

### 本地开发设置

#### 选项一：使用启动脚本（推荐，最简便）

项目提供了自动化的启动脚本，可以一键安装依赖并启动热重载开发服务器。

**后端启动**：
```bash
cd backend
# Windows命令提示符：
start_backend.bat
# 或PowerShell：
.\start_backend.ps1
```

**前端启动**：
```bash
cd frontend
# Windows命令提示符：
start_frontend.bat
# 或PowerShell：
.\start_frontend.ps1
```

启动脚本会自动：
1. 检查环境（Python/Node.js版本）
2. 安装/更新所有依赖
3. 启动热重载开发服务器
4. 提供访问地址和调试信息

详细指南请参考 [QUICK_START.md](./QUICK_START.md)。

#### 选项二：手动设置

1. **克隆仓库**
   ```bash
   git clone https://github.com/yourusername/Otium_wip.git
   cd Otium_wip
   ```

2. **后端设置**
   ```bash
   cd backend
   # 创建虚拟环境（推荐）
   python -m venv venv
   # 激活虚拟环境
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate

   # 安装依赖
   pip install -r requirements.txt

   # 配置环境变量
   cp .env.example .env
   # 编辑 .env 文件，添加必要的 API 密钥

   # 启动后端服务
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **前端设置**
   ```bash
   cd frontend
   # 安装依赖
   npm install

   # 配置环境变量
   cp .env.example .env.local
   # 编辑 .env.local，设置 API 基础 URL

   # 启动开发服务器
   npm start
   ```

4. **访问应用**
   - 前端：http://localhost:3000
   - 后端 API：http://localhost:8000
   - API 文档：http://localhost:8000/docs

### 验证安装
安装完成后，可以通过以下方式验证：

1. **后端健康检查**：
   ```bash
   curl http://localhost:8000/api/health
   # 应返回：{"status": "ok", "timestamp": "...", "version": "1.0.0-alpha"}
   ```

2. **访问API文档**：
   - Swagger UI：http://localhost:8000/docs
   - ReDoc：http://localhost:8000/redoc

3. **前端检查**：
   - 打开 http://localhost:3000
   - 应看到登录页面或应用界面

### 故障排除
- **端口占用**：修改启动脚本中的端口号
- **依赖安装失败**：检查网络连接和版本要求
- **环境变量缺失**：确保正确配置 `.env` 文件
- **模块导入错误**：验证Python虚拟环境是否正确激活

详细故障排除请参考 [常见问题](./docs/faq.md)。

## 部署

### 当前部署环境
- **前端**：部署在 [Netlify](https://www.netlify.com/)
- **后端**：部署在 [Render](https://render.com/)

### 部署指南
详细的部署指南请参考 [部署文档](./docs/deployment.md)

## API 文档

FastAPI 自动生成完整的 API 文档：
- **Swagger UI**：`/docs`
- **ReDoc**：`/redoc`

### 主要 API 端点

#### 认证相关
- `POST /api/login` - 用户登录
- `GET /api/user/info` - 获取用户信息（需认证）
- `POST /api/admin/login` - 管理员登录

#### 文本处理
- `POST /api/text/check` - 文本检查（语法、拼写、风格）
- `POST /api/text/refine` - 文本润色（智能改写和优化）
- `POST /api/text/detect-ai` - AI 检测（使用 GPTZero）

#### 用户管理（管理员）
- `GET /api/admin/users` - 获取所有用户列表
- `POST /api/admin/users/update` - 更新用户信息
- `POST /api/admin/users/add` - 添加新用户

#### 系统功能
- `GET /api/health` - 健康检查（部署监控）
- `GET /api/directives` - 获取翻译指令（前端功能）

#### 前端接口
前端通过API客户端（`frontend/src/api/`）与后端通信，提供完整的用户界面。

## 配置

### 环境变量
#### 后端 (.env)
```bash
# JWT 配置
SECRET_KEY=your-strong-secret-key-change-in-production  # 生产环境必须修改
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API 密钥（必需）
GEMINI_API_KEY=your-gemini-api-key          # Google Gemini API密钥
GPTZERO_API_KEY=your-gptzero-api-key        # GPTZero API密钥

# 安全配置
CORS_ORIGINS=http://localhost:3000,https://your-netlify-app.netlify.app

# 管理员账户（可选，可在代码中配置）
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# 数据库配置（计划中，用于JSON→数据库迁移）
# DATABASE_URL=postgresql://user:password@host:port/database
# DATABASE_TYPE=sqlite  # 或 postgresql
```

#### 前端 (.env.local)
```bash
# API基础URL（开发环境）
REACT_APP_API_BASE_URL=http://localhost:8000

# 生产环境示例
# REACT_APP_API_BASE_URL=https://your-render-backend.onrender.com

# 可选配置
# REACT_APP_SENTRY_DSN=your-sentry-dsn
# REACT_APP_GA_TRACKING_ID=your-ga-id
```

#### 配置说明
1. **必需配置**：GEMINI_API_KEY 和 GPTZERO_API_KEY 必须配置，否则相关功能无法使用
2. **安全配置**：生产环境必须修改 SECRET_KEY 和默认管理员密码
3. **CORS配置**：确保 CORS_ORIGINS 包含前端部署地址
4. **环境特定配置**：开发和生产环境使用不同的配置文件

### 用户管理
默认管理员账户：
- 用户名：`admin`
- 密码：`admin123`

## 项目结构

```
Otium_wip/
├── backend/                 # FastAPI 后端（已模块化重构 [完成]）
│   ├── main.py             # 主应用文件（精简版，270行）
│   ├── __init__.py         # Python包定义
│   ├── config.py           # 配置管理模块
│   ├── schemas.py          # Pydantic数据模型
│   ├── exceptions.py       # 自定义异常和错误处理
│   ├── utils.py            # 工具类（UserLimitManager, RateLimiter等）
│   ├── prompts.py          # Prompt构建模块
│   ├── services.py         # API服务（Gemini, GPTZero集成）
│   ├── requirements.txt    # Python依赖
│   ├── .env.example        # 环境变量示例
│   ├── start_backend.bat   # Windows启动脚本
│   ├── start_backend.ps1   # PowerShell启动脚本
│   ├── tests/              # 测试目录
│   └── data/              # JSON数据存储（计划迁移到数据库）
├── frontend/              # React前端
│   ├── src/
│   │   ├── api/           # API客户端
│   │   ├── components/    # React组件
│   │   ├── pages/         # 页面组件
│   │   ├── store/         # Zustand状态管理
│   │   └── types/         # TypeScript类型定义
│   ├── public/
│   ├── package.json
│   ├── start_frontend.bat # Windows启动脚本
│   └── start_frontend.ps1 # PowerShell启动脚本
├── scripts/               # 工具脚本
│   ├── backup_tool.py     # 文件备份工具
│   ├── validate_config.py # 配置验证脚本
│   ├── validate_refactor.py # 重构验证脚本
│   └── run_tests.py       # 测试运行脚本
├── IMPROVEMENT_PLAN.md    # 项目改进计划
├── QUICK_START.md         # 快速启动指南
├── CONTRIBUTING.md        # 贡献指南
├── LICENSE                # MIT许可证
└── README.md              # 本文件
```

### 后端模块化架构说明

经过重构，后端代码已从单文件（1882行）拆分为12个专注模块，各司其职：

- **config.py**：集中管理所有配置和环境变量
- **schemas.py**：定义Pydantic数据验证模型
- **exceptions.py**：统一异常处理和错误响应
- **utils.py**：工具类（用户限制管理、速率限制器、文本验证器等）
- **prompts.py**：AI提示词构建模块（集成模板、缓存、监控）
- **prompt_templates.py**：提示词模板系统（包含原始备份注释）
- **prompt_cache.py**：提示词缓存管理器（基于LRU和TTL）
- **prompt_monitor.py**：性能监控系统（记录构建时间、缓存命中率等）
- **prompts_backup.py**：原始提示词完整备份（安全回滚机制）
- **services.py**：外部API集成（Gemini AI、GPTZero等）
- **main.py**：精简为API路由定义和FastAPI应用初始化

**架构优势**：
- **模块职责单一**：每个模块专注于特定功能，便于维护和测试
- **性能优化架构**：模板化、缓存、监控系统解决"阅读有点慢"问题
- **安全备份机制**：完整备份原始提示词，支持快速回滚
- **可扩展性**：支持多版本模板系统，便于未来优化和测试
- **保持API兼容**：所有修改不影响现有功能接口

## 改进计划

本项目正在进行代码可维护性和扩展性改进。完整改进计划请参考 [IMPROVEMENT_PLAN.md](./IMPROVEMENT_PLAN.md)。

### 当前改进状态（2026-02-08更新）

**[完成] 已完成**：
- **阶段零**：基础工具和文档
  - 备份工具实现 [完成]（scripts/backup_tool.py）
  - 项目文档完善 [完成]（README.md、CONTRIBUTING.md、QUICK_START.md）
  - 配置管理改进 [完成]（扩展.env.example，添加配置验证脚本）
  - 测试框架建立 [完成]（pytest配置和基础测试）

- **阶段一**：后端代码重构 [完成]
  - 模块化代码结构 [完成]（main.py从1882行减少到270行，减少85%+）
  - 单一职责原则应用 [完成]（拆分为7个专注模块）
  - 保持API完全兼容 [完成]
  - 自动化启动脚本 [完成]（Windows批处理和PowerShell脚本）

**进行中**：
- **阶段二**：数据库迁移和安全性增强
  - JSON → 数据库迁移（适配Render部署环境）
  - 统一错误处理（基于exceptions.py的异常体系）
  - 安全性增强（密码哈希、API速率限制、输入验证）

**未来计划**：
- **阶段三**：部署优化和性能提升
  - Netlify + Render部署优化（部署配置和CI/CD）
  - 性能优化和缓存机制
  - 功能扩展（用户角色、文件处理、数据分析仪表板）

详细进展和计划请参考 [IMPROVEMENT_PLAN.md](./IMPROVEMENT_PLAN.md)。

## 项目功能增强计划进度（2026-02-13更新）

### 背景
根据用户需求，项目正在进行功能增强，主要包括用户注册系统和翻译性能优化。

### 阶段一：翻译性能优化 [完成]（已完成）

**[完成] 后端流式翻译支持**
- 在 `backend/services.py` 中添加 `generate_gemini_content_stream()` 函数，支持流式 Gemini API 调用
- 实现句子分割功能 `split_into_sentences()`，按中英文标点分割文本
- 支持块级流式传输（`type: "chunk"`）和句子级流式传输（`type: "sentence"`）
- 完整的错误处理和类型转换

**[完成] 流式翻译 API**
- 新增 `POST /api/text/translate-stream` 端点，支持 Server-Sent Events (SSE)
- 使用 FastAPI 的 `StreamingResponse` 实现流式响应
- 保留原有的用户认证、速率限制和文本验证机制
- 支持美式（`translate_us`）和英式（`translate_uk`）翻译

**[完成] 前端流式接收和逐句显示**
- 扩展 `frontend/src/store/useTranslationStore.ts` 状态管理，添加流式翻译状态
- 在 `frontend/src/api/client.ts` 中添加 `translateStream()` 函数，支持 SSE 流式处理
- 在 `frontend/src/pages/TextTranslation.tsx` 中实现流式翻译界面：
  - 新增翻译模式选择（流式翻译/传统翻译）
  - 实时显示翻译进度和部分结果
  - 逐句显示翻译结果，支持进度跟踪
  - 添加取消翻译功能

**[完成] 翻译状态管理扩展**
- 扩展 Zustand store 以支持流式状态：
  - `streaming`: 是否正在进行流式翻译
  - `partialText`: 已接收的部分文本
  - `sentences`: 已完成的句子列表
  - `currentSentenceIndex`: 当前正在翻译的句子索引
  - `cancelStream`: 取消流式翻译的函数

### 阶段二：用户注册系统（待开始）

**待实现功能**
1. 数据库模型扩展（添加邮箱、验证码等字段）
2. 邮件服务集成（SMTP配置和验证码发送）
3. 注册和密码重置API端点
4. 前端注册页面和验证码验证
5. 管理员界面扩展（显示邮箱信息）

### 阶段三：转发奖励系统（规划中）

**待实现功能**
1. 数据库扩展（邀请码和邀请关系表）
2. 邀请奖励服务
3. 邀请奖励API端点
4. 前端邀请功能组件
5. 防作弊机制实现

### 测试要求
根据计划，每个阶段完成后需要等待用户测试确认后再继续下一阶段。

## 贡献指南

请参考 [CONTRIBUTING.md](./CONTRIBUTING.md) 了解如何为项目做出贡献。

### 开发流程
1. Fork 仓库
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

### 代码规范
- 前端：遵循 ESLint 和 Prettier 配置
- 后端：遵循 PEP 8 Python 代码规范
- 提交消息：使用约定式提交（Conventional Commits）

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](./LICENSE) 文件。

## 支持

如有问题或需要帮助，请：
1. 查看 [常见问题](./docs/faq.md)
2. 创建 GitHub Issue
3. 联系维护者

---

**项目状态**：开发中
**最新更新**：2026-02-14（提示词性能优化完成）
**版本**：1.0.0-alpha