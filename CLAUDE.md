# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Otium 是一个全栈学术文本处理平台，专注于智能文本检查、AI 检测、文本润色和翻译指令管理功能。平台采用前后端分离架构，支持多用户管理和实时处理。

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
- **模块化架构** - 7个专注模块（config, schemas, exceptions, utils, prompts, services, main）
- **JWT认证** - 用户身份验证和授权
- **流式API** - 支持Server-Sent Events (SSE) 的流式翻译和文本修改

### 外部服务集成
- **Gemini AI** - Google的AI模型服务
- **GPTZero** - AI文本检测服务

## 项目结构

```
Otium/
├── backend/                 # FastAPI后端
│   ├── main.py             # 主应用文件（API路由定义）
│   ├── config.py           # 配置管理
│   ├── schemas.py          # Pydantic数据模型
│   ├── exceptions.py       # 自定义异常处理
│   ├── utils.py            # 工具类（UserLimitManager, RateLimiter等）
│   ├── prompts.py          # AI提示词构建
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

#### 后端（FastAPI）
```bash
cd backend
# Windows命令提示符
start_backend.bat
# 或PowerShell
.\start_backend.ps1
```

后端将在 http://localhost:8000 启动，自动重载。

#### 前端（React）
```bash
cd frontend
# Windows命令提示符
start_frontend.bat
# 或PowerShell
.\start_frontend.ps1
```

前端将在 http://localhost:3000 启动，热重载。

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

#### 后端测试
```bash
cd backend
pytest
```

#### 前端测试
```bash
cd frontend
npm test
```

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

## 最近UI修改（2026-02-13）

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