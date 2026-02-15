# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Otium 是一个全栈学术文本处理平台，专注于智能文本检查、AI 检测、文本润色和翻译指令管理功能。平台采用前后端分离架构，支持多用户管理和实时处理。

## 文档引用

**开始优化时的重要文档**：
1. **README.md** - 快速熟悉项目：包含项目概述、功能特性、技术栈、快速开始指南和项目结构
2. **OPTIMIZATION_GUIDE.md** - 了解用户要求：包含文档更新要求、UTF-8编码的PowerShell启动指令、单元测试检查要求等
3. **MANUAL_STARTUP.md** - 手动启动前后端：包含完全手动启动指令、虚拟环境配置、端口占用检查、热重载设置等

**关键要求**：
- 每次优化后需同步更新相关文档（CONTRIBUTING.md、README.md、CLAUDE.md）
- 使用UTF-8编码的PowerShell启动指令避免乱码：`$OutputEncoding = [System.Text.Encoding]::UTF8`
- **每次新增功能后必须检查并补充相应的单元测试**
- 手动启动时参考MANUAL_STARTUP.md，检查端口占用并寻找空闲端口

## 技术栈

### 前端
- **React 18** + **TypeScript** - 用户界面框架
- **Zustand** - 状态管理（每个功能模块有独立的store）
- **Axios** - HTTP客户端（封装在 `frontend/src/api/client.ts`）
- **模块化CSS** - 样式系统
- **全局进度管理** - 通过 `useGlobalProgressStore` 管理跨页面任务进度

### 后端
- **FastAPI** - Python Web框架
- **Pydantic** - 数据验证和序列化
- **模块化架构** - 11个专注模块（config, schemas, exceptions, utils, prompts, prompt_templates, prompt_cache, prompt_monitor, prompts_backup, services, main）
- **提示词性能优化** - 模板化、缓存、监控系统，提示词长度减少70%，构建时间减少80%+
- **JWT认证** - 用户身份验证和授权
- **流式API** - 支持Server-Sent Events (SSE) 的流式翻译和文本修改
- **性能监控** - 内置提示词构建性能监控和调试端点

### 外部服务集成
- **Gemini AI** - Google的AI模型服务
- **GPTZero** - AI文本检测服务

## 架构概览

Otium采用前后端分离架构，前端React应用通过REST API和SSE流式连接与后端FastAPI服务通信。核心架构特点：

### 后端模块化设计
- **配置管理** (`config.py`)：集中管理环境变量和设置
- **数据验证** (`schemas.py`)：Pydantic模型定义API请求/响应格式
- **异常处理** (`exceptions.py`)：统一错误处理和HTTP异常
- **工具类** (`utils.py`)：用户限制管理、速率限制、文本验证
- **提示词系统** (`prompts.py`, `prompt_templates.py`, `prompt_cache.py`, `prompt_monitor.py`)：模板化、缓存、监控的提示词构建系统
- **API服务** (`services.py`)：集成Gemini AI和GPTZero外部API
- **主应用** (`main.py`)：API路由定义和FastAPI应用初始化

### 前端状态管理
- **模块化Zustand stores**：每个功能（认证、翻译、纠错、检测、修改）有独立store
- **全局进度状态** (`useGlobalProgressStore`)：管理跨页面任务进度，显示全局进度条
- **持久化**：Zustand persist中间件保持用户状态

### API通信模式
- **传统REST API**：用于用户认证、文本检查、AI检测等同步操作
- **流式SSE API**：用于翻译和文本修改，支持逐句显示结果
- **认证**：JWT令牌通过Authorization头传递
- **错误处理**：统一错误响应格式，前端自动处理令牌刷新

### 数据流
1. 用户在前端页面输入文本并选择选项
2. 前端调用对应API（传统或流式）
3. 后端验证请求、检查用户限制、构建提示词（可能使用缓存）
4. 调用外部AI服务（Gemini/GPTZero）
5. 处理结果并返回给前端
6. 前端更新状态并显示结果，全局进度条显示任务状态

## 项目结构

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
│   ├── services.py         # 外部API集成（Gemini, GPTZero）
│   ├── requirements.txt    # Python依赖
│   ├── start_backend.bat   # Windows启动脚本
│   └── start_backend.ps1   # PowerShell启动脚本
├── frontend/               # React前端
│   ├── src/
│   │   ├── api/            # API客户端（基于Axios的封装）
│   │   ├── components/     # React组件
│   │   │   ├── ui/         # 通用UI组件（Button, Card, Textarea等）
│   │   │   ├── layout/     # 布局组件（AppLayout, Sidebar）
│   │   │   └── GlobalProgressBar/ # 全局进度条组件
│   │   ├── pages/          # 页面组件
│   │   │   ├── TextCorrection.tsx      # 智能纠错页面
│   │   │   ├── TextTranslation.tsx     # 文本翻译页面
│   │   │   ├── TextModification.tsx    # 文本修改页面
│   │   │   └── AIDetectionPage.tsx     # AI检测页面
│   │   ├── store/          # Zustand状态管理
│   │   │   ├── useAuthStore.ts         # 认证状态
│   │   │   ├── useGlobalProgressStore.ts # 全局进度状态（新增）
│   │   │   ├── useCorrectionStore.ts   # 纠错状态
│   │   │   ├── useTranslationStore.ts  # 翻译状态
│   │   │   ├── useModificationStore.ts # 文本修改状态
│   │   │   └── useDetectionStore.ts    # AI检测状态
│   │   └── types/          # TypeScript类型定义
│   ├── package.json
│   ├── start_frontend.bat  # Windows启动脚本
│   └── start_frontend.ps1  # PowerShell启动脚本
└── README.md               # 项目详细文档
```

## 开发工作流

### 启动开发服务器

#### 使用启动脚本（推荐）
**后端（FastAPI）**：
```bash
cd backend
# Windows命令提示符
start_backend.bat
```

```powershell
# PowerShell（使用UTF-8编码避免乱码）
$OutputEncoding = [System.Text.Encoding]::UTF8
cd backend
.\start_backend.ps1
```

**前端（React）**：
```bash
cd frontend
# Windows命令提示符
start_frontend.bat
```

```powershell
# PowerShell（使用UTF-8编码避免乱码）
$OutputEncoding = [System.Text.Encoding]::UTF8
cd frontend
.\start_frontend.ps1
```

后端将在 http://localhost:8000 启动（自动重载），前端将在 http://localhost:3000 启动（热重载）。

#### 手动启动（备用方式）
如果端口被占用或需要自定义配置，参考 `MANUAL_STARTUP.md` 进行手动启动：

**后端手动启动**：
```powershell
$OutputEncoding = [System.Text.Encoding]::UTF8
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**前端手动启动**：
```powershell
$OutputEncoding = [System.Text.Encoding]::UTF8
cd frontend
npm install
npm start
```

### 构建项目

#### 前端生产构建
```bash
cd frontend
npm run build
```
构建产物位于 `frontend/build/` 目录。

#### 后端依赖安装
```bash
cd backend
pip install -r requirements.txt
```

### 测试

**重要**：每次新增功能后必须检查并补充相应的单元测试。

#### 后端测试
```bash
cd backend
pytest                          # 运行所有测试
pytest tests/test_health.py     # 运行单个测试文件
pytest -v                       # 详细输出
pytest --cov=. --cov-report=html  # 生成覆盖率报告
```

#### 前端测试
```bash
cd frontend
npm test                       # 运行所有测试
npm test -- --testNamePattern="特定测试"  # 运行匹配的测试
```

#### 使用测试脚本
项目提供了 `scripts/run_tests.py` 脚本，支持更多测试选项：
```bash
cd backend
python ../scripts/run_tests.py              # 运行所有测试
python ../scripts/run_tests.py --unit       # 只运行单元测试
python ../scripts/run_tests.py --coverage   # 运行测试并生成覆盖率报告
python ../scripts/run_tests.py --health     # 只运行健康检查
```

### 数据库迁移
项目使用 Alembic 进行数据库迁移（计划迁移到数据库，目前为 JSON 文件存储）：

```bash
cd backend
alembic upgrade head      # 应用所有迁移
alembic revision --autogenerate -m "描述"  # 创建新迁移
alembic current           # 查看当前迁移版本
```

### 调试和监控

#### 提示词性能监控
提示词性能优化系统提供了监控端点：
- `GET /api/debug/prompt-metrics` - 查看性能指标（构建时间、缓存命中率等）
- `POST /api/debug/prompt-cache/clear` - 清空提示词缓存

#### 后端 API 文档
- Swagger UI：http://localhost:8000/docs
- ReDoc：http://localhost:8000/redoc

#### 验证配置
```bash
cd backend
python verify_final_config.py      # 验证提示词系统配置
python final_system_test.py        # 运行系统测试
```

### 脚本工具
`scripts/` 目录提供了多个实用脚本：
- `backup_tool.py` - 文件备份工具
- `validate_config.py` - 配置验证脚本
- `validate_refactor.py` - 重构验证脚本
- `run_tests.py` - 测试运行脚本（如上所述）
- `check_deployment.py` - 部署检查脚本

## 关键架构模式

### 状态管理
- 使用Zustand进行状态管理，每个主要功能有独立的store
- 新增 `useGlobalProgressStore` 用于管理跨页面的任务进度状态
- 状态持久化通过Zustand的persist中间件实现

### 全局进度系统
- 所有长时间运行的任务（翻译、纠错、AI检测、文本修改）通过全局进度条显示状态
- 进度条位于每个功能页面的workspaceContainer顶部
- 进度消息支持动态点号动画（...）
- 进度状态包括：任务类型、消息内容、可见性、点号动画状态

### API客户端
- 封装在 `frontend/src/api/client.ts`
- 支持传统API调用和流式SSE调用
- 自动处理JWT令牌、错误处理和用户认证
- 流式API使用Generator模式，支持进度回调

### 流式处理
- 翻译和文本修改支持流式处理，逐句显示结果
- 使用Server-Sent Events (SSE) 实现
- 前端通过 `StreamingResponse` 和 `EventSource` 处理流式数据
- 支持取消操作和错误处理

### 组件设计
- UI组件位于 `frontend/src/components/ui/`
- 遵循组合模式，提供一致的API
- Button组件已修改：loading状态只禁用按钮，不显示加载动画（符合最新UI要求）
- 全局进度条组件：`GlobalProgressBar` 显示在所有功能页面相同位置

## 页面结构

所有功能页面遵循相同布局：
1. AppLayout提供侧边栏导航
2. 页面容器包含workspaceContainer和可选的AIChatPanel
3. workspaceContainer顶部显示GlobalProgressBar
4. 主要内容区域（输入、选项、结果显示）

## 重要配置

### 环境变量
- 后端：`backend/.env` (参考 `.env.example`)
  - `GEMINI_API_KEY`、`GPTZERO_API_KEY` 必需
  - `SECRET_KEY` JWT密钥
- 前端：`frontend/.env.local` (参考 `.env.example`)
  - `REACT_APP_API_BASE_URL` API基础URL

### 用户管理
- 默认管理员：`admin` / `admin123`
- 用户限制通过 `UserLimitManager` 管理每日API调用次数

## 最近UI修改（2026-02-13及2026-02-15）

1. **取消所有"执行中，请稍后"提示**：
   - 移除了所有页面的loadingMessage组件
   - 改为使用全局进度条显示任务状态

2. **按钮加载状态修改**：
   - Button组件的loading属性不再显示加载动画
   - 只应用disabled状态，保持按钮形状大小和位置不变

3. **全局进度条系统**：
   - 新增 `useGlobalProgressStore` 状态管理
   - 新增 `GlobalProgressBar` 组件
   - 进度条显示在所有功能页面的workspaceContainer顶部
   - 支持任务类型识别和点号动画

4. **进度消息格式**：
   - 运行中：`"{任务名称}运行中，请稍后..."`
   - 完成：`"{任务名称}完成"`
   - 错误：`"{任务名称}错误: {错误信息}"`
   - 取消：`"{任务名称}已取消"`

5. **侧边栏优化（2026-02-15）**：
   - 移除侧边栏API密钥输入功能，后续通过环境变量配置
   - 登出图标替换为自定义logout.svg，使用fill="#000000"确保主题黑色填充
   - 登出图标放大至20px，按钮尺寸增至32px
   - 登出按钮对齐至侧边栏右侧（justify-content: flex-end）
   - 按钮背景与侧边栏底色一致（var(--color-gray-50)）
   - 侧边栏宽度从224px扩大至280px
   - 菜单项整体下移，通过增加.nav的padding-top至var(--spacing-12)实现与右侧工作区标题对齐
   - 用户信息（用户名、翻译次数、AI检测次数）从侧边栏移除（移至工作区右上角）

6. **工作区用户信息图标（2026-02-15）**：
   - 在工作区右上角（gemini图标上方，与全局状态栏高度齐平）添加圆形用户信息图标
   - 图标填充色为var(--color-gray-900)（主题黑色/深灰色），字体为白色
   - 图标内容为当前用户名的前两个字母大写
   - 点击图标显示弹出框，包含用户名、角色、今日翻译次数和AI检测次数
   - 在所有功能页面添加顶部状态栏区域（.topBarContainer），包含GlobalProgressBar和用户信息图标
   - 已修改的页面：TextCorrection.tsx、TextTranslation.tsx、AIDetectionPage.tsx、TextModification.tsx
   - 对应的CSS样式已添加到各页面的.module.css文件中

## 代码规范

### 前端
- TypeScript严格模式
- 组件使用函数式组件和React Hooks
- CSS模块化，变量通过CSS自定义属性定义
- 导入顺序：React → 外部库 → 内部模块 → 样式

### 后端
- PEP 8代码规范
- 类型提示（Type Hints）
- 模块化设计，单一职责原则
- 异常统一通过 `exceptions.py` 处理

## 故障排查

### 常见问题
1. **端口占用**：修改启动脚本中的端口号
2. **API密钥缺失**：确保 `.env` 文件正确配置
3. **CORS错误**：检查后端 `CORS_ORIGINS` 配置是否包含前端地址
4. **模块导入错误**：确保Python虚拟环境已激活

### 调试建议
- 后端API文档：http://localhost:8000/docs
- 前端React开发者工具
- 浏览器网络面板查看API请求

## 提示词性能优化系统（最终配置）

### 系统概述
提示词性能优化系统通过模板化、缓存和监控解决Gemini API处理提示词"阅读有点慢"的问题。根据用户最终决策，系统采用以下配置：
1. **所有主要提示词使用生产版本**：基于原始完整版本，确保翻译质量和语义完整性
2. **快捷批注使用修改后的原始版本**：进行用户指定的修改（移除"灵活表达"，修改"符号修正"，更新"人性化处理"）
3. **保留缓存机制和性能监控**：提升系统性能，提供可观测性
4. **保留多版本模板架构**：压缩版本已注释掉，便于未来优化和测试

### 核心特性
1. **生产稳定性优先**：
   - 使用原始完整提示词版本作为生产版本，确保100%语义完整性
   - 所有核心翻译指导原则、纠错规则、精修指令完整保留
   - 压缩版本模板已注释掉，保留架构便于未来优化

2. **智能缓存系统**：
   - 基于文本哈希的LRU缓存，最大1000条目，TTL 1小时
   - 缓存命中后构建时间减少100%（< 1ms）
   - 相似文本场景缓存命中率可达60-80%

3. **性能监控系统**：
   - 实时监控构建时间、缓存命中率、提示词长度
   - 调试端点：`/api/debug/prompt-metrics`, `/api/debug/prompt-cache/clear`
   - 低开销装饰器实现，不影响生产性能

4. **用户特定修改**：
   - "去AI词汇"批注：保持632字符原始完整内容
   - "人性化处理"批注：使用用户提供的新版本（融入原始例子）
   - "符号修正"批注：修改为"确保标点符号在引号外，同时用分号连接两个关系紧密的独立从句"
   - "灵活表达"批注：已从快捷批注系统中移除

### 配置文件（生产环境）
```python
# backend/prompts.py
PRODUCTION_TEMPLATE_VERSION = "production"           # 生产版本（基于原始版本）
DEFAULT_TEMPLATE_VERSION = PRODUCTION_TEMPLATE_VERSION  # 智能纠错使用生产版本
TRANSLATION_TEMPLATE_VERSION = PRODUCTION_TEMPLATE_VERSION  # 学术翻译使用生产版本
ENGLISH_REFINE_TEMPLATE_VERSION = PRODUCTION_TEMPLATE_VERSION  # 英文精修使用生产版本
DEFAULT_ANNOTATIONS_VERSION = "original_modified"  # 快捷批注使用修改后的原始版本
```

### 快捷批注修改详情
**"original_modified" 版本包含以下修改**：
1. **移除的批注**："灵活表达"完全移除
2. **修改的批注**：
   - "符号修正"：修改为"确保标点符号在引号外，同时用分号连接两个关系紧密的独立从句"
   - "人性化处理"：使用用户提供的新版本（融入原始例子）
3. **保持原始的批注**：
   - "去AI词汇"：保持632字符原始完整内容
   - 其他批注：基于原始版本

### 性能指标
- **构建时间**：缓存命中时减少100%（< 1ms）
- **缓存命中率**：相似文本场景可达60-80%
- **系统开销**：监控系统开销极小
- **可扩展性**：支持多版本模板架构（压缩版本已注释掉，便于未来优化）

### 维护与调试
1. **查看性能指标**：访问 `http://localhost:8000/api/debug/prompt-metrics`
2. **清空缓存**：POST `http://localhost:8000/api/debug/prompt-cache/clear`
3. **验证配置**：运行 `backend/verify_final_config.py` 验证系统配置是否正确
4. **切换模板版本**：修改 `DEFAULT_TEMPLATE_VERSION`（可选：`"production"`或`"original"`）
5. **回滚机制**：
   - 使用 `prompts_backup.py` 中的原始函数
   - 修改配置常量切换版本
   - 系统支持快速回滚到原始提示词

### 验证与测试
1. **配置验证**：
   ```bash
   cd backend
   python verify_final_config.py
   ```
2. **系统测试**：
   ```bash
   cd backend
   python final_system_test.py
   ```
3. **查看当前提示词**：
   - `backend/current_prompts_list.txt`：包含所有实际使用的提示词
   - `backend/FINAL_CONFIGURATION_SUMMARY.md`：最终配置总结报告

## 扩展开发

### 添加新功能页面
1. 在 `frontend/src/pages/` 创建新页面组件
2. 在 `frontend/src/store/` 创建对应的状态管理
3. 在 `frontend/src/types/` 添加类型定义
4. 在 `backend/main.py` 添加API端点
5. 在 `backend/schemas.py` 添加Pydantic模型
6. 在侧边栏添加导航链接

### 修改UI组件
- UI组件位于 `frontend/src/components/ui/`
- 修改后需测试所有使用该组件的页面
- 保持API向后兼容

### 添加新的AI服务
1. 在 `backend/services.py` 添加服务类
2. 在 `backend/prompts.py` 添加提示词模板
3. 在 `backend/main.py` 添加API端点
4. 在前端API客户端添加对应方法